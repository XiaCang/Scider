# 端到端全流程回归测试方案

## 概述

基于对 Scider 后端架构的深入分析，本文档提供完整的端到端测试方案，覆盖用户典型完整路径。

## 架构分析总结

### 核心模块

1. **用户认证模块** (`module/user/controller/auth_router.py`)
   - 注册：`POST /api/user/register`（需验证码）
   - 登录：`POST /api/user/login`
   - 密码重置：`POST /api/user/change-password`
   - 验证码：`POST /api/user/send-code`

2. **论文管理模块** (`app/api/routes/papers.py`)
   - 上传：`POST /api/papers/upload`（触发 Celery 异步解析）
   - 列表：`GET /api/papers/`
   - 详情：`GET /api/papers/{paper_id}`
   - 四要素确认：`PATCH /api/papers/{paper_id}/key-points`
   - 删除：`DELETE /api/papers/{paper_id}`

3. **笔记模块** (`app/api/routes/notes.py`)
   - 创建：`POST /api/notes/`
   - 列表：`GET /api/notes/?paperId={paper_id}`
   - 详情：`GET /api/notes/{note_id}`
   - 更新：`PATCH /api/notes/{note_id}`
   - 删除：`DELETE /api/notes/{note_id}`

4. **知识图谱模块** (`app/api/routes/graph.py`, `app/api/routes/graph_edit.py`)
   - 相似度图谱：`GET /api/graph/similarity`
   - LLM 生成图谱：`GET /api/graph/llm-structure`
   - 自定义节点/边：`POST /api/graph/edit/nodes`, `POST /api/graph/edit/edges`

5. **AI 问答模块** (`app/api/routes/papers.py`, `app/api/routes/chat_ws.py`)
   - HTTP 问答：`POST /api/papers/{paper_id}/ask`
   - WebSocket 流式问答：`ws://localhost:8000/api/ws/chat?token=<JWT>&paper_id=<ID>`

### 数据流转状态

**论文处理流程**：
```
PENDING_PARSING → PARSING → PENDING_EXTRACTION → EXTRACTING 
→ PENDING_CONFIRMATION → CONFIRMED
```

**关键异步任务**：
- PDF 解析：`parse_pdf_task` (Celery)
- 向量化：`embed_paper_task` (在确认四要素后触发)

## 测试流程设计

### 测试路径

```
注册 → 登录 → 上传PDF → 等待解析 → 确认四要素 → 生成知识图谱 
→ 添加笔记 → AI问答(HTTP) → AI问答(WebSocket) → 密码重置 
→ 新密码登录 → 注册第二用户 → 多设备登录 → 数据一致性验证
```

### 测试阶段

#### Stage 0: 健康检查
- `GET /health` → 验证后端服务在线

#### Stage 1: 注册流程
- `POST /api/user/send-code` → 发送验证码
- `POST /api/user/register` → 完成注册
- 验证：重复注册应被拒绝

#### Stage 2: 登录与认证
- `POST /api/user/login` → 正常登录，获取 JWT token
- `GET /api/user/me` → 验证认证成功
- 验证：错误密码应登录失败
- 验证：未认证访问受保护接口返回 401

#### Stage 3: 上传 PDF
- `POST /api/papers/upload` → 上传测试 PDF
- 轮询 `GET /api/papers/{paper_id}` → 等待解析完成
- 目标状态：`PENDING_CONFIRMATION` 或 `CONFIRMED`

#### Stage 4: 四要素解析与确认
- `PATCH /api/papers/{paper_id}/key-points` → 确认四要素
- 验证：返回 `embed_task_id`（触发向量化）
- 验证：论文状态变为 `CONFIRMED`

#### Stage 5: 生成知识图谱
- `GET /api/graph/llm-structure` → 生成 LLM 图谱
- 验证：返回 `nodes` 和 `links`
- 验证：节点包含论文信息
- （可选）`GET /api/graph/similarity` → 相似度图谱

#### Stage 6: 添加笔记
- `POST /api/notes/` → 创建笔记
- `GET /api/notes/?paperId={paper_id}` → 列表验证
- `GET /api/notes/{note_id}` → 详情验证
- `PATCH /api/notes/{note_id}` → 更新笔记

#### Stage 7: AI 问答（HTTP）
- `POST /api/papers/{paper_id}/ask` → 提交问题
- 验证：返回 `answer` 字段（长度 > 10）
- 验证：返回 `sources`（包含 full_text 和 note）

