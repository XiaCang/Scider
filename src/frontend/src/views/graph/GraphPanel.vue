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
import { fetchSimilarityGraphApi } from '../../api/graph'

const categories = [
  { name: '论文', itemStyle: { color: '#173668' } },
  { name: '研究背景', itemStyle: { color: '#a78bfa' } },
  { name: '研究方法', itemStyle: { color: '#3b82f6' } },
  { name: '创新点', itemStyle: { color: '#eab308' } },
  { name: '结论', itemStyle: { color: '#22c55e' } },
]

const router = useRouter()
const folderStore = useFolderStore()
const paperStore = usePaperStore()
const chartRef = ref<HTMLDivElement | null>(null)
let chartInstance: echarts.ECharts | null = null
const isLoading = ref(false)

// 节点详情
const nodeDetailVisible = ref(false)
const selectedNodeData = ref<GraphNode | null>(null)

// 筛选器
const filters = reactive({
  background: false,
  method: false,
  innovation: false,
  conclusion: false,
})

// 缓存全量节点与边（由论文数据构建）
let cachedNodes: GraphNode[] = []
let cachedLinks: GraphLink[] = []


const getSymbolByType = (type: NodeType) => {
  switch (type) {
    case 'background': return 'circle'
    case 'method': return 'rect'
    case 'innovation': return 'diamond'
    case 'conclusion': return 'triangle'
    default: return 'circle'
  }
}

// ---- 从论文数据构建图谱 ----
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

  // 跨论文语义关联：同类型要素之间建立关联
  for (const dim of dimensionConfig) {
    const elemNodes = nodes.filter(n => n.type === dim.nodeType)
    for (let i = 0; i < elemNodes.length; i++) {
      for (let j = i + 1; j < elemNodes.length; j++) {
        links.push({
          source: elemNodes[i].id,
          target: elemNodes[j].id,
          relationType: 'semantic',
          label: `同属「${dim.label}」维度`,
        })
      }
    }
  }

  cachedNodes = nodes
  cachedLinks = links
  applyFilterAndRender()
  isLoading.value = false

  // 异步加载后端相似度边（增强性，不阻塞主图谱）
  loadSimilarityEdges()
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

// ---- 从后端加载基于 embedding 余弦相似度的边 ----
async function loadSimilarityEdges() {
  try {
    const res: any = await fetchSimilarityGraphApi({
      folder_id: folderStore.currentFolderId,
      max_nodes: 200,
      min_similarity: 0.55,
      top_k: 8,
    })
    const payload = res?.data
    if (payload?.links?.length) {
      for (const link of payload.links) {
        cachedLinks.push({
          source: link.source,
          target: link.target,
          relationType: 'semantic' as const,
          label: link.label,
        })
      }
      applyFilterAndRender()
    }
  } catch {
    // 相似度边是增强性的，不阻塞主图谱渲染
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
            citation: '引用关系'
          }
          // 处理 label 可能是对象的情况
          let labelText = ''
          if (params.data.label) {
            labelText = typeof params.data.label === 'string' 
              ? params.data.label 
              : JSON.stringify(params.data.label)
          }
          return `
            <div style="padding: 4px 0;">
              <div style="font-weight: 600; margin-bottom: 4px;">${relationLabels[params.data.relationType] || '关联'}</div>
              ${labelText ? `<div style="color: #666; font-size: 11px;">${labelText}</div>` : ''}
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
        return `
          <div style="padding: 4px 0;">
            <div style="font-weight: 600; font-size: 13px; margin-bottom: 4px;">${params.name}</div>
            <div style="color: #666; font-size: 11px;">${typeLabels[params.data.type] || '节点'}</div>
          </div>
        `
      }
    },
    legend: { 
      data: categories.map(c => c.name), 
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
      selectedMode: false  // 禁用图例的点击和悬停交互
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
          type: l.relationType === 'semantic' ? 'dashed' : 'solid',
          color: l.relationType === 'citation' ? 'rgba(153,153,153,0.35)' :
                 l.relationType === 'semantic' ? 'rgba(99,132,180,0.4)' : 'rgba(120,140,170,0.25)',
          curveness: l.relationType === 'semantic' ? 0.25 : 0.08,
          width: l.relationType === 'ownership' ? 2.5 : 1.8,
          opacity: 0.7,
        },
        label: { show: false },
      })),
      categories,
      roam: true,
      draggable: true,
      force: { repulsion: 1000, gravity: 0.03, edgeLength: [180, 350], friction: 0.65 },
      emphasis: { /* 同原代码 */ },
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
      // 静默状态的样式
      blur: {
        itemStyle: {
          opacity: 0.3
        },
        lineStyle: {
          opacity: 0.1
        },
        label: {
          show: false
        }
      }
    }],
  }
  chartInstance.setOption(option, { notMerge: true })
  chartInstance?.on('click', handleChartClick) 
}

// 综合筛选并渲染
const applyFilterAndRender = () => {
  if (cachedNodes.length === 0) return

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

// 监听筛选条件
watch(
  () => [filters.background, filters.method, filters.innovation, filters.conclusion],
  applyFilterAndRender,
  { deep: true }
)
// 监听文件夹变化 → 重新构建图谱
watch(() => folderStore.currentFolderId, () => {
  buildGraphFromPapers()
})
// 监听论文列表变化 → 重新构建图谱
watch(() => paperStore.papers.length, () => {
  buildGraphFromPapers()
})

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
  // 确保论文数据已加载
  if (paperStore.papers.length === 0) {
    await paperStore.loadPapers()
  }
  buildGraphFromPapers()
  window.addEventListener('resize', () => chartInstance?.resize())
})
onUnmounted(() => {
  window.removeEventListener('resize', () => chartInstance?.resize())
  chartInstance?.dispose()
})
</script>

<template>
  <div class="graph-panel">
    <header class="graph-header">
      <div class="header-left">
        <div class="graph-filters">
          <el-checkbox v-model="filters.background" size="small" class="filter-chip">
            <span class="filter-icon" style="background: #a78bfa" /> 研究背景
          </el-checkbox>
          <el-checkbox v-model="filters.method" size="small" class="filter-chip">
            <span class="filter-icon" style="background: #3b82f6" /> 研究方法
          </el-checkbox>
          <el-checkbox v-model="filters.innovation" size="small" class="filter-chip">
            <span class="filter-icon" style="background: #eab308" /> 创新点
          </el-checkbox>
          <el-checkbox v-model="filters.conclusion" size="small" class="filter-chip">
            <span class="filter-icon" style="background: #22c55e" /> 结论
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

.section-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: #1a202c;
  margin: 0;
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