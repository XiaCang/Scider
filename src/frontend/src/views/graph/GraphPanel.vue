<script setup lang="ts">
import { ref, onMounted, onUnmounted, reactive, watch } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { useFolderStore } from '../../store/folder'
import { usePaperStore } from '../../store/paper'
import type { Folder } from '../../types/folder'
import type { PaperKeyPoints } from '../../types/library'
import type { GraphLink, GraphNode, NodeType } from '../../types/graph'
import GraphNodeDetail from './GraphNodeDetail.vue'
import { fetchSimilarityGraphApi, fetchLLMGraphApi } from '../../api/graph'

// 图谱配置常量
const SIMILARITY_THRESHOLD = 0.35 // 相似度阈值（可根据 embedding 模型质量调整）

// 默认分类（用于相似度图谱和四要素图谱）
const defaultCategories = [
  { name: '论文', itemStyle: { color: '#4a9d9a' } },
  { name: '研究背景', itemStyle: { color: '#6b8e8e' } },
  { name: '研究方法', itemStyle: { color: '#e8b86d' } },
  { name: '创新点', itemStyle: { color: '#c17767' } },
  { name: '结论', itemStyle: { color: '#4a9d9a' } },
]

// 聚类颜色映射（用于 LLM 图谱）
const clusterColors = ['#4a9d9a', '#e8b86d', '#c17767', '#6b8e8e', '#8b7cb3', '#5a9fd4']

const router = useRouter()
const folderStore = useFolderStore()
const paperStore = usePaperStore()
const chartRef = ref<HTMLDivElement | null>(null)
let chartInstance: echarts.ECharts | null = null
const isLoading = ref(false)

// 图谱类型切换：'elements' = 四要素图谱, 'similarity' = 相似度图谱, 'llm' = LLM主题聚类
const graphType = ref<'elements' | 'similarity' | 'llm'>('elements')

// 节点详情
const nodeDetailVisible = ref(false)
const selectedNodeData = ref<GraphNode | null>(null)

// 筛选器（仅用于四要素图谱）
const filters = reactive({
  background: true,
  method: true,
  innovation: true,
  conclusion: true,
})

// 缓存全量节点与边
let cachedNodes: GraphNode[] = []
let cachedLinks: GraphLink[] = []
// 当前使用的分类
let currentCategories = defaultCategories

const getSymbolByType = (type: NodeType) => {
  switch (type) {
    case 'background': return 'circle'
    case 'method': return 'rect'
    case 'innovation': return 'diamond'
    case 'conclusion': return 'triangle'
    default: return 'circle'
  }
}

// ---- 四要素图谱：从论文数据构建 ----
const dimensionConfig: { type: keyof PaperKeyPoints; nodeType: NodeType; label: string; category: number }[] = [
  { type: 'background', nodeType: 'background', label: '研究背景', category: 1 },
  { type: 'method',     nodeType: 'method',     label: '研究方法',  category: 2 },
  { type: 'innovation', nodeType: 'innovation', label: '创新点',    category: 3 },
  { type: 'conclusion', nodeType: 'conclusion', label: '结论',      category: 4 },
]

