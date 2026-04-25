# Scider 文库模块 API 接口文档

**文件位置**: `src/frontend/src/api/library.ts`  
**基础路径**: 通过 `request` 模块配置（见 `src/network/request.ts`）  
**数据格式**: JSON  
**认证方式**: 需要在请求头中携带 Token（由 request 拦截器自动处理）

---

## 📑 目录

1. [数据类型定义](#数据类型定义)
2. [论文管理接口](#论文管理接口)
3. [文件夹管理接口](#文件夹管理接口)
4. [论文与文件夹关联接口](#论文与文件夹关联接口)

---

## 数据类型定义

### LibraryPaper（论文对象）

```typescript
interface LibraryPaper {
  id: string              // 论文唯一标识
  title: string           // 论文标题
  authors: string         // 作者列表（JSON字符串或逗号分隔）
  year: number            // 发表年份
  status: 'Processing' | 'Completed' | 'Awaiting Review'  // 处理状态
  source: string          // 来源（期刊/会议名称）
  keyPoints: string[]     // 关键点列表
}
```

### Folder（文件夹对象）

```typescript
interface Folder {
  id: string              // 文件夹唯一标识
  name: string            // 文件夹名称
  user_id?: string        // 所属用户ID（可选）
  paperIds: string[]      // 包含的论文ID列表
  children?: Folder[]     // 子文件夹列表（支持无限层级）
  created_at?: string     // 创建时间（ISO 8601格式）
}
```

---

## 论文管理接口

### 1. 获取论文列表

**接口**: `GET /papers`  
**函数**: `fetchLibraryApi()`  
**描述**: 获取当前用户的所有论文列表

**请求参数**: 无

**响应示例**:
```json
{
  "code": 200,
  "data": [
    {
      "id": "paper-1",
      "title": "Transformers in Vision",
      "authors": "A. Calianham",
      "year": 2022,
      "status": "Processing",
      "source": "CVPR",
      "keyPoints": ["Visual tokenization", "Scalable encoder blocks"]
    }
  ]
}
```

---

### 2. 保存论文关键点

**接口**: `PATCH /papers/{paperId}/key-points`  
**函数**: `saveKeyPointsApi(paperId, keyPoints)`  
**描述**: 更新指定论文的关键点内容

**请求参数**:
- **Path Parameters**:
  - `paperId` (string): 论文ID

- **Request Body**:
```json
{
  "keyPoints": ["关键点1", "关键点2", "关键点3"]
}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "关键点保存成功",
  "data": {
    "id": "paper-1",
    "keyPoints": ["关键点1", "关键点2", "关键点3"]
  }
}
```

---

## 文件夹管理接口

### 3. 获取文件夹树

**接口**: `GET /folders`  
**函数**: `fetchFoldersApi()`  
**描述**: 获取当前用户的完整文件夹树结构（支持无限层级嵌套）

**请求参数**: 无

**响应示例**:
```json
{
  "code": 200,
  "data": [
    {
      "id": "folder-1",
      "name": "深度学习",
      "user_id": "user-123",
      "paperIds": ["paper-1", "paper-2"],
      "created_at": "2024-01-15T10:30:00Z",
      "children": [
        {
          "id": "folder-1-1",
          "name": "Transformer",
          "paperIds": ["paper-1"],
          "children": []
        }
      ]
    }
  ]
}
```

---

### 4. 创建根文件夹

**接口**: `POST /folders`  
**函数**: `createFolderApi(data)`  
**描述**: 在根级别创建新文件夹

**请求参数**:
- **Request Body**:
```json
{
  "name": "新文件夹名称",
  "user_id": "user-123"
}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "文件夹创建成功",
  "data": {
    "id": "folder-new",
    "name": "新文件夹名称",
    "user_id": "user-123",
    "paperIds": [],
    "created_at": "2024-01-20T14:25:00Z",
    "children": []
  }
}
```

---

### 5. 创建子文件夹

**接口**: `POST /folders/{parentId}/subfolders`  
**函数**: `createSubFolderApi(parentId, data)`  
**描述**: 在指定父文件夹下创建子文件夹

**请求参数**:
- **Path Parameters**:
  - `parentId` (string): 父文件夹ID

- **Request Body**:
```json
{
  "name": "子文件夹名称"
}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "子文件夹创建成功",
  "data": {
    "id": "folder-sub",
    "name": "子文件夹名称",
    "paperIds": [],
    "children": []
  }
}
```

---

### 6. 更新文件夹名称

**接口**: `PATCH /folders/{folderId}`  
**函数**: `updateFolderApi(folderId, data)`  
**描述**: 修改文件夹名称

**请求参数**:
- **Path Parameters**:
  - `folderId` (string): 文件夹ID

- **Request Body**:
```json
{
  "name": "新的文件夹名称"
}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "文件夹名称更新成功",
  "data": {
    "id": "folder-1",
    "name": "新的文件夹名称",
    "paperIds": ["paper-1"],
    "children": []
  }
}
```

---

### 7. 删除文件夹

**接口**: `DELETE /folders/{folderId}`  
**函数**: `deleteFolderApi(folderId)`  
**描述**: 删除指定文件夹及其所有子文件夹（级联删除）

**请求参数**:
- **Path Parameters**:
  - `folderId` (string): 要删除的文件夹ID

**响应示例**:
```json
{
  "code": 200,
  "message": "文件夹及子文件夹已删除"
}
```

**注意事项**:
- 此操作会递归删除所有子文件夹
- 被删除文件夹中的论文不会被删除，只是解除关联

---

### 8. 移动文件夹

**接口**: `PATCH /folders/{folderId}/move`  
**函数**: `moveFolderApi(folderId, newParentId)`  
**描述**: 将文件夹移动到新的父文件夹下

**请求参数**:
- **Path Parameters**:
  - `folderId` (string): 要移动的文件夹ID

- **Request Body**:
```json
{
  "parent_id": "new-parent-folder-id"  // null 表示移动到根级别
}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "文件夹移动成功",
  "data": {
    "id": "folder-1",
    "name": "深度学习",
    "parent_id": "folder-new-parent"
  }
}
```

**注意事项**:
- `newParentId` 为 `null` 时，文件夹移动到根级别
- 不能将文件夹移动到自己或其子文件夹下（后端需验证）

---

### 9. 复制文件夹

**接口**: `POST /folders/{folderId}/copy`  
**函数**: `copyFolderApi(folderId, targetParentId)`  
**描述**: 复制文件夹及其所有子文件夹和论文关联

**请求参数**:
- **Path Parameters**:
  - `folderId` (string): 要复制的文件夹ID

- **Request Body**:
```json
{
  "target_parent_id": "target-folder-id"  // null 表示复制到根级别
}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "文件夹复制成功",
  "data": {
    "id": "folder-copy-new",
    "name": "深度学习 (副本)",
    "paperIds": ["paper-1", "paper-2"],
    "children": [
      {
        "id": "folder-copy-sub",
        "name": "Transformer (副本)",
        "paperIds": ["paper-1"]
      }
    ]
  }
}
```

**注意事项**:
- 复制后的文件夹名称会自动添加 "(副本)" 后缀
- 所有子文件夹会被递归复制
- 论文关联关系会被复制，但不会复制论文本身

---

## 论文与文件夹关联接口

### 10. 添加论文到文件夹

**接口**: `POST /folders/{folderId}/papers`  
**函数**: `addPaperToFolderApi(folderId, paperId)`  
**描述**: 将单篇论文添加到指定文件夹

**请求参数**:
- **Path Parameters**:
  - `folderId` (string): 目标文件夹ID

- **Request Body**:
```json
{
  "paper_id": "paper-123"
}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "论文添加成功",
  "data": {
    "folder_id": "folder-1",
    "paper_id": "paper-123"
  }
}
```

---

### 11. 从文件夹移除论文

**接口**: `DELETE /folders/{folderId}/papers/{paperId}`  
**函数**: `removePaperFromFolderApi(folderId, paperId)`  
**描述**: 从指定文件夹中移除某篇论文

**请求参数**:
- **Path Parameters**:
  - `folderId` (string): 文件夹ID
  - `paperId` (string): 论文ID

**响应示例**:
```json
{
  "code": 200,
  "message": "论文已从文件夹移除"
}
```

**注意事项**:
- 仅解除关联，不会删除论文本身

---

### 12. 批量添加论文到文件夹

**接口**: `POST /folders/{folderId}/papers/batch`  
**函数**: `batchAddPapersToFolderApi(folderId, paperIds)`  
**描述**: 批量将多篇论文添加到指定文件夹

**请求参数**:
- **Path Parameters**:
  - `folderId` (string): 目标文件夹ID

- **Request Body**:
```json
{
  "paper_ids": ["paper-1", "paper-2", "paper-3"]
}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "批量添加成功",
  "data": {
    "added_count": 3,
    "failed_count": 0,
    "failed_papers": []
  }
}
```

---

### 13. 获取文件夹内的论文列表

**接口**: `GET /folders/{folderId}/papers`  
**函数**: `fetchFolderPapersApi(folderId)`  
**描述**: 获取指定文件夹内的所有论文（不包含子文件夹中的论文）

**请求参数**:
- **Path Parameters**:
  - `folderId` (string): 文件夹ID

**响应示例**:
```json
{
  "code": 200,
  "data": [
    {
      "id": "paper-1",
      "title": "Transformers in Vision",
      "authors": "A. Calianham",
      "year": 2022,
      "status": "Processing",
      "source": "CVPR",
      "keyPoints": ["Visual tokenization"]
    }
  ]
}
```

---

### 14. 移动论文到其他文件夹

**接口**: `PATCH /papers/{paperId}/folder`  
**函数**: `movePaperToFolderApi(paperId, folderId)`  
**描述**: 将论文从一个文件夹移动到另一个文件夹

**请求参数**:
- **Path Parameters**:
  - `paperId` (string): 论文ID

- **Request Body**:
```json
{
  "folder_id": "new-folder-id"  // null 表示移出所有文件夹
}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "论文移动成功",
  "data": {
    "paper_id": "paper-1",
    "old_folder_id": "folder-old",
    "new_folder_id": "folder-new"
  }
}
```

**注意事项**:
- `folderId` 为 `null` 时，论文将被移出所有文件夹（成为未分类论文）
- 一篇论文可以同时属于多个文件夹（根据业务需求决定）

---

## 🔧 错误码说明

| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| 200 | 请求成功 | - |
| 400 | 请求参数错误 | 检查请求参数格式和必填项 |
| 401 | 未授权 | 检查 Token 是否有效 |
| 403 | 禁止访问 | 确认用户是否有权限操作该资源 |
| 404 | 资源不存在 | 检查文件夹ID或论文ID是否正确 |
| 409 | 冲突 | 例如：文件夹名称重复、循环引用等 |
| 500 | 服务器内部错误 | 联系后端开发人员 |

---

## 📝 使用示例

### TypeScript 调用示例

```typescript
import { 
  fetchFoldersApi, 
  createFolderApi, 
  addPaperToFolderApi 
} from '@/api/library'

// 1. 获取文件夹树
const folders = await fetchFoldersApi()

// 2. 创建新文件夹
const newFolder = await createFolderApi({
  name: '我的研究',
  user_id: 'user-123'
})

// 3. 添加论文到文件夹
await addPaperToFolderApi(newFolder.id, 'paper-456')
```

### Vue 组件中使用

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { fetchFoldersApi, fetchLibraryApi } from '@/api/library'

const folders = ref([])
const papers = ref([])

onMounted(async () => {
  folders.value = await fetchFoldersApi()
  papers.value = await fetchLibraryApi()
})
</script>
```

---

## ⚠️ 注意事项

1. **无限层级支持**: 文件夹结构支持任意深度的嵌套，前端使用递归组件渲染
2. **级联删除**: 删除文件夹时会递归删除所有子文件夹，但不会影响论文数据
3. **论文多归属**: 根据业务需求，一篇论文可能同时属于多个文件夹
4. **移动限制**: 不能将文件夹移动到自己或其子孙文件夹下（需后端验证）
5. **复制命名**: 复制的文件夹会自动添加 "(副本)" 后缀避免命名冲突
6. **事务处理**: 批量操作建议使用事务，确保数据一致性

---

**文档版本**: v1.0  
**最后更新**: 2024-01-20  
**维护者**: Scider 开发团队
