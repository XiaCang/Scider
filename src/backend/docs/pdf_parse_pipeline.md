# PDF 解析与四要素提取功能说明

## 1. 功能概述

本功能实现了从 PDF 上传到论文四要素自动提取的完整异步流水线：

```
用户上传 PDF
    ↓
POST /api/papers/{paper_id}/upload
    ↓
parse_paper_task（Celery）
  ├─ PyMuPDF 提取文本
  ├─ 文本清洗与分段
  └─ 自动链式触发 ↓
extract_key_points_task（Celery）
  ├─ 调用 DeepSeek / Qwen 大模型
  ├─ 解析 JSON 四要素
  └─ 写入 KeyPoints 表
```

四要素定义：
- **background**：研究背景
- **methodology**：研究方法
- **innovation**：创新点
- **conclusion**：研究结论

---

## 2. 涉及文件

| 文件 | 职责 |
|------|------|
| `app/api/routes/papers.py` | PDF 上传 HTTP 端点 |
| `app/tasks/paper_tasks.py` | Celery 任务：PDF 解析、文本预处理、链式触发 |
| `app/tasks/llm_tasks.py` | Celery 任务：大模型调用、四要素写库 |
| `app/core/llm_client.py` | OpenAI 兼容客户端（DeepSeek / Qwen） |
| `app/core/prompts.py` | System Prompt 与 User Prompt 模板 |
| `app/tasks/__init__.py` | 确保 Celery worker 自动发现所有任务模块 |
| `db/models.py` | `Paper`、`KeyPoints`、`PaperStatus` 数据模型 |

---

## 3. 数据库状态流转

```
PENDING_PARSING
    → PARSING          （parse_paper_task 开始）
    → PENDING_EXTRACTION（解析完成，等待 LLM）
    → EXTRACTING       （extract_key_points_task 开始）
    → PENDING_CONFIRMATION（LLM 写库完成，等待人工确认）
    → CONFIRMED        （用户确认四要素）
    → FAILED           （任意阶段异常）
```

---

## 4. HTTP 接口

### 4.1 上传 PDF

```
POST /api/papers/{paper_id}/upload
Content-Type: multipart/form-data

字段：
  file  — PDF 文件（必填）

约束：
  - Content-Type 必须为 application/pdf
  - 文件大小不超过 50 MB
  - paper_id 对应的 Paper 记录必须已存在（先通过 /discover/import 创建）
```

**成功响应 200：**
```json
{
  "code": 200,
  "data": {
    "paper_id": "abc123",
    "task_id": "celery-task-uuid",
    "pdf_path": "/app/uploads/abc123.pdf"
  }
}
```

**错误响应：**

| 状态码 | 原因 |
|--------|------|
| 404 | paper_id 不存在 |
| 413 | 文件超过 50 MB |
| 415 | 非 PDF 文件 |
| 500 | 磁盘写入失败 |

### 4.2 查询任务状态

```
GET /api/tasks/{task_id}
```

返回 Celery 任务的当前状态（PENDING / STARTED / SUCCESS / FAILURE）及结果。

---

## 5. Celery 任务详解

### 5.1 parse_paper_task

**任务名：** `app.tasks.parse_paper`

**入参：** `paper_id: str`

**执行步骤：**

1. 从数据库加载 Paper 记录，将 `status` 置为 `PARSING`
2. 检查 `paper.pdf_path` 是否存在：
   - **有 PDF**：用 PyMuPDF 逐页提取文本，执行清洗与分段，状态置为 `PENDING_EXTRACTION`，将分段文本传给 LLM 任务
   - **无 PDF**：直接用 `paper.abstract` 作为文本，状态置为 `PENDING_EXTRACTION`，触发 LLM 任务
3. 链式调用 `extract_key_points_task.delay(paper_id, paper_text)`
4. 任何异常均将状态置为 `FAILED`

**文本处理逻辑：**

- `_extract_text`：PyMuPDF 逐页 `get_text()`，页间用 `\n` 拼接
- `_clean`：修复连字符断行（`trans-\nformer` → `transformer`）、合并多余空行、压缩行内空白
- `_segment`：按数字编号标题（`1. Introduction`）或全大写标题（`ABSTRACT`）分段；无标题时整体作为 `FULL TEXT` 段

**返回值：**
```json
{
  "paper_id": "abc123",
  "status": "parsed",
  "sections": [
    {"heading": "ABSTRACT", "content": "..."},
    {"heading": "1. Introduction", "content": "..."}
  ]
}
```

### 5.2 extract_key_points_task