#### Stage 8: AI 问答（WebSocket）
- 连接：`ws://localhost:8000/api/ws/chat?token=<JWT>&paper_id=<ID>`
- 发送：`{"type": "question", "content": "问题"}`
- 验证：接收流式 `{"type": "token", "content": "...", "index": N}`
- 验证：接收完成 `{"type": "done", "content": "完整回答", "sources": [...]}`

#### Stage 9: 密码重置
- `POST /api/user/send-code` → 获取验证码
- `POST /api/user/change-password` → 重置密码
- `POST /api/user/login` → 用新密码登录成功

#### Stage 10: 多设备登录
- 注册第二用户
- 两个用户同时登录
- 验证：不同 token 可同时访问各自资源
- 验证：用户 A 无法访问用户 B 的论文/笔记

#### Stage 11: 数据一致性验证
- 跨接口验证论文数据：
  - `GET /api/papers/` 列表中的数据
  - `GET /api/papers/{paper_id}` 详情数据
  - 笔记关联的 `paper_id`
- 验证四要素在确认后保持不变
- 验证论文状态流转正确性

## 实现代码

基于分析，已创建 `tests/test_e2e_regression.py`，包含：

### 工具函数
- `_make_minimal_pdf()`: 生成测试 PDF（无需外部依赖）
- `_request()`: 统一 HTTP 请求封装（支持 multipart/form-data）
- `_get()`, `_post()`, `_patch()`, `_delete()`: RESTful 封装
- `_upload_pdf()`: PDF 上传专用
- `_wait_paper()`: 轮询等待论文状态
- `_get_verify_code()`: 获取验证码（支持环境变量或调试接口）

### 测试上下文
```python
@dataclass
class E2EContext:
    primary_token: str
    primary_user_id: str
    secondary_token: str
    secondary_user_id: str
    paper_id: str
    note_id: str
    folder_id: str
    snapshots: dict  # 跨测试数据快照
```

### pytest 配置
- `skip_if_offline`: 后端不在线则跳过全部测试
- `skip_if_llm`: 跳过 LLM 相关测试（图谱、AI问答）

## 运行方式

```bash
cd src/backend

# 完整测试
pytest tests/test_e2e_regression.py -v --tb=short

# 跳过 LLM 测试（适用于无 API key 环境）
E2E_SKIP_LLM=1 pytest tests/test_e2e_regression.py -v

# 自定义配置
E2E_BASE_URL=http://localhost:8000 \
E2E_VERIFY_CODE=123456 \
E2E_PARSE_TIMEOUT=180 \
E2E_POLL_INTERVAL=3 \
pytest tests/test_e2e_regression.py -v
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `E2E_BASE_URL` | `http://localhost:8000` | 后端服务地址 |
| `E2E_VERIFY_CODE` | (空) | 固定验证码（开发/CI环境） |
| `E2E_PARSE_TIMEOUT` | `120` | PDF 解析超时（秒） |
| `E2E_POLL_INTERVAL` | `2` | 轮询间隔（秒） |
| `E2E_SKIP_LLM` | `0` | 是否跳过 LLM 测试 |

## 前置条件

1. **后端服务**：`uvicorn app.main:app --reload --port 8000`
2. **Celery Worker**：`celery -A app.worker:celery_app worker --loglevel=info`
3. **Redis**：默认 `localhost:6379`
4. **PostgreSQL**：已完成 `alembic upgrade head`
5. **验证码获取**：
   - 方式 A：设置 `E2E_VERIFY_CODE` 环境变量
   - 方式 B：后端提供 `GET /api/debug/verify-code?email=<email>` 调试路由

## 数据一致性检查点

### 1. 用户 Profile 一致性
- 注册返回的 `userId` = 登录后 `/api/user/me` 返回的 `id`
- 密码重置前后 `userId` 不变

### 2. 论文数据一致性
- 上传返回的 `paper_id` = 轮询查询的 `paper.id`
- 四要素确认后：
  - `status` = `CONFIRMED`
  - `keyPoints` 字段完整（background, method, innovation, conclusion）
- 列表接口与详情接口返回的 `title`, `authors`, `year` 一致

