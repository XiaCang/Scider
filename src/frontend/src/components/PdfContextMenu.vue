<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { ChatDotSquare } from '@element-plus/icons-vue'

const props = defineProps<{
  visible: boolean
  x: number
  y: number
  selectedText: string
}>()

const emit = defineEmits<{
  (e: 'ask-ai', text: string): void
  (e: 'close'): void
}>()

const menuRef = ref<HTMLElement | null>(null)

const askAi = () => {
  emit('ask-ai', props.selectedText)
  emit('close')
}

const handleClickOutside = (e: MouseEvent) => {
  if (menuRef.value && !menuRef.value.contains(e.target as Node)) {
    emit('close')
  }
}

onMounted(() => {
  document.addEventListener('mousedown', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('mousedown', handleClickOutside)
})
</script>

<template>
  <Teleport to="body">
    <div
      v-if="visible"
      class="pdf-context-menu"
      ref="menuRef"
      :style="{ left: x + 'px', top: y + 'px' }"
    >
      <div class="context-menu-item" @click="askAi">
        <el-icon :size="14"><ChatDotSquare /></el-icon>
        <span>向 AI 提问</span>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.pdf-context-menu {
  position: fixed;
  z-index: 9999;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  min-width: 140px;
  padding: 4px 0;
}

.context-menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  font-size: 0.82rem;
  color: #333;
  cursor: pointer;
  transition: background 0.12s;
}

.context-menu-item:hover {
  background: #f0f5ff;
  color: var(--brand);
}
</style>
