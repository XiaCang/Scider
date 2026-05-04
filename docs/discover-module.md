# 发现论文模块文档

## 1. 模块概览

发现论文模块提供关键词检索（对接 Semantic Scholar）和单篇导入功能，导入后自动触发异步解析任务。

涉及文件：

| 文件 | 职责 |
|------|------|
| [app/services/semantic_scholar.py](../app/services/semantic_scholar.py) | Semantic Scholar API 客户端，检索+格式化 |
| [app/tasks/paper_tasks.py](../app/tasks/paper_tasks.py) | 论文解析 Celery 异步任务 |
| [app/api/routes/discover.py](../app/api/routes/discover.py) | HTTP 路由：检索接口 + 导入接口 |

---

## 2. semantic_scholar.py

### 功能

封装对 [Semantic Scholar Graph API](https://api.semanticscholar.org/graph/v1) 的调用，返回格式化后的分页结果。

### 函数

#### `search_papers(query, offset, limit) -> dict`

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `query` | str | 必填 | 检索关键词 |
| `offset` | int | 0 | 分页偏移量 |
| `limit` | int | 10 | 每页条数（最大 50） |

返回结构：

```json
{
  "total": 1234,
  "offset": 0,
  "limit": 10,
  "data": [
    {
      "semantic_id": "abc123",
      "title": "...",
      "authors": "Alice, Bob",
      "year": 2024,
      "venue": "NeurIPS",
      "abstract": "...",
      "doi": "10.xxxx/xxxx"
    }
  ]
}
```

字段说明：
- `total` — Semantic Scholar 返回的总命中数
- `semantic_id` — Semantic Scholar 内部 paper ID
- `authors` — 逗号拼接的作者列表
- `doi` — 从 `externalIds.DOI` 提取，可为 `null`

---

## 3. paper_tasks.py

### 功能

定义 `parse_paper_task` Celery 任务，在论文导入后异步触发，负责 PDF 解析和 LLM 关键信息提取（当前为占位实现）。

### 任务

#### `parse_paper_task(paper_id: str) -> dict`

- 任务名：`app.tasks.parse_paper`
- 通过 `parse_paper_task.delay(paper_id)` 异步调用
- 返回 `{"paper_id": "...", "status": "parsed"}`

后续实现应在此任务中：
1. 下载/读取 PDF，调用 PDF 解析服务
2. 调用 LLM 提取背景/方法/创新/结论，写入 `KeyPoints` 表
3. 更新 `Paper.status` 为 `CONFIRMED` 或 `FAILED`

---

## 4. discover.py — API 接口

### `GET /api/discover/search`

关键词检索论文，结果来自 Semantic Scholar。

**Query 参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `q` | string | 是 | 检索关键词（最少1字符） |
| `offset` | int | 否（默认0） | 分页偏移 |
| `limit` | int | 否（默认10，最大50） | 每页条数 |

**响应示例：**

```json
{
  "total": 500,
  "offset": 0,
  "limit": 10,
  "data": [...]
}
```

**错误：**
- `502` — Semantic Scholar 请求失败

---

### `POST /api/discover/import`

将一篇论文导入用户文库，创建 `Paper` 数据库记录并触发异步解析任务。

**请求体：**

```json
{
  "title": "Attention Is All You Need",
  "authors": "Vaswani et al.",
  "abstract": "...",
  "doi": "10.48550/arXiv.1706.03762",
  "year": 2017,
  "venue": "NeurIPS",
  "user_id": "<user_id>"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | string | 是 | 论文标题 |
| `user_id` | string | 是 | 所属用户 ID |
| `authors/abstract/doi/year/venue` | string/int | 否 | 元数据 |

**响应示例：**

```json
{
  "paper_id": "a1b2c3...",
  "task_id": "celery-task-uuid",
  "status": "PENDING_PARSING"
}
```

导入后 `Paper.status` 初始为 `PENDING_PARSING`，Celery Worker 接管后续处理。

---

## 5. 单元测试

测试文件：[tests/test_semantic_scholar.py](../tests/test_semantic_scholar.py)

覆盖场景：

| 测试 | 说明 |
|------|------|
| `test_search_returns_pagination_envelope` | 返回结构包含 total/offset/limit/data |
| `test_search_passes_correct_params` | 正确传递 query/offset/limit 到 API |
| `test_fmt_full_paper` | 完整字段正确格式化（authors 拼接、doi 提取） |
| `test_fmt_missing_fields` | 缺失字段（authors 为空列表、externalIds 为 null）不报错 |
| `test_search_raises_on_http_error` | HTTP 错误正常向上抛出 |

运行测试：

```bash
cd src/backend
pytest tests/test_semantic_scholar.py -v
```
