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


## POST 头像上传

POST /api/user/avatar

- 主要行为：
  - 服务端保存到 `UPLOAD_DIR/avatars/` 下（文件名按 md5 +user_id+ ext 形式去重/保存）；
  - 更新 `User.avatar_path` / `User.avatar_url` 字段；
  - 若已有旧头像会尝试删除旧文件（若与新文件不同）。

> Body 请求参数

```yaml
file: cmMtdXBsb2FkLTE3Nzk2OTIwMzYwODQtMg==/屏幕截图 2026-05-09 143335.png

```

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|Authorization|header|string| 否 |none|
|body|body|object| 是 |none|
|» file|body|string(binary)| 否 |要上传的头像文件（支持后缀 `.png`, `.jpg`, `.jpeg`, `.webp`，大小受 `MAX_UPLOAD_SIZE_MB` 限制）|

> 返回示例

> 200 Response

```json
{
  "code": 0,
  "msg": "上传成功",
  "data": {
    "avatarUrl": "/uploads/avatars/abc123def.png"
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||none|
|» msg|string|true|none||none|
|» data|object|true|none||none|
|»» avatarUrl|string|true|none||none|

## GET 头像url获取

GET /api/user/avatar

返回当前登录用户的 `avatarUrl`（如果无头像，返回空或 `null`）

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|Authorization|header|string| 否 |none|

> 返回示例

> 200 Response

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "avatarUrl": "/uploads/avatars/abc123def.png"
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||none|
|» msg|string|true|none||none|
|» data|object|true|none||none|
|»» avatarUrl|string|true|none||none|

## DELETE 头像删除

DELETE /api/user/avatar

- 方法：DELETE
- 路径：`/api/user/avatar`
- 权限：登录用户（只能删除自己的头像）
- 描述：删除用户头像文件并清空 DB 中的 `avatar_path` / `avatar_url`。

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|Authorization|header|string| 否 |none|

> 返回示例

> 200 Response

```json
{
  "code": 0,
  "msg": "删除成功",
  "data": null
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||none|
|» msg|string|true|none||none|
|» data|null|true|none||none|

## POST apikey添加

POST /api/user/llm-providers

- 方法：POST
- 路径：`/api/user/llm-providers`
- 权限：登录用户
- Body（JSON）：

> Body 请求参数

```json
{
  "name": "OpenAI",
  "provider": "openai",
  "base_url": "https://.openai.com",
  "api_key": "sk-xxdddfx",
  "default_model": "gpt-5",
  "enabled": true
}
```

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|Authorization|header|string| 否 |none|
|body|body|object| 是 |none|
|» name|body|string| 是 |none|
|» provider|body|string| 是 |none|
|» base_url|body|string| 是 |none|
|» api_key|body|string| 是 |存加密后的apikey|
|» default_model|body|string| 是 |none|
|» enabled|body|boolean| 是 |none|

> 返回示例

> 200 Response

```json
{
  "code": 0,
  "msg": "created",
  "data": {
    "id": 2,
    "name": "OpenAI",
    "api_key_masked": "sk_****xxx",
    "default_model": "gpt-4",
    "enabled": true
  }
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||none|
|» msg|string|true|none||none|
|» data|object|true|none||none|
|»» id|integer|true|none||none|
|»» name|string|true|none||none|
|»» api_key_masked|string|true|none||none|
|»» default_model|string|true|none||none|
|»» enabled|boolean|true|none||none|

## GET 全部apikey获取

GET /api/user/llm-providers

权限：当前登录用户
列出当前用户所持有的所有apikey

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|Authorization|header|string| 否 |none|

> 返回示例

```json
{
  "code": 0,
  "msg": "ok",
  "data": [
    {
      "id": 1,
      "name": "OpenAI",
      "provider": "openai",
      "base_url": "https://api.openai.com",
      "api_key_masked": "sk_****abcd",
      "default_model": "gpt-4",
      "enabled": true,
      "user_id": null,
      "created_at": "2026-05-01T12:00:00Z"
    }
  ]
}
```

```json
{
    "code": 0,
    "msg": "查询成功",
    "data": [
        {
            "id": "53440878ff9d495f841b74e56eba13a1",
            "name": "OpenAI",
            "provider": "openai",
            "base_url": "https://.openai.com",
            "default_model": "gpt-5",
            "enabled": true,
            "api_key_masked": "******ddfx",
            "user_id": "08c5449bd77d42adb03b3d0bc302cbf1"
        },
        {
            "id": "bef918035d5f4f9fb49116f0d766b9a0",
            "name": "OpenAI",
            "provider": "openai",
            "base_url": "https://api.openai.com",
            "default_model": "gpt-4",
            "enabled": true,
            "api_key_masked": "**-xxx",
            "user_id": "08c5449bd77d42adb03b3d0bc302cbf1"
        }
    ]
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||none|
|» msg|string|true|none||none|
|» data|[object]|true|none||none|
|»» id|integer|false|none||none|
|»» name|string|false|none||none|
|»» provider|string|false|none||none|
|»» base_url|string|false|none||none|
|»» api_key_masked|string|false|none||none|
|»» default_model|string|false|none||none|
|»» enabled|boolean|false|none||none|
|»» user_id|null|false|none||none|
|»» created_at|string|false|none||none|

## PATCH apikey更新

PATCH /api/user/llm-providers/{id}

- 方法：PATCH
- 路径：`/api/user/llm-providers/{id}`
- 权限：登录用户（只能更新自己创建或有权限的 Provider）

这里apikey更新包括1.更新内容 2.更新唯一选中启用的apikey，一个key的enabled被设为true的话，自动将该用户其他key的enabled设为false

> Body 请求参数

```json
{
  "name": "OpenAI Updated-old22222",
  "base_url": "https://api.openai.com/v2",
  "api_key": "sk-new",
  "enabled": false
}
```

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|id|path|string| 是 |none|
|Authorization|header|string| 否 |none|
|body|body|object| 是 |none|
|» name|body|string| 是 |none|
|» base_url|body|string| 是 |none|
|» api_key|body|string| 是 |none|
|» enabled|body|boolean| 是 |更新唯一选中启用的apikey，一个key的enabled被设为true的话，自动将该用户其他key的enabled设为false|

> 返回示例

```json
{
  "code": 0,
  "msg": "更新成功",
  "data": {
    "id": "53440878ff9d495f841b74e56eba13a1"
  }
}
```

```json
{
    "code": 403,
    "msg": "无权限修改该 provider",
    "data": null
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||none|
|» msg|string|true|none||none|
|» data|object|true|none||none|
|»» id|string|true|none||none|

## DELETE apikey删除

DELETE /api/user/llm-providers/{id}

- 方法：DELETE
- 路径：`/api/user/llm-providers/{id}`
- 权限：登录用户（只能删除自己有权限的 Provider）

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|id|path|string| 是 |这里的id指的是apikey的id|
|Authorization|header|string| 否 |none|

> 返回示例

```json
{
  "code": 0,
  "msg": "deleted",
  "data": null
}
```

```json
{
    "code": 403,
    "msg": "无权限删除该 provider",
    "data": null
}
```

### 返回结果

|状态码|状态码含义|说明|数据模型|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|none|Inline|

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||none|
|» msg|string|true|none||none|
|» data|null|true|none||none|

# 数据模型
