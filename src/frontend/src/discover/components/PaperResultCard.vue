<template>
  <article class="paper-card">
    <h3 class="card-title">{{ paper.title }}</h3>

    <div class="card-meta">
      <span>{{ paper.year }}</span>
      <span class="meta-dot">·</span>
      <span v-if="paper.venue" class="meta-venue">{{ paper.venue }}</span>
      <span v-if="paper.venue" class="meta-dot">·</span>
      <span class="meta-citation">被引 {{ paper.citation_count ?? 0 }}</span>
      <span v-if="paper.in_library" class="meta-library">已在文库</span>
    </div>

    <div class="card-authors" :title="paper.authors">{{ paper.authors || '未知作者' }}</div>

    <div class="card-divider" />

    <p v-if="abstract" class="card-abstract">{{ abstract }}</p>
    <p v-else class="card-abstract card-abstract-empty">暂无摘要</p>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { SearchResult, CitationPaper } from '../../discover/types'

type PaperItem = (SearchResult | CitationPaper) & { in_library?: boolean }

const props = defineProps<{
  paper: PaperItem
}>()

const abstract = computed(() => {
  const p = props.paper as any
  return p.abstract || p.description || ''
})
</script>

<style scoped>
.paper-card {
  width: 100%;
  min-width: 0;
  box-sizing: border-box;
  padding: 1.1rem 1.25rem;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(148, 163, 184, 0.08);
  box-shadow: 0 2px 12px rgba(15, 23, 42, 0.04);
  transition: all 0.2s ease;
}

.paper-card:hover {
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 6px 24px rgba(15, 23, 42, 0.06);
  border-color: rgba(148, 163, 184, 0.15);
}

.card-title {
  margin: 0 0 0.35rem;
  font-size: 0.98rem;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.45;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.card-meta {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.78rem;
  color: var(--text-secondary);
  flex-wrap: wrap;
  overflow: hidden;
}

.meta-venue {
  color: var(--brand-accent);
  opacity: 0.75;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.meta-citation {
  color: var(--brand-accent);
  font-weight: 500;
  opacity: 0.85;
}

.meta-library {
  color: #10b981;
  font-weight: 500;
  font-size: 0.72rem;
  background: rgba(16, 185, 129, 0.1);
  padding: 1px 6px;
  border-radius: 4px;
}

.card-authors {
  margin-top: 0.2rem;
  font-size: 0.78rem;
  color: var(--text-tertiary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-divider {
  margin: 0.55rem 0;
  height: 1px;
  background: rgba(148, 163, 184, 0.12);
}

.card-abstract {
  margin: 0;
  font-size: 0.75rem;
  color: var(--text-tertiary);
  line-height: 1.65;
  display: -webkit-box;
  -webkit-line-clamp: 6;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-abstract-empty {
  font-style: italic;
  opacity: 0.5;
}
</style>