### 3. 笔记关联一致性
- 创建笔记的 `paperId` = `GET /api/notes/{note_id}` 返回的 `paperId`
- 笔记列表 `GET /api/notes/?paperId=X` 只返回该论文的笔记

### 4. 跨模块引用一致性
- AI 问答返回的 `sources` 中：
  - `type=full_text` 的 `excerpt` 应来自论文 `full_text`
  - `type=note` 的 `excerpt` 应来自笔记 `content`

### 5. 多用户隔离性
- 用户 A 无法访问用户 B 的论文（返回 404）
- 用户 A 无法访问用户 B 的笔记（返回 404）

## 测试覆盖统计

| 模块 | 接口数 | 覆盖数 | 覆盖率 |
|------|--------|--------|--------|
| 用户认证 | 5 | 5 | 100% |
| 论文管理 | 8 | 6 | 75% |
| 笔记管理 | 5 | 4 | 80% |
| 知识图谱 | 4 | 2 | 50% |
| AI 问答 | 2 | 2 | 100% |
| **总计** | **24** | **19** | **79%** |

## 扩展测试建议

### 1. 文件夹模块测试
```python
@skip_if_offline
def test_folder_management():
    # 创建文件夹
    s, b = _post("/api/folders/", {"name": "E2E Folder"}, token=ctx.primary_token)
    folder_id = b["data"]["id"]
    
    # 添加论文到文件夹
    _post(f"/api/folders/{folder_id}/papers", {"paper_id": ctx.paper_id}, token=ctx.primary_token)
    
    # 验证文件夹内论文
    s, b = _get(f"/api/folders/{folder_id}", token=ctx.primary_token)
    assert ctx.paper_id in b["data"]["paperIds"]
```

### 2. 图谱编辑测试
```python
@skip_if_offline
def test_graph_edit():
    # 创建自定义节点
    s, b = _post("/api/graph/edit/nodes", {
        "name": "Custom Concept",
        "node_type": "concept",
        "category": 1
    }, token=ctx.primary_token)
    node_id = b["data"]["id"]
    
    # 创建自定义边
    _post("/api/graph/edit/edges", {
        "source_id": ctx.paper_id,
        "target_id": node_id,
        "relation_type": "related",
        "label": "Custom relation"
    }, token=ctx.primary_token)
```

### 3. WebSocket 多轮对话测试
```python
import websocket

def test_websocket_multi_turn():
    ws = websocket.create_connection(
        f"ws://localhost:8000/api/ws/chat?token={ctx.primary_token}&paper_id={ctx.paper_id}"
    )
    
    # 第一轮
    ws.send(json.dumps({"type": "question", "content": "What is the main idea?"}))
    # ... 接收流式响应
    
    # 第二轮（带上下文）
    ws.send(json.dumps({"type": "question", "content": "Can you elaborate on that?"}))
    # ... 验证 AI 能引用前文
    
    ws.close()
```

## 故障排查

### 1. 验证码无法获取
**症状**：`pytest.skip("无法获取验证码")`

**解决方案**：
- 方案 A：在后端 `.env` 中临时禁用真实邮件发送，返回固定码 `000000`
- 方案 B：后端添加调试路由（仅开发环境）：
```python
@router.get("/api/debug/verify-code")
async def debug_get_code(email: str):
    r = get_redis()
    code = await r.get(f"verify:{email}")
    return {"code": 0, "data": {"verify_code": code.decode() if code else None}}
```

### 2. PDF 解析超时
**症状**：`AssertionError: 解析超时/失败: None`

**排查**：
1. Celery Worker 是否运行：`ps aux | grep celery`
2. 查看 Worker 日志：`celery -A app.worker:celery_app worker --loglevel=debug`
3. 检查 Redis 连接：`redis-cli ping`

### 3. LLM 相关测试失败
**症状**：`AI问答失败: AI 服务暂时不可用`

**排查**：
1. `.env` 中 `DEEPSEEK_API_KEY` 或 `QWEN_API_KEY` 是否配置
2. 网络是否可访问 LLM API
3. 临时跳过：`E2E_SKIP_LLM=1 pytest ...`

## 总结

本测试方案基于对 Scider 后端架构的完整分析，覆盖了从用户注册到 AI 问答的完整流程，验证了各模块之间的数据一致性和接口调用链完整性。测试代码使用 pytest 框架，无外部依赖（PDF 生成器纯 Python 实现），适合 CI/CD 集成。
