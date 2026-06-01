<script setup lang="ts">
import { ref, onMounted, onUnmounted, reactive, watch } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { Download, Document } from '@element-plus/icons-vue'
import { useFolderStore } from '../../store/folder'
import { usePaperStore } from '../../store/paper'
import type { PaperKeyPoints } from '../../types/library'
import type { GraphLink, GraphNode, NodeType } from '../../types/graph'
import GraphNodeDetail from './GraphNodeDetail.vue'
import { fetchSimilarityGraphApi, fetchLLMGraphApi } from '../../api/graph'

// 图谱配置常量
const SIMILARITY_THRESHOLD = 0.35

// 默认分类（用于相似度图谱显示四要素时）
const defaultCategories = [
  { name: '论文', itemStyle: { color: '#4a9d9a' } },
  { name: '研究背景', itemStyle: { color: '#6b8e8e' } },
  { name: '研究方法', itemStyle: { color: '#e8b86d' } },
  { name: '创新点', itemStyle: { color: '#c17767' } },
  { name: '结论', itemStyle: { color: '#4a9d9a' } },
]

// 聚类颜色映射（用于 LLM 图谱）
const clusterColors = ['#4a9d9a', '#e8b86d', '#c17767', '#6b8e8e', '#8b7cb3', '#5a9fd4']

// 关系类型样式映射（用于 LLM 图谱）
const relationStyleMap: Record<string, { color: string; type: 'solid' | 'dashed' | 'dotted'; label: string }> = {
  extends: { color: '#7caf7a', type: 'solid', label: '扩展关系' },
  applies: { color: '#6a9fb5', type: 'solid', label: '应用关系' },
  compares: { color: '#e09d6e', type: 'dashed', label: '对比关系' },
  related: { color: '#b796c9', type: 'dotted', label: '相关关系' },
  semantic: { color: '#9ea9c1', type: 'dashed', label: '语义关联' },
  ownership: { color: 'rgba(120,140,170,0.5)', type: 'solid', label: '归属关系' },
}

const router = useRouter()
const folderStore = useFolderStore()
const paperStore = usePaperStore()
const chartRef = ref<HTMLDivElement | null>(null)
let chartInstance: echarts.ECharts | null = null
const isLoading = ref(false)

// 图谱类型切换：只保留 similarity 和 llm
const graphType = ref<'similarity' | 'llm'>('similarity')

// 节点详情
const nodeDetailVisible = ref(false)
const selectedNodeData = ref<GraphNode | null>(null)

// 相似度图谱专用：四要素独立筛选（默认全部关闭）
const similarityFilters = reactive({
  background: false,
  method: false,
  innovation: false,
  conclusion: false,
})

// 相似度图谱专用缓存（基础论文节点和相似边）
let similarityBaseNodes: GraphNode[] = []
let similarityBaseLinks: GraphLink[] = []
// 相似度缓存键与数据
let similarityCache = { key: '', baseNodes: [] as GraphNode[], baseLinks: [] as GraphLink[] }

// LLM 图谱缓存
let llmCache = { key: '', nodes: [] as GraphNode[], links: [] as GraphLink[], categories: [] as any[] }

// 当前使用的分类（用于图例）
let currentCategories = defaultCategories

// 导出功能所需状态
const isExporting = ref(false)
let currentNodes: GraphNode[] = []
let currentLinks: GraphLink[] = []

// 生成缓存键（文件夹ID + 论文数量）
function getCacheKey() {
  return `${folderStore.currentFolderId || 'all'}_${paperStore.papers.length}`
}

const getSymbolByType = (type: NodeType) => {
  switch (type) {
    case 'background': return 'circle'
    case 'method': return 'rect'
    case 'innovation': return 'diamond'
    case 'conclusion': return 'triangle'
    default: return 'circle'
  }
}

// ---- 从论文数据构建四要素节点（通用） ----
const dimensionConfig: { type: keyof PaperKeyPoints; nodeType: NodeType; label: string; category: number }[] = [
  { type: 'background', nodeType: 'background', label: '研究背景', category: 1 },
  { type: 'method',     nodeType: 'method',     label: '研究方法',  category: 2 },
  { type: 'innovation', nodeType: 'innovation', label: '创新点',    category: 3 },
  { type: 'conclusion', nodeType: 'conclusion', label: '结论',      category: 4 },
]

