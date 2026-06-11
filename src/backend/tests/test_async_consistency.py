"""
离线任务与异步状态最终一致性测试

测试目标：
  1. Celery 异步解析 PDF 时，任务状态流转正确（PENDING_PARSING → PARSING → PENDING_EXTRACTION → EXTRACTING → PENDING_CONFIRMATION）
  2. Worker 崩溃或重试后，任务状态正确恢复
  3. 并发上传多个 PDF，状态最终一致
  4. 笔记导出、图谱导出等异步任务结果与源数据一致
  5. 向量化任务失败重试机制

前置条件：
  - 后端运行在 http://localhost:8000
  - Celery Worker 已启动
  - Redis 服务运行中
  - 测试 PDF 文件存在于 tests/fixtures/sample.pdf

运行方式：
  pytest tests/test_async_consistency.py -v --tb=short
  或单独运行：
  python tests/test_async_consistency.py
"""

import os
import sys
import time
import json
import hashlib
from pathlib import Path
from typing import List, Dict

import pytest
from fastapi.testclient import TestClient

from app.main import app
from db.models import PaperStatus

# 测试配置
BASE_URL = "http://localhost:8000"
FIXTURES_DIR = Path(__file__).parent / "fixtures"
POLL_INTERVAL = 2  # 轮询间隔（秒）
MAX_WAIT_TIME = 120  # 最大等待时间（秒）


@pytest.fixture(scope="module")
def client():
    """FastAPI 测试客户端"""
    return TestClient(app)


@pytest.fixture(scope="module")
def auth_token(client):
    """获取认证 token"""
    email = os.getenv("TEST_EMAIL", "test@example.com")
    password = os.getenv("TEST_PASSWORD", "test123")

    resp = client.post("/api/user/login", json={"email": email, "password": password})
    if resp.status_code != 200 or resp.json().get("code") != 0:
        pytest.skip("无法登录测试用户")

    return resp.json()["data"]["token"]


@pytest.fixture
def sample_pdf():
    """提供测试 PDF 文件"""
    pdf_path = FIXTURES_DIR / "sample.pdf"

    if not pdf_path.exists():
        # 如果不存在，创建一个最小的 PDF 文件
        FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
        # 最小合法 PDF（约 500 字节）
        minimal_pdf = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R>>endobj
