# Scider 前端项目重构建议

## 项目现状分析

经过代码分析，Scider 是一个基于 Vue 3 + TypeScript + Element Plus 的论文管理系统前端项目，具有以下特点：

### 技术栈
- Vue 3 + Composition API + `<script setup>`
- TypeScript
- Element Plus UI 组件库
- Pinia 状态管理
- Vue Router

### 项目结构
```
src/
├── api/           # API 接口定义
├── components/    # 通用组件
├── layouts/       # 布局组件
├── network/       # 请求封装
├── router/        # 路由配置
├── store/         # Pinia store
├── types/         # TypeScript 类型定义
├── utils/         # 工具函数
├── views/         # 页面组件
├── theme.css      # 主题变量
└── ...
```

### 当前问题

1. **Vue 文件中 TypeScript 代码占比过高**
   - LibraryView.vue: script 部分占 324 行 (68%)
   - LibraryFolder.vue: script 部分占 460 行 (70%)
   - 单个文件功能过重，职责不清晰

2. **组件耦合度较高**
   - 父子组件之间通过 props/emit 传递复杂数据结构
   - 业务逻辑与 UI 渲染混杂
   - 缺乏统一的状态管理

3. **代码复用性不足**
   - 重复的对话框逻辑
   - 相似的处理函数重复定义
   - 缺乏通用的工具组件

4. **类型定义分散**
   - 接口定义在多个地方重复
   - 缺乏统一的类型管理

---

## 重构建议

### 一、减少 Vue 文件中的 TypeScript 代码占比

#### 1.1 提取业务逻辑到 Composition Functions

创建 `src/composables/` 目录，将复杂的业务逻辑提取为独立的 Composition Functions：

```typescript
// src/composables/useLibraryManagement.ts
import { ref, computed } from 'vue'
import type { LibraryPaper, LibraryFolder } from '@/types/library'

export function useLibraryManagement() {
  const searchQuery = ref('')
  const selectedFolderId = ref('all')
  
  // 数据过滤逻辑
  const filteredPapers = computed(() => {
    // 提取自 LibraryView.vue 的过滤逻辑
  })
  
  // 文件夹管理逻辑
  const handleCreateFolder = async () => {
    // 提取自 LibraryFolder.vue 的创建文件夹逻辑
  }
  
  return {
    searchQuery,
    selectedFolderId,
    filteredPapers,
    handleCreateFolder
  }
}
```

#### 1.2 提取通用对话框逻辑

```typescript
// src/composables/useDialogHandlers.ts
import { ElMessageBox, ElMessage } from 'element-plus'

export function useDialogHandlers() {
  const showConfirmDialog = async (options) => {
    try {
      await ElMessageBox({
        // 统一配置
      })
      return true
    } catch {
      return false
    }
  }
  
  const showInputDialog = async (options) => {
    // 统一的输入对话框逻辑
  }
  
  return {
    showConfirmDialog,
    showInputDialog
  }
}
```

#### 1.3 使用自定义 Hooks 分离关注点

```typescript
// src/composables/useFolderOperations.ts
export function useFolderOperations() {
  const { showInputDialog } = useDialogHandlers()
  
  const createFolder = async (parentId?: string) => {
    const name = await showInputDialog({
      title: parentId ? '新建子文件夹' : '新建文件夹',
      placeholder: '文件夹名称'
    })
    
    if (name) {
      // 调用 API
    }
  }
  
  const renameFolder = async (folderId: string, currentName: string) => {
    // 重命名逻辑
  }
  
  return {
    createFolder,
    renameFolder
  }
}
```

### 二、组件封装与解耦

#### 2.1 创建通用的业务组件

```vue
<!-- src/components/Library/FolderTree.vue -->
<template>
  <div class="folder-tree">
    <FolderTreeNode
      v-for="folder in folders"
      :key="folder.id"
      :folder="folder"
      :depth="0"
      :selected-id="selectedId"
      @select="emit('select', $event)"
    />
  </div>
</template>

<script setup lang="ts">
// 只负责渲染，不包含业务逻辑
</script>
```

#### 2.2 实现无渲染组件 (Renderless Components)

```vue
<!-- src/components/Library/FolderManager.vue -->
<script setup lang="ts">
import { provide, ref } from 'vue'
import type { LibraryFolder } from '@/types/library'

const folders = ref<LibraryFolder[]>([])
const selectedId = ref<string>()

provide('folder-context', {
  folders,
  selectedId
})
</script>

<template>
  <slot :folders="folders" :selected-id="selectedId" />
</template>
```

#### 2.3 使用 Provide/Inject 替代 Props 透传

```vue
<!-- 父组件 -->
<script setup lang="ts">
const { provideFolderContext } = useFolderContext()

provideFolderContext({
  folders,
  selectedId,
  onSelect,
  onCreate
})
</script>

<!-- 子组件 -->
<script setup lang="ts">
const { folders, selectedId } = injectFolderContext()
</script>
```

### 三、状态管理与数据流优化

#### 3.1 创建专用的 Pinia Store

```typescript
// src/store/library.ts
import { defineStore } from 'pinia'

export const useLibraryStore = defineStore('library', {
  state: () => ({
    papers: [] as LibraryPaper[],
    folders: [] as LibraryFolder[],
    searchQuery: '',
    selectedFolderId: 'all'
  }),
  
  getters: {
    filteredPapers: (state) => {
      // 集中管理过滤逻辑
    }
  },
  
  actions: {
    async fetchPapers() {
      // API 调用
    },
    
    async deletePaper(paperId: string) {
      // 删除逻辑
    }
  }
})
```

#### 3.2 使用 Service 层封装 API 调用

