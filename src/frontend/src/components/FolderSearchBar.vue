<script setup lang="ts">
import { ref, watch } from 'vue'
import { Search } from '@element-plus/icons-vue'

const props = defineProps<{
  modelValue: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const inputValue = ref(props.modelValue)
watch(() => props.modelValue, val => { inputValue.value = val })
watch(inputValue, val => emit('update:modelValue', val))
</script>

<template>
  <div class="search-bar">
    <el-icon class="search-icon"><Search /></el-icon>
    <input
      v-model="inputValue"
      class="search-input"
      placeholder="搜索文件夹..."
    />
  </div>
</template>

<style scoped>
.search-bar {
  display: flex;
  align-items: center;
  gap: 4px;
  background: var(--bg-soft);
  border-radius: 10px;
  padding: 4px 10px;
  margin-top: 8px;
  margin-bottom: 4px;
  border: 1px solid transparent;
  transition: border-color 0.2s;
}

.search-bar:focus-within {
  border-color: var(--brand);
  background: white;
}

.search-icon {
  font-size: 0.9rem;
  color: var(--text-secondary);
  flex-shrink: 0;
}

.search-input {
  border: none;
  background: transparent;
  outline: none;
  font-size: 0.85rem;
  color: var(--text-primary);
  width: 100%;
  padding: 2px 0;
}

.search-input::placeholder {
  color: var(--text-secondary);
  opacity: 0.7;
}
</style>