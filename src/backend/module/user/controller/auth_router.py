from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr


from module.user.service.auth_service import (
    register_user,
    authenticate_user,
)
from utils.response import success, error
from utils.redis_client import get_redis
from utils.rate_limit import incr_and_check
import random
import os
import logging

logger = logging.getLogger(__name__)


router = APIRouter()

# rate limit defaults (can be overridden via env)
EMAIL_LIMIT = int(os.getenv("LOGIN_EMAIL_LIMIT", "5"))
EMAIL_PERIOD = int(os.getenv("LOGIN_EMAIL_PERIOD", "900"))  # seconds (15m)
IP_LIMIT = int(os.getenv("LOGIN_IP_LIMIT", "10"))
IP_PERIOD = int(os.getenv("LOGIN_IP_PERIOD", "3600"))  # seconds (1h)


class RegisterIn(BaseModel):
    email: EmailStr
    password: str
    name: str | None = None
    code: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class SendCodeIn(BaseModel):
    email: EmailStr


class ChangePasswordIn(BaseModel):
    email: EmailStr
    code: str
    new_password: str



@router.post("/api/user/register")
async def register(payload: RegisterIn):
    try:
        # verify code from redis
        r = get_redis()
        key = f"verify:{payload.email}"
        stored = await r.get(key)
        if not stored or stored.decode() != payload.code:
            return error(msg="验证码错误或已过期", code=400, data=None, status_code=200)
        # delete used code
        await r.delete(key)

        user = await register_user(payload.email, payload.password, payload.name)
        # return flattened response structure: userId, username, email
        data = {"userId": user.get("id"), "username": user.get("name"), "email": user.get("email")}
        return success(data=data, msg="注册成功", code=0, status_code=200)
    except ValueError as e:
        return error(msg=str(e), code=400, data=None, status_code=200)
    except Exception as e:
        logger.exception("register failed")
        return error(msg=f"服务器内部错误: {str(e)}", code=500, data=None, status_code=500)


@router.post("/api/user/login")
async def login(payload: LoginIn, request: Request):
    try:
        # rate limit checks (per-account and per-IP)
        r = get_redis()
        ip = request.headers.get("x-forwarded-for") or (request.client.host if request.client else "unknown")
        if isinstance(ip, str) and "," in ip:
            ip = ip.split(",")[0].strip()
        limited = False
        try:
            limited_email, _ = await incr_and_check(r, f"rl:login:email:{payload.email}", EMAIL_LIMIT, EMAIL_PERIOD)
            limited_ip, _ = await incr_and_check(r, f"rl:login:ip:{ip}", IP_LIMIT, IP_PERIOD)
            limited = limited_email or limited_ip
        except Exception:
            logger.exception("rate limit check failed")

        if limited:
            return error(msg="操作过于频繁，请稍后再试", code=429, data=None, status_code=200)

        token, user = await authenticate_user(payload.email, payload.password)
        # on successful login, clear account-specific counter
        try:
            await r.delete(f"rl:login:email:{payload.email}")
        except Exception:
            logger.exception("failed to clear login rate limit key")
        data = {"token": token, "userInfo": {"userId": user.get("id"), "username": user.get("name")}}
        return success(data=data, msg="登录成功", code=0)
    except ValueError:
        return error(msg="邮箱或密码错误", code=401, data=None, status_code=200)


