<!-- src/components/PdfUploadDialog.vue -->
<template>
  <el-dialog
    v-model="isVisible"
    title="批量上传PDF论文"
    width="600px"
    :close-on-click-modal="false"
    :show-close="!isUploading"
    @close="handleClose"
  >
    <div class="upload-container">
      <!-- 上传区域（仅当文件列表为空时显示） -->
      <div
        v-if="fileList.length === 0"
        class="upload-area"
        :class="{ 'is-dragging': isDragging }"
        @dragover="handleDragOver"
        @dragleave="handleDragLeave"
        @drop="handleDrop"
        @click="triggerFileSelect"
      >
        <el-icon class="upload-icon" :size="48">
          <Upload />
        </el-icon>
        <p class="upload-text">点击或拖拽PDF文件到此处</p>
        <p class="upload-hint">支持批量上传，一次最多5个，每个不超过50MB</p>
        <input
          ref="fileInput"
          type="file"
          accept=".pdf"
          multiple
          class="file-input"
          @change="handleFileSelect"
        />
      </div>

      <!-- 文件列表 -->
      <div v-else class="file-list">
        <div class="file-list-header">
          <span>已选择 {{ fileList.length }} 个文件</span>
          <el-button text type="primary" @click="clearFiles" :disabled="isUploading">
            清空
          </el-button>
        </div>
        <div class="file-items">
          <div v-for="(item, idx) in fileList" :key="idx" class="file-item">
            <el-icon class="file-icon" :size="24">
              <component :is="statusIcon(item.status)" />
            </el-icon>
            <div class="file-info">
              <div class="file-name">{{ item.file.name }}</div>
              <div class="file-size">{{ formatFileSize(item.file.size) }}</div>
              <el-progress
                v-if="item.status === 'uploading'"
                :percentage="item.progress"
                :stroke-width="6"
                :show-text="false"
              />
              <div v-if="item.status === 'error'" class="error-msg">
                {{ item.errorMsg }}
              </div>
            </div>
            <el-icon
              v-if="!isUploading && item.status !== 'uploading'"
              class="remove-icon"
              @click="removeFile(idx)"
            >
              <Close />
            </el-icon>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <el-button @click="handleClose" :disabled="isUploading">
        取消
      </el-button>
      <el-button
        type="primary"
        @click="handleBatchUpload"
        :loading="isUploading"
        :disabled="fileList.length === 0 || isUploading"
      >
        {{ isUploading ? '上传中...' : `批量上传 (${fileList.length})` }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Upload, Close, Document, Loading, CircleCheck, CircleClose } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { batchUploadPapersApi } from '../api/library'
import { useAuthStore } from '../store/auth'
import { useRouter } from 'vue-router'

interface Props {
  modelValue: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'batchSuccess': [results: Array<{ paper_id: string; task_id: string; filename: string }>]
}>()

const authStore = useAuthStore()
const router = useRouter()

// 文件项状态
interface FileItem {
  file: File
  status: 'pending' | 'uploading' | 'success' | 'error'
  progress: number
  errorMsg?: string
  result?: { paper_id: string; task_id: string }
}

const fileList = ref<FileItem[]>([])
const isUploading = ref(false)
const isDragging = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

const isVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const fileSizeLimit = 50 * 1024 * 1024  // 50MB
const maxFileCount = 5

// 添加文件（校验）
const addFiles = (files: FileList | File[]) => {
  const fileArray = Array.from(files)
  const currentCount = fileList.value.length
  const availableSlots = maxFileCount - currentCount
  if (availableSlots <= 0) {
    ElMessage.warning(`最多只能上传 ${maxFileCount} 个文件`)
    return
  }

  const toAdd = fileArray.slice(0, availableSlots)
  for (const file of toAdd) {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      ElMessage.warning(`文件 "${file.name}" 不是PDF格式，已跳过`)
      continue
    }
    if (file.size > fileSizeLimit) {
      ElMessage.warning(`文件 "${file.name}" 超过50MB，已跳过`)
      continue
    }
    // 检查重复（可选）
    const exists = fileList.value.some(item => item.file.name === file.name && item.file.size === file.size)
    if (exists) {
      ElMessage.warning(`文件 "${file.name}" 已在列表中`)
      continue
    }
    fileList.value.push({
      file,
      status: 'pending',
      progress: 0
    })
  }
  if (toAdd.length < fileArray.length) {
    ElMessage.info(`由于数量限制，仅添加了 ${toAdd.length} 个文件`)
  }
}

// 移除文件
const removeFile = (index: number) => {
  if (!isUploading.value) {
    fileList.value.splice(index, 1)
  }
}

// 清空所有文件
const clearFiles = () => {
  if (!isUploading.value) {
    fileList.value = []
  }
}

// 拖拽事件
const handleDragOver = (e: DragEvent) => {
  e.preventDefault()
  isDragging.value = true
}
const handleDragLeave = (e: DragEvent) => {
  e.preventDefault()
  isDragging.value = false
}
const handleDrop = (e: DragEvent) => {
  e.preventDefault()
  isDragging.value = false
  if (e.dataTransfer?.files) {
    addFiles(e.dataTransfer.files)
  }
}

const triggerFileSelect = () => {
  fileInput.value?.click()
}
const handleFileSelect = (e: Event) => {
  const target = e.target as HTMLInputElement
  if (target.files?.length) {
    addFiles(target.files)
  }
  target.value = ''  // 清空以便重复选择相同文件
}

