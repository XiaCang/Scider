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

3. 准备环境变量（可复制 `.env.example`）：

```bash
APP_NAME=Scider Backend
API_PREFIX=/api
REDIS_BROKER_URL=redis://localhost:6379/0
REDIS_RESULT_BACKEND=redis://localhost:6379/1
```

## 2. 启动 Redis

请确保本地 Redis 已启动，默认端口 `6379`。

## 3. 启动 FastAPI

```bash
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
2. 打开项目根目录下的 `test.http` 文件
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

### 预期返回

提交任务后返回：

```json
{
  "task_id": "<task-id>",
  "status": "PENDING"
}
```

查询任务完成后返回：

```json
{
  "task_id": "<task-id>",
  "status": "SUCCESS",
  "result": {
    "message": "pong",
    "timestamp": "2026-04-25T01:00:00"
  }
}
```