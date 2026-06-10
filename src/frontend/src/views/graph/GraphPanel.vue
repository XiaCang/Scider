<script setup lang="ts">
import { ref, onMounted, onUnmounted, reactive, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { Plus, Connection, PictureFilled, DataLine } from '@element-plus/icons-vue'
import { useFolderStore } from '../../store/folder'
import { usePaperStore } from '../../store/paper'
import type { PaperKeyPoints } from '../../types/library'
import type { GraphLink, GraphNode, NodeType, GraphNodeData } from '../../types/graph'
import GraphNodeDetail from './GraphNodeDetail.vue'
import GraphEdgeDetail from './GraphEdgeDetail.vue'
import {
  fetchSimilarityGraphApi,
  fetchLLMGraphApi,
  createGraphNode,
  createGraphEdge,
} from '../../api/graph'

// 图谱配置常量
const SIMILARITY_THRESHOLD = 0.4

const defaultCategories = [
  { name: '论文', itemStyle: { color: '#4a9d9a' } },
  { name: '研究背景', itemStyle: { color: '#6b8e8e' } },
  { name: '研究方法', itemStyle: { color: '#e8b86d' } },
  { name: '创新点', itemStyle: { color: '#c17767' } },
  { name: '结论', itemStyle: { color: '#4a9d9a' } },
]

const clusterColors = ['#4a9d9a', '#e8b86d', '#c17767', '#6b8e8e', '#8b7cb3', '#5a9fd4']

const relationStyleMap: Record<string, { color: string; type: 'solid' | 'dashed' | 'dotted'; label: string }> = {
  extends: { color: '#7caf7a', type: 'solid', label: '扩展关系' },
  applies: { color: '#6a9fb5', type: 'solid', label: '应用关系' },
  compares: { color: '#e09d6e', type: 'dashed', label: '对比关系' },
  related: { color: '#b796c9', type: 'dotted', label: '相关关系' },
  semantic: { color: '#9ea9c1', type: 'dashed', label: '语义关联' },
  ownership: { color: 'rgba(120,140,170,0.5)', type: 'solid', label: '归属关系' },
  custom: { color: '#8b7cb3', type: 'dashed', label: '自定义' },
}

const router = useRouter()
const folderStore = useFolderStore()
const paperStore = usePaperStore()
const chartRef = ref<HTMLDivElement | null>(null)
let chartInstance: echarts.ECharts | null = null
const isLoading = ref(false)

const graphType = ref<'similarity' | 'llm'>('similarity')

// 节点详情
const nodeDetailVisible = ref(false)
const selectedNodeData = ref<GraphNodeData | null>(null)

// 边详情
const edgeDetailVisible = ref(false)
const selectedEdge = ref<any>(null)

// 相似度图谱筛选
const similarityFilters = reactive({
  background: false,
  method: false,
  innovation: false,
  conclusion: false,
})

let similarityBaseNodes: GraphNode[] = []
let similarityBaseLinks: GraphLink[] = []
let similarityCache = { key: '', baseNodes: [] as GraphNode[], baseLinks: [] as GraphLink[] }
let llmCache = { key: '', nodes: [] as GraphNode[], links: [] as GraphLink[], categories: [] as any[] }
let currentCategories = defaultCategories
let currentNodes: GraphNode[] = []
let currentLinks: GraphLink[] = []

// 连线模式状态
const isLinkingMode = ref(false)
let linkingSourceNode: GraphNode | null = null

// 添加节点弹窗（已移除 paper_id 字段）
const addNodeDialogVisible = ref(false)
const newNodeForm = ref({
  name: '',
  node_type: 'custom',
  category: 0,
})

// 选择关系类型弹窗
const relationDialogVisible = ref(false)
const pendingEdge = ref<{ source: GraphNode; target: GraphNode } | null>(null)
const edgeRelationType = ref('related')
const edgeLabel = ref('')

// 计算当前是否为 LLM 模式
const isLLMMode = computed(() => graphType.value === 'llm')

const getCacheKey = () => `${folderStore.currentFolderId || 'all'}_${paperStore.papers.length}`

const getSymbolByType = (type: NodeType) => {
  switch (type) {
    case 'background': return 'circle'
    case 'method': return 'rect'
    case 'innovation': return 'diamond'
    case 'conclusion': return 'triangle'
    default: return 'circle'
  }
}

const dimensionConfig: { type: keyof PaperKeyPoints; nodeType: NodeType; label: string; category: number }[] = [
  { type: 'background', nodeType: 'background', label: '研究背景', category: 1 },
  { type: 'method', nodeType: 'method', label: '研究方法', category: 2 },
  { type: 'innovation', nodeType: 'innovation', label: '创新点', category: 3 },
  { type: 'conclusion', nodeType: 'conclusion', label: '结论', category: 4 },
]

const extractElementNodesAndLinks = (paperNode: GraphNode, filterTypes?: Set<string>): { nodes: GraphNode[]; links: GraphLink[] } => {
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
    links.push({ source: paperId, target: elemId, relationType: 'ownership', label: '归属' })
  }
  return { nodes, links }
}

