<script setup lang="ts">
const workflowSteps = [
  {
    title: '上传论文',
    description: '支持 PDF 上传与元数据解析，形成论文条目。',
  },
  {
    title: 'AI 提炼',
    description: '异步生成 Key Points，方便后续人工审核确认。',
  },
  {
    title: '知识关联',
    description: '把关键词、主题与论文关系沉淀进知识图谱。',
  },
  {
    title: '智能推荐',
    description: '围绕方向推荐与上下游文献检索扩展阅读面。',
  },
]

const stats = [
  { label: 'Tracked Papers', value: '18', hint: '本周新增 4 篇' },
  { label: 'Pending Review', value: '6', hint: '等待 Key Points 审核' },
  { label: 'Linked Concepts', value: '29', hint: '已进入知识图谱' },
  { label: 'Fresh Recommendations', value: '14', hint: '过去 24 小时' },
]

const recentReads = [
  { title: 'Transformers in Vision', meta: 'Awaiting review · 2023 · CVPR' },
  { title: 'Graph Neural Retrieval for Scientific Search', meta: 'Completed · 2024 · arXiv' },
  { title: 'Small Language Models for Research Assistance', meta: 'Processing · 2025 · ACL Findings' },
]

const focusList = [
  '完成 2 篇新上传论文的 Key Points 审核',
  '把“多模态检索”相关关键词补入图谱节点',
  '围绕 research direction 再扩 5 篇上游论文',
]
</script>

<template>
  <section class="dashboard-page">
    <div class="dashboard-hero">
      <div>
        <span class="status-pill is-brand">Reading to Insight</span>
        <h1>让每篇论文不只被读过，还能被复用、被关联、被再次发现。</h1>
        <p>
          现在的首页把论文上传、阅读提炼、图谱关联和方向推荐集中到一个统一工作台里。
        </p>
      </div>
      <div class="dashboard-metrics">
        <article v-for="item in stats" :key="item.label" class="dashboard-metrics__item">
          <small>{{ item.label }}</small>
          <strong>{{ item.value }}</strong>
          <span>{{ item.hint }}</span>
        </article>
      </div>
    </div>

    <div class="dashboard-grid">
      <section class="dashboard-section">
        <header>
          <h2 class="section-title">Core Workflow</h2>
          <p class="section-description">围绕“上传 → 提炼 → 关联 → 推荐”的完整流程来组织前台入口。</p>
        </header>
        <ol class="workflow-list">
          <li v-for="(step, index) in workflowSteps" :key="step.title">
            <span>{{ index + 1 }}</span>
            <div>
              <strong>{{ step.title }}</strong>
              <p>{{ step.description }}</p>
            </div>
          </li>
        </ol>
      </section>

      <section class="dashboard-section">
        <header>
          <h2 class="section-title">This Week</h2>
          <p class="section-description">保持对阅读队列、审核任务和新方向的连续推进。</p>
        </header>
        <ul class="focus-list">
          <li v-for="item in focusList" :key="item">{{ item }}</li>
        </ul>
      </section>
    </div>

    <section class="dashboard-section">
      <header>
        <h2 class="section-title">Recent Papers</h2>
        <p class="section-description">最近进入工作台的论文，可以作为 Library 页面之后的列表入口。</p>
      </header>
      <div class="recent-list">
        <article v-for="paper in recentReads" :key="paper.title" class="recent-list__item">
          <strong>{{ paper.title }}</strong>
          <span>{{ paper.meta }}</span>
        </article>
      </div>
    </section>
  </section>
</template>

<style scoped>
.dashboard-page {
  display: grid;
  gap: 0.9rem;
}

.dashboard-hero {
  display: grid;
  grid-template-columns: 1.2fr 0.9fr;
  gap: 1.1rem;
  padding-bottom: 1.4rem;
  border-bottom: 1px solid var(--line-soft);
}

.dashboard-hero h1 {
  margin: 0.75rem 0 0.7rem;
  font-size: clamp(1.45rem, 2.2vw, 2.2rem);
  line-height: 1.12;
  letter-spacing: -0.05em;
}

.dashboard-hero p {
  margin: 0;
  max-width: 34rem;
  color: var(--text-secondary);
  font-size: 0.9rem;
  line-height: 1.65;
}

.dashboard-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.55rem;
}

.dashboard-metrics__item {
  padding: 0.8rem 0.8rem 0.8rem 0;
  border-top: 1px solid var(--line-soft);
}

.dashboard-metrics__item small,
.dashboard-metrics__item span {
  display: block;
  color: var(--text-secondary);
}

.dashboard-metrics__item strong {
  display: block;
  margin: 0.25rem 0;
  font-size: 1.45rem;
  letter-spacing: -0.04em;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  gap: 0.9rem;
  padding: 1.2rem 0;
  border-bottom: 1px solid var(--line-soft);
}

.dashboard-section {
  padding: 0;
}

.workflow-list,
.focus-list {
  margin: 1rem 0 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 0.7rem;
}

.workflow-list li,
.focus-list li {
  display: flex;
  gap: 0.95rem;
  padding-top: 0.7rem;
  border-top: 1px solid var(--line-soft);
}

.workflow-list li:first-child,
.focus-list li:first-child {
  padding-top: 0;
  border-top: 0;
}

.workflow-list span {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.7rem;
  height: 1.7rem;
  border-radius: 999px;
  background: var(--brand-soft);
  color: var(--brand);
  font-weight: 700;
  font-size: 0.8rem;
}

.workflow-list p {
  margin: 0.24rem 0 0;
  color: var(--text-secondary);
  font-size: 0.88rem;
}

.recent-list {
  display: grid;
  gap: 0.7rem;
  margin-top: 1rem;
}

.recent-list__item {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding-top: 0.7rem;
  border-top: 1px solid var(--line-soft);
}

.recent-list__item:first-child {
  padding-top: 0;
  border-top: 0;
}

.recent-list__item span {
  color: var(--text-secondary);
  text-align: right;
  font-size: 0.84rem;
}

@media (max-width: 980px) {
  .dashboard-hero,
  .dashboard-grid {
    grid-template-columns: 1fr;
  }

  .recent-list__item {
    flex-direction: column;
  }

  .recent-list__item span {
    text-align: left;
  }
}
</style>