// 为某篇论文提取指定类型的四要素节点和归属边
function extractElementNodesAndLinks(paperNode: GraphNode, filterTypes?: Set<string>): { nodes: GraphNode[]; links: GraphLink[] } {
  const nodes: GraphNode[] = []
  const links: GraphLink[] = []
  const paperId = paperNode.id
  const paperInfo = paperNode.paperInfo || paperStore.papers.find(p => p.id === paperId)
  if (!paperInfo) return { nodes, links }

  for (const dim of dimensionConfig) {
    if (filterTypes && !filterTypes.has(dim.nodeType)) continue
    const content = paperInfo.keyPoints?.[dim.type]
    if (!content || !content.trim()) continue

    const elemId = `${paperId}_${dim.type}`
    nodes.push({
      id: elemId,
      name: content.length > 15 ? content.substring(0, 15) + '…' : content,
      type: dim.nodeType,
      category: dim.category,
      paperId: paperId,
      paperTitle: paperInfo.title,
      content: content,
      paperInfo: paperInfo,
    })
    links.push({ 
      source: paperId, 
      target: elemId, 
      relationType: 'ownership',
      label: '归属'
    })
  }
  return { nodes, links }
}

// 构建完整的相似度图谱（根据四要素筛选条件）
function buildSimilarityFullGraph(): { nodes: GraphNode[]; links: GraphLink[]; categories: typeof defaultCategories } {
  const allNodes: GraphNode[] = [...similarityBaseNodes]
  const allLinks: GraphLink[] = [...similarityBaseLinks]
  
  const enabledTypes: NodeType[] = []
  if (similarityFilters.background) enabledTypes.push('background')
  if (similarityFilters.method) enabledTypes.push('method')
  if (similarityFilters.innovation) enabledTypes.push('innovation')
  if (similarityFilters.conclusion) enabledTypes.push('conclusion')
  
  if (enabledTypes.length > 0) {
    const filterSet = new Set(enabledTypes)
    for (const paperNode of similarityBaseNodes) {
      const { nodes: elemNodes, links: elemLinks } = extractElementNodesAndLinks(paperNode, filterSet)
      for (const node of elemNodes) {
        if (!allNodes.some(n => n.id === node.id)) allNodes.push(node)
      }
      for (const link of elemLinks) {
        if (!allLinks.some(l => l.source === link.source && l.target === link.target)) allLinks.push(link)
      }
    }
  }

  const categories = [
    { name: '论文', itemStyle: { color: '#4a9d9a' } },
    { name: '研究背景', itemStyle: { color: '#6b8e8e' } },
    { name: '研究方法', itemStyle: { color: '#e8b86d' } },
    { name: '创新点', itemStyle: { color: '#c17767' } },
    { name: '结论', itemStyle: { color: '#4a9d9a' } },
  ]
  return { nodes: allNodes, links: allLinks, categories }
}

// 刷新相似度图谱渲染（根据当前筛选条件）
function refreshSimilarityGraphRender() {
  if (graphType.value !== 'similarity') return
  const { nodes, links, categories } = buildSimilarityFullGraph()
  currentCategories = categories
  renderChart(nodes, links)
}