**任务名：** `app.tasks.llm.extract_key_points`

**入参：** `paper_id: str`, `paper_text: str`

**执行步骤：**

1. 将 `Paper.status` 置为 `EXTRACTING`
2. 调用 `chat_completion(EXTRACT_SYSTEM_PROMPT, build_user_prompt(paper_text))`
3. 从模型回复中解析 JSON，提取四要素字段，每字段截断至 200 字符
4. Upsert `KeyPoints` 表，将 `Paper.status` 置为 `PENDING_CONFIRMATION`
5. 失败时最多重试 2 次（间隔 30 秒），超限后置 `FAILED`

**Prompt 设计：**

System Prompt 要求模型输出严格的 JSON 对象，包含 `background`、`methodology`、`innovation`、`conclusion` 四个字段，每字段不超过 200 字符。User Prompt 将论文文本截断至 8000 字符后传入。

---

## 6. 大模型配置

通过环境变量切换提供商：

```env
LLM_PROVIDER=deepseek        # 或 qwen

# DeepSeek
DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat

# Qwen（通义千问）
QWEN_API_KEY=sk-xxx
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus

# 共享参数
LLM_TIMEOUT=120
LLM_MAX_TOKENS=1024
LLM_TEMPERATURE=0.2
```

两者均使用 OpenAI SDK 的兼容模式，切换时无需修改代码。

---

## 7. 启动方式

### 7.1 环境准备

```bash
# 安装依赖
pip install -r requirements.txt

# 复制并填写环境变量
cp .env.example .env
# 必填：DATABASE_URL, REDIS_BROKER_URL, REDIS_RESULT_BACKEND
# 必填：DEEPSEEK_API_KEY 或 QWEN_API_KEY
# 可选：UPLOAD_DIR（默认 /app/uploads）
```

### 7.2 启动 Redis（Broker + Backend）

```bash
# Docker 方式（推荐）
docker run -d -p 6379:6379 redis:7

# 或本地已安装 Redis
redis-server
```

### 7.3 启动 FastAPI 服务

```bash
cd src/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 7.4 启动 Celery Worker

```bash
cd src/backend

# 开发环境（单进程，带日志）
celery -A app.worker worker --loglevel=info

# 生产环境（多进程，后台运行）
celery -A app.worker worker --loglevel=warning --concurrency=4 --detach
```

> **注意**：Worker 的工作目录必须是 `src/backend`，否则 `db.*`、`app.*` 模块路径无法解析。

### 7.5 验证任务注册

```bash
# 列出所有已注册任务，确认以下三个存在：
celery -A app.worker inspect registered

# 期望看到：
#   app.tasks.example.ping
#   app.tasks.parse_paper
#   app.tasks.llm.extract_key_points
```

### 7.6 完整调用示例

```bash
# Step 1：导入论文元数据，获取 paper_id
curl -X POST http://localhost:8000/api/discover/import \
  -H "Content-Type: application/json" \
  -d '{"title":"Attention Is All You Need","user_id":"user-001"}'

# Step 2：上传 PDF（替换 <paper_id> 为上一步返回的值）
curl -X POST http://localhost:8000/api/papers/<paper_id>/upload \
  -F "file=@/path/to/paper.pdf"

# Step 3：轮询任务状态（替换 <task_id> 为上传接口返回的值）
curl http://localhost:8000/api/tasks/<task_id>
```

---

## 8. 常见问题

**Q：Worker 启动后看不到 `app.tasks.parse_paper`？**

确认 `app/tasks/__init__.py` 中已导入 `paper_tasks`：
```python
from app.tasks import example_tasks, paper_tasks, llm_tasks
```

**Q：LLM 任务一直重试失败？**

检查 `.env` 中的 API Key 是否正确，以及 `LLM_PROVIDER` 与实际填写的 Key 是否匹配。可用以下命令手动测试：
```python
from app.core.llm_client import chat_completion
print(chat_completion("你好", "介绍一下自己"))
```

**Q：上传 PDF 后状态停在 `PENDING_EXTRACTION`，LLM 任务未触发？**

确认 Celery Worker 正在运行，且 Redis 连接正常：
```bash
celery -A app.worker inspect ping
```

**Q：`no_pdf` 状态下四要素提取效果差？**

这是因为只用了摘要文本（`paper.abstract`）作为 LLM 输入。上传完整 PDF 后重新触发解析可获得更好的提取效果：重新调用 `POST /api/papers/{paper_id}/upload` 即可，接口会重置状态并重新派发任务。
