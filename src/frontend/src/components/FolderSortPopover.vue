<script setup lang="ts">
import { ref } from 'vue'
import { Sort } from '@element-plus/icons-vue'
import type { SortField, SortOrder } from '../hooks/useFolderTreeFilter'

const props = defineProps<{
  sortField: SortField
  sortOrder: SortOrder
}>()

const emit = defineEmits<{
  'update:sortField': [field: SortField]
  'update:sortOrder': [order: SortOrder]
}>()

const visible = ref(false)

const options: { label: string; field: SortField; order: SortOrder }[] = [
  { label: '名称 A-Z', field: 'name', order: 'asc' },
  { label: '名称 Z-A', field: 'name', order: 'desc' },
  { label: '日期 新→旧', field: 'created_at', order: 'desc' },
  { label: '日期 旧→新', field: 'created_at', order: 'asc' }
]

const selectOption = (opt: typeof options[0]) => {
  emit('update:sortField', opt.field)
  emit('update:sortOrder', opt.order)
  visible.value = false
}

const getCurrentLabel = () => {
  const found = options.find(o => o.field === props.sortField && o.order === props.sortOrder)
  return found ? found.label : '排序'
}
</script>

<template>
  <el-popover
    v-model:visible="visible"
    placement="bottom-end"
    :width="160"
    trigger="click"
    :show-arrow="false"
  >
    <template #reference>
      <el-icon class="sort-trigger" :title="getCurrentLabel()"><Sort /></el-icon>
    </template>
    <div class="sort-menu">
      <button
        v-for="opt in options"
        :key="opt.label"
        class="sort-option"
        :class="{ active: sortField === opt.field && sortOrder === opt.order }"
        @click="selectOption(opt)"
      >
        {{ opt.label }}
      </button>
    </div>
  </el-popover>
</template>

<style scoped>
.sort-trigger {
  font-size: 1.1rem;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
  transition: all 0.2s;
}

.sort-trigger:hover {
  background: var(--bg-soft);
  color: var(--text-primary);
}

.sort-menu {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.sort-option {
  display: block;
  width: 100%;
  text-align: left;
  padding: 6px 12px;
  border: none;
  background: transparent;
  font-size: 0.85rem;
  color: var(--text-secondary);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s;
}

.sort-option:hover {
  background: var(--bg-soft);
  color: var(--text-primary);
}

.sort-option.active {
  color: var(--brand);
  font-weight: 600;
  background: var(--brand-soft);
}
</style>