// ---- 相似度图谱：从后端加载（支持缓存） ----
async function loadSimilarityGraph(forceRefresh = false) {
  isLoading.value = true
  const cacheKey = getCacheKey()
  
  // 尝试使用缓存
  if (!forceRefresh && similarityCache.key === cacheKey && similarityCache.baseNodes.length) {
    similarityBaseNodes = similarityCache.baseNodes
    similarityBaseLinks = similarityCache.baseLinks
    refreshSimilarityGraphRender()
    isLoading.value = false
    return
  }

  try {
    const res: any = await fetchSimilarityGraphApi({
      folder_id: folderStore.currentFolderId,
      max_nodes: 200,
      min_similarity: SIMILARITY_THRESHOLD,
      top_k: 8,
    })
    const payload = res?.data
    
    if (!payload?.nodes?.length) {
      ElMessage.info('暂无已向量的论文，请先确认论文四要素')
      similarityBaseNodes = []
      similarityBaseLinks = []
      renderChart([], [])
      return
    }

    similarityBaseNodes = payload.nodes.map((n: any) => ({
      id: n.id,
      name: n.name,
      type: 'paper' as const,
      category: 0,
      paperInfo: n.paperInfo,
    }))

    similarityBaseLinks = []
    if (payload.links?.length) {
      const nodeIds = new Set(similarityBaseNodes.map(n => n.id))
      for (const link of payload.links) {
        if (!nodeIds.has(link.source) || !nodeIds.has(link.target)) continue
        const similarityMatch = link.label?.match(/相似度\s+([\d.]+)/)
        const similarityValue = similarityMatch ? parseFloat(similarityMatch[1]) : 0
        if (similarityValue >= SIMILARITY_THRESHOLD) {
          similarityBaseLinks.push({
            source: link.source,
            target: link.target,
            relationType: 'semantic',
            reason: similarityValue.toFixed(2),
          })
        }
      }
    }

    // 更新缓存
    similarityCache = { key: cacheKey, baseNodes: similarityBaseNodes, baseLinks: similarityBaseLinks }
    refreshSimilarityGraphRender()

    if (payload?.meta?.reason) {
      const reasonMap: Record<string, string> = {
        no_embeddings: '论文尚未生成向量，需要先完成四要素提取或确认',
        need_two_or_more_for_similarity_edges: '至少需要2篇已向量的论文才能计算相似度',
      }
      const msg = reasonMap[payload.meta.reason as string] || `暂无语义相似边（${payload.meta.reason}）`
      ElMessage.info(msg)
    }
  } catch (e) {
    console.error('[GraphPanel] 加载相似度图谱失败:', e)
    ElMessage.error('加载相似度图谱失败')
  } finally {
    isLoading.value = false
  }
}

// ---- LLM 主题聚类图谱（支持缓存） ----
function assignClusterInitialPositions(nodes: GraphNode[], clusters: any[]) {
  const clusterCount = clusters.length
  if (clusterCount === 0) return

  const baseRadius = Math.min(400, Math.max(250, nodes.length * 1.5))
  const clusterCenters: { angle: number; radius: number; count: number }[] = []
  for (let i = 0; i < clusterCount; i++) {
    const angle = (i / clusterCount) * Math.PI * 2
    const radius = baseRadius * (0.8 + (i % 2) * 0.3)
    clusterCenters.push({ angle, radius, count: 0 })
  }

  nodes.forEach(node => {
    const category = node.category as number
    if (category >= 0 && category < clusterCount) clusterCenters[category].count++
  })

  nodes.forEach(node => {
    const category = node.category as number
    if (category >= 0 && category < clusterCount) {
      const center = clusterCenters[category]
      const angleOffset = (Math.random() - 0.5) * (Math.PI / 4)
      const radiusOffset = (Math.random() - 0.5) * 80
      const finalAngle = center.angle + angleOffset
      const finalRadius = Math.max(20, center.radius + radiusOffset)
      ;(node as any).x = Math.cos(finalAngle) * finalRadius
      ;(node as any).y = Math.sin(finalAngle) * finalRadius
    } else {
      ;(node as any).x = (Math.random() - 0.5) * 500
      ;(node as any).y = (Math.random() - 0.5) * 400
    }
  })
}

async function loadLLMGraph(forceRefresh = false) {
  isLoading.value = true
  const cacheKey = getCacheKey()

  if (!forceRefresh && llmCache.key === cacheKey && llmCache.nodes.length) {
    currentCategories = llmCache.categories
    renderChart(llmCache.nodes, llmCache.links)
    isLoading.value = false
    return
  }

  try {
    const res: any = await fetchLLMGraphApi({
      folder_id: folderStore.currentFolderId,
      max_nodes: 50,
    })
    const payload = res?.data
    
    if (!payload?.nodes?.length) {
      const reason = payload?.meta?.reason || 'no_confirmed_papers'
      if (reason === 'no_confirmed_papers') ElMessage.info('没有已确认的论文，请先确认论文四要素')
      else ElMessage.info('暂无数据')
      renderChart([], [])
      return
    }

    currentCategories = payload.clusters.map((c: any, idx: number) => ({
      name: c.name,
      itemStyle: { color: clusterColors[idx % clusterColors.length] }
    }))

    const nodes: GraphNode[] = payload.nodes.map((n: any) => ({
      id: n.id,
      name: n.name,
      type: 'paper',
      category: n.category,
      paperInfo: n.paperInfo,
    }))

    assignClusterInitialPositions(nodes, payload.clusters)

    const links: GraphLink[] = (payload.links || []).map((l: any) => ({
      source: l.source,
      target: l.target,
      relationType: l.relationType,
      label: l.label,
      reason: l.label,
    }))

    // 更新缓存
    llmCache = { key: cacheKey, nodes, links, categories: currentCategories }
    renderChart(nodes, links)
  } catch (e) {
    console.error('[GraphPanel] 加载 LLM 图谱失败:', e)
    ElMessage.error('加载 LLM 图谱失败')
  } finally {
    isLoading.value = false
  }
}

