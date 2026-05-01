import type { LibraryPaper } from '../types/library'
import type { SearchResult, CitationPaper } from '../discover/types'

export const yearOptions = [
  { label: '全部年份', value: '' },
  { label: '2025', value: '2025' },
  { label: '2024', value: '2024' },
  { label: '2023', value: '2023' },
  { label: '2022', value: '2022' },
  { label: '2021及更早', value: '2021' },
]

export const venueOptions = [
  { label: '全部来源', value: '' },
  { label: 'arXiv', value: 'arXiv' },
  { label: 'SIGIR', value: 'SIGIR' },
  { label: 'CHI', value: 'CHI' },
  { label: 'ACL', value: 'ACL' },
  { label: 'NeurIPS', value: 'NeurIPS' },
]

export const sortOptions = [
  { label: '相关性', value: 'relevance' },
  { label: '最新发表', value: 'year-desc' },
  { label: '最早发表', value: 'year-asc' },
  { label: '标题 A-Z', value: 'title-asc' },
]

/** 推荐论文 mock 数据 */
export const recommendations: SearchResult[] = [
  {
    id: 'rec-1',
    title: 'Scientific Document VLMs for Reading Assistance',
    authors: 'Smith, J. et al.',
    venue: 'arXiv',
    year: 2025,
    relation: 'Trending',
    reason: '和你当前的"多模态论文理解"方向高度接近，可作为入门综述入口。',
    description: '该研究探讨了视觉语言模型在科学文档阅读辅助中的应用，提供了系统性的分析和评估。',
  },
  {
    id: 'rec-2',
    title: 'Citation-aware Retrieval for Research Exploration',
    authors: 'Johnson, M. et al.',
    venue: 'SIGIR',
    year: 2024,
    relation: 'Upstream',
    reason: '适合作为文献追踪与上下游检索能力的技术参考。',
    description: '提出了一种基于引用感知的检索方法，能够有效追踪学术文献的上下游关系。',
  },
  {
    id: 'rec-3',
    title: 'Interactive Knowledge Graphs for Scholarly Search',
    authors: 'Williams, K. et al.',
    venue: 'CHI',
    year: 2024,
    relation: 'Downstream',
    reason: '和知识图谱可视化及科研探索交互关系较强。',
    description: '研究了交互式知识图谱在学术搜索中的应用，提升了用户探索和理解复杂研究领域的能力。',
  },
  {
    id: 'rec-4',
    title: 'Large Language Models for Scientific Discovery',
    authors: 'Zhang, L. et al.',
    venue: 'NeurIPS',
    year: 2025,
    description: '探讨了大语言模型在科学发现过程中自动化的潜力和挑战。',
  },
  {
    id: 'rec-5',
    title: 'Attention Mechanisms in Transformer Architectures',
    authors: 'Chen, W. et al.',
    venue: 'ACL',
    year: 2023,
    description: '系统分析比较了各类注意力机制在Transformer架构中的表现和效率。',
  },
]

export const libraryPapers: LibraryPaper[] = [
  {
    id: 'paper-1',
    title: 'Transformers in Vision',
    authors: 'A. Calianham',
    year: 2022,
    status: 'Confirmed',
    source: 'CVPR',
    keyPoints: {
      background: '视觉任务中传统CNN的局限性，需要更好的长距离依赖建模',
      method: '将图像分割为visual tokens，使用Transformer编码器处理',
      innovation: '首次将纯Transformer架构应用于计算机视觉任务',
      conclusion: 'ViT在大规模数据集上可以达到甚至超越SOTA CNN的性能',
    },
  },
  {
    id: 'paper-2',
    title: 'Transformers in Poraios and Grapheni Methods',
    authors: 'R. K. Rainur',
    year: 2023,
    status: 'Confirmed',
    source: 'arXiv',
    keyPoints: {
      background: '多模态数据对齐和检索存在语义鸿沟问题',
      method: '采用跨模态对齐技术和混合检索策略',
      innovation: '提出新颖的跨模态表示学习方法',
      conclusion: '显著提升了跨模态检索的准确性和效率',
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
      conclusion: '在多个基准测试中实现了优异的零样本迁移性能',
    },
  },
  {
    id: 'paper-4',
    title: 'Transformers in Vision',
    authors: 'R. C. Bamer, R.A',
    year: 2022,
    status: 'Confirmed',
    source: 'ICLR',
    keyPoints: {
      background: '传统序列模型的训练效率和并行化能力不足',
      method: '引入自注意力机制实现并行处理',
      innovation: 'Attention机制大幅减少训练时间并提升模型表现',
      conclusion: 'Transformer成为NLP和CV领域的基础架构',
    },
  },
]

export function buildUpstreamPapers(selectedPaperTitle: string): CitationPaper[] {
  return [
    {
      id: 'up-1',
      title: 'Transformer Architecture Analysis',
      authors: 'Vaswani, A. et al.',
      venue: 'NeurIPS',
      year: 2017,
      relation: 'upstream',
      citationCount: 15240,
      description: `基于 "${selectedPaperTitle}" 的原始Transformer论文，奠定了注意力机制的基础。`,
    },
    {
      id: 'up-2',
      title: 'BERT: Pre-training of Deep Bidirectional Transformers',
      authors: 'Devlin, J. et al.',
      venue: 'NAACL',
      year: 2019,
      relation: 'upstream',
      citationCount: 24320,
      description: 'BERT模型开创了双向预训练的新时代。',
    },
    {
      id: 'up-3',
      title: 'RoBERTa: A Robustly Optimized BERT Pretraining Approach',
      authors: 'Liu, Y. et al.',
      venue: 'arXiv',
      year: 2019,
      relation: 'upstream',
      citationCount: 8760,
      description: '对BERT的训练方式进行了优化，提升了性能。',
    },
  ]
}

export function buildDownstreamPapers(): CitationPaper[] {
  return [
    {
      id: 'down-1',
      title: 'GPT-3: Language Models are Few-Shot Learners',
      authors: 'Brown, T. et al.',
      venue: 'NeurIPS',
      year: 2020,
      relation: 'downstream',
      citationCount: 12540,
      description: 'GPT-3展示了大规模语言模型的强大能力。',
    },
    {
      id: 'down-2',
      title: 'T5: Exploring the Limits of Transfer Learning',
      authors: 'Raffel, C. et al.',
      venue: 'JMLR',
      year: 2020,
      relation: 'downstream',
      citationCount: 7890,
      description: 'Text-to-Text Transfer Transformer统一了NLP任务框架。',
    },
  ]
}

/** 获取额外的下游推荐（模拟更多结果） */
export function buildMoreDownstreamPapers(): CitationPaper[] {
  return [
    {
      id: 'down-3',
      title: 'CLIP: Learning Transferable Visual Models From Natural Language Supervision',
      authors: 'Radford, A. et al.',
      venue: 'ICML',
      year: 2021,
      relation: 'downstream',
      citationCount: 9870,
      description: '多模态对比学习实现了图像与文本的统一表示。',
    },
    {
      id: 'down-4',
      title: 'BLOOM: A 176B-Parameter Open-Access Multilingual Language Model',
      authors: 'Scao, L. et al.',
      venue: 'arXiv',
      year: 2022,
      relation: 'downstream',
      citationCount: 3450,
      description: '开源多语言大语言模型的代表性工作。',
    },
  ]
}