@router.post("/api/user/token")
async def token(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        # rate limit checks for token endpoint (OAuth2 password)
        r = get_redis()
        email = form_data.username
        ip = request.headers.get("x-forwarded-for") or (request.client.host if request.client else "unknown")
        if isinstance(ip, str) and "," in ip:
            ip = ip.split(",")[0].strip()
        limited = False
        try:
            limited_email, _ = await incr_and_check(r, f"rl:login:email:{email}", EMAIL_LIMIT, EMAIL_PERIOD)
            limited_ip, _ = await incr_and_check(r, f"rl:login:ip:{ip}", IP_LIMIT, IP_PERIOD)
            limited = limited_email or limited_ip
        except Exception:
            logger.exception("rate limit check failed")

        if limited:
            return error(msg="操作过于频繁，请稍后再试", code=429, data=None, status_code=200)

        token, user = await authenticate_user(form_data.username, form_data.password)
        try:
            await r.delete(f"rl:login:email:{email}")
        except Exception:
            logger.exception("failed to clear login rate limit key")
        data = {"token": token, "userInfo": {"userId": user.get("id"), "username": user.get("name")}}
        return success(data=data, msg="登录成功", code=0)
    except ValueError:
        return error(msg="邮箱或密码错误", code=401, data=None, status_code=200)
    


@router.post("/api/user/send-code")
async def send_code(payload: SendCodeIn, request: Request):
    # rate limit for sending verification codes (per-email and per-IP)
    r = get_redis()
    ip = request.headers.get("x-forwarded-for") or (request.client.host if request.client else "unknown")
    if isinstance(ip, str) and "," in ip:
        ip = ip.split(",")[0].strip()
    EMAIL_VERIFY_LIMIT = int(os.getenv("VERIFY_EMAIL_LIMIT", "5"))
    EMAIL_VERIFY_PERIOD = int(os.getenv("VERIFY_EMAIL_PERIOD", "3600"))
    IP_VERIFY_LIMIT = int(os.getenv("VERIFY_IP_LIMIT", "10"))
    IP_VERIFY_PERIOD = int(os.getenv("VERIFY_IP_PERIOD", "3600"))
    try:
        limited_email, _ = await incr_and_check(r, f"rl:verify:email:{payload.email}", EMAIL_VERIFY_LIMIT, EMAIL_VERIFY_PERIOD)
        limited_ip, _ = await incr_and_check(r, f"rl:verify:ip:{ip}", IP_VERIFY_LIMIT, IP_VERIFY_PERIOD)
        if limited_email or limited_ip:
            return error(msg="发送验证码操作过于频繁，请稍后再试", code=429, data=None, status_code=200)
    except Exception:
        logger.exception("verify rate limit check failed")

    # generate 6-digit code and store in redis with 5-minute expiry
    code = str(random.randint(0, 999999)).zfill(6)
    key = f"verify:{payload.email}"
    try:
        await r.set(key, code, ex=300)
    except Exception as e:
        logger.exception("failed to set verification code in redis")
        return error(msg=f"内部服务错误: {str(e)}", code=500, data=None, status_code=500)

    # enqueue email sending as a Celery task if SMTP configured
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "0")) if os.getenv("SMTP_PORT") else None
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    subject = "Your verification code"
    body = f"Your verification code is: {code}. It is valid for 5 minutes."

    sent = False
    if smtp_host and smtp_port and smtp_user and smtp_pass:
        try:
            # lazy import to avoid circular import during app startup
            from app.tasks.email_tasks import send_verification_email
            # fire-and-forget: enqueue task to worker
            send_verification_email.delay(payload.email, subject, body)
            sent = True
        except Exception:
            logger.exception("enqueue send_verification_email failed")

    # do not expose code in production; but return success and indicate whether email was sent
    return success(data={"email": payload.email, "sent": sent}, msg="验证码已生成并存储", code=0)


@router.post("/api/user/change-password")
async def change_password(payload: ChangePasswordIn):
    try:
        # verify code from redis
        r = get_redis()
        key = f"verify:{payload.email}"
        try:
            stored = await r.get(key)
        except Exception:
            logger.exception("failed to get verification code from redis")
            return error(msg="内部服务错误: 无法连接到 Redis", code=500, data=None, status_code=500)

        if not stored or stored.decode() != payload.code:
            return error(msg="验证码错误或已过期", code=400, data=None, status_code=200)
        # delete used code
        try:
            await r.delete(key)
        except Exception:
            logger.exception("failed to delete verification code from redis")
            # proceed — deletion failure is non-fatal for the password change flow

        # perform password change via service
        from module.user.service.auth_service import change_user_password

        updated = await change_user_password(payload.email, payload.new_password)
        if not updated:
            return error(msg="用户不存在", code=404, data=None, status_code=200)
        return success(data={"userId": updated.get("id"), "email": updated.get("email")}, msg="密码已更新", code=0)
    except ValueError as e:
        return error(msg=str(e), code=400, data=None, status_code=200)
    except Exception as e:
        logger.exception("change_password failed")
        return error(msg=f"服务器内部错误: {str(e)}", code=500, data=None, status_code=500)

