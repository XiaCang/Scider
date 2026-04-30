# User 模块 API 文档

以下为目前已实现并可用于测试的 API：

## 1) 发送邮件验证码

- 方法：POST
- 路径：`/api/user/send-code`
- 请求头：`Content-Type: application/json`
- 请求体示例：

```json
{ "email": "alice@example.com" }
```
- 成功响应（HTTP 200）：

```json
{ "code": 0, "msg": "验证码已生成并存储", "data": { "email": "alice@example.com", "sent": true } }
```

说明：如果 SMTP 未配置，`sent` 可能为 `false`，但验证码仍会写入 Redis（5 分钟过期）。

## 2) 注册（含验证码）

- 方法：POST
- 路径：`/api/user/register`
- 请求头：`Content-Type: application/json`
- 请求体示例：

```json
{
  "email": "alice@example.com",
  "password": "secret123",
  "name": "Alice",
  "code": "123456"
}
```
- 成功响应（HTTP 200）：

```json
{
  "code": 0,
  "msg": "注册成功",
  "data": { "userId": "<uuid>", "username": "Alice", "email": "alice@example.com" }
}
```

失败示例（验证码错误或已过期，HTTP 200 但 body.code=400）：

```json
{ "code": 400, "msg": "验证码错误或已过期", "data": null }
```

## 3) 登录（JSON）

- 方法：POST
- 路径：`/api/user/login`
- 请求头：`Content-Type: application/json`
- 请求体示例：

```json
{
  "email": "alice@example.com",
  "password": "secret123"
}
```
- 成功响应（HTTP 200）：

```json
{
  "code": 0,
  "msg": "登录成功",
  "data": {
    "token": "<jwt>",
    "userInfo": { "userId": "<uuid>", "username": "Alice" }
  }
}
```

## 4) Token（用于 Swagger 的 OAuth2 password 流程）

- 方法：POST
- 路径：`/api/user/token`
- 请求体：`application/x-www-form-urlencoded`（`username`, `password`）
- 成功响应同登录。

示例 curl（表单）：

```bash
curl -X POST -d "username=alice@example.com&password=secret123" http://127.0.0.1:8000/api/user/token
```

## 5) 获取当前用户（需认证）

- 方法：GET
- 路径：`/api/user/me`
- 授权：在请求头加入 `Authorization: Bearer <token>`
- 成功响应（HTTP 200）：

```json
{ "code": 0, "msg": "查询成功", "data": { "user": { "id": "<uuid>", "email": "alice@example.com", "name": "Alice" } } }
```

## 6) 修改当前用户名称（需认证）

- 方法：PATCH
- 路径：`/api/user/me`
- 授权：`Authorization: Bearer <token>`
- 请求头：`Content-Type: application/json`
- 请求体示例：

```json
{ "name": "Alice New" }
```
- 成功响应（HTTP 200）：

```json
{ "code": 0, "msg": "更新成功", "data": { "user": { "id": "<uuid>", "email": "alice@example.com", "name": "Alice New" } } }
```

## 认证说明

- 项目使用 JWT 做认证，生成 Token 的签名与过期时间由环境变量控制：
  - `JWT_SECRET`（签名密钥）
  - `JWT_ALGORITHM`（例如 `HS256`）
  - `JWT_EXPIRE_MINUTES`（过期分钟数）
- 中间件会校验所有非放行路径（EXEMPT_PATHS）并把用户信息注入 `Request.state.user`，路由通过读取 `request.state.user` 获取当前用户。

## 错误码（常见）

- 400: 请求参数错误（例如邮箱格式不对 / 密码过短 / 邮箱已注册）
- 401: 未认证或 Token 无效
- 404: 用户不存在（例如 Token 中的 sub 对应用户在数据库中已被删除）

## 前端 demo

- 访问根路径 `/` 即可打开 `src/frontend/auth_demo/index.html`，演示：注册、登录、获取/修改用户信息。

## 调试与验证建议

- 使用 `curl` 或 Swagger (`/docs`) 调试接口。
- 若无法通过前端访问，请在浏览器开发者工具查看请求头中是否带上 `Authorization`。