const buildSimilarityFullGraph = (): { nodes: GraphNode[]; links: GraphLink[]; categories: typeof defaultCategories } => {
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
  return { nodes: allNodes, links: allLinks, categories: defaultCategories }
}

const refreshSimilarityGraphRender = () => {
  if (graphType.value !== 'similarity') return
  const { nodes, links, categories } = buildSimilarityFullGraph()
  currentCategories = categories
  renderChart(nodes, links)
}

const loadSimilarityGraph = async (forceRefresh = false) => {
  isLoading.value = true
  const cacheKey = getCacheKey()

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

    similarityCache = { key: cacheKey, baseNodes: similarityBaseNodes, baseLinks: similarityBaseLinks }
    refreshSimilarityGraphRender()
  } catch (e) {
    console.error('[GraphPanel] 加载相似度图谱失败:', e)
    ElMessage.error('加载相似度图谱失败')
  } finally {
    isLoading.value = false
  }
}

const assignClusterInitialPositions = (nodes: GraphNode[], clusters: any[]) => {
  const clusterCount = clusters.length
  if (clusterCount === 0) return
  const baseRadius = Math.min(400, Math.max(250, nodes.length * 1.5))
  const clusterCenters: { angle: number; radius: number; count: number }[] = []
  for (let i = 0; i < clusterCount; i++) {
    const angle = (i / clusterCount) * Math.PI * 2
    const radius = baseRadius * (0.8 + (i % 2) * 0.3)
    clusterCenters.push({ angle, radius, count: 0 })
  }
  nodes.forEach(node => { const cat = node.category; if (cat >= 0 && cat < clusterCount) clusterCenters[cat].count++ })
  nodes.forEach(node => {
    const cat = node.category
    if (cat >= 0 && cat < clusterCount) {
      const center = clusterCenters[cat]
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

const loadLLMGraph = async (forceRefresh = false) => {
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
      ElMessage.info('没有已确认的论文，请先确认论文四要素')
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
      type: n.type || 'paper',
      category: n.category,
      paperInfo: n.paperInfo,
    }))
    assignClusterInitialPositions(nodes, payload.clusters)
    const links: GraphLink[] = (payload.links || []).map((l: any) => ({
      id: l.id,
      source: l.source,
      target: l.target,
      relationType: l.relationType,
      label: l.label,
      reason: l.label,
    }))
    llmCache = { key: cacheKey, nodes, links, categories: currentCategories }
    renderChart(nodes, links)
  } catch (e) {
    console.error('[GraphPanel] 加载 LLM 图谱失败:', e)
    ElMessage.error('加载 LLM 图谱失败')
  } finally {
    isLoading.value = false
  }
}

