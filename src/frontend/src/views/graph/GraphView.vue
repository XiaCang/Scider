<script setup lang="ts">
import { ref, onMounted, onUnmounted, reactive, watch } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import GraphNodeDetail from './GraphNodeDetail.vue'
import type { LibraryPaper } from '../../api/library'

// --- 类型定义 ---
type NodeType = 'paper' | 'background' | 'method' | 'innovation' | 'conclusion'
type RelationType = 'ownership' | 'semantic' | 'citation'

interface GraphNode {
  id: string
  name: string
  type: NodeType
  category: number // 对应 ECharts categories 索引
  value?: number
  symbol?: string
  paperId?: string  // 关联的论文ID（仅四要素节点有）
  paperTitle?: string  // 论文名称简称（用于显示）
  content?: string  // 要素内容文本
  paperInfo?: LibraryPaper  // 论文完整信息（仅论文节点有）
}

interface GraphLink {
  source: string
  target: string
  relationType: RelationType
  label?: string
}

// --- 状态管理 ---
const router = useRouter()
const chartRef = ref<HTMLDivElement | null>(null)
let chartInstance: echarts.ECharts | null = null
const isLoading = ref(false)

// 节点详情抽屉状态
const nodeDetailVisible = ref(false)
const selectedNodeData = ref<GraphNode | null>(null)

// 筛选器状态（默认全部为 false，只显示论文节点）
const filters = reactive({
  background: false,
  method: false,
  innovation: false,
  conclusion: false,
})

// 缓存图谱数据，用于筛选时重新渲染
let cachedNodes: GraphNode[] = []
let cachedLinks: GraphLink[] = []

// 画布高度控制
const canvasHeight = ref(600) // 初始高度 600px
let isResizing = false // 简化为普通变量,无需响应式
const resizeStartY = ref(0)
const resizeStartHeight = ref(0)
const MIN_HEIGHT = 300 // 最小高度
const MAX_HEIGHT = 2000 // 最大高度

// --- 数据模拟与配置 ---
const categories = [
  { name: '论文', itemStyle: { color: '#173668' } },
  { name: '研究背景', itemStyle: { color: '#a78bfa' } },
  { name: '研究方法', itemStyle: { color: '#3b82f6' } },
  { name: '创新点', itemStyle: { color: '#eab308' } },
  { name: '结论', itemStyle: { color: '#22c55e' } },
]

const getSymbolByType = (type: NodeType) => {
  switch (type) {
    case 'background': return 'circle'
    case 'method': return 'rect'
    case 'innovation': return 'diamond'
    case 'conclusion': return 'triangle'
    default: return 'circle'
  }
}

// 模拟论文数据（扩展为3篇论文，便于测试）
const mockPapers: Record<string, LibraryPaper> = {
  'p1': {
    id: 'p1',
    title: 'An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale',
    authors: 'Alexey Dosovitskiy, Lucas Beyer, Alexander Kolesnikov et al.',
    year: 2021,
    status: 'Confirmed',
    source: 'ICLR 2021',
    keyPoints: {
      background: '传统CNN在处理长距离依赖时存在局限性，需要更好的全局上下文建模能力。视觉任务中局部感受野限制了模型对图像整体结构的理解。',
      method: '将图像分割为固定大小的visual patches（如16x16像素），将其线性嵌入为tokens序列，使用标准的Transformer编码器进行处理。引入位置编码保持空间信息。',
      innovation: '首次将纯Transformer架构（不含任何卷积操作）成功应用于计算机视觉任务，证明了自注意力机制在视觉领域的有效性。',
      conclusion: 'ViT在大规模数据集（如JFT-300M）预训练后，在ImageNet等基准测试上可以达到甚至超越SOTA CNN的性能，且计算效率更高。'
    }
  },
  'p2': {
    id: 'p2',
    title: 'Attention Is All You Need',
    authors: 'Ashish Vaswani, Noam Shazeer, Niki Parmar et al.',
    year: 2017,
    status: 'Confirmed',
    source: 'NeurIPS 2017',
    keyPoints: {
      background: '传统的RNN和CNN序列模型存在训练效率低、难以并行化、长距离依赖建模困难等问题。递归结构限制了计算效率。',
      method: '提出完全基于自注意力机制的Transformer架构，采用多头注意力（Multi-Head Attention）、位置编码和前馈神经网络。摒弃了循环和卷积结构。',
      innovation: '引入缩放点积注意力（Scaled Dot-Product Attention）和多头机制，实现了高度并行化的序列建模。提出了Encoder-Decoder架构的标准范式。',
      conclusion: 'Transformer在机器翻译任务上取得了当时最好的结果（BLEU分数显著提升），同时训练时间大幅减少。成为NLP领域的基础架构。'
    }
  },
  'p3': {
    id: 'p3',
    title: 'BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding',
    authors: 'Jacob Devlin, Ming-Wei Chang, Kenton Lee, Kristina Toutanova',
    year: 2019,
    status: 'PendingConfirmation',
    source: 'NAACL 2019',
    keyPoints: {
      background: '传统的语言模型只能单向（从左到右或从右到左）捕捉上下文信息，无法充分利用双向语境。下游任务需要大量标注数据进行微调。',
      method: '采用Masked Language Model (MLM) 和 Next Sentence Prediction (NSP) 两个预训练任务。使用Transformer Encoder进行双向编码，随机掩盖15%的输入token进行预测。',
      innovation: '首次实现深度双向语言表示的预训练，通过MLM任务让模型同时关注左右两侧上下文。提出了"预训练+微调"的范式，显著降低了对标注数据的需求。',
      conclusion: 'BERT在11个NLP任务上刷新了最佳记录，包括GLUE、SQuAD等基准测试。证明了大规模预训练对自然语言理解的巨大价值。'
    }
  }
}

