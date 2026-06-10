<script setup lang="ts">
const nodes = [
  { label: 'Vision Transformer', x: 18, y: 34, type: 'core' },
  { label: 'Attention', x: 42, y: 18, type: 'keyword' },
  { label: 'Image Retrieval', x: 66, y: 35, type: 'paper' },
  { label: 'Multimodal Search', x: 31, y: 64, type: 'topic' },
  { label: 'Prompted Reading', x: 60, y: 70, type: 'paper' },
]

const links = [
  { x1: 18, y1: 34, x2: 42, y2: 18 },
  { x1: 42, y1: 18, x2: 66, y2: 35 },
  { x1: 18, y1: 34, x2: 31, y2: 64 },
  { x1: 31, y1: 64, x2: 60, y2: 70 },
  { x1: 42, y1: 18, x2: 60, y2: 70 },
]
</script>

<template>
  <section class="graph-page">
    <header class="graph-header">
      <div>
        <h1 class="section-title">Knowledge Graph</h1>
        <p class="section-description">
          当前先搭建图谱画布框架，后续可以把真实关键词共现结果、拖拽交互和缩放能力接进来。
        </p>
      </div>
      <div class="graph-tags">
        <span class="status-pill is-brand">Keyword Co-occurrence</span>
        <span class="status-pill">Canvas Ready</span>
      </div>
    </header>

    <section class="graph-canvas">
      <svg class="graph-canvas__lines" viewBox="0 0 100 100" preserveAspectRatio="none">
        <line
          v-for="(link, index) in links"
          :key="index"
          :x1="link.x1"
          :y1="link.y1"
          :x2="link.x2"
          :y2="link.y2"
        />
      </svg>

      <button
        v-for="node in nodes"
        :key="node.label"
        class="graph-node"
        :class="`graph-node--${node.type}`"
        :style="{ left: `${node.x}%`, top: `${node.y}%` }"
        type="button"
      >
        {{ node.label }}
      </button>
    </section>
  </section>
</template>

<style scoped>
.graph-page {
  display: grid;
  gap: 0.9rem;
}

.graph-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding-bottom: 0.9rem;
  border-bottom: 1px solid var(--line-soft);
}

.graph-tags {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.graph-canvas {
  position: relative;
  margin-top: 1rem;
  min-height: 70vh;
  overflow: hidden;
  border: 1px solid var(--line-soft);
  border-radius: 12px;
  background:
    radial-gradient(circle at top, rgba(237, 244, 255, 0.9), transparent 40%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.88) 0%, rgba(247, 250, 252, 0.96) 100%);
}

.graph-canvas::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(148, 163, 184, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148, 163, 184, 0.08) 1px, transparent 1px);
  background-size: 40px 40px;
}

.graph-canvas__lines {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.graph-canvas__lines line {
  stroke: rgba(22, 50, 95, 0.18);
  stroke-width: 0.24;
}

.graph-node {
  position: absolute;
  transform: translate(-50%, -50%);
  border-radius: 999px;
  border: 1px solid rgba(22, 50, 95, 0.1);
  background: white;
  padding: 0.62rem 0.8rem;
  cursor: grab;
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.08);
  font-size: 0.82rem;
}

.graph-node--core {
  background: #173668;
  color: white;
}

.graph-node--keyword {
  background: #eef4ff;
  color: var(--brand);
}

.graph-node--topic {
  background: #eef9f3;
  color: var(--success);
}

@media (max-width: 820px) {
  .graph-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
