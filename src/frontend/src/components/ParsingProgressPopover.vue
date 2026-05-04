<script setup lang="ts">
import { ref, computed, watch, onUnmounted, onMounted } from 'vue'
import { ElPopover, ElIcon, ElTag, ElBadge, ElProgress } from 'element-plus'
import { Loading, CircleCheck, CircleClose } from '@element-plus/icons-vue'
import { fetchTaskResultApi } from '../api/tasks'
import type { LibraryPaper } from '../types/library'

interface ParsingTask {
  taskId: string
  paperId: string
  filename: string
  status: string
  progress?: number
  error?: string
  createdAt: number
}

const props = defineProps<{
  papers: LibraryPaper[]
}>()

// 弹窗可见性
const visible = ref(false)

// 解析中的任务列表
const parsingTasks = ref<ParsingTask[]>([])

// localStorage键名
const STORAGE_KEY = 'parsing_tasks'

// 从localStorage加载任务
const loadTasksFromStorage = () => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      const tasks = JSON.parse(stored)
      // 只保留24小时内的任务
      const oneDayAgo = Date.now() - 24 * 60 * 60 * 1000
      parsingTasks.value = tasks.filter((t: ParsingTask) => t.createdAt > oneDayAgo)
      
      // 如果有未完成的任务，开始轮询
      const hasPendingTasks = parsingTasks.value.some(task => 
        task.status === 'PENDING' || 
        task.status === 'STARTED' || 
        task.status === 'PROGRESS'
      )
      if (hasPendingTasks) {
        startPolling()
      }
    }
  } catch (error) {
    console.error('Failed to load tasks from storage:', error)
  }
}

// 保存任务到localStorage
const saveTasksToStorage = () => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(parsingTasks.value))
  } catch (error) {
    console.error('Failed to save tasks to storage:', error)
  }
}

// 计算需要显示的任务（正在解析或刚完成的任务）
const activeTasks = computed(() => {
  return parsingTasks.value.filter(task => 
    task.status === 'PENDING' || 
    task.status === 'STARTED' || 
    task.status === 'PROGRESS' ||
    task.status === 'SUCCESS' ||
    task.status === 'FAILURE'
  )
})

// 是否有正在进行的任务
const hasActiveTasks = computed(() => {
  return activeTasks.value.some(task => 
    task.status === 'PENDING' || 
    task.status === 'STARTED' || 
    task.status === 'PROGRESS'
  )
})

// 进行中任务数量徽章
const activeCount = computed(() => {
  return activeTasks.value.filter(task => 
    task.status === 'PENDING' || 
    task.status === 'STARTED' || 
    task.status === 'PROGRESS'
  ).length
})

// 轮询定时器
let pollTimer: number | null = null

// 开始轮询
const startPolling = () => {
  if (pollTimer) return
  
  pollTimer = window.setInterval(async () => {
    await updateTaskStatuses()
  }, 2000) // 每2秒更新一次
}

// 停止轮询
const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

// 更新所有任务状态
const updateTaskStatuses = async () => {
  const tasksToUpdate = parsingTasks.value.filter(task => 
    task.status === 'PENDING' || 
    task.status === 'STARTED' || 
    task.status === 'PROGRESS'
  )
  
  if (tasksToUpdate.length === 0) {
    stopPolling()
    return
  }

  for (const task of tasksToUpdate) {
    try {
      const response = await fetchTaskResultApi(task.taskId)
      const data = response.data as any
      
      task.status = data.status
      
      if (data.status === 'SUCCESS') {
        task.progress = 100
      } else if (data.status === 'FAILURE') {
        task.error = data.error || '未知错误'
      }
      
      // 如果任务已完成或失败，3秒后从列表中移除
      if (data.status === 'SUCCESS' || data.status === 'FAILURE') {
        setTimeout(() => {
          removeTask(task.taskId)
        }, 3000)
      }
    } catch (error) {
      console.error(`Failed to fetch task ${task.taskId}:`, error)
    }
  }
}