// ---- 图表渲染 ----
const renderChart = (nodes: GraphNode[], links: GraphLink[]) => {
  // 保存当前数据供导出使用
  currentNodes = nodes
  currentLinks = links

  if (!chartRef.value) return
  if (!chartInstance) chartInstance = echarts.init(chartRef.value)

  const nodeConnCount: Record<string, number> = {}
  links.forEach(l => {
    nodeConnCount[l.source] = (nodeConnCount[l.source] || 0) + 1
    nodeConnCount[l.target] = (nodeConnCount[l.target] || 0) + 1
  })

  const nodeCount = nodes.length
  let forceConfig: any
  if (nodeCount > 50) {
    forceConfig = { repulsion: 1500, gravity: 0.02, edgeLength: [200, 400], friction: 0.7, initIterations: 300, layoutAnimation: true }
  } else if (nodeCount < 20) {
    forceConfig = { repulsion: 800, gravity: 0.05, edgeLength: [150, 250], friction: 0.6, initIterations: 200, layoutAnimation: true }
  } else {
    forceConfig = { repulsion: 1000, gravity: 0.03, edgeLength: [180, 350], friction: 0.65, initIterations: 250, layoutAnimation: true }
  }

  if (graphType.value === 'llm') {
    forceConfig = { ...forceConfig, repulsion: 1200, gravity: 0.02, edgeLength: [180, 400] }
  }

  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e0e6ed',
      borderWidth: 1,
      textStyle: { color: '#333', fontSize: 12, align: 'center' },
      formatter: (params: any) => {
        if (params.dataType === 'edge') {
          if (graphType.value === 'similarity') {
            const similarityValue = params.data.reason
            return `
              <div style="text-align: center; padding: 4px 8px;">
                <div style="font-weight: 600; margin-bottom: 4px;">相似度</div>
                <div style="color: #4a9d9a; font-size: 13px;">${similarityValue || '—'}</div>
              </div>
            `
          }
          // LLM 图谱的边
          const relationType = params.data.relationType
          const typeTitleMap: Record<string, string> = {
            extends: '扩展', applies: '应用', compares: '对比', related: '相关', semantic: '语义关联'
          }
          const relationTitle = typeTitleMap[relationType] || '关联'
          const rawContent = params.data.reason || params.data.label || ''
          let relationContent = rawContent
          if (rawContent.includes('：')) relationContent = rawContent.split('：')[1]
          else if (rawContent.includes(':')) relationContent = rawContent.split(':')[1]
          
          return `
            <div style="text-align: center; padding: 4px 8px;">
              <div style="font-weight: 600; margin-bottom: 4px;">${relationTitle}</div>
              <div style="color: #555; font-size: 12px;">${relationContent || '—'}</div>
            </div>
          `
        }
        // 节点 tooltip（保持不变）
        const typeLabels: Record<string, string> = {
          paper: '📄 论文', background: '🎯 研究背景', method: '⚙️ 研究方法',
          innovation: '💡 创新点', conclusion: '✅ 结论'
        }
        if (params.data.type === 'paper' && params.data.paperInfo) {
          const paper = params.data.paperInfo
          return `
            <div style="padding: 4px 0; max-width: 300px;">
              <div style="font-weight: 600; font-size: 13px; margin-bottom: 6px; line-height: 1.4;">${params.name}</div>
              <div style="color: #666; font-size: 11px; margin-bottom: 2px;">作者: ${paper.authors}</div>
              <div style="color: #666; font-size: 11px; margin-bottom: 2px;">年份: ${paper.year}</div>
              <div style="color: #666; font-size: 11px;">来源: ${paper.source}</div>
            </div>
          `
        }
        return `
          <div style="padding: 4px 0;">
            <div style="font-weight: 600; font-size: 13px; margin-bottom: 4px;">${params.name}</div>
            <div style="color: #666; font-size: 11px;">${typeLabels[params.data.type] || '节点'}</div>
          </div>
        `
      }
    },
    legend: {
      data: currentCategories.map(c => c.name),
      orient: 'vertical', right: 15, top: 15,
      backgroundColor: 'rgba(255,255,255,0.95)', borderRadius: 10, padding: [12, 16],
      textStyle: { fontSize: 12, color: '#555' }, itemWidth: 16, itemHeight: 10, itemGap: 10,
    },
    series: [{
      type: 'graph', layout: 'force',
      data: nodes.map(n => {
        const nodeWithPos = n as any
        return {
          ...n,
          symbol: getSymbolByType(n.type),
          symbolSize: (n.type === 'paper' ? 55 : 38) + Math.min(nodeConnCount[n.id] || 0, 12),
          itemStyle: {
            borderWidth: n.type === 'paper' ? 3 : 2,
            borderColor: n.type === 'paper' ? '#fff' : 'rgba(255,255,255,0.6)',
            shadowBlur: n.type === 'paper' ? 15 : 8,
            shadowColor: 'rgba(0,0,0,0.12)', shadowOffsetY: 2,
          },
          x: nodeWithPos.x, y: nodeWithPos.y,
        }
      }),
      links: links.map(l => {
        const style = relationStyleMap[l.relationType] || { color: '#9ea9c1', type: 'dashed', label: '关联' }
        const lineType = style.type as 'solid' | 'dashed' | 'dotted'
        return {
          source: l.source, target: l.target,
          lineStyle: { type: lineType, color: style.color, curveness: l.relationType === 'ownership' ? 0.05 : 0.25, width: l.relationType === 'ownership' ? 2.5 : 1.8, opacity: 0.8 },
          label: { show: false }, relationType: l.relationType, reason: l.reason,
        }
      }),
      categories: currentCategories, roam: true, draggable: true, force: forceConfig,
      emphasis: { focus: 'adjacency', itemStyle: { shadowBlur: 20, shadowColor: 'rgba(74,157,154,0.4)', shadowOffsetY: 3 }, label: { fontWeight: 700, fontSize: 12 } },
      label: {
        show: true, position: 'right', fontSize: 11, fontWeight: 500, color: '#2c3e50', distance: 10,
        formatter: (params: any) => params.data.type === 'paper' ? params.name : (params.name.length > 10 ? params.name.substring(0,10)+'…' : params.name)
      },
      blur: { itemStyle: { opacity: 0.15 }, lineStyle: { opacity: 0.05 }, label: { show: false } }
    }],
  }
  chartInstance.setOption(option, { notMerge: true })
  chartInstance?.off('click', handleChartClick)
  chartInstance?.on('click', handleChartClick)
}