function buildGraphFromPapers() {
  isLoading.value = true
  const nodes: GraphNode[] = []
  const links: GraphLink[] = []

  // 确定当前文件夹范围内的论文ID
  let paperIdsInScope: Set<string> | null = null
  const folderId = folderStore.currentFolderId
  if (folderId) {
    const folder = findFolder(folderStore.folders, folderId)
    if (folder) {
      paperIdsInScope = new Set(folder.paperIds ?? [])
    }
  }

  for (const paper of paperStore.papers) {
    if (paperIdsInScope && !paperIdsInScope.has(paper.id)) continue

    // 论文节点
    nodes.push({
      id: paper.id,
      name: paper.title.length > 20 ? paper.title.substring(0, 20) + '…' : paper.title,
      type: 'paper',
      category: 0,
      paperInfo: paper,
    })

    // 四要素节点
    for (const dim of dimensionConfig) {
      const content = paper.keyPoints?.[dim.type]
      if (!content || !content.trim()) continue

      const elemId = `${paper.id}_${dim.type}`
      nodes.push({
        id: elemId,
        name: content.length > 15 ? content.substring(0, 15) + '…' : content,
        type: dim.nodeType,
        category: dim.category,
        paperId: paper.id,
        paperTitle: paper.title,
        content,
        paperInfo: paper,
      })
      links.push({ source: paper.id, target: elemId, relationType: 'ownership' })
    }
  }

  cachedNodes = nodes
  cachedLinks = links
  currentCategories = defaultCategories
  applyFilterAndRender()
  isLoading.value = false

  // 异步加载后端相似度边（增强性，不阻塞主图谱）
  if (graphType.value === 'elements') {
    loadSimilarityEdges()
  }
}

function findFolder(tree: Folder[], id: string): Folder | undefined {
  for (const node of tree) {
    if (node.id === id) return node
    if (node.children) {
      const found = findFolder(node.children, id)
      if (found) return found
    }
  }
  return undefined
}

// ---- 相似度图谱：从后端加载 ----
async function loadSimilarityGraph() {
  isLoading.value = true
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
      cachedNodes = []
      cachedLinks = []
      renderChart([], [])
      return
    }

    // 构建节点
    cachedNodes = payload.nodes.map((n: any) => ({
      id: n.id,
      name: n.name,
      type: 'paper',
      category: 0,
      paperInfo: n.paperInfo,
    }))

    // 构建边
    cachedLinks = []
    if (payload.links?.length) {
      const nodeIds = new Set(cachedNodes.map(n => n.id))
      for (const link of payload.links) {
        if (!nodeIds.has(link.source) || !nodeIds.has(link.target)) continue
        const similarityMatch = link.label?.match(/相似度\s+([\d.]+)/)
        const similarityValue = similarityMatch ? parseFloat(similarityMatch[1]) : 0

        if (similarityValue >= SIMILARITY_THRESHOLD) {
          cachedLinks.push({
            source: link.source,
            target: link.target,
            relationType: 'semantic' as const,
            reason: similarityValue.toFixed(2),
          })
        }
      }
    }

    currentCategories = [{ name: '论文', itemStyle: { color: '#4a9d9a' } }]
    renderChart(cachedNodes, cachedLinks)

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

// 异步加载相似度边（用于四要素图谱增强）
async function loadSimilarityEdges() {
  try {
    const res: any = await fetchSimilarityGraphApi({
      folder_id: folderStore.currentFolderId,
      max_nodes: 200,
      min_similarity: SIMILARITY_THRESHOLD,
      top_k: 8,
    })
    const payload = res?.data
    if (payload?.links?.length) {
      const nodeIds = new Set(cachedNodes.map(n => n.id))
      for (const link of payload.links) {
        if (!nodeIds.has(link.source) || !nodeIds.has(link.target)) continue
        const similarityMatch = link.label?.match(/相似度\s+([\d.]+)/)
        const similarityValue = similarityMatch ? parseFloat(similarityMatch[1]) : 0

        if (similarityValue >= SIMILARITY_THRESHOLD) {
          cachedLinks.push({
            source: link.source,
            target: link.target,
            relationType: 'semantic' as const,
            reason: similarityValue.toFixed(2),
          })
        }
      }
      applyFilterAndRender()
    }
  } catch (e) {
    console.warn('[GraphPanel] 加载语义相似边失败:', e)
  }
}

