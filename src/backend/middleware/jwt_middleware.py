import os
import jwt
from fastapi import Request
from starlette.responses import JSONResponse

from module.user.service.auth_service import get_user_by_id

JWT_SECRET = os.getenv("JWT_SECRET", "devsecret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

EXEMPT_PATHS = (
    "/api/user/register",
    "/api/user/login",
    "/api/user/token",
    "/api/user/send-code",
    "/api/user/change-password",
    "/api/tasks/",
    "/uploads",  # 静态文件服务（PDF预览）
    "/docs",
    "/openapi.json",
    "/redoc",
)


class JWTAuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Allow OPTIONS preflight requests to pass through for CORS
        method = scope.get("method", "")
        if method == "OPTIONS":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        # Allow non-API paths (SPA frontend routes) to be served without JWT
        # This lets client-side routes like /register or /me load index.html first
        if not path.startswith("/api"):
            await self.app(scope, receive, send)
            return
        # allow exempt paths
        # also allow root, index and common static asset extensions so the demo static files are accessible
        PUBLIC_EXTS = (".js", ".css", ".html", ".ico", ".png", ".jpg", ".jpeg", ".svg", ".map")
        if path == "/" or path == "/index.html" or path.endswith(PUBLIC_EXTS):
            await self.app(scope, receive, send)
            return
        for p in EXEMPT_PATHS:
            if path.startswith(p):
                await self.app(scope, receive, send)
                return

        headers = dict((k.decode().lower(), v.decode()) for k, v in scope.get("headers", []))
        auth = headers.get("authorization")
        
        # 调试日志
        import sys
        print(f"[JWT Middleware] Path: {path}, Method: {method}", file=sys.stderr)
        print(f"[JWT Middleware] Authorization header present: {auth is not None}", file=sys.stderr)
        if auth:
            print(f"[JWT Middleware] Authorization: {auth[:30]}...", file=sys.stderr)
        
        if not auth:
            res = JSONResponse({"code": 401, "msg": "未认证", "data": None}, status_code=401)
            await res(scope, receive, send)
            return

        # support case-insensitive 'Bearer' scheme and robust splitting
        parts = auth.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            res = JSONResponse({"code": 401, "msg": "未认证", "data": None}, status_code=401)
            await res(scope, receive, send)
            return

        token = parts[1]
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user_id = payload.get("sub")
            if not user_id:
                res = JSONResponse({"code": 401, "msg": "无效的Token", "data": None}, status_code=401)
                await res(scope, receive, send)
                return
            # fetch user and attach to scope state
            user = await get_user_by_id(user_id)
            if not user:
                res = JSONResponse({"code": 404, "msg": "用户不存在", "data": None}, status_code=404)
                await res(scope, receive, send)
                return
            scope.setdefault("state", {})
            scope["state"]["user"] = user
        except jwt.ExpiredSignatureError:
            res = JSONResponse({"code": 401, "msg": "Token已过期", "data": None}, status_code=401)
            await res(scope, receive, send)
            return
        except jwt.InvalidTokenError:
            res = JSONResponse({"code": 401, "msg": "无效的Token", "data": None}, status_code=401)
            await res(scope, receive, send)
            return

        await self.app(scope, receive, send)