```typescript
// src/services/libraryService.ts
import { useLibraryStore } from '@/store/library'

export class LibraryService {
  private store = useLibraryStore()
  
  async loadLibrary() {
    const [papers, folders] = await Promise.all([
      this.fetchPapers(),
      this.fetchFolders()
    ])
    
    this.store.setPapers(papers)
    this.store.setFolders(folders)
  }
  
  private async fetchPapers() {
    // API 调用
  }
}
```

### 四、类型系统优化

#### 4.1 统一类型定义

```typescript
// src/types/library.ts
export interface PaperKeyPoints {
  background: string
  method: string
  innovation: string
  conclusion: string
}

export interface LibraryPaper {
  id: string
  title: string
  authors: string
  year: number
  status: PaperStatus
  source: string
  keyPoints: PaperKeyPoints
}

export type PaperStatus = 'Processing' | 'PendingConfirmation' | 'Confirmed'

// 状态映射
export const statusTextMap: Record<PaperStatus, string> = {
  Processing: '处理中',
  PendingConfirmation: '未确认',
  Confirmed: '已确认'
}
```

#### 4.2 使用泛型工具类型

```typescript
// src/types/utility.ts
export type PartialBy<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>
export type RequiredBy<T, K extends keyof T> = Omit<T, K> & Required<Pick<T, K>>
```

### 五、代码组织结构重构

#### 5.1 按照功能模块组织代码

```
src/
├── modules/
│   ├── library/
│   │   ├── components/     # 模块特定组件
│   │   ├── composables/    # 模块 Composition Functions
│   │   ├── services/       # 模块服务层
│   │   ├── types/          # 模块类型定义
│   │   ├── views/          # 模块页面
│   │   └── index.ts        # 模块导出
│   ├── auth/
│   └── dashboard/
├── shared/
│   ├── components/         # 通用组件
│   ├── composables/        # 通用 Composition Functions
│   ├── utils/              # 通用工具函数
│   └── types/              # 通用类型定义
└── ...
```

#### 5.2 创建组件索引文件

```typescript
// src/shared/components/index.ts
export { default as AppLogo } from './AppLogo.vue'
export { default as IconButton } from './IconButton.vue'
export { default as StatusBadge } from './StatusBadge.vue'

// 使用时
import { StatusBadge } from '@/shared/components'
```

### 六、性能优化建议

#### 6.1 组件懒加载

```typescript
// router/index.ts
const LibraryView = () => import('../modules/library/views/LibraryView.vue')
```

#### 6.2 列表虚拟滚动

大数据量时使用 `vue-virtual-scroller` 或 `element-plus` 的虚拟表格。

#### 6.3 防抖与节流

```vue
<script setup lang="ts">
import { useDebounceFn } from '@vueuse/core'

const searchQuery = ref('')
const debouncedSearch = useDebounceFn(() => {
  // 搜索逻辑
}, 300)
</script>
```

### 七、代码质量与规范

#### 7.1 引入 ESLint + Prettier

```json
// .eslintrc.js
{
  "extends": [
    "@vue/typescript/recommended",
    "@vue/eslint-config-prettier"
  ]
}
```

#### 7.2 添加单元测试

```typescript
// tests/composables/useLibraryManagement.spec.ts
import { describe, it, expect } from 'vitest'
import { useLibraryManagement } from '@/composables/useLibraryManagement'

describe('useLibraryManagement', () => {
  it('should filter papers by search query', () => {
    // 测试逻辑
  })
})
```

#### 7.3 配置路径别名

```typescript
// vite.config.ts
export default defineConfig({
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      '@components': resolve(__dirname, 'src/components'),
      '@composables': resolve(__dirname, 'src/composables')
    }
  }
})
```

---

## 实施路线图

### Phase 1: 基础架构重构 (1-2周)
1. 创建 `src/composables/` 目录，提取主要业务逻辑
2. 统一类型定义到 `src/types/`
3. 配置 ESLint + Prettier
4. 添加路径别名

### Phase 2: 组件重构 (2-3周)
1. 将大型 Vue 文件拆分为多个组件
2. 创建通用业务组件
3. 实现 Composition Functions
4. 优化 Props/Events 设计

### Phase 3: 状态管理优化 (1-2周)
1. 创建专用 Pinia Store
2. 实现 Service 层
3. 优化数据流

### Phase 4: 代码组织与模块化 (1周)
1. 按功能模块重组目录结构
2. 创建组件索引
3. 文档化组件接口

### Phase 5: 性能优化与测试 (1-2周)
1. 实现组件懒加载
2. 添加虚拟滚动
3. 编写单元测试
4. 性能测试与优化

---

## 预期收益

1. **可维护性提升**: Vue 文件更专注 UI 渲染，业务逻辑可独立测试
2. **代码复用性增强**: Composition Functions 和通用组件减少重复代码
3. **开发效率提高**: 清晰的模块边界和类型定义
4. **团队协作改善**: 统一的代码规范和架构模式
5. **性能优化空间**: 更精细的组件拆分和懒加载策略

---

## 风险与缓解措施

1. **重构风险**: 分阶段进行，确保每个阶段可独立验证
2. **学习成本**: 提供充分的文档和示例代码
3. **兼容性问题**: 保持 API 向后兼容，逐步迁移
4. **时间估算**: 预留 20% 的缓冲时间

---

## 结论

通过系统性的重构，Scider 前端项目将从当前的单文件混合模式转变为现代的、模块化的、可维护的架构。核心策略是通过 Composition API 分离关注点，通过模块化组织代码，通过类型系统保证代码质量。

建议优先实施 Phase 1 和 Phase 2，这能带来最直接的代码质量提升，同时为后续的重构打下良好基础。