// ---- LLM 主题聚类图谱 ----
async function loadLLMGraph() {
  isLoading.value = true
  try {
    const res: any = await fetchLLMGraphApi({
      folder_id: folderStore.currentFolderId,
      max_nodes: 50,
    })
    const payload = res?.data
    
    if (!payload?.nodes?.length) {
      const reason = payload?.meta?.reason || 'no_confirmed_papers'
      if (reason === 'no_confirmed_papers') {
        ElMessage.info('没有已确认的论文，请先确认论文四要素')
      } else {
        ElMessage.info('暂无数据')
      }
      cachedNodes = []
      cachedLinks = []
      renderChart([], [])
      return
    }

    // 使用 clusters 构建动态分类
    currentCategories = payload.clusters.map((c: any, idx: number) => ({
      name: c.name,
      itemStyle: { color: clusterColors[idx % clusterColors.length] }
    }))

    // 构建节点
    cachedNodes = payload.nodes.map((n: any) => ({
      id: n.id,
      name: n.name,
      type: 'paper',
      category: n.category,
      paperInfo: n.paperInfo,
    }))

    // 构建边（LLM 生成的语义关系）
    const relationTypeMap: Record<string, string> = {
      extends: '扩展',
      applies: '应用',
      compares: '对比',
      related: '相关',
    }
    
    cachedLinks = (payload.links || []).map((l: any) => ({
      source: l.source,
      target: l.target,
      relationType: l.relationType,
      label: l.label,
      reason: l.label, // 使用 label 作为 reason 显示
    }))

    renderChart(cachedNodes, cachedLinks)
  } catch (e) {
    console.error('[GraphPanel] 加载 LLM 图谱失败:', e)
    ElMessage.error('加载 LLM 图谱失败')
  } finally {
    isLoading.value = false
  }
}

