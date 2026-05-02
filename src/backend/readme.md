# Backend - FastAPI + Celery + Redis

## 1. 环境准备

1. 进入后端目录：

```bash
cd src/backend
```

2. 安装依赖：

```bash
python -m pip install -r requirements.txt
```

3. 准备环境变量（复制 `.env.example` 为 `.env`，按需修改）：

```bash
cp .env.example .env
# Windows PowerShell:
Copy-Item .env.example .env
```

> `.env` 文件已预填 MySQL + Redis 本地开发配置，通常无需修改即可使用。

## 2. 启动基础设施（MySQL + Redis）

项目使用 **Docker Compose** 一键启动 MySQL 和 Redis：

```bash
cd src/backend
docker compose up -d
```

确认服务已就绪：

```bash
docker ps
```

> **要求**：本地需安装并运行 **Docker Desktop**。首次启动会自动拉取镜像，耗时约 1-2 分钟。

## 3. 启动 FastAPI

确保 `.env` 文件已正确配置（见 §1），然后启动：

```bash
cd src/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

健康检查：

```bash
GET http://127.0.0.1:8000/health
```

## 4. 启动 Celery Worker

新开一个终端，**确保在 `src/backend` 目录下**执行：

Windows（本地开发推荐，避免 prefork 兼容问题）：

```bash
cd src/backend
celery -A app.worker:celery_app worker --loglevel=info --pool=solo --concurrency=1
```

Linux / macOS：

```bash
cd src/backend
celery -A app.worker:celery_app worker --loglevel=info
```

## 5. 验证异步任务

### 方式一：VS Code REST Client 插件（推荐）

1. 在 VS Code 扩展市场搜索并安装 **REST Client**
2. 打开项目根目录下的 `test_example.http` 文件，然后拷贝一份，命名为 `test.http`，**不要直接在 `test_example.http` 文件里修改内容**
3. 点击每条请求上方出现的 **Send Request**，结果显示在右侧面板

```http
### 健康检查
GET http://127.0.0.1:8000/health

### 提交 ping 任务
POST http://127.0.0.1:8000/api/tasks/ping

### 查询任务状态（替换为实际 task_id）
GET http://127.0.0.1:8000/api/tasks/<task-id>
```

### 方式二：浏览器 Swagger UI

FastAPI 自带交互文档，直接访问：

```
http://127.0.0.1:8000/docs
```

点击接口 → **Try it out** → **Execute** 即可。

### 方式三：curl

```bash
# 健康检查
curl http://127.0.0.1:8000/health

# 提交任务
curl -X POST http://127.0.0.1:8000/api/tasks/ping

# 查询任务状态
curl http://127.0.0.1:8000/api/tasks/<task-id>
```

## 6. 数据库迁移（Alembic）

本项目的数据库版本管理使用 **Alembic**，迁移文件位于 `db/alembic/versions/`。

### 数据库驱动

| 数据库 | 驱动 | 连接串示例 |
|--------|------|-----------|
| MySQL | `asyncmy` | `mysql+asyncmy://user:pass@host:3306/db?charset=utf8mb4` |
| PostgreSQL | `asyncpg` | `postgresql+asyncpg://user:pass@host:5432/db` |

> 更换数据库时，只需修改 `.env` 中的 `DATABASE_URL` 并安装对应驱动即可。

### 执行迁移

先确认 `DATABASE_URL` 已正确设置（在 `.env` 中），然后：

```bash
cd src/backend/db
alembic upgrade head
```

### 生成新迁移（修改 Model 后）

```bash
cd src/backend/db
alembic revision --autogenerate -m "描述你的修改"
```

### 查看迁移状态

```bash
cd src/backend/db
alembic current
```

## 7. JWT 认证中间件

全局 ASGI 中间件，自动拦截 `/api/*` 路径的请求并进行 JWT 鉴权。

- 白名单路径（免登录）在 `middleware/jwt_middleware.py` 的 `EXEMPT_PATHS` 中定义
- 鉴权通过后，用户信息注入到 `request.state.user`（`dict` 类型，包含 `id`、`email`、`name`）
- 鉴权失败返回 `401` JSON 响应

### 获取当前用户

```python
from fastapi import Request

@router.post("/some-endpoint")
async def handler(request: Request):
    user = getattr(request.state, "user", None)
    if not user:
        # 未认证
        ...
    user_id = user["id"]
```

## 8. PDF 论文上传

### 接口

```
POST /api/papers/upload
```

- **Headers**: `Authorization: Bearer <token>`
- **Body**: `multipart/form-data`，字段名 `file`，仅支持 `.pdf`
- **文件大小上限**: 由 `MAX_UPLOAD_SIZE_MB` 控制（默认 50MB）
- **去重机制**: 基于文件内容 MD5 哈希，文件完全相同则返回 `409` 错误

### 上传流程

1. JWT 鉴权 → 2. 文件类型/大小校验 → 3. MD5 计算 → 4. 查重 → 5. 存储（以 `{md5}.pdf` 命名） → 6. 入库 → **7. 触发异步解析任务链**

### 异步任务链

上传成功后自动触发后台任务链：

```
parse_pdf_task (PDF 文本提取) → extract_key_points_task (LLM 四要素提取)
```

| 任务 | 说明 | Paper 状态流转 |
|------|------|---------------|
| `parse_pdf_task` | 用 PyMuPDF 提取 PDF 纯文本 | `PENDING_PARSING → PARSING → PENDING_EXTRACTION` |
| `extract_key_points_task` | 调用大模型提取四要素并写入 KeyPoints 表 | `PENDING_EXTRACTION → EXTRACTING → PENDING_CONFIRMATION` |

可通过返回的 `task_id` 调用 `GET /api/tasks/{task_id}` 查询任务进度。

### curl 示例

```bash
# 先登录获取 token
curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"123456"}'

# 上传 PDF（将 <token> 替换为实际 token）
curl -X POST http://127.0.0.1:8000/api/papers/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@/path/to/paper.pdf"
```

### 成功响应

```json
{
  "code": 0,
  "msg": "上传成功，后台解析中",
  "data": {
    "paper_id": "xxx",
    "filename": "paper.pdf",
    "file_size": 123456,
    "md5": "d41d8cd98f00b204e9800998ecf8427e",
    "status": "pending_parsing",
    "task_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
  }
}
```

### 实现文件

- `app/core/pdf_parser.py` — PyMuPDF 文本提取
- `app/tasks/parse_task.py` — PDF 解析 Celery 任务
- `app/tasks/llm_tasks.py` — LLM 四要素提取 Celery 任务

## 9. 文件夹管理（CRUD）

文件夹用于对论文进行分类管理，所有接口均需 JWT 认证。

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/folders/` | 创建文件夹 |
| `GET` | `/api/folders/` | 获取当前用户的文件夹列表 |
| `GET` | `/api/folders/{id}` | 获取单个文件夹详情 |
| `PATCH` | `/api/folders/{id}` | 重命名文件夹 |
| `DELETE` | `/api/folders/{id}` | 删除文件夹（其中的论文自动解绑，论文本身不受影响） |

### 实现文件

- `db/crud_folder.py` — 文件夹 CRUD 异步方法
- `app/api/routes/folders.py` — 5 个 RESTful 接口，含用户归属校验