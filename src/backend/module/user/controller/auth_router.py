from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr


from module.user.service.auth_service import (
    register_user,
    authenticate_user,
)
from utils.response import success, error
from utils.redis_client import get_redis
import random
import os
import smtplib
from email.message import EmailMessage
import logging

logger = logging.getLogger(__name__)


router = APIRouter()


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
async def login(payload: LoginIn):
    try:
        token, user = await authenticate_user(payload.email, payload.password)
        data = {"token": token, "userInfo": {"userId": user.get("id"), "username": user.get("name")}}
        return success(data=data, msg="登录成功", code=0)
    except ValueError:
        return error(msg="邮箱或密码错误", code=401, data=None, status_code=200)


@router.post("/api/user/token")
async def token(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        token, user = await authenticate_user(form_data.username, form_data.password)
        data = {"token": token, "userInfo": {"userId": user.get("id"), "username": user.get("name")}}
        return success(data=data, msg="登录成功", code=0)
    except ValueError:
        return error(msg="邮箱或密码错误", code=401, data=None, status_code=200)
    

@router.post("/api/user/send-code")
async def send_code(payload: SendCodeIn):
    # generate 6-digit code and store in redis with 5-minute expiry
    code = str(random.randint(0, 999999)).zfill(6)
    r = get_redis()
    key = f"verify:{payload.email}"
    await r.set(key, code, ex=300)

    # try send email if SMTP configured
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "0")) if os.getenv("SMTP_PORT") else None
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    subject = "Your verification code"
    body = f"Your verification code is: {code}. It is valid for 5 minutes."

    sent = False
    if smtp_host and smtp_port and smtp_user and smtp_pass:
        try:
            msg = EmailMessage()
            msg['Subject'] = subject
            msg['From'] = smtp_user
            msg['To'] = payload.email
            msg.set_content(body)
            if smtp_port == 465:
                with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
                    server.login(smtp_user, smtp_pass)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(smtp_host, smtp_port) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_pass)
                    server.send_message(msg)
            sent = True
        except Exception:
            logger.exception("send mail failed")

    # do not expose code in production; but return success and indicate whether email was sent
    return success(data={"email": payload.email, "sent": sent}, msg="验证码已生成并存储", code=0)


@router.post("/api/user/change-password")
async def change_password(payload: ChangePasswordIn):
    try:
        # verify code from redis
        r = get_redis()
        key = f"verify:{payload.email}"
        stored = await r.get(key)
        if not stored or stored.decode() != payload.code:
            return error(msg="验证码错误或已过期", code=400, data=None, status_code=200)
        # delete used code
        await r.delete(key)

        # perform password change via service
        from module.user.service.auth_service import change_user_password

        updated = await change_user_password(payload.email, payload.new_password)
        if not updated:
            return error(msg="用户不存在", code=404, data=None, status_code=200)
        return success(data={"userId": updated.get("id"), "email": updated.get("email")}, msg="密码已更新", code=0)
    except ValueError as e:
        return error(msg=str(e), code=400, data=None, status_code=200)