// 批量上传
const handleBatchUpload = async () => {
  if (fileList.value.length === 0) {
    ElMessage.warning('请先选择文件')
    return
  }
  if (!authStore.isAuthenticated) {
    ElMessage.warning('请先登录')
    router.push('/auth')
    return
  }

  isUploading.value = true
  const pendingFiles = fileList.value.filter(item => item.status === 'pending')
  if (pendingFiles.length === 0) {
    ElMessage.info('没有待上传的文件')
    isUploading.value = false
    return
  }

  // 收集待上传的原始 File 对象
  const filesToUpload = pendingFiles.map(item => item.file)

  // 标记所有文件为 uploading
  for (const item of pendingFiles) {
    item.status = 'uploading'
    item.progress = 0
  }

  try {
    // 模拟进度（简单起见，不做精细化每个文件的进度，仅做整体模拟）
    const progressInterval = setInterval(() => {
      // 只更新还在 uploading 状态的文件进度，最多到 90%
      const uploadingItems = fileList.value.filter(item => item.status === 'uploading')
      for (const item of uploadingItems) {
        if (item.progress < 90) {
          item.progress += 10
        }
      }
    }, 200)

    const response = await batchUploadPapersApi(filesToUpload)
    clearInterval(progressInterval)

    // 根据后端返回的结果更新每个文件的状态
    const results = response.data?.results || []
    const successItems: Array<{ paper_id: string; task_id: string; filename: string }> = []

    for (const result of results) {
      const fileItem = fileList.value.find(item => item.file.name === result.filename)
      if (fileItem) {
        if (result.success) {
          fileItem.status = 'success'
          fileItem.progress = 100
          fileItem.result = {
            paper_id: result.paper_id!,
            task_id: result.task_id!
          }
          successItems.push({
            paper_id: result.paper_id!,
            task_id: result.task_id!,
            filename: result.filename
          })
        } else {
          fileItem.status = 'error'
          fileItem.errorMsg = result.msg
          fileItem.progress = 0
        }
      }
    }

    // 对于后端未返回的文件（理论上不会发生），标记为错误
    for (const item of fileList.value) {
      if (item.status === 'uploading') {
        item.status = 'error'
        item.errorMsg = '上传失败，未收到响应'
      }
    }

    ElMessage.success(`上传完成：成功 ${response.data?.success_count || 0} 个，失败 ${(response.data?.total || 0) - (response.data?.success_count || 0)} 个`)

    // 触发批量成功事件，供父组件刷新列表等
    if (successItems.length > 0) {
      emit('batchSuccess', successItems)
    }

    // 延迟关闭对话框（给用户看到结果）
    setTimeout(() => {
      if (fileList.value.every(item => item.status !== 'uploading')) {
        handleClose()
      }
    }, 1500)

  } catch (error: any) {
    console.error('批量上传错误:', error)
    ElMessage.error(error.message || '批量上传失败，请稍后重试')
    // 将所有 uploading 状态标记为错误
    for (const item of fileList.value) {
      if (item.status === 'uploading') {
        item.status = 'error'
        item.errorMsg = error.message || '网络错误'
      }
    }
  } finally {
    isUploading.value = false
  }
}

const handleClose = () => {
  if (isUploading.value) {
    ElMessage.warning('上传进行中，请稍候')
    return
  }
  fileList.value = []
  isVisible.value = false
}

const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

// 状态图标
const statusIcon = (status: string) => {
  switch (status) {
    case 'success': return CircleCheck
    case 'error': return CircleClose
    case 'uploading': return Loading
    default: return Document
  }
}
</script>

<style scoped>
.upload-container {
  padding: 8px 0;
}
.upload-area {
  border: 2px dashed var(--line-soft);
  border-radius: 16px;
  padding: 48px 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  background: var(--bg-soft);
}
.upload-area:hover {
  border-color: var(--brand);
  background: rgba(74, 157, 154, 0.05);
}
.upload-area.is-dragging {
  border-color: var(--brand);
  background: rgba(74, 157, 154, 0.1);
  transform: scale(1.02);
}
.upload-icon {
  color: var(--brand);
  margin-bottom: 16px;
}
.upload-text {
  font-size: 1rem;
  color: var(--text-primary);
  margin: 0 0 8px;
  font-weight: 500;
}
.upload-hint {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin: 0;
}
.file-input {
  display: none;
}
.file-list {
  max-height: 400px;
  overflow-y: auto;
}
.file-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-size: 0.9rem;
  color: var(--text-secondary);
}
.file-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.file-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--bg-soft);
  border-radius: 12px;
  transition: all 0.2s;
}
.file-icon {
  flex-shrink: 0;
  color: var(--brand);
}
.file-info {
  flex: 1;
  min-width: 0;
}
.file-name {
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.file-size {
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-top: 4px;
}
.error-msg {
  font-size: 0.75rem;
  color: var(--danger, #f56c6c);
  margin-top: 4px;
}
.remove-icon {
  color: var(--text-secondary);
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s;
}
.remove-icon:hover {
  color: var(--danger, #f56c6c);
  background: rgba(245, 108, 108, 0.1);
}
:deep(.el-progress-bar__outer) {
  background-color: var(--bg-base);
}
:deep(.el-progress-bar__inner) {
  background-color: var(--brand);
}
</style>