// --- 核心逻辑：按需加载与图谱渲染 ---
const fetchGraphData = async (seedPaperId?: string, expandDirection?: 'upstream' | 'downstream') => {
  isLoading.value = true
  try {
    // TODO: 替换为真实 API 调用
    // const res = await fetch(`/api/graph/nodes?seed=${seedPaperId}&direction=${expandDirection}`)
    
    // 模拟数据：展示3篇论文及其四要素节点，以及跨论文的语义关联
    const mockNodes: GraphNode[] = [
      // === 论文1: ViT ===
      { 
        id: 'p1', 
        name: 'Dosovitskiy(2021)', 
        type: 'paper', 
        category: 0, 
        value: 20,
        paperInfo: mockPapers['p1']
      },
      { 
        id: 'b1', 
        name: 'CNN长距离依赖局限', 
        type: 'background', 
        category: 1, 
        value: 5,
        paperId: 'p1',
        paperTitle: 'An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale',
        paperInfo: mockPapers['p1'],
        content: '传统CNN在处理长距离依赖时存在局限性，需要更好的全局上下文建模能力。视觉任务中局部感受野限制了模型对图像整体结构的理解。'
      },
      { 
        id: 'm1', 
        name: 'Visual Patches + Transformer', 
        type: 'method', 
        category: 2, 
        value: 8,
        paperId: 'p1',
        paperTitle: 'An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale',
        paperInfo: mockPapers['p1'],
        content: '将图像分割为固定大小的visual patches（如16x16像素），将其线性嵌入为tokens序列，使用标准的Transformer编码器进行处理。引入位置编码保持空间信息。'
      },
      { 
        id: 'i1', 
        name: '纯Transformer视觉架构', 
        type: 'innovation', 
        category: 3, 
        value: 6,
        paperId: 'p1',
        paperTitle: 'An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale',
        paperInfo: mockPapers['p1'],
        content: '首次将纯Transformer架构（不含任何卷积操作）成功应用于计算机视觉任务，证明了自注意力机制在视觉领域的有效性。'
      },
      { 
        id: 'c1', 
        name: 'ImageNet SOTA性能', 
        type: 'conclusion', 
        category: 4, 
        value: 5,
        paperId: 'p1',
        paperTitle: 'An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale',
        paperInfo: mockPapers['p1'],
        content: 'ViT在大规模数据集（如JFT-300M）预训练后，在ImageNet等基准测试上可以达到甚至超越SOTA CNN的性能，且计算效率更高。'
      },
      
      // === 论文2: Attention Is All You Need ===
      { 
        id: 'p2', 
        name: 'Vaswani(2017)', 
        type: 'paper', 
        category: 0, 
        value: 18,
        paperInfo: mockPapers['p2']
      },
      { 
        id: 'b2', 
        name: 'RNN并行化困难', 
        type: 'background', 
        category: 1, 
        value: 5,
        paperId: 'p2',
        paperTitle: 'Attention Is All You Need',
        paperInfo: mockPapers['p2'],
        content: '传统的RNN和CNN序列模型存在训练效率低、难以并行化、长距离依赖建模困难等问题。递归结构限制了计算效率。'
      },
      { 
        id: 'm2', 
        name: 'Multi-Head Self-Attention', 
        type: 'method', 
        category: 2, 
        value: 9,
        paperId: 'p2',
        paperTitle: 'Attention Is All You Need',
        paperInfo: mockPapers['p2'],
        content: '提出完全基于自注意力机制的Transformer架构，采用多头注意力（Multi-Head Attention）、位置编码和前馈神经网络。摒弃了循环和卷积结构。'
      },
      { 
        id: 'i2', 
        name: '缩放点积注意力机制', 
        type: 'innovation', 
        category: 3, 
        value: 7,
        paperId: 'p2',
        paperTitle: 'Attention Is All You Need',
        paperInfo: mockPapers['p2'],
        content: '引入缩放点积注意力（Scaled Dot-Product Attention）和多头机制，实现了高度并行化的序列建模。提出了Encoder-Decoder架构的标准范式。'
      },
      { 
        id: 'c2', 
        name: '机器翻译BLEU提升', 
        type: 'conclusion', 
        category: 4, 
        value: 6,
        paperId: 'p2',
        paperTitle: 'Attention Is All You Need',
        paperInfo: mockPapers['p2'],
        content: 'Transformer在机器翻译任务上取得了当时最好的结果（BLEU分数显著提升），同时训练时间大幅减少。成为NLP领域的基础架构。'
      },
      
      // === 论文3: BERT ===
      { 
        id: 'p3', 
        name: 'Devlin(2019)', 
        type: 'paper', 
        category: 0, 
        value: 19,
        paperInfo: mockPapers['p3']
      },
      { 
        id: 'b3', 
        name: '单向语言模型局限', 
        type: 'background', 
        category: 1, 
        value: 5,
        paperId: 'p3',
        paperTitle: 'BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding',
        paperInfo: mockPapers['p3'],
        content: '传统的语言模型只能单向（从左到右或从右到左）捕捉上下文信息，无法充分利用双向语境。下游任务需要大量标注数据进行微调。'
      },
      { 
        id: 'm3', 
        name: 'Masked LM + NSP预训练', 
        type: 'method', 
        category: 2, 
        value: 8,
        paperId: 'p3',
        paperTitle: 'BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding',
        paperInfo: mockPapers['p3'],
        content: '采用Masked Language Model (MLM) 和 Next Sentence Prediction (NSP) 两个预训练任务。使用Transformer Encoder进行双向编码，随机掩盖15%的输入token进行预测。'
      },
      { 
        id: 'i3', 
        name: '深度双向语言表示', 
        type: 'innovation', 
        category: 3, 
        value: 7,
        paperId: 'p3',
        paperTitle: 'BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding',
        paperInfo: mockPapers['p3'],
        content: '首次实现深度双向语言表示的预训练，通过MLM任务让模型同时关注左右两侧上下文。提出了"预训练+微调"的范式，显著降低了对标注数据的需求。'
      },
      { 
        id: 'c3', 
        name: '11项NLP任务SOTA', 
        type: 'conclusion', 
        category: 4, 
        value: 6,
        paperId: 'p3',
        paperTitle: 'BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding',
        paperInfo: mockPapers['p3'],
        content: 'BERT在11个NLP任务上刷新了最佳记录，包括GLUE、SQuAD等基准测试。证明了大规模预训练对自然语言理解的巨大价值。'
      },
    ]

    const mockLinks: GraphLink[] = [
      // === 论文1的归属关系 ===
      { source: 'p1', target: 'b1', relationType: 'ownership' },
      { source: 'p1', target: 'm1', relationType: 'ownership' },
      { source: 'p1', target: 'i1', relationType: 'ownership' },
      { source: 'p1', target: 'c1', relationType: 'ownership' },
      
      // === 论文2的归属关系 ===
      { source: 'p2', target: 'b2', relationType: 'ownership' },
      { source: 'p2', target: 'm2', relationType: 'ownership' },
      { source: 'p2', target: 'i2', relationType: 'ownership' },
      { source: 'p2', target: 'c2', relationType: 'ownership' },
      
      // === 论文3的归属关系 ===
      { source: 'p3', target: 'b3', relationType: 'ownership' },
      { source: 'p3', target: 'm3', relationType: 'ownership' },
      { source: 'p3', target: 'i3', relationType: 'ownership' },
      { source: 'p3', target: 'c3', relationType: 'ownership' },
      
      // === 跨论文语义关联 ===
      // ViT的方法 与 Attention的方法 相近（都使用Transformer）
      { source: 'm1', target: 'm2', relationType: 'semantic', label: '方法相近：均采用Transformer架构' },
      
      // BERT继承了Attention的架构
      { source: 'm3', target: 'm2', relationType: 'semantic', label: '技术传承：基于Transformer Encoder' },
      
      // ViT的创新点受到Attention启发
      { source: 'i1', target: 'i2', relationType: 'semantic', label: '思想借鉴：自注意力机制迁移到视觉' },
      
      // BERT的双向性与Attention的多头机制有共通之处
      { source: 'i3', target: 'i2', relationType: 'semantic', label: '机制相似：均优化上下文建模' },
      
      // === 引文关系 ===
      // ViT 引用了 Attention
      { source: 'p1', target: 'p2', relationType: 'citation', label: '引用' },
      
      // BERT 引用了 Attention
      { source: 'p3', target: 'p2', relationType: 'citation', label: '引用' },
    ]

    renderChart(mockNodes, mockLinks)
  } catch (error) {
    ElMessage.error('加载图谱数据失败')
  } finally {
    isLoading.value = false
  }
}

