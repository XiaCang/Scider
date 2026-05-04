<script setup lang="ts">
import { ref, computed } from 'vue'
import { Upload, Close, Document } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { uploadPaperApi } from '../api/library'
import { useAuthStore } from '../store/auth'
import { useRouter } from 'vue-router'

interface Props {
  modelValue: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'success': []
}>()

const authStore = useAuthStore()
const router = useRouter()

// 状态管理
const selectedFile = ref<File | null>(null)
const isUploading = ref(false)
const uploadProgress = ref(0)
const isDragging = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

// 计算属性
const isVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const fileSizeLimit = 50 * 1024 * 1024 // 50MB

// 方法
const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    validateAndSetFile(file)
  }
  // 清空input，允许重复选择同一文件
  target.value = ''
}

const validateAndSetFile = (file: File) => {
  // 验证文件类型
  if (!file.name.toLowerCase().endsWith('.pdf')) {
    ElMessage.warning('仅支持PDF格式')
    return
  }

  // 验证文件大小
  if (file.size > fileSizeLimit) {
    ElMessage.warning('文件大小不能超过50MB')
    return
  }

  selectedFile.value = file
  uploadProgress.value = 0
}

const handleDragOver = (event: DragEvent) => {
  event.preventDefault()
  isDragging.value = true
}

const handleDragLeave = (event: DragEvent) => {
  event.preventDefault()
  isDragging.value = false
}

const handleDrop = (event: DragEvent) => {
  event.preventDefault()
  isDragging.value = false
  
  const files = event.dataTransfer?.files
  if (files && files.length > 0) {
    validateAndSetFile(files[0])
  }
}

const triggerFileSelect = () => {
  fileInput.value?.click()
}

const handleUpload = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }

  // 检查登录状态
  if (!authStore.isAuthenticated) {
    ElMessage.warning('请先登录')
    router.push('/auth')
    return
  }

  isUploading.value = true
  uploadProgress.value = 0

  try {
    // 模拟进度更新（因为axios不支持上传进度回调）
    const progressInterval = setInterval(() => {
      if (uploadProgress.value < 90) {
        uploadProgress.value += 10
      }
    }, 200)

    const response = await uploadPaperApi(selectedFile.value)
    
    clearInterval(progressInterval)
    uploadProgress.value = 100

    // 响应拦截器返回的是response.data，即ApiResponse对象
    if (response.code === 0 && response.data) {
      ElMessage.success(response.msg || '上传成功，后台解析中')
      emit('success')
      handleClose()
    } else {
      // 处理业务错误
      if (response.code === 401) {
        ElMessage.warning('未认证，请登录')
        router.push('/auth')
      } else if (response.code === 409) {
        ElMessage.warning(response.msg || '该论文已存在')
      } else {
        ElMessage.error(response.msg || '上传失败')
      }
    }
  } catch (error: any) {
    console.error('Upload error:', error)
    
    // 提取错误信息
    let errorMessage = '上传失败，请稍后重试'
    
    if (error.response) {
      // 服务器返回了错误响应（HTTP错误）
      const status = error.response.status
      const data = error.response.data
      
      if (status === 401) {
        errorMessage = '未认证，请登录'
        router.push('/auth')
      } else if (status === 400) {
        errorMessage = data?.msg || data?.detail || '请求参数错误'
      } else if (status === 409) {
        errorMessage = data?.msg || '该论文已存在，请勿重复上传'
      } else if (status === 413) {
        errorMessage = '文件太大，请上传小于50MB的PDF'
      } else {
        errorMessage = data?.msg || data?.detail || `上传失败 (${status})`
      }
    } else if (error.request) {
      // 请求已发送但没有收到响应
      errorMessage = '网络连接失败，请检查网络'
    }
    
    ElMessage.error(errorMessage)
  } finally {
    isUploading.value = false
  }
}

const handleClose = () => {
  if (isUploading.value) {
    ElMessage.warning('上传进行中，请稍候')
    return
  }
  selectedFile.value = null
  uploadProgress.value = 0
  isVisible.value = false
}

const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}
</script>

<template>
  <el-dialog
    v-model="isVisible"
    title="上传PDF论文"
    width="500px"
    :close-on-click-modal="false"
    :show-close="!isUploading"
    @close="handleClose"
  >
    <div class="upload-container">
      <!-- 上传区域 -->
      <div
        v-if="!selectedFile"
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
        <p class="upload-hint">支持 .pdf 格式，最大 50MB</p>
        <input
          ref="fileInput"
          type="file"
          accept=".pdf"
          class="file-input"
          @change="handleFileSelect"
        />
      </div>

      <!-- 文件信息展示 -->
      <div v-else class="file-info">
        <div class="file-header">
          <el-icon class="file-icon" :size="32">
            <Document />
          </el-icon>
          <div class="file-details">
            <p class="file-name">{{ selectedFile.name }}</p>
            <p class="file-size">{{ formatFileSize(selectedFile.size) }}</p>
          </div>
          <el-icon
            v-if="!isUploading"
            class="remove-icon"
            @click="selectedFile = null"
          >
            <Close />
          </el-icon>
        </div>

        <!-- 进度条 -->
        <el-progress
          v-if="isUploading || uploadProgress > 0"
          :percentage="uploadProgress"
          :status="uploadProgress === 100 ? 'success' : undefined"
        />
      </div>
    </div>

    <template #footer>
      <el-button @click="handleClose" :disabled="isUploading">
        取消
      </el-button>
      <el-button
        type="primary"
        @click="handleUpload"
        :loading="isUploading"
        :disabled="!selectedFile"
      >
        {{ isUploading ? '上传中...' : '确认上传' }}
      </el-button>
    </template>
  </el-dialog>
</template>

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
  background: rgba(79, 70, 229, 0.05);
}

.upload-area.is-dragging {
  border-color: var(--brand);
  background: rgba(79, 70, 229, 0.1);
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

.file-info {
  padding: 16px;
  background: var(--bg-soft);
  border-radius: 12px;
}

.file-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.file-icon {
  color: var(--brand);
  flex-shrink: 0;
}

.file-details {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-size: 0.95rem;
  color: var(--text-primary);
  margin: 0 0 4px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin: 0;
}

.remove-icon {
  color: var(--text-secondary);
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s;
  flex-shrink: 0;
}

.remove-icon:hover {
  color: var(--danger, #f56c6c);
  background: rgba(245, 108, 108, 0.1);
}
</style>