// 监听相似度图谱的四要素筛选变化
watch(
  () => [similarityFilters.background, similarityFilters.method, similarityFilters.innovation, similarityFilters.conclusion],
  () => { if (graphType.value === 'similarity') refreshSimilarityGraphRender() },
  { deep: true }
)

// 监听图谱类型切换
watch(graphType, (type) => {
  if (type === 'similarity') loadSimilarityGraph()
  else loadLLMGraph()
})

// 监听文件夹变化（清空缓存并重新加载）
watch(() => folderStore.currentFolderId, () => {
  similarityCache.key = ''
  llmCache.key = ''
  if (graphType.value === 'similarity') loadSimilarityGraph()
  else loadLLMGraph()
})

// 监听论文数量变化（数据可能变化，清空缓存）
watch(() => paperStore.papers.length, () => {
  similarityCache.key = ''
  llmCache.key = ''
})

const handleChartClick = (params: any) => {
  if (params.dataType === 'node') {
    selectedNodeData.value = params.data
    nodeDetailVisible.value = true
  }
}

const handleNavigateToPaper = (paperId: string) => {
  nodeDetailVisible.value = false
  if (!paperId) { ElMessage.warning('该节点未关联论文'); return }
  router.push({ name: 'paper-pdf', params: { paperId } }).catch(() => ElMessage.error('页面跳转失败'))
}

// ---- 导出功能实现 ----
const handleExportImage = async (format: 'png' | 'svg') => {
  if (!chartInstance) {
    ElMessage.warning('图谱尚未加载完成')
    return
  }
  isExporting.value = true
  try {
    // 短暂延迟确保渲染稳定
    await new Promise(resolve => setTimeout(resolve, 100))
    const url = chartInstance.getDataURL({
      type: format,
      pixelRatio: 2,
      backgroundColor: '#fff'
    })
    const link = document.createElement('a')
    link.download = `knowledge-graph-${graphType.value}.${format}`
    link.href = url
    link.click()
    ElMessage.success(`导出 ${format.toUpperCase()} 成功`)
  } catch (error) {
    console.error('导出图片失败:', error)
    ElMessage.error('导出图片失败')
  } finally {
    isExporting.value = false
  }
}

