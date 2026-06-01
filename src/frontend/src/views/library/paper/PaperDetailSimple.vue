<script setup lang="ts">
import { Link, Download, Plus } from '@element-plus/icons-vue'
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'

import type { LibraryPaper } from '../../../types/library'
import { importPaperApi, downloadDiscoverPdfApi } from '../../../api/discover'

interface Props {
  modelValue: boolean
  paper: LibraryPaper | null
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'imported', paperId: string): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 计算属性：抽屉显示状态
const drawerVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

// 获取论文链接（优先使用 Semantic Scholar URL，其次 DOI URL）
const paperUrl = computed(() => {
  if (!props.paper) return null

  // 优先使用直接提供的 url 字段
  if (props.paper.url) {
    return props.paper.url
  }

  // 其次使用 doi_url
  if (props.paper.doi_url) {
    return props.paper.doi_url
  }

  // 如果有 semantic_id，构造 Semantic Scholar 链接
  if (props.paper.id && !props.paper.id.startsWith('local-')) {
    return `https://www.semanticscholar.org/paper/${props.paper.id}`
  }

  // 最后尝试从 doi 构造
  if (props.paper.doi) {
    return `https://doi.org/${props.paper.doi}`
  }

  return null
})

// 跳转到来源网址
const handleJumpToSource = () => {
  if (paperUrl.value) {
    window.open(paperUrl.value, '_blank')
  }
}

// ── 导入论文 ──
const importing = ref(false)

const handleImport = async () => {
  if (!props.paper || importing.value) return

  importing.value = true
  try {
    // importPaperApi 返回 ApiResponse<ImportPaperResult>
    // 响应拦截器已处理 code≠0 的情况，成功时直接返回 response.data
    const res = await importPaperApi({
      title: props.paper.title,
      authors: props.paper.authors || null,
      abstract: props.paper.abstract || null,
      doi: props.paper.doi || null,
      year: props.paper.year || null,
      venue: props.paper.source || null,
      pdf_url: props.paper.pdf_url || null,
    })

    // res 为 ApiResponse<ImportPaperResult>，data 为 ImportPaperResult
    ElMessage.success('论文已成功导入文库')
    emit('imported', (res as any)?.data?.paper_id || props.paper.id)
  } catch (err: any) {
    const msg = err?.message || '导入失败'
    // 如果后端返回 409（论文已存在），也算成功
    if (msg.includes('已在文库中')) {
      ElMessage.info('该论文已在文库中')
      emit('imported', props.paper.id)
    } else {
      ElMessage.error(msg)
    }
  } finally {
    importing.value = false
  }
}

// ── 下载 PDF ──
const downloading = ref(false)

