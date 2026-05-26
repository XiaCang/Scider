import json
import asyncio

import pytest
from fastapi.testclient import TestClient

from app.main import app


# 自动把 DB 依赖替换为轻量假 session，避免需要真实 DATABASE_URL
@pytest.fixture(autouse=True)
def patch_get_db(monkeypatch):
    async def fake_get_db():
        class DummySession:
            pass

        yield DummySession()

    monkeypatch.setattr("db.session.get_db", fake_get_db)
    # Ensure middleware's imported reference delegates to the auth_service function
    import module.user.service.auth_service as auth_service

    async def delegate_get_user_by_id(uid):
        return await auth_service.get_user_by_id(uid)

    monkeypatch.setattr("middleware.jwt_middleware.get_user_by_id", delegate_get_user_by_id)


class AsyncFakeRedis:
    def __init__(self):
        self._store = {}

    async def set(self, key, value, ex=None):
        # store bytes to mimic real aioredis behaviour
        self._store[key] = str(value).encode()

    async def get(self, key):
        return self._store.get(key)

    async def delete(self, key):
        self._store.pop(key, None)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.mark.asyncio
async def test_send_code_and_change_password(monkeypatch, client):
    # patch redis to avoid external dependency
    fake_redis = AsyncFakeRedis()

    def fake_get_redis():
        return fake_redis

    # auth_router imported get_redis at module import time, patch that name so the route uses our fake
    monkeypatch.setattr("module.user.controller.auth_router.get_redis", lambda: fake_redis)

    # patch email task enqueue (optional) to prevent side effects
    monkeypatch.setattr("module.user.controller.auth_router.send_verification_email", lambda *a, **k: None, raising=False)

    # call send-code
    resp = client.post(
        "/api/user/send-code",
        json={"email": "test@example.com"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("code") == 0
    assert body["data"]["email"] == "test@example.com"

    # ensure redis has stored the code
    stored = await fake_redis.get("verify:test@example.com")
    assert stored is not None

    # patch change_user_password to simulate DB update
    async def fake_change_user_password(email, new_password):
        return {"id": "u1", "email": email}

    monkeypatch.setattr("module.user.controller.auth_router.change_user_password", fake_change_user_password, raising=False)
    # The real change_password imports change_user_password inside function, so patch the service
    monkeypatch.setattr("module.user.service.auth_service.change_user_password", fake_change_user_password)

    # use the stored code for change-password
    code = stored.decode()

    resp2 = client.post(
        "/api/user/change-password",
        json={"email": "test@example.com", "code": code, "new_password": "newpass123"},
    )
    assert resp2.status_code == 200
    b2 = resp2.json()
    assert b2.get("code") == 0
    assert b2["data"]["email"] == "test@example.com"


def test_refresh_endpoint_absent(client):
    # 缺少刷新接口：中间件可能返回 401（未认证）或路由不存在 404/405
    resp = client.post("/api/user/refresh")
    assert resp.status_code in (401, 404, 405)


def _row(paper_id, title="T", year=2020, authors="A", key_points=None, embedding=None, status="CONFIRMED"):
    return {
        "paper_id": paper_id,
        "title": title,
        "authors": authors,
        "year": year,
        "key_points": key_points or {},
        "embedding": embedding,
        "status": status,
    }


def test_graph_similarity_no_embeddings(monkeypatch, client):
    # patch user lookup in middleware to simulate authenticated user
    async def fake_get_user_by_id(uid):
        return {"id": uid, "email": "u@example.com", "name": "u"}

    monkeypatch.setattr("module.user.service.auth_service.get_user_by_id", fake_get_user_by_id)

    async def fake_list(session, user_id, folder_id=None, max_nodes=200):
        return []

    # patch both the module and the name imported into the route
    monkeypatch.setattr("db.crud_graph.list_papers_with_embeddings", fake_list)
    monkeypatch.setattr("app.api.routes.graph.list_papers_with_embeddings", fake_list)

    # create a valid token payload with 'sub' and encode using same secret
    import jwt, os
    token = jwt.encode({"sub": "u1", "email": "u@example.com"}, os.getenv("JWT_SECRET", "devsecret"), algorithm=os.getenv("JWT_ALGORITHM", "HS256"))

    resp = client.get("/api/graph/similarity", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("code") == 0
    data = body.get("data")
    assert data["nodes"] == []
    assert data["meta"]["reason"] == "no_embeddings"


def test_graph_similarity_single_and_multi(monkeypatch, client):
    # patch user lookup
    async def fake_get_user_by_id(uid):
        return {"id": uid, "email": "u@example.com", "name": "u"}

    monkeypatch.setattr("module.user.service.auth_service.get_user_by_id", fake_get_user_by_id)

    # single row
    async def list_single(session, user_id, folder_id=None, max_nodes=200):
        return [
            _row("p1", title="A Long Paper Title That Exceeds Twenty Four Chars", embedding=[0.1, 0.2], key_points={"background": "b"}),
        ]

    monkeypatch.setattr("db.crud_graph.list_papers_with_embeddings", list_single)
    monkeypatch.setattr("app.api.routes.graph.list_papers_with_embeddings", list_single)

    import jwt, os
    token = jwt.encode({"sub": "u1", "email": "u@example.com"}, os.getenv("JWT_SECRET", "devsecret"), algorithm=os.getenv("JWT_ALGORITHM", "HS256"))

    resp = client.get("/api/graph/similarity", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("code") == 0
    data = body.get("data")
    assert len(data["nodes"]) == 1
    assert data["meta"]["reason"] == "need_two_or_more_for_similarity_edges"

    # multiple rows
    async def list_multi(session, user_id, folder_id=None, max_nodes=200):
        return [
            _row("p1", embedding=[0.1, 0.2], key_points={"background": "b"}),
            _row("p2", embedding=[0.11, 0.19], key_points={"background": "c"}),
        ]

    monkeypatch.setattr("db.crud_graph.list_papers_with_embeddings", list_multi)
    monkeypatch.setattr("app.api.routes.graph.list_papers_with_embeddings", list_multi)

    # patch similarity builder to return an edge pair
    def fake_build_edges(ids, embeddings, min_similarity=0.55, top_k_per_node=8):
        return [("p1", "p2", 0.88)]

    monkeypatch.setattr("app.core.graph_similarity.build_similarity_edges", fake_build_edges)
    monkeypatch.setattr("app.api.routes.graph.build_similarity_edges", fake_build_edges)

    resp2 = client.get("/api/graph/similarity", headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 200
    b2 = resp2.json()
    assert b2.get("code") == 0
    d2 = b2.get("data")
    assert len(d2["nodes"]) == 2
    assert len(d2["links"]) == 1
    assert "相似度" in d2["links"][0]["label"]