const downloadBlob = (blob: Blob, filename: string) => {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

const handleExportData = (cmd: 'json' | 'csv') => {
  if (!currentNodes.length && !currentLinks.length) {
    ElMessage.warning('当前没有图谱数据可导出')
    return
  }

  if (cmd === 'json') {
    const exportObj = {
      graphType: graphType.value,
      timestamp: new Date().toISOString(),
      nodes: currentNodes.map(n => ({
        id: n.id,
        name: n.name,
        type: n.type,
        category: n.category,
        paperId: n.paperId,
        paperTitle: n.paperTitle,
        content: n.content,
        authors: n.paperInfo?.authors,
        year: n.paperInfo?.year,
        source: n.paperInfo?.source
      })),
      links: currentLinks.map(l => ({
        source: l.source,
        target: l.target,
        relationType: l.relationType,
        reason: l.reason
      }))
    }
    const blob = new Blob([JSON.stringify(exportObj, null, 2)], { type: 'application/json' })
    downloadBlob(blob, `knowledge-graph-${graphType.value}-${Date.now()}.json`)
    ElMessage.success('导出 JSON 成功')
  } else if (cmd === 'csv') {
    // 节点 CSV
    const nodesCsvRows = [
      ['id', 'name', 'type', 'category', 'paperId', 'authors', 'year', 'source'],
      ...currentNodes.map(n => [
        n.id,
        n.name,
        n.type,
        n.category,
        n.paperId || '',
        n.paperInfo?.authors || '',
        n.paperInfo?.year || '',
        n.paperInfo?.source || ''
      ])
    ]
    const nodesCsv = nodesCsvRows.map(row => row.join(',')).join('\n')
    
    // 边 CSV
    const linksCsvRows = [
      ['source', 'target', 'relationType', 'reason'],
      ...currentLinks.map(l => [l.source, l.target, l.relationType, l.reason || ''])
    ]
    const linksCsv = linksCsvRows.map(row => row.join(',')).join('\n')
    
    // 添加 BOM 处理中文
    downloadBlob(new Blob(['\uFEFF' + nodesCsv], { type: 'text/csv' }), `nodes-${graphType.value}-${Date.now()}.csv`)
    downloadBlob(new Blob(['\uFEFF' + linksCsv], { type: 'text/csv' }), `links-${graphType.value}-${Date.now()}.csv`)
    ElMessage.success('导出 CSV 文件成功')
  }
}

onMounted(async () => {
  if (paperStore.papers.length === 0) await paperStore.loadPapers()
  await loadSimilarityGraph()
  const handleWindowResize = () => chartInstance?.resize()
  window.addEventListener('resize', handleWindowResize)
  const handleSidebarToggle = () => chartInstance?.resize()
  window.addEventListener('sidebar-toggle', handleSidebarToggle)
  ;(chartInstance as any)._cleanupHandlers = () => {
    window.removeEventListener('resize', handleWindowResize)
    window.removeEventListener('sidebar-toggle', handleSidebarToggle)
  }
})

onUnmounted(() => {
  if ((chartInstance as any)?._cleanupHandlers) (chartInstance as any)._cleanupHandlers()
  chartInstance?.dispose()
})
</script>

<template>
  <div class="graph-panel">
    <header class="graph-header">
      <div class="header-left">
        <el-radio-group v-model="graphType" size="small" class="graph-type-switch">
          <el-radio-button label="similarity">相似度图谱</el-radio-button>
          <el-radio-button label="llm">主题聚类</el-radio-button>
        </el-radio-group>

        <div v-if="graphType === 'similarity'" class="graph-filters">
          <el-checkbox v-model="similarityFilters.background" size="small" class="filter-chip">
            <span class="filter-icon" style="background: #6b8e8e" /> 研究背景
          </el-checkbox>
          <el-checkbox v-model="similarityFilters.method" size="small" class="filter-chip">
            <span class="filter-icon" style="background: #e8b86d" /> 研究方法
          </el-checkbox>
          <el-checkbox v-model="similarityFilters.innovation" size="small" class="filter-chip">
            <span class="filter-icon" style="background: #c17767" /> 创新点
          </el-checkbox>
          <el-checkbox v-model="similarityFilters.conclusion" size="small" class="filter-chip">
            <span class="filter-icon" style="background: #4a9d9a" /> 结论
          </el-checkbox>
        </div>
      </div>

      <div class="header-right">
        <el-dropdown trigger="click" @command="handleExportImage">
          <el-button type="primary" plain size="small" :loading="isExporting">
            <el-icon><Download /></el-icon> 导出图片
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="png">PNG 图片</el-dropdown-item>
              <el-dropdown-item command="svg">SVG 矢量图</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <el-dropdown trigger="click" @command="handleExportData">
          <el-button type="info" plain size="small">
            <el-icon><Document /></el-icon> 导出数据
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="json">JSON 数据</el-dropdown-item>
              <el-dropdown-item command="csv">CSV 数据（节点+边）</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>

    <div class="graph-canvas-wrapper">
      <div class="graph-canvas">
        <div v-loading="isLoading" ref="chartRef" class="graph-chart" />
      </div>
    </div>

    <GraphNodeDetail
      v-model="nodeDetailVisible"
      :node-data="selectedNodeData"
      @navigate-to-paper="handleNavigateToPaper"
    />
  </div>
</template>

<style scoped>
.graph-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 0 1.5rem 1.5rem;
}

