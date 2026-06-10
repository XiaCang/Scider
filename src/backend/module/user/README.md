# User 模块说明

该目录包含用户模块的路由（controller）、业务（service）以及用于本地测试的简易前端页面。目的是提供：

- 注册接口（邮箱校验、bcrypt 密码加密）
- 注册接口（邮箱校验、bcrypt 密码加密） — 新增: 注册前需获取邮件验证码，注册请求体包含 `code` 字段
- 登录接口（签发 JWT）
- 全局 JWT ASGI 中间件（除注册/登录/Token/文档外所有接口需带 Token）
- 获取/修改当前用户信息接口（通过中间件将 user 注入到 `Request.state.user`）
- 简易前端演示页面（用于功能验证）

## 文件位置

- 路由（controller）： `src/backend/module/user/controller/` 
- 业务（service）： `src/backend/module/user/service/auth_service.py`
- 中间件： `src/backend/middleware/jwt_middleware.py`
- 前端 demo： `src/frontend/auth_demo/`（`index.html`、`app.js`、`style.css`）

（注意：仓库中可能存在 `src/db` 与 `src/backend/db` 两个副本，请以项目配置的 `DATABASE_URL` 与导入路径为准。）

## 启动前准备（Windows / PowerShell 示例）

1. 创建并激活虚拟环境（可选，但推荐）

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. 安装依赖

在仓库根或合适位置运行：

```powershell
pip install -r requirements.txt
# 如果仓库把依赖拆分在 src/db，请也检查并安装：
pip install -r src/db/requirements.txt
```

若没有统一的 `requirements.txt`，至少安装下面常用包：

```powershell
pip install fastapi uvicorn "SQLAlchemy>=1.4" asyncmy aiomysql alembic passlib[bcrypt] PyJWT python-multipart
```

此外，邮件验证码使用 Redis 存储，建议安装 redis 客户端：

```powershell
pip install redis
```

3. 配置环境变量（示例）

```powershell
$env:DATABASE_URL = "mysql+asyncmy://user:password@127.0.0.1:3306/dbname"
$env:JWT_SECRET = "your_jwt_secret"
$env:JWT_ALGORITHM = "HS256"
$env:JWT_EXPIRE_MINUTES = "60"

```
配置 SMTP 环境变量 `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS` 







## 验证码工作流说明

- 请求发送验证码：POST `/api/user/send-code`，Body: `{ "email": "..." }`，服务将生成 6 位验证码并写入 Redis（键 `verify:{email}`，过期 300 秒）。
- 注册时提交验证码：在 POST `/api/user/register` 的请求体中加入 `code` 字段，服务会从 Redis 校验并删除已使用的验证码。

