# Scider 后端测试套件

## 测试概览

本测试套件包含三大核心测试场景，确保系统在生产环境的安全性、可靠性和可恢复性。

---

## 测试文件

### 1. `test_auth_isolation.py` - 用户数据隔离与越权测试

**测试目标：**
- 用户 A 无法访问用户 B 的 PDF、笔记、图谱数据（水平越权）
- JWT 篡改检测（修改 token 中的 user_id）
- 未授权端点访问（垂直越权）
- 文件夹、论文、笔记的跨用户隔离

**测试用例（15 个）：**
- `test_user_isolation_papers_list` - 论文列表隔离
- `test_horizontal_privilege_escalation_paper_detail` - 论文详情越权
- `test_horizontal_privilege_escalation_paper_pdf` - PDF 下载越权
- `test_horizontal_privilege_escalation_notes` - 笔记访问越权
- `test_jwt_tampering_user_id` - JWT 签名篡改检测
- `test_jwt_tampering_correct_secret` - JWT 内容篡改检测
- `test_graph_similarity_isolation` - 知识图谱隔离
- `test_graph_ask_isolation` - 图谱问答隔离（新功能）
- `test_unauthorized_access_without_token` - 无 token 访问拒绝
- `test_expired_token_rejection` - 过期 token 拒绝
- `test_folder_isolation` - 文件夹隔离
- `test_paper_deletion_isolation` - 删除操作隔离

**前置条件：**
```bash
# 创建两个测试用户
export TEST_USER_A_EMAIL=usera@test.com
export TEST_USER_A_PASSWORD=passworda
export TEST_USER_B_EMAIL=userb@test.com
export TEST_USER_B_PASSWORD=passwordb
```

**运行方式：**
```bash
pytest tests/test_auth_isolation.py -v
```

---

### 2. `test_async_consistency.py` - 离线任务与异步状态最终一致性测试

**测试目标：**
- Celery 异步解析 PDF 时，任务状态流转正确
- Worker 崩溃或重试后，任务状态正确恢复
- 并发上传多个 PDF，状态最终一致
- 笔记导出、图谱导出等异步任务结果与源数据一致
- 向量化任务幂等性

**测试用例（9 个）：**
- `test_pdf_upload_and_status_flow` - PDF 上传状态流转（PENDING_PARSING → PARSING → PENDING_EXTRACTION → EXTRACTING → PENDING_CONFIRMATION → CONFIRMED）
- `test_concurrent_pdf_upload_consistency` - 并发上传一致性
- `test_task_retry_on_failure` - 任务失败重试（跳过，需真实环境）
- `test_embedding_task_idempotency` - 向量化幂等性
- `test_note_export_consistency` - 笔记数据一致性
- `test_graph_cache_consistency` - 图谱 LLM 缓存一致性
- `test_paper_deletion_cascades` - 级联删除测试

**前置条件：**
```bash
# 启动 Celery Worker
celery -A app.celery_app worker --loglevel=info

# 启动 Redis
redis-server

# 配置测试用户
export TEST_EMAIL=test@example.com
export TEST_PASSWORD=test123
```

**运行方式：**
```bash
pytest tests/test_async_consistency.py -v -s
```

---

### 3. `test_deployment.py` - 生产环境部署演练与回滚验证测试

**测试目标：**
- 在类生产环境执行一键部署脚本
- 验证数据库迁移正确执行
- 验证 Redis 缓存连接正常
- 验证对象存储（PDF 上传/下载）配置
- 模拟部署失败后的回滚流程
- 确认数据无损、服务快速恢复

**测试用例（13 个）：**
- `test_deployment_script_exists` - 部署脚本存在
- `test_database_migration` - 数据库迁移验证
- `test_redis_connection` - Redis 连接测试
- `test_service_health_check` - 健康检查端点
- `test_pdf_upload_storage` - 上传目录配置
- `test_environment_variables` - 环境变量完整性
- `test_backup_and_restore` - 备份恢复流程
- `test_rollback_script_dry_run` - 回滚脚本演练
- `test_deployment_rollback_simulation` - 部署失败回滚模拟
- `test_database_connection_pool` - 连接池配置
- `test_cors_configuration` - CORS 安全配置
- `test_log_files_exist` - 日志文件检查

**前置条件：**
```bash
# 配置环境变量
export DATABASE_URL=mysql+aiomysql://user:pass@host:3306/scider
export REDIS_BROKER_URL=redis://localhost:6379/0
export JWT_SECRET=your_production_secret
export DEPLOY_TEST_URL=http://localhost:8000

# 创建部署脚本目录
mkdir -p scripts backups
```

**运行方式：**
```bash
pytest tests/test_deployment.py -v -s
```

---

## 快速开始