const renderChart = (nodes: GraphNode[], links: GraphLink[]) => {
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
  let forceConfig: any = { repulsion: 1000, gravity: 0.03, edgeLength: [180, 350], friction: 0.65, initIterations: 250, layoutAnimation: true }
  if (nodeCount > 50) forceConfig = { repulsion: 1500, gravity: 0.02, edgeLength: [200, 400], friction: 0.7, initIterations: 300, layoutAnimation: true }
  if (nodeCount < 20) forceConfig = { repulsion: 800, gravity: 0.05, edgeLength: [150, 250], friction: 0.6, initIterations: 200, layoutAnimation: true }
  if (graphType.value === 'llm') forceConfig = { ...forceConfig, repulsion: 1200, gravity: 0.02, edgeLength: [180, 400] }

  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e0e6ed',
      borderWidth: 1,
      textStyle: { color: '#333', fontSize: 12 },
      formatter: (params: any) => {
        if (params.dataType === 'edge') {
          if (graphType.value === 'similarity') {
            return `<div style="text-align:center;padding:4px 8px;"><div style="font-weight:600;">相似度</div><div>${params.data.reason || '—'}</div></div>`
          }
          const typeMap: Record<string,string> = { extends:'扩展', applies:'应用', compares:'对比', related:'相关', semantic:'语义关联' }
          const relationTitle = typeMap[params.data.relationType] || '关联'
          let content = params.data.reason || params.data.label || ''
          if (content.includes('：')) content = content.split('：')[1]
          if (content.includes(':')) content = content.split(':')[1]
          return `<div style="text-align:center;padding:4px 8px;"><div style="font-weight:600;">${relationTitle}</div><div>${content || '—'}</div></div>`
        }
        if (params.data.type === 'paper' && params.data.paperInfo) {
          const p = params.data.paperInfo
          return `<div style="padding:4px 0;max-width:300px;"><div style="font-weight:600;">${params.name}</div><div>作者: ${p.authors}</div><div>年份: ${p.year}</div><div>来源: ${p.source}</div></div>`
        }
        const typeLabels: Record<string,string> = { paper:'📄 论文', background:'🎯 研究背景', method:'⚙️ 研究方法', innovation:'💡 创新点', conclusion:'✅ 结论', custom:'📌 自定义' }
        return `<div><div style="font-weight:600;">${params.name}</div><div>${typeLabels[params.data.type] || '节点'}</div></div>`
      }
    },
    legend: { data: currentCategories.map(c => c.name), orient: 'vertical', right: 15, top: 15, backgroundColor: 'rgba(255,255,255,0.95)', borderRadius: 10, padding: [12,16] },
    series: [{
      type: 'graph', layout: 'force', data: nodes.map(n => ({ ...n, symbol: getSymbolByType(n.type), symbolSize: (n.type === 'paper' ? 55 : 38) + Math.min(nodeConnCount[n.id] || 0, 12), itemStyle: { borderWidth: n.type === 'paper' ? 3 : 2, borderColor: '#fff', shadowBlur: n.type === 'paper' ? 15 : 8, shadowColor: 'rgba(0,0,0,0.12)' }, x: (n as any).x, y: (n as any).y })),
      links: links.map(l => {
        const style = relationStyleMap[l.relationType] || relationStyleMap.custom
        const edgeId = (l as any).id || `edge_${l.source}_${l.target}_${l.relationType}`
        return { 
          id: edgeId,
          source: l.source, 
          target: l.target, 
          lineStyle: { 
            type: style.type, 
            color: style.color, 
            curveness: l.relationType === 'ownership' ? 0.05 : 0.25, 
            width: l.relationType === 'ownership' ? 2.5 : 1.8, 
            opacity: 0.8 
          }, 
          label: { show: false }, 
          relationType: l.relationType, 
          reason: l.reason 
        }
      }),
      categories: currentCategories, roam: true, draggable: true, force: forceConfig,
      emphasis: { focus: 'adjacency', itemStyle: { shadowBlur: 20, shadowColor: 'rgba(74,157,154,0.4)' }, label: { fontWeight: 700 } },
      label: { show: true, position: 'right', fontSize: 11, fontWeight: 500, color: '#2c3e50', distance: 10, formatter: (params: any) => params.data.type === 'paper' ? params.name : (params.name.length > 10 ? params.name.substring(0,10)+'…' : params.name) },
      blur: { itemStyle: { opacity: 0.15 }, lineStyle: { opacity: 0.05 }, label: { show: false } }
    }],
  }
  chartInstance.setOption(option, { notMerge: true })
  chartInstance?.off('click', handleChartClick)
  chartInstance?.on('click', handleChartClick)
}

