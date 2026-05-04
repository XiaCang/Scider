# Discover 模块 API 文档

Base URL: `/api/discover`

---

## 1. 关键词检索

**GET** `/api/discover/search`

### Query Parameters

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `q` | string | 是 | 检索关键词（最少 1 字符） |
| `offset` | int | 否 | 分页偏移，默认 0 |
| `limit` | int | 否 | 每页数量，1–50，默认 10 |
| `year_from` | int | 否 | 年份下限（含） |
| `year_to` | int | 否 | 年份上限（含） |
| `source_type` | string | 否 | 来源类型筛选：`conference` / `journal` / `arXiv` |
| `sort` | string | 否 | 排序方式：`relevance`（默认）/ `citations` / `date` |

### Response `200`

```json
{
  "code": 200,
  "msg": "",
  "data": {
    "total": 1234,
    "offset": 0,
    "limit": 10,
    "data": [
      {
        "semantic_id": "abc123",
        "title": "Attention Is All You Need",
        "authors": "Vaswani, A., Shazeer, N.",
        "year": 2017,
        "venue": "NeurIPS",
        "source_type": "conference",
        "abstract": "...",
        "doi": "10.48550/arXiv.1706.03762",
        "citation_count": 90000
      }
    ]
  }
}
```

### Response `502`

```json
{ "code": 502, "msg": "Semantic Scholar unreachable after 3 attempts: ...", "data": null }
```

---

## 2. 单篇导入

**POST** `/api/discover/import`

### Request Body

```json
{
  "title": "Attention Is All You Need",
  "authors": "Vaswani, A., Shazeer, N.",
  "abstract": "...",
  "doi": "10.48550/arXiv.1706.03762",
  "year": 2017,
  "venue": "NeurIPS",
  "user_id": "user_abc"
}
```

| 字段 | 类型 | 必填 |
|------|------|------|
| `title` | string | 是 |
| `user_id` | string | 是 |
| `authors` / `abstract` / `doi` / `year` / `venue` | string/int | 否 |

### Response `200`

```json
{
  "code": 200,
  "msg": "",
  "data": {
    "paper_id": "d41d8cd98f00b204",
    "task_id": "celery-task-uuid",
    "status": "PENDING_PARSING"
  }
}
```

### Response `409` — 论文已在文库中

```json
{ "code": 409, "msg": "论文已在文库中", "data": null }
```

---

## 3. 批量导入

**POST** `/api/discover/import/bulk`

单次上限 20 篇，后台逐篇创建 Celery 异步任务。

### Request Body

```json
{
  "user_id": "user_abc",
  "papers": [
    { "title": "Paper A", "doi": "10.1/a", "year": 2020 },
    { "title": "Paper B", "doi": "10.1/b", "year": 2021 }
  ]
}
```

### Response `200`

```json
{
  "code": 200,
  "msg": "",
  "data": {
    "results": [
      { "paper_id": "id1", "task_id": "tid1", "skipped": false },
      { "title": "Paper B", "skipped": true, "reason": "论文已在文库中" }
    ]
  }
}
```

### Response `400` — 超过上限

```json
{ "code": 400, "msg": "单次批量导入上限为 20 篇", "data": null }
```

---

## 4. 上游参考文献（References）

**GET** `/api/discover/references/{semantic_id}`

返回该论文引用的文献列表（上游），并标注哪些已在用户文库中。

### Path Parameters

| 参数 | 说明 |
|------|------|
| `semantic_id` | Semantic Scholar Paper ID |

### Query Parameters

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `user_id` | string | 是 | 当前用户 ID，用于标注 `in_library` |

### Response `200`

```json
{
  "code": 200,
  "msg": "",
  "data": {
    "data": [
      {
        "semantic_id": "xyz",
        "title": "BERT",
        "authors": "Devlin, J.",
        "year": 2019,
        "doi": "10.18653/v1/N19-1423",
        "in_library": true
      }
    ]
  }
}
```

---

## 5. 下游引用文献（Citations）

**GET** `/api/discover/citations/{semantic_id}`

返回引用该论文的文献列表（下游），字段结构与 References 相同。

---

## 6. 异步任务状态查询

**GET** `/api/tasks/{task_id}`

导入后可轮询此接口获取解析进度。

### Response

```json
{
  "task_id": "celery-task-uuid",
  "status": "SUCCESS",
  "result": {
    "paper_id": "d41d8cd98f00b204",
    "status": "parsed",
    "sections": [
      { "heading": "ABSTRACT", "content": "..." },
      { "heading": "1. INTRODUCTION", "content": "..." }
    ]
  }
}
```

`status` 取值：`PENDING` / `STARTED` / `SUCCESS` / `FAILURE`

---

## 错误码汇总

| HTTP 状态码 | code | 含义 |
|-------------|------|------|
| 200 | 200 | 成功 |
| 400 | 400 | 请求参数错误 |
| 409 | 409 | 论文已在文库中 |
| 502 | 502 | 上游 Semantic Scholar API 不可达 |