// ---- 图表渲染 ----
const renderChart = (nodes: GraphNode[], links: GraphLink[]) => {
  if (!chartRef.value) return
  if (!chartInstance) chartInstance = echarts.init(chartRef.value)

  // 统计连接数用于动态大小
  const nodeConnCount: Record<string, number> = {}
  links.forEach(l => {
    nodeConnCount[l.source] = (nodeConnCount[l.source] || 0) + 1
    nodeConnCount[l.target] = (nodeConnCount[l.target] || 0) + 1
  })

  // 根据节点数量动态调整力导向布局参数
  const nodeCount = nodes.length
  let forceConfig
  if (nodeCount > 50) {
    forceConfig = { 
      repulsion: 1500,
      gravity: 0.02,
      edgeLength: [200, 400],
      friction: 0.7
    }
  } else if (nodeCount < 20) {
    forceConfig = { 
      repulsion: 800,
      gravity: 0.05,
      edgeLength: [150, 250],
      friction: 0.6
    }
  } else {
    forceConfig = { 
      repulsion: 1000,
      gravity: 0.03,
      edgeLength: [180, 350],
      friction: 0.65
    }
  }

  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e0e6ed',
      borderWidth: 1,
      textStyle: { color: '#333', fontSize: 12 },
      formatter: (params: any) => {
        if (params.dataType === 'edge') {
          const relationLabels: Record<string, string> = {
            ownership: '归属关系',
            semantic: '语义关联',
            citation: '引用关系',
            extends: '扩展关系',
            applies: '应用关系',
            compares: '对比关系',
            related: '相关关系',
          }
          
          let reasonHtml = ''
          if (params.data.relationType === 'semantic' || 
              ['extends', 'applies', 'compares', 'related'].includes(params.data.relationType)) {
            const reasonText = params.data.reason || params.data.label
            if (reasonText && typeof reasonText === 'string') {
              reasonHtml = `<div style="color: #666; font-size: 11px;">${reasonText}</div>`
            }
          }
          
          return `
            <div style="padding: 4px 0;">
              <div style="font-weight: 600; margin-bottom: 4px;">${relationLabels[params.data.relationType] || '关联'}</div>
              ${reasonHtml}
            </div>
          `
        }
        const typeLabels: Record<string, string> = {
          paper: '📄 论文',
          background: '🎯 研究背景',
          method: '⚙️ 研究方法',
          innovation: '💡 创新点',
          conclusion: '✅ 结论'
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
      orient: 'vertical', 
      right: 15, 
      top: 15,
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderRadius: 10,
      padding: [12, 16],
      textStyle: { fontSize: 12, color: '#555' },
      itemWidth: 16,
      itemHeight: 10,
      itemGap: 10,
      selector: false,
      selectedMode: false
    },
    series: [{
      type: 'graph',
      layout: 'force',
      data: nodes.map(n => ({
        ...n,
        symbol: getSymbolByType(n.type),
        symbolSize: (n.type === 'paper' ? 55 : 38) + Math.min(nodeConnCount[n.id] || 0, 12),
        itemStyle: {
          borderWidth: n.type === 'paper' ? 3 : 2,
          borderColor: n.type === 'paper' ? '#fff' : 'rgba(255,255,255,0.6)',
          shadowBlur: n.type === 'paper' ? 15 : 8,
          shadowColor: 'rgba(0,0,0,0.12)',
          shadowOffsetY: 2,
        },
      })),
      links: links.map(l => ({
        ...l,
        lineStyle: {
          type: ['semantic', 'extends', 'applies', 'compares', 'related'].includes(l.relationType) ? 'dashed' : 'solid',
          color: l.relationType === 'citation' ? 'rgba(153,153,153,0.35)' :
                 ['semantic', 'extends', 'applies', 'compares', 'related'].includes(l.relationType) ? 'rgba(99,132,180,0.4)' : 'rgba(120,140,170,0.25)',
          curveness: ['semantic', 'extends', 'applies', 'compares', 'related'].includes(l.relationType) ? 0.25 : 0.05,
          width: l.relationType === 'ownership' ? 2.5 : 1.8,
          opacity: 0.7,
        },
        label: { show: false },
      })),
      categories: currentCategories,
      roam: true,
      draggable: true,
      force: forceConfig,
      emphasis: {
        focus: 'adjacency',
        itemStyle: {
          shadowBlur: 20,
          shadowColor: 'rgba(74, 157, 154, 0.4)',
          shadowOffsetY: 3,
        },
        label: {
          fontWeight: 700,
          fontSize: 12,
        },
      },
      label: { 
        show: true, 
        position: 'right', 
        fontSize: 11,
        fontWeight: 500,
        color: '#2c3e50',
        distance: 10,
        formatter: (params: any) => {
          if (params.data.type === 'paper') {
            return params.name
          }
          const name = params.name
          return name.length > 10 ? name.substring(0, 10) + '…' : name
        }
      },
      blur: {
        itemStyle: {
          opacity: 0.15
        },
        lineStyle: {
          opacity: 0.05
        },
        label: {
          show: false
        }
      }
    }],
  }
  chartInstance.setOption(option, { notMerge: true })
  chartInstance?.off('click', handleChartClick)
  chartInstance?.on('click', handleChartClick) 
}

// 综合筛选并渲染（仅用于四要素图谱）
const applyFilterAndRender = () => {
  if (graphType.value !== 'elements') {
    renderChart(cachedNodes, cachedLinks)
    return
  }
  
  const visibleTypes: NodeType[] = ['paper']
  if (filters.background) visibleTypes.push('background')
  if (filters.method) visibleTypes.push('method')
  if (filters.innovation) visibleTypes.push('innovation')
  if (filters.conclusion) visibleTypes.push('conclusion')

  const filteredNodes = cachedNodes.filter(n => visibleTypes.includes(n.type))
  const nodeIds = new Set(filteredNodes.map(n => n.id))
  const filteredLinks = cachedLinks.filter(l => nodeIds.has(l.source) && nodeIds.has(l.target))

  renderChart(filteredNodes, filteredLinks)
}

// 监听筛选条件（仅四要素图谱）
watch(
  () => [filters.background, filters.method, filters.innovation, filters.conclusion],
  () => {
    if (graphType.value === 'elements') {
      applyFilterAndRender()
    }
  },
  { deep: true }
)

// 监听图谱类型切换
watch(graphType, (type) => {
  if (type === 'elements') {
    buildGraphFromPapers()
  } else if (type === 'similarity') {
    loadSimilarityGraph()
  } else if (type === 'llm') {
    loadLLMGraph()
  }
})

