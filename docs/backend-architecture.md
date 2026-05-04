# Scider 后端架构文档

## 1. 项目概述

Scider 是一款面向科研新手的学术论文智能辅助平台，后端采用 **FastAPI + Celery + Redis + PostgreSQL** 技术栈。

---

## 2. 目录结构

```
src/backend/
├── .env                        # 环境变量配置
├── requirements.txt            # Python 依赖
├── readme.md                   # 后端启动说明
├── test.http                   # REST Client 测试文件
│
├── app/                        # FastAPI 应用主体
│   ├── main.py                 # 应用入口，注册路由
│   ├── worker.py               # Celery Worker 入口
│   ├── celery_app.py           # Celery 实例配置
│   │
│   ├── core/
│   │   └── config.py           # 全局配置（从环境变量读取）
│   │
│   ├── api/
│   │   └── routes/
│   │       └── tasks.py        # 任务相关 HTTP 接口
│   │
│   └── tasks/
│       └── example_tasks.py    # Celery 异步任务定义
│
└── db/                         # 数据库模块（独立于 app）
    ├── base.py                 # SQLAlchemy Base 声明
    ├── models.py               # 所有 ORM 数据模型
    ├── session.py              # 异步数据库会话管理
    ├── crud_user.py            # User 表 CRUD 操作
    ├── alembic.ini             # Alembic 配置
    └── alembic/
        └── versions/
            └── 0001_initial.py # 初始建表迁移脚本
```

---

## 3. 核心模块说明

### 3.1 应用入口 — `app/main.py`

```python
app = FastAPI(title=settings.APP_NAME)
app.include_router(tasks_router, prefix=settings.API_PREFIX)
```

- 创建 FastAPI 实例
- 注册 `/api/tasks` 路由
- 提供 `GET /health` 健康检查接口

### 3.2 配置管理 — `app/core/config.py`

从环境变量读取，支持 `.env` 文件覆盖：

| 变量                   | 默认值                     | 说明            |
| ---------------------- | -------------------------- | --------------- |
| `APP_NAME`             | `Scider Backend`           | 应用名称        |
| `API_PREFIX`           | `/api`                     | 路由前缀        |
| `REDIS_BROKER_URL`     | `redis://localhost:6379/0` | Celery Broker   |
| `REDIS_RESULT_BACKEND` | `redis://localhost:6379/1` | Celery 结果存储 |
| `DATABASE_URL`         | `postgresql+asyncpg://...` | 数据库连接      |

### 3.3 Celery 异步任务

**`app/celery_app.py`** — 创建 Celery 实例，连接 Redis，自动发现 `app.tasks` 下的任务模块。

**`app/worker.py`** — Worker 启动入口，仅导出 `celery_app`。

**`app/tasks/example_tasks.py`** — 示例任务：

```python
@celery_app.task(name="app.tasks.ping")
def ping_task() -> dict:
    return {"message": "pong", "timestamp": ...}
```

### 3.4 HTTP 接口 — `app/api/routes/tasks.py`

| 方法   | 路径                   | 说明                               |
| ------ | ---------------------- | ---------------------------------- |
| `POST` | `/api/tasks/ping`      | 提交 ping 异步任务，返回 `task_id` |
| `GET`  | `/api/tasks/{task_id}` | 查询任务状态和结果                 |

### 3.5 数据库模块 — `db/`

#### ORM 数据模型（`db/models.py`）

| 模型        | 表名        | 说明                              |
| ----------- | ----------- | --------------------------------- |
| `User`      | `user`      | 用户账号                          |
| `Folder`    | `folder`    | 论文文件夹（属于用户）            |
| `Paper`     | `paper`     | 论文记录，含处理状态流转          |
| `KeyPoints` | `keypoints` | 论文关键点（背景/方法/创新/结论） |
| `Tag`       | `tag`       | 标签                              |
| `Task`      | `task`      | 异步处理任务记录                  |

**Paper 状态流转：**

```
PENDING_PARSING → PARSING → PENDING_EXTRACTION → EXTRACTING → PENDING_CONFIRMATION → CONFIRMED
                                                                                    ↘ FAILED
```

**Task 类型：**

- `PDF_PARSE` — PDF 解析
- `LLM_EXTRACT` — LLM 关键信息提取

#### 数据库会话（`db/session.py`）

基于 SQLAlchemy 异步引擎，提供：

- `get_session()` — 异步上下文管理器，用于获取 `AsyncSession`
- `create_tables_if_needed()` — 快速测试用建表工具

#### CRUD（`db/crud_user.py`）

提供 User 表的异步 CRUD：`create_user` / `get_user_by_email` / `get_user` / `update_user_name` / `delete_user`

---

## 4. 启动方法

### 前置条件

- Python 3.10+
- Redis（本地默认端口 6379）
- PostgreSQL（可选，数据库功能尚未集成进 app）

### 步骤一：安装依赖

```bash
cd src/backend
pip install -r requirements.txt
```

### 步骤二：配置环境变量

`.env` 文件已包含默认配置，按需修改：

```env
APP_NAME=Scider Backend
API_PREFIX=/api
REDIS_BROKER_URL=redis://localhost:6379/0
REDIS_RESULT_BACKEND=redis://localhost:6379/1
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/scider
```

### 步骤三：启动 Redis

确保本地 Redis 已运行（默认端口 6379）。

### 步骤四：启动 FastAPI

```bash
cd src/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 步骤五：启动 Celery Worker（新终端）

```bash
cd src/backend
celery -A app.worker:celery_app worker --loglevel=info
```

### 步骤六（可选）：数据库迁移

```bash
cd src/backend/db
alembic upgrade head
```

---

## 5. 接口验证

**健康检查：**

```
GET http://127.0.0.1:8000/health
```

**Swagger UI（推荐）：**

```
http://127.0.0.1:8000/docs
```

**提交任务 → 查询结果：**

```bash
# 提交
curl -X POST http://127.0.0.1:8000/api/tasks/ping

# 查询（替换 <task_id>）
curl http://127.0.0.1:8000/api/tasks/<task_id>
```

---

## 6. 技术栈总览

| 组件         | 技术               | 版本要求 |
| ------------ | ------------------ | -------- |
| Web 框架     | FastAPI            | ≥ 0.110  |
| ASGI 服务器  | Uvicorn            | ≥ 0.30   |
| 异步任务队列 | Celery             | ≥ 5.4    |
| 消息中间件   | Redis              | ≥ 5.0    |
| ORM          | SQLAlchemy (async) | ≥ 2.0    |
| 数据库迁移   | Alembic            | ≥ 1.13   |
| 数据库驱动   | asyncpg            | ≥ 0.29   |
| 数据库       | PostgreSQL         | —        |
