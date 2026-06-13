"""
用户数据隔离与越权测试

测试目标：
  1. 用户 A 无法访问用户 B 的 PDF、笔记、图谱数据（水平越权）
  2. JWT 篡改检测（修改 token 中的 user_id）
  3. 未授权端点访问（垂直越权）
  4. 文件夹、论文、笔记的跨用户隔离

前置条件：
  - 后端运行在 http://localhost:8000
  - 至少创建两个测试用户（TEST_USER_A_EMAIL/PASSWORD 和 TEST_USER_B_EMAIL/PASSWORD）
  - 数据库包含真实数据或测试数据

运行方式：
  pytest tests/test_auth_isolation.py -v
"""

import os
import json
import jwt as pyjwt
import pytest
from fastapi.testclient import TestClient

from app.main import app

# 测试配置
BASE_URL = "http://localhost:8000"
JWT_SECRET = os.getenv("JWT_SECRET", "devsecret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

USER_A = {
    "email": os.getenv("TEST_USER_A_EMAIL", "usera@test.com"),
    "password": os.getenv("TEST_USER_A_PASSWORD", "passworda"),
    "name": "User A"
}

USER_B = {
    "email": os.getenv("TEST_USER_B_EMAIL", "userb@test.com"),
    "password": os.getenv("TEST_USER_B_PASSWORD", "passwordb"),
    "name": "User B"
}


@pytest.fixture(scope="module")
def client():
    """FastAPI 测试客户端"""
    return TestClient(app)


@pytest.fixture(scope="module")
def user_a_token(client):
    """获取用户 A 的认证 token"""
    try:
        resp = client.post("/api/user/login", json=USER_A)
        if resp.status_code != 200:
            pytest.skip(f"无法登录用户 A: {resp.text}")
        data = resp.json()
        if data.get("code") != 0:
            pytest.skip(f"用户 A 登录失败: {data.get('msg')}")
        return data["data"]["token"]
    except Exception:
        pytest.skip("登录请求异常（可能数据库未就绪）")


@pytest.fixture(scope="module")
def user_b_token(client):
    """获取用户 B 的认证 token"""
    try:
        resp = client.post("/api/user/login", json=USER_B)
        if resp.status_code != 200:
            pytest.skip(f"无法登录用户 B: {resp.text}")
        data = resp.json()
        if data.get("code") != 0:
            pytest.skip(f"用户 B 登录失败: {data.get('msg')}")
        return data["data"]["token"]
    except Exception:
        pytest.skip("登录请求异常（可能数据库未就绪）")


@pytest.fixture(scope="module")
def user_a_id(user_a_token):
    """从 token 中提取用户 A 的 ID"""
    payload = pyjwt.decode(user_a_token, options={"verify_signature": False})
    return payload.get("sub")


@pytest.fixture(scope="module")
def user_b_id(user_b_token):
    """从 token 中提取用户 B 的 ID"""
    payload = pyjwt.decode(user_b_token, options={"verify_signature": False})
    return payload.get("sub")


# ========== 测试用例 ==========

def test_user_isolation_papers_list(client, user_a_token, user_b_token):
    """测试：用户 A 和用户 B 的论文列表互不可见"""
    resp_a = client.get("/api/papers/", headers={"Authorization": f"Bearer {user_a_token}"})
    resp_b = client.get("/api/papers/", headers={"Authorization": f"Bearer {user_b_token}"})

    assert resp_a.status_code == 200
    assert resp_b.status_code == 200

    papers_a = resp_a.json()["data"]
    papers_b = resp_b.json()["data"]

    # 提取论文 ID
    ids_a = {p["id"] for p in papers_a}
    ids_b = {p["id"] for p in papers_b}

    # 确保两个用户的论文 ID 集合无交集
    assert ids_a.isdisjoint(ids_b), "用户 A 和用户 B 的论文列表存在重叠"


def test_horizontal_privilege_escalation_paper_detail(client, user_a_token, user_b_token):
    """测试：用户 A 无法访问用户 B 的论文详情（水平越权）"""
    # 获取用户 B 的第一篇论文 ID
    resp_b = client.get("/api/papers/", headers={"Authorization": f"Bearer {user_b_token}"})
    papers_b = resp_b.json()["data"]

    if not papers_b:
        pytest.skip("用户 B 没有论文数据")

    paper_b_id = papers_b[0]["id"]

    # 用户 A 尝试访问用户 B 的论文
    resp = client.get(f"/api/papers/{paper_b_id}", headers={"Authorization": f"Bearer {user_a_token}"})

    # 预期返回 403 或 404
    assert resp.status_code in (403, 404), f"用户 A 成功访问了用户 B 的论文 {paper_b_id}"


def test_horizontal_privilege_escalation_paper_pdf(client, user_a_token, user_b_token):
    """测试：用户 A 无法下载用户 B 的 PDF 文件（水平越权）"""
    resp_b = client.get("/api/papers/", headers={"Authorization": f"Bearer {user_b_token}"})
    papers_b = resp_b.json()["data"]

    if not papers_b:
        pytest.skip("用户 B 没有论文数据")

    paper_b_id = papers_b[0]["id"]

    # 用户 A 尝试获取用户 B 的 PDF
    resp = client.get(f"/api/papers/{paper_b_id}/pdf-file", headers={"Authorization": f"Bearer {user_a_token}"})

    assert resp.status_code in (403, 404), f"用户 A 成功下载了用户 B 的 PDF {paper_b_id}"


def test_horizontal_privilege_escalation_notes(client, user_a_token, user_b_token):
    """测试：用户 A 无法访问用户 B 的笔记（水平越权）"""
    resp_b = client.get("/api/papers/", headers={"Authorization": f"Bearer {user_b_token}"})
    papers_b = resp_b.json()["data"]

    if not papers_b:
        pytest.skip("用户 B 没有论文数据")

    paper_b_id = papers_b[0]["id"]

    # 用户 A 尝试获取用户 B 的笔记
    resp = client.get(f"/api/papers/{paper_b_id}/notes", headers={"Authorization": f"Bearer {user_a_token}"})

    # 预期返回空列表或 403/404
    if resp.status_code == 200:
        notes = resp.json()["data"]
        assert notes == [], f"用户 A 看到了用户 B 的笔记"
    else:
        assert resp.status_code in (403, 404)


def test_jwt_tampering_user_id(client, user_a_token, user_b_id):
    """测试：篡改 JWT 中的 user_id 应被拒绝"""
    # 解码用户 A 的 token
    payload = pyjwt.decode(user_a_token, options={"verify_signature": False})

    # 篡改 sub（user_id）为用户 B 的 ID
    payload["sub"] = user_b_id

    # 用错误的密钥重新签名（模拟攻击）
    fake_token = pyjwt.encode(payload, "wrong_secret", algorithm=JWT_ALGORITHM)

    # 尝试使用篡改的 token 访问
    resp = client.get("/api/papers/", headers={"Authorization": f"Bearer {fake_token}"})

    # 预期返回 401（签名验证失败）
    assert resp.status_code == 401, "篡改的 JWT 未被拒绝"


def test_jwt_tampering_correct_secret(client, user_a_token, user_b_id):
    """测试：即使用正确密钥签名，修改 user_id 后的行为"""
    payload = pyjwt.decode(user_a_token, options={"verify_signature": False})
    original_user_id = payload["sub"]

    # 篡改 sub 为用户 B 的 ID，用正确密钥签名
    payload["sub"] = user_b_id
    tampered_token = pyjwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    # 使用篡改后的 token 获取论文列表
    resp = client.get("/api/papers/", headers={"Authorization": f"Bearer {tampered_token}"})

    if resp.status_code != 200:
        pytest.skip("Token 验证失败（可能有额外验证逻辑）")

    papers = resp.json()["data"]

    # 如果成功，应返回用户 B 的论文（不是用户 A 的）
    # 这是一个安全风险提示：JWT 篡改成功但业务逻辑隔离正确
    # 理想情况：token 应包含更多验证信息（如签发时间、设备指纹）
    print(f"⚠️ JWT sub 篡改成功，返回了用户 {user_b_id} 的数据（共 {len(papers)} 篇论文）")


def test_graph_similarity_isolation(client, user_a_token, user_b_token):
    """测试：知识图谱数据隔离"""
    resp_a = client.get("/api/graph/similarity", headers={"Authorization": f"Bearer {user_a_token}"})
    resp_b = client.get("/api/graph/similarity", headers={"Authorization": f"Bearer {user_b_token}"})

    assert resp_a.status_code == 200
    assert resp_b.status_code == 200

    nodes_a = resp_a.json()["data"]["nodes"]
    nodes_b = resp_b.json()["data"]["nodes"]

    # 提取节点 ID
    ids_a = {n["id"] for n in nodes_a}
    ids_b = {n["id"] for n in nodes_b}

    # 确保图谱节点无交集
    assert ids_a.isdisjoint(ids_b), "用户 A 和用户 B 的知识图谱节点存在重叠"


def test_graph_ask_isolation(client, user_a_token, user_b_token):
    """测试：知识图谱问答隔离（新功能）"""
    # 获取用户 B 的论文 ID
    resp_b = client.get("/api/papers/", headers={"Authorization": f"Bearer {user_b_token}"})
    papers_b = resp_b.json()["data"]

    if not papers_b:
        pytest.skip("用户 B 没有论文数据")

    paper_b_ids = [p["id"] for p in papers_b[:3]]

    # 用户 A 尝试用用户 B 的论文 ID 调用图谱问答
    resp = client.post(
        "/api/graph/ask",
        headers={"Authorization": f"Bearer {user_a_token}"},
        json={"question": "这些论文的主要研究方向是什么？", "paper_ids": paper_b_ids}
    )

    # 预期返回 404（未找到论文）或 403（无权限）
    if resp.status_code == 200:
        data = resp.json()["data"]
        assert data["paper_count"] == 0, "用户 A 成功访问了用户 B 的论文进行图谱问答"
    else:
        assert resp.status_code in (403, 404)


def test_unauthorized_access_without_token(client):
    """测试：无 token 访问受保护端点（垂直越权）"""
    endpoints = [
        ("/api/papers/", "GET"),
        ("/api/graph/similarity", "GET"),
        ("/api/folders/", "GET"),
    ]

    for path, method in endpoints:
        if method == "GET":
            resp = client.get(path)
        else:
            resp = client.post(path, json={})

        assert resp.status_code == 401, f"端点 {method} {path} 未正确拒绝无 token 访问"


def test_expired_token_rejection(client, user_a_id):
    """测试：过期 token 应被拒绝"""
    import time

    # 创建一个已过期的 token（exp 设置为过去时间）
    payload = {
        "sub": user_a_id,
        "email": USER_A["email"],
        "exp": int(time.time()) - 3600  # 1 小时前过期
    }
    expired_token = pyjwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    resp = client.get("/api/papers/", headers={"Authorization": f"Bearer {expired_token}"})

    # 预期返回 401
    assert resp.status_code == 401, "过期的 token 未被拒绝"


def test_folder_isolation(client, user_a_token, user_b_token):
    """测试：文件夹数据隔离"""
    resp_a = client.get("/api/folders/", headers={"Authorization": f"Bearer {user_a_token}"})
    resp_b = client.get("/api/folders/", headers={"Authorization": f"Bearer {user_b_token}"})

    assert resp_a.status_code == 200
    assert resp_b.status_code == 200

    folders_a = resp_a.json()["data"]
    folders_b = resp_b.json()["data"]

    # 提取文件夹 ID
    ids_a = {f["id"] for f in folders_a}
    ids_b = {f["id"] for f in folders_b}

    # 确保文件夹无交集
    assert ids_a.isdisjoint(ids_b), "用户 A 和用户 B 的文件夹存在重叠"


def test_paper_deletion_isolation(client, user_a_token, user_b_token):
    """测试：用户 A 无法删除用户 B 的论文"""
    resp_b = client.get("/api/papers/", headers={"Authorization": f"Bearer {user_b_token}"})
    papers_b = resp_b.json()["data"]

    if not papers_b:
        pytest.skip("用户 B 没有论文数据")

    paper_b_id = papers_b[0]["id"]

    # 用户 A 尝试删除用户 B 的论文
    resp = client.delete(f"/api/papers/{paper_b_id}", headers={"Authorization": f"Bearer {user_a_token}"})

    # 预期返回 403 或 404
    assert resp.status_code in (403, 404), f"用户 A 成功删除了用户 B 的论文 {paper_b_id}"

    # 验证论文仍然存在于用户 B 的列表中
    resp_verify = client.get("/api/papers/", headers={"Authorization": f"Bearer {user_b_token}"})
    papers_b_after = resp_verify.json()["data"]
    assert any(p["id"] == paper_b_id for p in papers_b_after), "论文被意外删除"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