const handleDownloadPdf = async () => {
  if (!props.paper?.pdf_url || downloading.value) return

  downloading.value = true
  try {
    const response = await downloadDiscoverPdfApi(props.paper.pdf_url)
    const blob = new Blob([response.data], { type: 'application/pdf' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    // 使用论文标题作为文件名
    const safeName = (props.paper.title || 'paper').replace(/[/\\?%*:|"<>]/g, '_')
    link.download = `${safeName}.pdf`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success('PDF 下载成功')
  } catch (err: any) {
    ElMessage.error(err?.message || 'PDF 下载失败')
  } finally {
    downloading.value = false
  }
}

// 是否有 PDF 下载链接
const hasPdfUrl = computed(() => !!props.paper?.pdf_url)
// 论文是否已在文库中
const isInLibrary = computed(() => props.paper?.in_library === true)

// 状态映射（中文显示）
const statusTextMap: Record<string, string> = {
  PENDING_PARSING: '解析中',
  PARSING: '解析中',
  PENDING_EXTRACTION: '提取中',
  EXTRACTING: '提取中',
  PENDING_CONFIRMATION: '待确认',
  CONFIRMED: '已确认',
  FAILED: '失败',
}

const statusClassMap: Record<string, string> = {
  PENDING_PARSING: 'is-warning',
  PARSING: 'is-warning',
  PENDING_EXTRACTION: 'is-brand',
  EXTRACTING: 'is-brand',
  PENDING_CONFIRMATION: 'is-success',
  CONFIRMED: 'is-success',
  FAILED: 'is-danger',
}
</script>

<template>
  <el-drawer
    v-model="drawerVisible"
    title="论文详情"
    direction="rtl"
    size="680px"
  >
    <div v-if="paper" class="paper-detail">
      <!-- 论文基本信息 -->
      <section class="paper-info">
        <h2 class="paper-title">{{ paper.title }}</h2>

        <div class="paper-meta">
          <div class="meta-item meta-item--full">
            <span class="meta-label">作者：</span>
            <span class="meta-value meta-value--ellipsis" :title="paper.authors">{{ paper.authors }}</span>
          </div>

          <div class="meta-row">
            <div class="meta-item">
              <span class="meta-label">年份：</span>
              <span class="meta-value">{{ paper.year }}</span>
            </div>

            <div class="meta-item">
              <span class="meta-label">来源：</span>
              <span class="meta-value meta-value--ellipsis" :title="paper.source">{{ paper.source }}</span>
            </div>

            <div class="meta-item">
              <span class="meta-label">状态：</span>
              <span v-if="isInLibrary" class="status-pill" :class="statusClassMap[paper.status]">
                {{ statusTextMap[paper.status] }}
              </span>
              <span v-else class="status-pill is-external">外部来源</span>
            </div>
          </div>
        </div>
      </section>

      <!-- 摘要信息 -->
      <section v-if="paper.abstract" class="abstract-section">
        <h3 class="section-title">摘要</h3>
        <p class="abstract-text">{{ paper.abstract }}</p>
      </section>

      <!-- 操作按钮区 -->
      <section class="action-section">
        <el-button
          type="primary"
          size="large"
          :disabled="!paperUrl"
          @click="handleJumpToSource"
        >
          <el-icon><Link /></el-icon>
          跳转到来源网址
        </el-button>

        <el-button
          type="success"
          size="large"
          :loading="importing"
          :disabled="importing || isInLibrary"
          @click="handleImport"
        >
          <el-icon><Plus /></el-icon>
          {{ isInLibrary ? '已在文库中' : '导入我的文库' }}
        </el-button>

        <el-button
          size="large"
          :loading="downloading"
          :disabled="!hasPdfUrl || downloading"
          @click="handleDownloadPdf"
        >
          <el-icon><Download /></el-icon>
          下载 PDF
        </el-button>
      </section>
    </div>

    <div v-else class="empty-state">
      <el-empty description="请选择一篇论文查看详情" />
    </div>
  </el-drawer>
</template>

<style scoped>
.paper-detail {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  padding: 0 0.25rem;
}

/* 论文基本信息 */
.paper-info {
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--line-soft);
}

.paper-title {
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.7rem 0;
  line-height: 1.45;
}

.paper-meta {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  font-size: 0.8rem;
}

/* 作者行独占一行 */
.meta-item--full {
  max-width: 100%;
}

/* 年份 / 来源 / 状态 一行排列 */
.meta-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  min-width: 0;
}

.meta-label {
  color: var(--text-secondary);
  font-weight: 500;
  flex-shrink: 0;
}

.meta-value {
  color: var(--text-primary);
}

.meta-value--ellipsis {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100%;
}

/* 状态标签 */
.status-pill {
  display: inline-block;
  padding: 0.15rem 0.5rem;
  border-radius: 100px;
  font-size: 0.75rem;
  font-weight: 500;
}

.status-pill.is-warning {
  background: rgba(245, 158, 11, 0.1);
  color: #d97706;
}

.status-pill.is-brand {
  background: rgba(74, 157, 154, 0.1);
  color: #4a9d9a;
}

.status-pill.is-success {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.status-pill.is-danger {
  background: rgba(239, 68, 68, 0.1);
  color: #dc2626;
}

.status-pill.is-external {
  background: rgba(99, 102, 241, 0.1);
  color: #6366f1;
}

/* 摘要区域 */
.abstract-section {
  flex: 1;
}

.section-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.5rem 0;
}

.abstract-text {
  font-size: 0.85rem;
  line-height: 1.7;
  color: var(--text-secondary);
  margin: 0;
  white-space: pre-wrap;
}

/* 操作按钮区 */
.action-section {
  display: flex;
  gap: 0.75rem;
  padding-top: 1rem;
  border-top: 1px solid var(--line-soft);
  flex-wrap: wrap;
}

.action-section .el-button {
  flex: 1;
  min-width: 140px;
}

/* 空状态 */
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .meta-row {
    flex-direction: column;
    gap: 0.3rem;
  }

  .action-section {
    flex-direction: column;
  }
}
</style>