.graph-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 0.5rem 1rem 0;
  margin-bottom: 0.5rem;
  border-bottom: 1px solid var(--line-soft, #e8edf2);
  background: transparent;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.header-right {
  display: flex;
  gap: 12px;
}

.graph-type-switch {
  display: flex;
  gap: 0.5rem;
}

.graph-type-switch :deep(.el-radio-button__inner) {
  padding: 6px 20px;
  border-radius: 40px !important;
  border: 1px solid var(--line-soft, #e0e6ed);
  background: rgba(255,255,255,0.8);
  font-weight: 500;
  transition: all 0.2s ease;
  box-shadow: none;
}

.graph-type-switch :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: #4a9d9a;
  border-color: #4a9d9a;
  color: white;
  box-shadow: 0 2px 8px rgba(74, 157, 154, 0.25);
}

.graph-type-switch :deep(.el-radio-button__inner:hover) {
  background: rgba(74, 157, 154, 0.08);
  border-color: #4a9d9a;
  color: #4a9d9a;
}

.graph-filters {
  display: flex;
  gap: 0.8rem;
  flex-wrap: wrap;
  align-items: center;
}

.filter-chip {
  padding: 0 8px 0 4px !important;
  margin: 0 !important;
  border-radius: 32px !important;
  background: rgba(255,255,255,0.7) !important;
  border: 1px solid var(--line-soft, #e0e6ed) !important;
  font-size: 13px !important;
  transition: all 0.2s ease;
  backdrop-filter: blur(2px);
}

.filter-chip:hover {
  background: rgba(74, 157, 154, 0.08) !important;
  border-color: #4a9d9a !important;
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}

.filter-chip :deep(.el-checkbox__label) {
  font-size: 13px;
  font-weight: 500;
  color: #3e4a5c;
  padding-left: 4px;
}

.filter-chip :deep(.el-checkbox__input.is-checked + .el-checkbox__label) {
  color: #4a9d9a;
}

.filter-icon {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 6px;
  vertical-align: middle;
  transition: transform 0.1s ease;
}

.filter-chip:hover .filter-icon {
  transform: scale(1.2);
}

.graph-canvas-wrapper {
  flex: 1;
  position: relative;
  min-height: 0;
}

.graph-canvas {
  position: absolute;
  inset: 0;
  border: 1px solid var(--line-soft);
  border-radius: 20px;
  background: linear-gradient(135deg, #f8fafc 0%, #eef2f7 50%, #f1f5f9 100%);
  box-shadow: inset 0 1px 3px rgba(0,0,0,0.02), 0 8px 20px rgba(0,0,0,0.04);
  overflow: hidden;
}

.graph-chart {
  width: 100%;
  height: 100%;
}

@media (max-width: 768px) {
  .graph-panel {
    padding: 0 1rem 1rem;
  }
  .graph-header {
    padding: 0.75rem 0 0.75rem 0;
  }
  .filter-chip {
    padding: 0 6px !important;
    font-size: 12px !important;
  }
  .graph-type-switch :deep(.el-radio-button__inner) {
    padding: 4px 12px;
    font-size: 12px;
  }
}
</style>