const handleChartClick = (params: any) => {
  if (params.dataType === 'node') {
    if (isLinkingMode.value) {
      if (!linkingSourceNode) {
        linkingSourceNode = params.data
        ElMessage.info('已选中源节点，请点击目标节点')
      } else {
        pendingEdge.value = { source: linkingSourceNode, target: params.data }
        relationDialogVisible.value = true
        isLinkingMode.value = false
        linkingSourceNode = null
      }
    } else {
      selectedNodeData.value = params.data
      nodeDetailVisible.value = true
    }
  } else if (params.dataType === 'edge') {
    const edge = params.data
    selectedEdge.value = {
      id: edge.id,
      source: edge.source,
      target: edge.target,
      relationType: edge.relationType,
      label: edge.label,
      reason: edge.reason,
    }
    edgeDetailVisible.value = true
  }
}

const toggleLinkingMode = () => {
  if (!isLLMMode.value) {
    ElMessage.warning('仅在 LLM 图谱模式下支持手动添加边')
    return
  }
  if (isLinkingMode.value) {
    isLinkingMode.value = false
    linkingSourceNode = null
    ElMessage.info('已取消连线模式')
  } else {
    isLinkingMode.value = true
    ElMessage.info('连线模式已开启，请点击第一个节点')
  }
}

const openAddNodeDialog = () => {
  if (!isLLMMode.value) {
    ElMessage.warning('仅在 LLM 图谱模式下支持添加自定义节点')
    return
  }
  newNodeForm.value = { name: '', node_type: 'custom', category: 0 }
  addNodeDialogVisible.value = true
}

const submitAddNode = async () => {
  if (!newNodeForm.value.name.trim()) {
    ElMessage.warning('请输入节点名称')
    return
  }
  try {
    await createGraphNode({
      name: newNodeForm.value.name,
      node_type: newNodeForm.value.node_type,
      category: newNodeForm.value.category,
    })
    ElMessage.success('节点添加成功')
    addNodeDialogVisible.value = false
    refreshAfterEdit()
  } catch (error) {
    ElMessage.error('添加失败')
  }
}

const submitCreateEdge = async () => {
  if (!pendingEdge.value) return
  try {
    await createGraphEdge({
      source_id: pendingEdge.value.source.id,
      target_id: pendingEdge.value.target.id,
      relation_type: edgeRelationType.value,
      label: edgeLabel.value || undefined,
    })
    ElMessage.success('边创建成功')
    relationDialogVisible.value = false
    pendingEdge.value = null
    edgeRelationType.value = 'related'
    edgeLabel.value = ''
    refreshAfterEdit()
  } catch (error) {
    ElMessage.error('创建边失败')
  }
}

const refreshAfterEdit = () => {
  if (graphType.value === 'similarity') {
    similarityCache.key = ''
    loadSimilarityGraph(true)
  } else {
    llmCache.key = ''
    loadLLMGraph(true)
  }
}

const handleExportImage = async (format: 'png' | 'svg') => {
  if (!chartInstance) { ElMessage.warning('图谱尚未加载完成'); return }
  const url = chartInstance.getDataURL({ type: format, pixelRatio: 2, backgroundColor: '#fff' })
  const link = document.createElement('a')
  link.download = `knowledge-graph-${graphType.value}.${format}`
  link.href = url
  link.click()
  ElMessage.success(`导出 ${format.toUpperCase()} 成功`)
}

