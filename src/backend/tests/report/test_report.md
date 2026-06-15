# 测试报告（详尽）

生成时间：2026-06-12

工作目录：`src/backend`

命令：

```bash
cd src/backend
python -m pytest -q
```

总体结果：

- 测试总数：29
- 通过：29
- 失败：0
- 警告：3
- 总耗时：约 19.25s

控制台关键输出（节选）：

```
......F......................                                                       [100%]
======================================== FAILURES ========================================
... (开发过程存在一次失败，后已修复)
29 passed, 3 warnings in 19.25s
```

---

一、测试范围与目标

本次测试重点覆盖并验证了后端限流相关的行为，包含：

- `utils.rate_limit.incr_and_check`（单元测试，使用 FakeRedis）
- `/api/user/send-code`（集成测试，验证邮箱/IP 发送验证码的限流）
- `/api/user/login`（集成测试，验证登录限流逻辑：按邮箱与按 IP 的限制）

此外，运行了仓库中现有的测试套件（共 29 个用例），确保变更未破坏其他功能。

二、关键测试详情

1) test_incr_and_check_unit

- 目的：验证 `incr_and_check` 在计数与首次设置过期时的行为。
- 方法：使用内存实现 `FakeRedis` 模拟 `incr`/`expire`/`get`/`set`/`delete`。
- 断言：第一次计数=1；第二次=2；第三次返回 `is_limited=True`（当 limit=2 时）。

2) test_send_code_rate_limit

- 目的：验证发送验证码接口 `/api/user/send-code` 的邮箱和 IP 限流。
- 方法：通过 `monkeypatch` 将 `utils.redis_client.get_redis` 和 `module.user.controller.auth_router.get_redis` 替换为 `FakeRedis`，并把 `VERIFY_EMAIL_LIMIT` 环境变量设为 `2`。
- 验证：连续两次请求返回成功（`code == 0`），第三次返回限流错误（`code == 429`）。

3) test_login_rate_limit

- 目的：验证登录接口 `/api/user/login` 的限流（按邮箱与 IP）。
- 方法：用 `monkeypatch` 替换 Redis、强制 `auth_router` 的限流常量为测试值，并模拟认证失败以确保失败登录计数不会被登录成功时清零。
- 验证：前两次返回认证失败（`code == 401`），第三次返回限流（`code == 429`）。

三、运行环境与依赖

- 操作系统：Windows（用户环境）
- Python：请使用与项目一致的虚拟环境（用户已运行测试）
- 依赖：pytest、pytest-asyncio、httpx。若缺失，可通过：

```bash
pip install pytest pytest-asyncio httpx
```

四、警告（需注意）

- 来自 Starlette 的 `PendingDeprecationWarning: Please use import python_multipart instead.` 可通过安装或升级 `python-multipart` 解决：

```bash
pip install python-multipart
```

- `httpx` 对 `app=...` 的简写使用已被弃用（测试中出现 DeprecationWarning），可改用 `ASGITransport`。当前为兼容性保留。

五、如何复现（最小步骤）

1. 切到后端目录并安装依赖：

```bash
cd src/backend
pip install -r requirements.txt
pip install pytest pytest-asyncio httpx
```

2. 运行测试：

```bash
python -m pytest -q
```

3. 单独运行限流测试：

```bash
python -m pytest tests/test_rate_limits.py -q
```

六、建议与后续改进

- 将对 `auth_router` 顶层常量的读取改为运行时读取（从 env 或设置对象），以便测试更容易通过环境变量控制，而不是在模块导入后才修改。
- 考虑为测试输出生成 JUnit XML 或 HTML 报告（CI 集成），可使用 `--junitxml` 或 `pytest-html` 插件。示例：

```bash
python -m pytest --junitxml=tests/report/junit.xml -q
pip install pytest-html
python -m pytest --html=tests/report/report.html --self-contained-html -q
```