// 添加新任务
const addTask = (paperId: string, taskId: string, filename: string) => {
  // 检查是否已存在
  const existing = parsingTasks.value.find(t => t.taskId === taskId)
  if (existing) return
  
  parsingTasks.value.unshift({
    taskId,
    paperId,
    filename,
    status: 'PENDING',
    progress: 0,
    createdAt: Date.now()
  })
  
  // 保存到localStorage
  saveTasksToStorage()
  
  // 如果有进行中的任务，确保轮询在运行
  startPolling()
}

// 移除任务
const removeTask = (taskId: string) => {
  const index = parsingTasks.value.findIndex(t => t.taskId === taskId)
  if (index !== -1) {
    parsingTasks.value.splice(index, 1)
    saveTasksToStorage()
  }
}

// 清除已完成/失败的任务
const clearCompleted = () => {
  parsingTasks.value = parsingTasks.value.filter(task => 
    task.status === 'PENDING' || 
    task.status === 'STARTED' || 
    task.status === 'PROGRESS'
  )
  saveTasksToStorage()
}

// 获取状态标签类型
const getStatusType = (status: string) => {
  switch (status) {
    case 'PENDING':
    case 'STARTED':
    case 'PROGRESS':
      return 'warning'
    case 'SUCCESS':
      return 'success'
    case 'FAILURE':
      return 'danger'
    default:
      return 'info'
  }
}

// 获取状态文本
const getStatusText = (status: string) => {
  switch (status) {
    case 'PENDING':
      return '等待中'
    case 'STARTED':
      return '已开始'
    case 'PROGRESS':
      return '解析中'
    case 'SUCCESS':
      return '已完成'
    case 'FAILURE':
      return '失败'
    default:
      return status
  }
}

// 监听论文列表变化，检测新上传的论文
watch(() => props.papers, (newPapers) => {
  // 这里可以通过某种方式检测新任务，比如从 localStorage 或其他状态管理
  // 目前暂时手动添加，后续可以改进
}, { deep: true })

// 组件卸载时清理
onUnmounted(() => {
  stopPolling()
})

// 组件挂载时加载任务
onMounted(() => {
  loadTasksFromStorage()
})

// 监听任务变化，自动保存
watch(parsingTasks, () => {
  saveTasksToStorage()
}, { deep: true })

// 暴露方法给父组件
defineExpose({
  addTask,
  removeTask,
  clearCompleted
})
</script>

<template>
  <el-popover
    v-model:visible="visible"
    placement="bottom-end"
    :width="380"
    trigger="click"
    popper-class="parsing-progress-popover"
  >
    <template #reference>
      <div class="progress-trigger" :class="{ 'has-active': hasActiveTasks }">
        <el-icon class="trigger-icon" :class="{ rotating: hasActiveTasks }">
          <Loading v-if="hasActiveTasks" />
          <CircleCheck v-else-if="activeTasks.length > 0" />
        </el-icon>
        <span class="trigger-text">解析进度</span>
        <el-badge 
          v-if="activeCount > 0" 
          :value="activeCount" 
          class="progress-badge"
          type="primary"
        />
      </div>
    </template>

    <div class="parsing-progress-content">
      <div class="progress-header">
        <h4 class="progress-title">PDF解析进度</h4>
        <button 
          v-if="activeTasks.length > 0 && !hasActiveTasks" 
          class="clear-btn"
          @click="clearCompleted"
        >
          清除已完成
        </button>
      </div>

      <div v-if="activeTasks.length === 0" class="empty-state">
        <el-icon class="empty-icon"><CircleCheck /></el-icon>
        <p>暂无解析任务</p>
      </div>

      <div v-else class="task-list">
        <div 
          v-for="task in activeTasks" 
          :key="task.taskId"
          class="task-item"
          :class="`status-${task.status.toLowerCase()}`"
        >
          <div class="task-info">
            <div class="task-filename" :title="task.filename">
              {{ task.filename }}
            </div>
            <div class="task-meta">
              <el-tag 
                :type="getStatusType(task.status)" 
                size="small"
                class="status-tag"
              >
                {{ getStatusText(task.status) }}
              </el-tag>
              <span class="task-id" title="任务ID">
                {{ task.taskId.substring(0, 8) }}...
              </span>
            </div>
          </div>

          <div v-if="task.status === 'PROGRESS'" class="task-progress">
            <el-progress 
              :percentage="task.progress || 0" 
              :stroke-width="6"
              :show-text="false"
            />
          </div>

          <div v-if="task.status === 'FAILURE' && task.error" class="task-error">
            {{ task.error }}
          </div>

          <div v-if="task.status === 'SUCCESS'" class="task-success-icon">
            <el-icon color="#67c23a"><CircleCheck /></el-icon>
          </div>

          <div v-if="task.status === 'FAILURE'" class="task-failure-icon">
            <el-icon color="#f56c6c"><CircleClose /></el-icon>
          </div>
        </div>
      </div>
    </div>
  </el-popover>