const handleExportData = (cmd: 'json' | 'csv') => {
  if (!currentNodes.length && !currentLinks.length) { ElMessage.warning('没有数据可导出'); return }
  if (cmd === 'json') {
    const exportObj = { graphType: graphType.value, timestamp: new Date().toISOString(), nodes: currentNodes.map(n => ({ id: n.id, name: n.name, type: n.type, category: n.category, paperId: n.paperId, paperTitle: n.paperTitle, content: n.content, authors: n.paperInfo?.authors, year: n.paperInfo?.year, source: n.paperInfo?.source })), links: currentLinks.map(l => ({ source: l.source, target: l.target, relationType: l.relationType, reason: l.reason })) }
    const blob = new Blob([JSON.stringify(exportObj, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = `kg-${graphType.value}-${Date.now()}.json`; a.click(); URL.revokeObjectURL(url)
    ElMessage.success('导出 JSON 成功')
  } else if (cmd === 'csv') {
    const nodesCsv = ['id,name,type,category,paperId,authors,year,source', ...currentNodes.map(n => `${n.id},${n.name},${n.type},${n.category},${n.paperId || ''},${n.paperInfo?.authors || ''},${n.paperInfo?.year || ''},${n.paperInfo?.source || ''}`)].join('\n')
    const linksCsv = ['source,target,relationType,reason', ...currentLinks.map(l => `${l.source},${l.target},${l.relationType},${l.reason || ''}`)].join('\n')
    const blobNodes = new Blob(['\uFEFF' + nodesCsv], { type: 'text/csv' }); const blobLinks = new Blob(['\uFEFF' + linksCsv], { type: 'text/csv' })
    const urlNodes = URL.createObjectURL(blobNodes); const urlLinks = URL.createObjectURL(blobLinks)
    const aNodes = document.createElement('a'); aNodes.href = urlNodes; aNodes.download = `nodes-${graphType.value}-${Date.now()}.csv`; aNodes.click()
    const aLinks = document.createElement('a'); aLinks.href = urlLinks; aLinks.download = `links-${graphType.value}-${Date.now()}.csv`; aLinks.click()
    URL.revokeObjectURL(urlNodes); URL.revokeObjectURL(urlLinks)
    ElMessage.success('导出 CSV 文件成功')
  }
}

watch(
  () => [similarityFilters.background, similarityFilters.method, similarityFilters.innovation, similarityFilters.conclusion],
  () => { if (graphType.value === 'similarity') refreshSimilarityGraphRender() },
  { deep: true }
)
watch(graphType, (type) => {
  if (type === 'similarity') loadSimilarityGraph()
  else loadLLMGraph()
})
watch(() => folderStore.currentFolderId, () => {
  similarityCache.key = ''
  llmCache.key = ''
  if (graphType.value === 'similarity') loadSimilarityGraph()
  else loadLLMGraph()
})
watch(() => paperStore.papers.length, () => {
  similarityCache.key = ''
  llmCache.key = ''
})

onMounted(async () => {
  if (paperStore.papers.length === 0) await paperStore.loadPapers()
  await loadSimilarityGraph()
  const handleWindowResize = () => chartInstance?.resize()
  window.addEventListener('resize', handleWindowResize)
  window.addEventListener('sidebar-toggle', () => chartInstance?.resize())
  ;(chartInstance as any)._cleanup = () => window.removeEventListener('resize', handleWindowResize)
})

onUnmounted(() => {
  if ((chartInstance as any)?._cleanup) (chartInstance as any)._cleanup()
  chartInstance?.dispose()
})
</script>

<template>
  <div class="graph-panel">
    <header class="graph-header">
      <div class="header-row">
        <div class="header-left">
          <el-radio-group v-model="graphType" size="small" class="graph-type-switch">
            <el-radio-button label="similarity">相似度图谱</el-radio-button>
            <el-radio-button label="llm">主题聚类</el-radio-button>
          </el-radio-group>
          <div class="header-divider" />
          <div v-if="graphType === 'similarity'" class="graph-filters">
            <label class="filter-chip" :class="{ active: similarityFilters.background }" @click.prevent="similarityFilters.background = !similarityFilters.background">
              <span class="filter-dot" style="background:#6b8e8e" />研究背景
            </label>
            <label class="filter-chip" :class="{ active: similarityFilters.method }" @click.prevent="similarityFilters.method = !similarityFilters.method">
              <span class="filter-dot" style="background:#e8b86d" />研究方法
            </label>
            <label class="filter-chip" :class="{ active: similarityFilters.innovation }" @click.prevent="similarityFilters.innovation = !similarityFilters.innovation">
              <span class="filter-dot" style="background:#c17767" />创新点
            </label>
            <label class="filter-chip" :class="{ active: similarityFilters.conclusion }" @click.prevent="similarityFilters.conclusion = !similarityFilters.conclusion">
              <span class="filter-dot" style="background:#4a9d9a" />结论
            </label>
          </div>
        </div>
        <div class="header-right">
          <el-tooltip content="添加自定义节点" placement="top" :show-after="500">
            <el-button size="small" class="toolbar-btn" @click="openAddNodeDialog" :disabled="!isLLMMode">
              <el-icon><Plus /></el-icon>
            </el-button>
          </el-tooltip>
          <el-tooltip :content="isLinkingMode ? '取消连线模式' : '添加关联边'" placement="top" :show-after="500">
            <el-button size="small" class="toolbar-btn" :class="{ 'linking-active': isLinkingMode }" @click="toggleLinkingMode" :disabled="!isLLMMode">
              <el-icon><Connection /></el-icon>
            </el-button>
          </el-tooltip>
          <el-tooltip content="导出图片" placement="top" :show-after="500">
            <el-dropdown trigger="click" @command="handleExportImage" class="toolbar-dropdown">
              <el-button size="small" class="toolbar-btn">
                <el-icon><PictureFilled /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="png">PNG 图片</el-dropdown-item>
                  <el-dropdown-item command="svg">SVG 矢量图</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </el-tooltip>
          <el-tooltip content="导出数据" placement="top" :show-after="500">
            <el-dropdown trigger="click" @command="handleExportData" class="toolbar-dropdown">
              <el-button size="small" class="toolbar-btn">
                <el-icon><DataLine /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="json">JSON 数据</el-dropdown-item>
                  <el-dropdown-item command="csv">CSV 数据</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </el-tooltip>
        </div>
      </div>
    </header>

    <div class="graph-canvas-wrapper">
      <div class="graph-canvas">
        <div v-loading="isLoading" ref="chartRef" class="graph-chart" />
      </div>
    </div>

    <GraphNodeDetail v-model="nodeDetailVisible" :node-data="selectedNodeData" @navigate-to-paper="(pid) => router.push({ name: 'paper-pdf', params: { paperId: pid } })" @refresh="refreshAfterEdit" />
    <GraphEdgeDetail v-model="edgeDetailVisible" :edge-data="selectedEdge" @refresh="refreshAfterEdit" />

    <!-- 添加节点弹窗（已移除关联论文字段） -->
    <el-dialog v-model="addNodeDialogVisible" title="添加自定义节点" width="500px">
      <el-form :model="newNodeForm" label-width="100px">
        <el-form-item label="节点名称" required><el-input v-model="newNodeForm.name" /></el-form-item>
        <el-form-item label="节点类型"><el-input v-model="newNodeForm.node_type" placeholder="custom" /></el-form-item>
        <el-form-item label="分类索引"><el-input-number v-model="newNodeForm.category" :min="0" :max="10" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="addNodeDialogVisible = false">取消</el-button><el-button type="primary" @click="submitAddNode">确认</el-button></template>
    </el-dialog>

    <!-- 选择关系类型弹窗 -->
    <el-dialog v-model="relationDialogVisible" title="创建关联边" width="450px">
      <el-form label-width="100px">
        <el-form-item label="关系类型">
          <el-select v-model="edgeRelationType">
            <el-option label="扩展关系 (extends)" value="extends" />
            <el-option label="应用关系 (applies)" value="applies" />
            <el-option label="对比关系 (compares)" value="compares" />
            <el-option label="相关关系 (related)" value="related" />
            <el-option label="自定义 (custom)" value="custom" />
          </el-select>
        </el-form-item>
        <el-form-item label="标签"><el-input v-model="edgeLabel" placeholder="可选，如：基于...扩展" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="relationDialogVisible = false">取消</el-button><el-button type="primary" @click="submitCreateEdge">确认</el-button></template>
    </el-dialog>
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
  flex-shrink: 0;
  padding: 0.75rem 0;
}

.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(12px);
  border: 1px solid var(--line-soft, #e8edf2);
  border-radius: 14px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.header-divider {
  width: 1px;
  height: 24px;
  background: var(--line-soft, #e0e6ed);
  flex-shrink: 0;
}

.header-right {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
  align-items: center;
}

.header-right > * {
  display: flex !important;
  align-items: center;
  justify-content: center;
  margin: 0 !important;
  line-height: 1;
}

.graph-type-switch :deep(.el-radio-button) {
  margin-right: 6px;
}

.graph-type-switch :deep(.el-radio-button:last-child) {
  margin-right: 0;
}

.graph-type-switch :deep(.el-radio-button) {
  margin-right: 6px;
}

.graph-type-switch :deep(.el-radio-button:last-child) {
  margin-right: 0;
}

.graph-type-switch :deep(.el-radio-button__inner) {
  padding: 5px 16px;
  border-radius: 20px;
  border: 1px solid var(--line-soft);
  background: transparent;
  font-weight: 500;
  font-size: 13px;
  color: var(--text-secondary, #666);
  transition: all 0.2s ease;
  box-shadow: none;
}

.graph-type-switch :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: #4a9d9a;
  border-color: #4a9d9a;
  color: white;
  box-shadow: 0 2px 8px rgba(74, 157, 154, 0.3);
}

.graph-filters {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.filter-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 12px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid var(--line-soft, #e0e6ed);
  font-size: 12px;
  color: var(--text-secondary, #888);
  cursor: pointer;
  user-select: none;
  transition: all 0.2s ease;
  line-height: 1.4;
}

.filter-chip:hover {
  border-color: #c0c8d2;
  background: rgba(255, 255, 255, 0.9);
}

.filter-chip.active {
  background: rgba(74, 157, 154, 0.08);
  border-color: rgba(74, 157, 154, 0.4);
  color: var(--text-primary, #333);
  font-weight: 500;
}

.filter-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  transition: transform 0.2s ease;
}

.filter-chip.active .filter-dot {
  transform: scale(1.3);
}

.toolbar-btn {
  width: 34px;
  height: 34px;
  padding: 0;
  border-radius: 10px;
  border: 1px solid var(--line-soft, #e0e6ed);
  background: rgba(255, 255, 255, 0.6);
  color: var(--text-secondary, #666);
  transition: all 0.2s ease;
}

.toolbar-btn:hover:not(:disabled) {
  background: rgba(74, 157, 154, 0.08);
  border-color: rgba(74, 157, 154, 0.3);
  color: #4a9d9a;
}

.toolbar-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.toolbar-btn.linking-active {
  background: rgba(193, 119, 103, 0.1);
  border-color: rgba(193, 119, 103, 0.5);
  color: #c17767;
  animation: pulse-border 1.5s ease-in-out infinite;
}

@keyframes pulse-border {
  0%, 100% { box-shadow: 0 0 0 0 rgba(193, 119, 103, 0.2); }
  50% { box-shadow: 0 0 0 4px rgba(193, 119, 103, 0.1); }
}

.toolbar-dropdown :deep(.el-button) {
  margin-left: 0;
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
  .header-row {
    padding: 6px 10px;
    flex-wrap: wrap;
  }
  .header-left {
    gap: 8px;
  }
  .header-divider {
    display: none;
  }
  .filter-chip {
    padding: 3px 8px;
    font-size: 11px;
  }
  .graph-type-switch :deep(.el-radio-button) {
  margin-right: 6px;
}

.graph-type-switch :deep(.el-radio-button:last-child) {
  margin-right: 0;
}

.graph-type-switch :deep(.el-radio-button__inner) {
    padding: 4px 10px;
    font-size: 12px;
  }
  .toolbar-btn {
    width: 30px;
    height: 30px;
  }
}
</style>