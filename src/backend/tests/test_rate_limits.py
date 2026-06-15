import os
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


class FakeRedis:
    def __init__(self):
        self.store = {}

    async def incr(self, key):
        v = self.store.get(key)
        if v is None:
            v = 1
        else:
            v = int(v) + 1
        self.store[key] = v
        return v

    async def expire(self, key, period):
        # expiry is best-effort for tests
        return True

    async def set(self, key, value, ex=None):
        # store as string
        self.store[key] = value if isinstance(value, bytes) else str(value)

    async def get(self, key):
        v = self.store.get(key)
        if v is None:
            return None
        if isinstance(v, bytes):
            return v
        return str(v).encode()

    async def delete(self, key):
        self.store.pop(key, None)


@pytest.mark.asyncio
async def test_incr_and_check_unit():
    from utils.rate_limit import incr_and_check

    r = FakeRedis()
    limited, count = await incr_and_check(r, "test:key", 2, 60)
    assert limited is False and count == 1
    limited, count = await incr_and_check(r, "test:key", 2, 60)
    assert limited is False and count == 2
    limited, count = await incr_and_check(r, "test:key", 2, 60)
    assert limited is True and count == 3


@pytest.mark.asyncio
async def test_send_code_rate_limit(monkeypatch):
    fake = FakeRedis()
    # make the verify limit small for test
    monkeypatch.setenv("VERIFY_EMAIL_LIMIT", "2")
    monkeypatch.setenv("VERIFY_EMAIL_PERIOD", "3600")

    import utils.redis_client as rc
    # also patch the auth_router binding if already imported
    try:
        import module.user.controller.auth_router as auth_router
        monkeypatch.setattr(auth_router, "get_redis", lambda: fake)
    except Exception:
        pass
    monkeypatch.setattr(rc, "get_redis", lambda: fake)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        for _ in range(2):
            resp = await ac.post("/api/user/send-code", json={"email": "a@example.com"})
            assert resp.status_code == 200
            assert resp.json()["code"] == 0

        # third attempt should be limited
        resp = await ac.post("/api/user/send-code", json={"email": "a@example.com"})
        assert resp.status_code == 200
        assert resp.json()["code"] == 429


@pytest.mark.asyncio
async def test_login_rate_limit(monkeypatch):
    fake = FakeRedis()
    monkeypatch.setenv("LOGIN_EMAIL_LIMIT", "2")
    monkeypatch.setenv("LOGIN_EMAIL_PERIOD", "3600")

    import utils.redis_client as rc
    # ensure auth_router uses our fake redis binding and test limits
    import module.user.controller.auth_router as auth_router
    monkeypatch.setattr(auth_router, "get_redis", lambda: fake)
    monkeypatch.setattr(rc, "get_redis", lambda: fake)
    # auth_router reads EMAIL_LIMIT/IP_LIMIT at import time — override them directly
    monkeypatch.setattr(auth_router, "EMAIL_LIMIT", 2)
    monkeypatch.setattr(auth_router, "EMAIL_PERIOD", 3600)
    monkeypatch.setattr(auth_router, "IP_LIMIT", 100)
    monkeypatch.setattr(auth_router, "IP_PERIOD", 3600)

    # simulate failed authentication to exercise failed-login rate limit
    async def fake_auth_fail(email, password):
        raise ValueError("invalid credentials")

    monkeypatch.setattr(auth_router, "authenticate_user", fake_auth_fail)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # first two attempts should return credential error (code 401)
        for _ in range(2):
            resp = await ac.post("/api/user/login", json={"email": "b@example.com", "password": "pwd"})
            assert resp.status_code == 200
            assert resp.json()["code"] == 401

        # third attempt should be rate-limited (code 429)
        resp = await ac.post("/api/user/login", json={"email": "b@example.com", "password": "pwd"})
        assert resp.status_code == 200
        assert resp.json()["code"] == 429
