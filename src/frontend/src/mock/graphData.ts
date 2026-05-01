import type { LibraryPaper } from '../types/library'
import type { GraphNode, GraphLink } from '../types/graph'

export const mockPapers: Record<string, LibraryPaper> = {
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

export const categories = [
  { name: '论文', itemStyle: { color: '#173668' } },
  { name: '研究背景', itemStyle: { color: '#a78bfa' } },
  { name: '研究方法', itemStyle: { color: '#3b82f6' } },
  { name: '创新点', itemStyle: { color: '#eab308' } },
  { name: '结论', itemStyle: { color: '#22c55e' } },
]

export function buildMockGraphData() {
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
      paperTitle: mockPapers['p1'].title,
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
      paperTitle: mockPapers['p1'].title,
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
      paperTitle: mockPapers['p1'].title,
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
      paperTitle: mockPapers['p2'].title,
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
      paperTitle: mockPapers['p2'].title,
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
      paperTitle: mockPapers['p2'].title,
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
      paperTitle: mockPapers['p2'].title,
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
      paperTitle: mockPapers['p3'].title,
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
      paperTitle: mockPapers['p3'].title,
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
      paperTitle: mockPapers['p3'].title,
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
      paperTitle: mockPapers['p3'].title,
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
    { source: 'm1', target: 'm2', relationType: 'semantic', label: '方法相近：均采用Transformer架构' },
    { source: 'm3', target: 'm2', relationType: 'semantic', label: '技术传承：基于Transformer Encoder' },
    { source: 'i1', target: 'i2', relationType: 'semantic', label: '思想借鉴：自注意力机制迁移到视觉' },
    { source: 'i3', target: 'i2', relationType: 'semantic', label: '机制相似：均优化上下文建模' },

    // === 引文关系 ===
    { source: 'p1', target: 'p2', relationType: 'citation', label: '引用' },
    { source: 'p3', target: 'p2', relationType: 'citation', label: '引用' },
  ]

  return { mockNodes, mockLinks }
}