// 监听文件夹变化
watch(() => folderStore.currentFolderId, () => {
  if (graphType.value === 'elements') {
    buildGraphFromPapers()
  } else if (graphType.value === 'similarity') {
    loadSimilarityGraph()
  } else if (graphType.value === 'llm') {
    loadLLMGraph()
  }
})

// 监听论文列表变化
watch(paperStore.papers, () => {
  if (graphType.value === 'elements') {
    buildGraphFromPapers()
  }
}, { deep: true })

// ---- 点击节点 ----
const handleChartClick = (params: any) => {
  if (params.dataType === 'node') {
    selectedNodeData.value = params.data
    nodeDetailVisible.value = true
  }
}

// 跳转论文
const handleNavigateToPaper = (paperId: string) => {
  nodeDetailVisible.value = false
  if (!paperId) {
    ElMessage.warning('该节点未关联论文')
    return
  }
  router.push({ name: 'paper-pdf', params: { paperId } })
    .catch(() => ElMessage.error('页面跳转失败'))
}

// ---- 生命周期 ----
onMounted(async () => {
  if (paperStore.papers.length === 0) {
    await paperStore.loadPapers()
  }
  
  // 根据当前图谱类型加载数据
  if (graphType.value === 'elements') {
    buildGraphFromPapers()
  } else if (graphType.value === 'similarity') {
    loadSimilarityGraph()
  } else if (graphType.value === 'llm') {
    loadLLMGraph()
  }
  
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
  if ((chartInstance as any)?._cleanupHandlers) {
    ;(chartInstance as any)._cleanupHandlers()
  }
  chartInstance?.dispose()
})
</script>

<template>
  <div class="graph-panel">
    <header class="graph-header">
      <div class="header-left">
        <!-- 图谱类型切换 -->
        <el-radio-group v-model="graphType" size="small" class="graph-type-switch">
          <el-radio-button label="elements">四要素图谱</el-radio-button>
          <el-radio-button label="similarity">相似度图谱</el-radio-button>
          <el-radio-button label="llm">主题聚类</el-radio-button>
        </el-radio-group>
        
        <!-- 四要素筛选器（仅四要素图谱显示） -->
        <div v-if="graphType === 'elements'" class="graph-filters">
          <el-checkbox v-model="filters.background" size="small" class="filter-chip">
            <span class="filter-icon" style="background: #6b8e8e" /> 研究背景
          </el-checkbox>
          <el-checkbox v-model="filters.method" size="small" class="filter-chip">
            <span class="filter-icon" style="background: #e8b86d" /> 研究方法
          </el-checkbox>
          <el-checkbox v-model="filters.innovation" size="small" class="filter-chip">
            <span class="filter-icon" style="background: #c17767" /> 创新点
          </el-checkbox>
          <el-checkbox v-model="filters.conclusion" size="small" class="filter-chip">
            <span class="filter-icon" style="background: #4a9d9a" /> 结论
          </el-checkbox>
        </div>
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
  justify-content: flex-start;
  padding-bottom: 1rem;
  border-bottom: 2px solid var(--line-soft);
  background: linear-gradient(to bottom, rgba(255,255,255,0.9), transparent);
  flex-shrink: 0;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}

.graph-type-switch {
  display: flex;
  gap: 0.5rem;
}

.graph-filters {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.filter-chip {
  padding: 6px 14px !important;
  border-radius: 20px !important;
  background: rgba(255,255,255,0.8) !important;
  border: 1px solid var(--line-soft) !important;
  font-size: 13px !important;
}

.filter-icon {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 6px;
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
  border-radius: 16px;
  background: linear-gradient(135deg, #f8fafc 0%, #eef2f7 50%, #f1f5f9 100%);
  box-shadow: inset 0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.04);
  overflow: hidden;
}

.graph-chart {
  width: 100%;
  height: 100%;
}
</style>