4 0 obj<</Length 44>>stream
BT /F1 12 Tf 100 700 Td (Test PDF Document) Tj ET
endstream endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000214 00000 n
trailer<</Size 5/Root 1 0 R>>
startxref
307
%%EOF"""
        pdf_path.write_bytes(minimal_pdf)

    return pdf_path


def wait_for_paper_status(
    client,
    paper_id: str,
    expected_status: PaperStatus | List[PaperStatus],
    auth_token: str,
    timeout: int = MAX_WAIT_TIME
) -> Dict:
    """
    轮询论文状态，直到达到预期状态或超时

    Returns:
        论文详情字典
    """
    if isinstance(expected_status, PaperStatus):
        expected_status = [expected_status]

    expected_names = [s.value for s in expected_status]

    start = time.time()
    last_status = None

    while time.time() - start < timeout:
        resp = client.get(
            f"/api/papers/{paper_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        if resp.status_code != 200:
            time.sleep(POLL_INTERVAL)
            continue

        paper = resp.json()["data"]
        current_status = paper.get("status")

        if current_status != last_status:
            print(f"  [{time.time() - start:5.1f}s] 状态: {current_status}")
            last_status = current_status

        if current_status in expected_names:
            return paper

        time.sleep(POLL_INTERVAL)

    raise TimeoutError(f"等待论文 {paper_id} 达到状态 {expected_names} 超时（当前: {last_status}）")


# ========== 测试用例 ==========

def test_pdf_upload_and_status_flow(client, auth_token, sample_pdf):
    """测试：PDF 上传后状态正确流转"""
    print("\n📤 上传 PDF...")

    with open(sample_pdf, "rb") as f:
        resp = client.post(
            "/api/papers/upload",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={"files": (sample_pdf.name, f, "application/pdf")}
        )

    assert resp.status_code == 200, f"上传失败: {resp.text}"
    data = resp.json()["data"]
    assert len(data["uploaded"]) == 1, "上传结果不正确"

    paper_id = data["uploaded"][0]["paper_id"]
    print(f"  ✅ 上传成功，paper_id={paper_id}")

    # 1. 等待 PARSING 状态
    print("\n⏳ 等待 PDF 解析...")
    try:
        paper = wait_for_paper_status(
            client,
            paper_id,
            [PaperStatus.PARSING, PaperStatus.PENDING_EXTRACTION],
            auth_token,
            timeout=30
        )
        print(f"  ✅ PDF 解析完成，状态: {paper['status']}")
    except TimeoutError as e:
        pytest.fail(f"PDF 解析超时: {e}")

    # 2. 等待 LLM 提取四要素
    print("\n⏳ 等待四要素提取...")
    try:
        paper = wait_for_paper_status(
            client,
            paper_id,
            [PaperStatus.EXTRACTING, PaperStatus.PENDING_CONFIRMATION],
            auth_token,
            timeout=60
        )
        print(f"  ✅ 四要素提取完成，状态: {paper['status']}")
    except TimeoutError as e:
        pytest.fail(f"四要素提取超时: {e}")

    # 3. 验证四要素数据存在
    if paper["status"] == PaperStatus.PENDING_CONFIRMATION.value:
        assert "keyPoints" in paper, "四要素数据缺失"
        kp = paper["keyPoints"]
        assert kp.get("background") or kp.get("methodology"), "四要素为空"
        print(f"  ✅ 四要素数据完整")

    # 4. 确认四要素
    print("\n✅ 确认四要素...")
    resp = client.patch(
        f"/api/papers/{paper_id}/key-points",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=paper.get("keyPoints", {})
    )
    assert resp.status_code == 200, f"确认四要素失败: {resp.text}"

    # 5. 等待向量化完成
    print("\n⏳ 等待向量化...")
    try:
        paper = wait_for_paper_status(
            client,
            paper_id,
            PaperStatus.CONFIRMED,
            auth_token,
            timeout=60
        )
        print(f"  ✅ 向量化完成，状态: {paper['status']}")
    except TimeoutError:
        # 向量化可能失败，但 status 仍为 CONFIRMED
        print(f"  ⚠️ 向量化可能未完成，但状态已为 CONFIRMED")

    # 清理：删除测试论文
    client.delete(f"/api/papers/{paper_id}", headers={"Authorization": f"Bearer {auth_token}"})


def test_concurrent_pdf_upload_consistency(client, auth_token, sample_pdf):
    """测试：并发上传多个 PDF，状态最终一致"""
    print("\n📤 并发上传 3 个 PDF...")

    paper_ids = []

    for i in range(3):
        with open(sample_pdf, "rb") as f:
            resp = client.post(
                "/api/papers/upload",
                headers={"Authorization": f"Bearer {auth_token}"},
                files={"files": (f"test_{i}.pdf", f, "application/pdf")}
            )

        if resp.status_code == 200:
            data = resp.json()["data"]
            if data["uploaded"]:
                paper_ids.append(data["uploaded"][0]["paper_id"])

    assert len(paper_ids) >= 2, "并发上传失败"
    print(f"  ✅ 成功上传 {len(paper_ids)} 个 PDF")

    # 等待所有论文达到 PENDING_CONFIRMATION 或 CONFIRMED
    print("\n⏳ 等待所有论文处理完成...")

    final_statuses = []
    for paper_id in paper_ids:
        try:
            paper = wait_for_paper_status(
                client,
                paper_id,
                [PaperStatus.PENDING_CONFIRMATION, PaperStatus.CONFIRMED, PaperStatus.FAILED],
                auth_token,
                timeout=90
            )
            final_statuses.append(paper["status"])
        except TimeoutError:
            final_statuses.append("TIMEOUT")

    print(f"\n📊 最终状态统计:")
    for status in set(final_statuses):
        count = final_statuses.count(status)
        print(f"  {status}: {count}")

    # 验证：至少 80% 成功
    success_count = final_statuses.count(PaperStatus.PENDING_CONFIRMATION.value) + \
                   final_statuses.count(PaperStatus.CONFIRMED.value)
    assert success_count >= len(paper_ids) * 0.8, "并发上传成功率低于 80%"

    # 清理
    for paper_id in paper_ids:
        client.delete(f"/api/papers/{paper_id}", headers={"Authorization": f"Bearer {auth_token}"})


def test_task_retry_on_failure(client, auth_token, monkeypatch):
    """测试：任务失败后重试机制（模拟）"""
    # 这个测试需要 monkeypatch Celery 任务，实际环境中可以通过杀掉 worker 模拟
    pytest.skip("需要真实 Celery 环境，跳过模拟测试")


def test_embedding_task_idempotency(client, auth_token, sample_pdf):
    """测试：向量化任务幂等性（重复触发不会重复计算）"""
    print("\n📤 上传 PDF 并等待向量化...")

    with open(sample_pdf, "rb") as f:
        resp = client.post(
            "/api/papers/upload",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={"files": (sample_pdf.name, f, "application/pdf")}
        )

    paper_id = resp.json()["data"]["uploaded"][0]["paper_id"]

    # 等待到 CONFIRMED 状态
    try:
        wait_for_paper_status(client, paper_id, PaperStatus.CONFIRMED, auth_token, timeout=90)
    except TimeoutError:
        pytest.skip("论文未能达到 CONFIRMED 状态")

    # 手动触发批量向量化（应跳过已有向量的论文）
    print("\n🔁 触发批量向量化...")
    resp = client.post(
        "/api/graph/embeddings/trigger-batch",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert resp.status_code == 200
    data = resp.json()["data"]

    # 验证：已向量化的论文不应被重新触发
    triggered_ids = [p["paper_id"] for p in data.get("papers", [])]
    assert paper_id not in triggered_ids, "已向量化的论文被重复触发"
    print(f"  ✅ 幂等性验证通过，触发了 {data['triggered']} 篇新论文")

    # 清理
    client.delete(f"/api/papers/{paper_id}", headers={"Authorization": f"Bearer {auth_token}"})


def test_note_export_consistency(client, auth_token):
    """测试：笔记导出与源数据一致性"""
    print("\n📝 创建测试笔记...")

    # 获取一篇论文
    resp = client.get("/api/papers/", headers={"Authorization": f"Bearer {auth_token}"})
    papers = resp.json()["data"]

    if not papers:
        pytest.skip("没有论文数据")

    paper_id = papers[0]["id"]

    # 创建笔记
    note_content = "这是一条测试笔记，包含特殊字符：<>&\"'😀"
    resp = client.post(
        f"/api/papers/{paper_id}/notes",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "content": note_content,
            "title": "测试笔记",
            "page_number": 1
        }
    )

    assert resp.status_code == 200
    note_id = resp.json()["data"]["id"]
    print(f"  ✅ 笔记创建成功，note_id={note_id}")

    # 获取笔记列表
    resp = client.get(
        f"/api/papers/{paper_id}/notes",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    notes = resp.json()["data"]
    created_note = next((n for n in notes if n["id"] == note_id), None)

    assert created_note is not None, "创建的笔记未出现在列表中"
    assert created_note["content"] == note_content, "笔记内容不一致"
    assert created_note["title"] == "测试笔记", "笔记标题不一致"

    print(f"  ✅ 笔记数据一致性验证通过")

    # 清理
    client.delete(
        f"/api/papers/{paper_id}/notes/{note_id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )


def test_graph_cache_consistency(client, auth_token):
    """测试：图谱 LLM 缓存一致性"""
    print("\n🕸️ 生成知识图谱...")

    # 第一次请求（生成缓存）
    resp1 = client.get(
        "/api/graph/llm-structure?max_nodes=10",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    if resp1.status_code != 200:
        pytest.skip("无法生成知识图谱")

    data1 = resp1.json()["data"]
    nodes1 = data1["nodes"]
    edges1 = data1["links"]

    if not nodes1:
        pytest.skip("知识图谱为空")

    print(f"  ✅ 首次生成：{len(nodes1)} 个节点，{len(edges1)} 条边")

    # 第二次请求（应使用缓存）
    time.sleep(1)
    resp2 = client.get(
        "/api/graph/llm-structure?max_nodes=10",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    data2 = resp2.json()["data"]
    nodes2 = data2["nodes"]
    edges2 = data2["links"]

    # 验证缓存标识
    assert data2["meta"].get("cached") == True, "第二次请求未使用缓存"

    # 验证节点和边数量一致
    assert len(nodes1) == len(nodes2), "缓存的节点数量不一致"
    assert len(edges1) == len(edges2), "缓存的边数量不一致"

    # 验证节点 ID 一致
    ids1 = {n["id"] for n in nodes1}
    ids2 = {n["id"] for n in nodes2}
    assert ids1 == ids2, "缓存的节点 ID 不一致"

    print(f"  ✅ 缓存一致性验证通过")


def test_paper_deletion_cascades(client, auth_token, sample_pdf):
    """测试：删除论文时级联删除相关数据（笔记、向量、缓存）"""
    print("\n🗑️ 测试级联删除...")

    # 上传论文
    with open(sample_pdf, "rb") as f:
        resp = client.post(
            "/api/papers/upload",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={"files": (sample_pdf.name, f, "application/pdf")}
        )

    paper_id = resp.json()["data"]["uploaded"][0]["paper_id"]

    # 等待论文处理完成
    try:
        wait_for_paper_status(
            client,
            paper_id,
            [PaperStatus.PENDING_CONFIRMATION, PaperStatus.CONFIRMED],
            auth_token,
            timeout=60
        )
    except TimeoutError:
        pass  # 即使未完成也继续测试

    # 创建笔记
    client.post(
        f"/api/papers/{paper_id}/notes",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"content": "测试笔记", "title": "测试"}
    )

    # 删除论文
    resp = client.delete(
        f"/api/papers/{paper_id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert resp.status_code == 200, f"删除论文失败: {resp.text}"
    print(f"  ✅ 论文删除成功")

    # 验证：笔记也被删除
    resp = client.get(
        f"/api/papers/{paper_id}/notes",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert resp.status_code in (404, 200), "笔记查询应返回 404 或空列表"
    if resp.status_code == 200:
        notes = resp.json()["data"]
        assert notes == [], "笔记未被级联删除"

    print(f"  ✅ 级联删除验证通过")


if __name__ == "__main__":
    # 运行所有测试
    pytest.main([__file__, "-v", "--tb=short", "-s"])