const renderChart = (nodes: GraphNode[], links: GraphLink[]) => {
  if (!chartRef.value) return
  if (!chartInstance) chartInstance = echarts.init(chartRef.value)

  // 缓存数据供筛选时使用
  cachedNodes = nodes
  cachedLinks = links

  // 根据筛选器过滤节点（论文节点始终显示）
  const visibleTypes: NodeType[] = ['paper']
  if (filters.background) visibleTypes.push('background')
  if (filters.method) visibleTypes.push('method')
  if (filters.innovation) visibleTypes.push('innovation')
  if (filters.conclusion) visibleTypes.push('conclusion')

  const filteredNodes = nodes.filter(n => visibleTypes.includes(n.type))
  const nodeIds = new Set(filteredNodes.map(n => n.id))
  const filteredLinks = links.filter(l => nodeIds.has(l.source) && nodeIds.has(l.target))

  // 统计每个节点的连接数，用于动态调整大小
  const nodeConnectionCount: Record<string, number> = {}
  filteredLinks.forEach(link => {
    nodeConnectionCount[link.source] = (nodeConnectionCount[link.source] || 0) + 1
    nodeConnectionCount[link.target] = (nodeConnectionCount[link.target] || 0) + 1
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
          return `
            <div style="padding: 4px 0;">
              <div style="font-weight: 600; margin-bottom: 4px;">${relationLabels[params.data.relationType] || '关联'}</div>
              ${params.data.label ? `<div style="color: #666; font-size: 11px;">${params.data.label}</div>` : ''}
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
      data: filteredNodes.map(n => {
        const connections = nodeConnectionCount[n.id] || 0
        const baseSize = n.type === 'paper' ? 55 : 38
        const sizeBoost = Math.min(connections * 3, 12)  // 根据连接数适度增大
        
        return { 
          ...n, 
          symbol: getSymbolByType(n.type),
          symbolSize: baseSize + sizeBoost,
          itemStyle: {
            borderWidth: n.type === 'paper' ? 3 : 2,
            borderColor: n.type === 'paper' ? '#fff' : 'rgba(255, 255, 255, 0.6)',
            shadowBlur: n.type === 'paper' ? 15 : 8,
            shadowColor: 'rgba(0, 0, 0, 0.12)',
            shadowOffsetY: 2
          }
        }
      }),
      links: filteredLinks.map(l => ({
        ...l,
        lineStyle: {
          type: l.relationType === 'semantic' ? 'dashed' : 'solid',
          color: l.relationType === 'citation' ? 'rgba(153, 153, 153, 0.35)' : 
                 l.relationType === 'semantic' ? 'rgba(99, 132, 180, 0.4)' : 'rgba(120, 140, 170, 0.25)',
          curveness: l.relationType === 'semantic' ? 0.25 : 0.08,
          width: l.relationType === 'ownership' ? 2.5 : 1.8,
          opacity: 0.7
        },
        label: { 
          show: false,  // 默认隐藏连线标签，保持简洁
          formatter: l.label,
          fontSize: 10,
          color: '#666',
          backgroundColor: 'rgba(255, 255, 255, 0.9)',
          padding: [2, 6],
          borderRadius: 4
        }
      })),
      categories,
      roam: true,
      draggable: true,
      force: { 
        repulsion: 1000,  // 更强的排斥力
        gravity: 0.03,    // 更低的重力
        edgeLength: [180, 350],  // 更长的边距
        friction: 0.65,   // 更高摩擦力
        layoutAnimation: true
      },
      emphasis: { 
        focus: 'adjacency',
        scale: true,
        lineStyle: {
          width: 5,
          opacity: 0.9,
          shadowBlur: 8,
          shadowColor: 'rgba(0, 0, 0, 0.2)'
        },
        itemStyle: {
          shadowBlur: 25,
          shadowColor: 'rgba(0, 0, 0, 0.35)',
          borderColor: '#fff',
          borderWidth: 4
        },
        label: {
          show: true,
          fontSize: 13,
          fontWeight: 'bold'
        }
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
    }]
  }

  chartInstance.setOption(option, { notMerge: true })

  // 绑定点击事件处理节点详情
  chartInstance.off('click')
  chartInstance.on('click', handleChartClick)
}

// --- 交互事件处理 ---
const handleChartClick = (params: any) => {
  if (params.dataType === 'node') {
    selectedNodeData.value = params.data
    nodeDetailVisible.value = true
  }
}

// 监听筛选器变化，重新渲染图谱
watch(
  () => [filters.background, filters.method, filters.innovation, filters.conclusion],
  () => {
    if (cachedNodes.length > 0 && cachedLinks.length > 0) {
      renderChart(cachedNodes, cachedLinks)
    }
  },
  { deep: true }
)

// 从节点详情跳转到论文PDF预览页
const handleNavigateToPaper = (paperId: string) => {
  // 关闭节点详情抽屉
  nodeDetailVisible.value = false
  
  // 验证论文ID是否存在
  if (!paperId) {
    ElMessage.warning('该节点未关联论文')
    return
  }
  
  // 执行路由跳转
  router.push({
    name: 'paper-pdf',
    params: { paperId }
  }).then(() => {
    ElMessage.success('正在打开论文PDF预览')
  }).catch((error) => {
    console.error('路由跳转失败:', error)
    ElMessage.error('页面跳转失败，请重试')
  })
}

// 开始拖拽调整大小
const startResize = (event: MouseEvent) => {
  event.preventDefault()
  isResizing = true
  resizeStartY.value = event.clientY
  resizeStartHeight.value = canvasHeight.value
  
  document.addEventListener('mousemove', handleResizeMove)
  document.addEventListener('mouseup', stopResize)
  document.body.style.cursor = 'ns-resize'
  document.body.style.userSelect = 'none'
}

// 拖拽移动
const handleResizeMove = (event: MouseEvent) => {
  if (!isResizing) return
  
  const deltaY = event.clientY - resizeStartY.value
  let newHeight = resizeStartHeight.value + deltaY
  
  // 限制高度范围
  newHeight = Math.max(MIN_HEIGHT, Math.min(MAX_HEIGHT, newHeight))
  canvasHeight.value = newHeight
  
  // 实时调整图表大小
  if (chartInstance) {
    chartInstance.resize()
  }
}

// 停止拖拽
const stopResize = () => {
  isResizing = false
  document.removeEventListener('mousemove', handleResizeMove)
  document.removeEventListener('mouseup', stopResize)
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
  
  // 确保最终尺寸正确应用
  setTimeout(() => {
    if (chartInstance) {
      chartInstance.resize()
    }
  }, 50)
}

const handleResize = () => chartInstance?.resize()

onMounted(() => {
  fetchGraphData()
  window.addEventListener('resize', handleResize)
  // 移除冗余的 chartInstance 初始化,由 renderChart 统一处理并绑定事件
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  // 清理可能残留的拖拽监听器
  if (isResizing) {
    document.removeEventListener('mousemove', handleResizeMove)
    document.removeEventListener('mouseup', stopResize)
  }
  chartInstance?.dispose()
})
</script>

<template>
  <section class="graph-page">
    <header class="graph-header">
      <div class="header-left">
        <h1 class="section-title">Knowledge Graph</h1>
        <div class="graph-filters">
          <el-checkbox v-model="filters.background" size="small" class="filter-chip">
            <span class="filter-icon" style="background: #a78bfa;"></span>
            研究背景
          </el-checkbox>
          <el-checkbox v-model="filters.method" size="small" class="filter-chip">
            <span class="filter-icon" style="background: #3b82f6;"></span>
            研究方法
          </el-checkbox>
          <el-checkbox v-model="filters.innovation" size="small" class="filter-chip">
            <span class="filter-icon" style="background: #eab308;"></span>
            创新点
          </el-checkbox>
          <el-checkbox v-model="filters.conclusion" size="small" class="filter-chip">
            <span class="filter-icon" style="background: #22c55e;"></span>
            结论
          </el-checkbox>
        </div>
      </div>
      <div class="graph-tags">
        <span class="status-pill is-brand">
          <span class="pill-icon">🔬</span>
          Semantic Units
        </span>
      </div>
    </header>

    <section class="graph-canvas-wrapper">
      <div 
        class="graph-canvas" 
        :style="{ height: `${canvasHeight}px` }"
      >
        <div v-loading="isLoading" ref="chartRef" class="graph-chart"></div>
        
        <!-- 拖拽调整手柄 -->
        <div 
          class="resize-handle"
          @mousedown="startResize"
          title="拖拽调整画布高度"
        >
          <div class="resize-handle-bar"></div>
        </div>
      </div>
    </section>

    <!-- 节点详情抽屉 -->
    <GraphNodeDetail
      v-model="nodeDetailVisible"
      :node-data="selectedNodeData"
      @navigate-to-paper="handleNavigateToPaper"
    />
  </section>
</template>

<style scoped>
.graph-page { 
  display: flex;
  flex-direction: column;
  gap: 1.2rem; 
  height: 100%;
  padding: 0 1.5rem 1.5rem;
  overflow-y: auto;
}

.graph-header { 
  display: flex; 
  align-items: center; 
  justify-content: space-between; 
  padding-bottom: 1rem; 
  border-bottom: 2px solid var(--line-soft);
  background: linear-gradient(to bottom, rgba(255,255,255,0.9), transparent);
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
  letter-spacing: -0.02em;
}

.graph-filters { 
  display: flex; 
  gap: 0.75rem;
  flex-wrap: wrap;
}

.filter-chip {
  padding: 6px 14px !important;
  border-radius: 20px !important;
  background: rgba(255, 255, 255, 0.8) !important;
  border: 1px solid var(--line-soft) !important;
  transition: all 0.2s ease !important;
  font-size: 13px !important;
}

.filter-chip:hover {
  background: rgba(255, 255, 255, 1) !important;
  border-color: #cbd5e0 !important;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06) !important;
}

.filter-icon {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 6px;
}

.graph-tags {
  display: flex;
  align-items: center;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.08), rgba(99, 102, 241, 0.08));
  border: 1px solid rgba(59, 130, 246, 0.15);
  border-radius: 24px;
  font-size: 13px;
  font-weight: 600;
  color: #3b82f6;
}

.pill-icon {
  font-size: 14px;
}

.graph-canvas-wrapper {
  position: relative;
  width: 100%;
}

.graph-canvas { 
  position: relative; 
  width: 100%;
  min-height: 300px;
  border: 1px solid var(--line-soft); 
  border-radius: 16px;
  background: linear-gradient(135deg, #f8fafc 0%, #eef2f7 50%, #f1f5f9 100%);
  box-shadow: 
    inset 0 1px 3px rgba(0, 0, 0, 0.04),
    0 4px 12px rgba(0, 0, 0, 0.04);
  overflow: hidden;
  transition: height 0.1s ease-out;
}

.graph-chart { 
  width: 100%; 
  height: 100%; 
}

/* 拖拽调整手柄样式 */
.resize-handle {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 12px;
  cursor: ns-resize;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(to bottom, transparent, rgba(59, 130, 246, 0.05));
  transition: background 0.2s ease;
}

.resize-handle:hover {
  background: linear-gradient(to bottom, transparent, rgba(59, 130, 246, 0.15));
}

.resize-handle-bar {
  width: 60px;
  height: 4px;
  background: rgba(59, 130, 246, 0.3);
  border-radius: 2px;
  transition: all 0.2s ease;
}

.resize-handle:hover .resize-handle-bar {
  width: 80px;
  background: rgba(59, 130, 246, 0.5);
  box-shadow: 0 0 8px rgba(59, 130, 246, 0.3);
}

/* Element Plus 复选框样式覆盖 */
:deep(.el-checkbox__input.is-checked + .el-checkbox__label) {
  color: #2c3e50 !important;
  font-weight: 600;
}

:deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background-color: #3b82f6 !important;
  border-color: #3b82f6 !important;
}

:deep(.el-checkbox__label) {
  font-size: 13px;
  padding-left: 6px !important;
}
</style>