</template>

<style scoped>
.progress-trigger {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(148, 163, 184, 0.2);
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  font-size: 0.8rem;
  color: var(--text-secondary, #526071);
}

.progress-trigger:hover {
  background: rgba(255, 255, 255, 1);
  border-color: var(--brand, #4f46e5);
  color: var(--brand, #4f46e5);
}

.progress-trigger.has-active {
  border-color: var(--brand, #4f46e5);
  color: var(--brand, #4f46e5);
}

.trigger-icon {
  font-size: 1rem;
}

.trigger-icon.rotating {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.trigger-text {
  font-weight: 500;
}

.progress-badge {
  position: absolute;
  top: -4px;
  right: -4px;
}

.parsing-progress-content {
  max-height: 400px;
  overflow-y: auto;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.1);
}

.progress-title {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-primary, #101828);
}

.clear-btn {
  background: none;
  border: none;
  color: var(--brand, #4f46e5);
  font-size: 0.75rem;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 4px;
  transition: all 0.2s;
}

.clear-btn:hover {
  background: rgba(79, 70, 229, 0.1);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 16px;
  color: var(--text-tertiary, #8a94a6);
}

.empty-icon {
  font-size: 2rem;
  margin-bottom: 8px;
  color: #67c23a;
}

.empty-state p {
  margin: 0;
  font-size: 0.85rem;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.task-item {
  padding: 10px 12px;
  border-radius: 8px;
  background: rgba(248, 250, 252, 0.6);
  border: 1px solid rgba(148, 163, 184, 0.1);
  transition: all 0.2s;
}

.task-item:hover {
  background: rgba(241, 245, 249, 0.8);
}

.task-item.status-success {
  background: rgba(240, 253, 244, 0.6);
  border-color: rgba(103, 194, 58, 0.2);
}

.task-item.status-failure {
  background: rgba(254, 242, 242, 0.6);
  border-color: rgba(245, 108, 108, 0.2);
}

.task-info {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 6px;
}

.task-filename {
  flex: 1;
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--text-primary, #101828);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.status-tag {
  font-size: 0.7rem;
}

.task-id {
  font-size: 0.65rem;
  color: var(--text-tertiary, #8a94a6);
  font-family: monospace;
}

.task-progress {
  margin-top: 6px;
}

.task-error {
  margin-top: 6px;
  font-size: 0.75rem;
  color: #f56c6c;
  padding: 4px 8px;
  background: rgba(245, 108, 108, 0.1);
  border-radius: 4px;
}

.task-success-icon,
.task-failure-icon {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 1.2rem;
}

/* 滚动条样式 */
.parsing-progress-content::-webkit-scrollbar {
  width: 4px;
}

.parsing-progress-content::-webkit-scrollbar-track {
  background: transparent;
}

.parsing-progress-content::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.3);
  border-radius: 2px;
}

.parsing-progress-content::-webkit-scrollbar-thumb:hover {
  background: rgba(148, 163, 184, 0.5);
}
</style>
