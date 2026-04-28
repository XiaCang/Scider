import type { LibraryPaper } from '../types/library'
import type { Folder } from '../types/folder'

// ==================== 测试数据定义 ====================
const testPapers: LibraryPaper[] = [
  {
    id: 'paper-1',
    title: 'Transformers in Vision',
    authors: 'A. Calianham',
    year: 2022,
    status: 'Processing',
    source: 'CVPR',
    keyPoints: {
      background: '视觉任务中传统CNN的局限性，需要更好的长距离依赖建模',
      method: '将图像分割为visual tokens，使用Transformer编码器处理',
      innovation: '首次将纯Transformer架构应用于计算机视觉任务',
      conclusion: 'ViT在大规模数据集上可以达到甚至超越SOTA CNN的性能'
    },
  },
  {
    id: 'paper-2',
    title: 'Transformers in Poraios and Grapheni Methods',
    authors: 'R. K. Rainur',
    year: 2023,
    status: 'PendingConfirmation',
    source: 'arXiv',
    keyPoints: {
      background: '多模态数据对齐和检索存在语义鸿沟问题',
      method: '采用跨模态对齐技术和混合检索策略',
      innovation: '提出新颖的跨模态表示学习方法',
      conclusion: '显著提升了跨模态检索的准确性和效率'
    },
  },
  {
    id: 'paper-3',
    title: 'Transformers in Vision',
    authors: 'R. S. Soft',
    year: 2023,
    status: 'Confirmed',
    source: 'NeurIPS',
    keyPoints: {
      background: '域适应和零样本迁移在实际应用中面临挑战',
      method: '利用领域自适应技术和零样本学习框架',
      innovation: '设计了新的域不变特征提取器',
      conclusion: '在多个基准测试中实现了优异的零样本迁移性能'
    },
  },
  {
    id: 'paper-4',
    title: 'Transformers in Vision',
    authors: 'R. C. Bamer, R.A',
    year: 2022,
    status: 'PendingConfirmation',
    source: 'ICLR',
    keyPoints: {
      background: '传统序列模型的训练效率和并行化能力不足',
      method: '引入自注意力机制实现并行处理',
      innovation: 'Attention机制大幅减少训练时间并提升模型表现',
      conclusion: 'Transformer成为NLP和CV领域的基础架构'
    },
  },
  {
    id: 'paper-5',
    title: 'Transformens and Meal Designers in Vision',
    authors: 'A. Steruan R. Maris',
    year: 2023,
    status: 'Confirmed',
    source: 'ECCV',
    keyPoints: {
      background: '视觉模型训练需要大量数据和计算资源',
      method: '优化数据集效率和训练配方设计',
      innovation: '提出更高效的训练策略和数据增强方法',
      conclusion: '在减少资源消耗的同时保持了模型性能'
    },
  },
]

const testFolders: Folder[] = [
  {
    id: 'folder-1',
    name: '深度学习',
    paperIds: ['paper-1', 'paper-2'],
    children: [
      {
        id: 'folder-1-1',
        name: 'Transformer',
        paperIds: ['paper-1'],
        children: [
          {
            id: 'folder-1-1-1',
            name: 'Attention机制',
            paperIds: [],
            children: [
              {
                id: 'folder-1-1-1-1',
                name: 'Self-Attention',
                paperIds: [],
                children: [
                  {
                    id: 'folder-1-1-1-1-1',
                    name: 'Multi-Head Attention',
                    paperIds: [],
                    children: []
                  }
                ]
              }
            ]
          },
          {
            id: 'folder-1-1-2',
            name: 'Positional Encoding',
            paperIds: [],
            children: []
          }
        ]
      },
      {
        id: 'folder-1-2',
        name: 'CNN',
        paperIds: ['paper-2'],
        children: []
      }
    ]
  },
  {
    id: 'folder-2',
    name: '计算机视觉',
    paperIds: ['paper-1', 'paper-3', 'paper-5'],
    children: [
      {
        id: 'folder-2-1',
        name: '目标检测',
        paperIds: ['paper-3'],
        children: []
      }
    ]
  },
  {
    id: 'folder-3',
    name: '自然语言处理',
    paperIds: ['paper-2', 'paper-4'],
    children: []
  }
]

export { testPapers, testFolders }