### 安装依赖

```bash
pip install pytest pytest-asyncio httpx
```

### 运行所有测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行指定测试文件
pytest tests/test_auth_isolation.py -v

# 运行指定测试用例
pytest tests/test_auth_isolation.py::test_user_isolation_papers_list -v

# 显示打印输出
pytest tests/ -v -s

# 生成 HTML 报告
pytest tests/ --html=report.html --self-contained-html
```

### 跳过在线测试

```bash
# 跳过需要真实服务的测试
pytest tests/ -v -m "not online"
```

---

## 测试覆盖率

### 生成覆盖率报告

```bash
pip install pytest-cov

pytest tests/ --cov=app --cov-report=html
```

### 查看报告

```bash
# 打开 htmlcov/index.html
```

---

## CI/CD 集成

### GitHub Actions 示例

```yaml
name: Backend Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: testpass
          MYSQL_DATABASE: scider_test
        ports:
          - 3306:3306

      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests
        env:
          DATABASE_URL: mysql+aiomysql://root:testpass@localhost:3306/scider_test
          REDIS_BROKER_URL: redis://localhost:6379/0
          JWT_SECRET: test_secret_key_for_ci
        run: |
          pytest tests/ -v --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## 故障排查

### 常见问题

**1. 数据库连接失败**
```bash
# 检查 DATABASE_URL
echo $DATABASE_URL

# 测试数据库连接
mysql -h localhost -u root -p
```

**2. Redis 连接失败**
```bash
# 检查 Redis 是否运行
redis-cli ping

# 检查 REDIS_BROKER_URL
echo $REDIS_BROKER_URL
```

**3. Celery Worker 未启动**
```bash
# 启动 Worker
celery -A app.celery_app worker --loglevel=info

# 检查任务状态
celery -A app.celery_app inspect active
```

**4. JWT 验证失败**
```bash
# 检查 JWT_SECRET
echo $JWT_SECRET

# 确保密钥长度 >= 32 字符
```

---

## 测试最佳实践

### 1. 隔离性
- 每个测试用例独立运行，不依赖其他测试
- 使用 `@pytest.fixture` 管理共享资源
- 测试后清理数据（删除创建的论文、笔记等）

### 2. 幂等性
- 测试可以重复运行多次，结果一致
- 使用唯一标识符（时间戳、UUID）避免冲突

### 3. 可读性
- 测试名称清晰描述测试目标
- 使用注释说明复杂逻辑
- 打印关键步骤便于调试

### 4. 性能
- 使用 `scope="module"` 共享耗时的 fixture（如登录 token）
- 跳过需要真实服务的测试（使用 `pytest.skip`）
- 并发运行独立测试（`pytest-xdist`）

---

## 测试数据管理

### Fixtures 目录

```
tests/
├── fixtures/
│   ├── sample.pdf          # 测试 PDF 文件
│   ├── large_paper.pdf     # 大文件测试（>10MB）
│   └── corrupted.pdf       # 损坏文件测试
├── test_auth_isolation.py
├── test_async_consistency.py
└── test_deployment.py
```

### 创建测试 PDF

```python
# tests/fixtures/generate_pdf.py
from reportlab.pdfgen import canvas

def create_test_pdf(filename, pages=10):
    c = canvas.Canvas(filename)
    for i in range(pages):
        c.drawString(100, 750, f"Page {i+1}")
        c.drawString(100, 700, "This is a test PDF document.")
        c.showPage()
    c.save()

if __name__ == "__main__":
    create_test_pdf("sample.pdf", pages=5)
```

---

## 性能基准

### 预期执行时间

| 测试文件 | 用例数 | 预期时长 | 依赖服务 |
|---------|-------|---------|---------|
| `test_auth_isolation.py` | 15 | 30-60s | MySQL, Redis |
| `test_async_consistency.py` | 9 | 5-10min | MySQL, Redis, Celery |
| `test_deployment.py` | 13 | 2-5min | MySQL, Redis, 文件系统 |

### 加速技巧

```bash
# 并发运行
pip install pytest-xdist
pytest tests/ -n auto

# 只运行失败的测试
pytest tests/ --lf

# 跳过慢速测试
pytest tests/ -v -m "not slow"
```

---

## 贡献指南

### 添加新测试

1. 创建新的测试文件 `test_<feature>.py`
2. 编写测试用例，遵循命名规范 `test_<scenario>`
3. 添加文档字符串说明测试目标
4. 更新本 README 文档

### 代码风格

- 遵循 PEP 8
- 使用 `black` 格式化代码
- 使用 `flake8` 检查代码质量

```bash
pip install black flake8
black tests/
flake8 tests/
```

---

## 联系方式

如有问题或建议，请提交 Issue 或 Pull Request。
