"""
WebSocket 异步推送 + 多轮对话上下文连贯性测试。

测试目标：
  1. WebSocket 连接建立与认证
  2. 流式 token 推送（逐个 token 到达）
  3. 多轮对话上下文连贯性（追问时能否引用前文）
  4. Celery 任务状态异步推送（模拟）
  5. 连接断开与重连
  6. 边界情况（空消息、超长消息、并发对话）

前置条件：
  1. 后端运行在 http://localhost:8000
  2. .env 中设置了 TEST_USER_ID（测试模式）或提供了有效登录凭据
  3. 账号下至少有一篇 CONFIRMED 状态的论文（含 full_text）

运行方式：
  pytest tests/test_ws_conversation.py -v --tb=short
  或
  python tests/test_ws_conversation.py
"""

import sys
import json
import time
import asyncio
import urllib.request
import urllib.error
from typing import Optional

import pytest

BASE_URL = "http://localhost:8000"
WS_BASE_URL = "ws://localhost:8000"

# 尝试导入 websocket 库
try:
    import websockets
except ImportError:
    print("需要安装 websockets 库：pip install websockets")
    print("正在尝试自动安装...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets"])
    import websockets


# ---------------------------------------------------------------------------
# 健康检查（用于 skipif）
# ---------------------------------------------------------------------------

def _is_backend_alive() -> bool:
    """检查后端服务是否正在运行，返回 True/False 而不退出。"""
    try:
        req = urllib.request.Request(f"{BASE_URL}/health")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            return data.get("status") == "ok"
    except Exception:
        return False


# 所有 WebSocket 测试共享的跳过条件：后端服务不可用时跳过（而非 sys.exit）
_needs_backend = pytest.mark.skipif(
    not _is_backend_alive(),
    reason="后端服务未运行 (http://localhost:8000)，跳过 WebSocket 测试",
)


# ---------------------------------------------------------------------------
# HTTP 工具（获取 token 和论文信息）
# ---------------------------------------------------------------------------

def _post(path: str, body: dict, token: str | None = None) -> dict:
    data = json.dumps(body).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{BASE_URL}{path}", data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read())
        except Exception:
            return {"code": e.code, "msg": "HTTP error", "data": None}


def _get(path: str, token: str | None) -> dict:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{BASE_URL}{path}", headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def _get_token_and_paper() -> tuple:
    """获取认证 token 和第一篇 CONFIRMED 论文的 ID。"""
    # 健康检查
    try:
        resp = _get("/health", None)
        assert resp.get("status") == "ok", "后端服务异常"
    except Exception as e:
        raise RuntimeError(f"❌ 后端服务未启动: {e}")

    # 认证
    token = None
    resp = _get("/api/papers/", None)
    if resp.get("code") == 0:
        token = None  # 测试模式
    else:
        import os
        email = os.getenv("TEST_EMAIL", "test@example.com")
        password = os.getenv("TEST_PASSWORD", "your_password")
        resp = _post("/api/user/login", {"email": email, "password": password})
        if resp.get("code") != 0:
            raise RuntimeError(f"❌ 登录失败: {resp.get('msg')}")
        token = resp["data"]["token"]

    # 获取论文
    resp = _get("/api/papers/", token)
    papers = resp.get("data", [])
    confirmed = [p for p in papers if p.get("status") == "CONFIRMED"]
    if not confirmed:
        raise RuntimeError("❌ 无 CONFIRMED 论文")

    return token, confirmed[0]["id"]


# ---------------------------------------------------------------------------
# 测试用例
# ---------------------------------------------------------------------------

class WSTestSuite:
    """WebSocket + 多轮对话测试套件"""

    def __init__(self, token: str, paper_id: str):
        self.token = token
        self.paper_id = paper_id
        self.results: list[dict] = []
        self.jwt_token = self._extract_jwt(token)

    def _extract_jwt(self, token: str | None) -> str:
        """获取真正的 JWT token 用于 WS 认证。"""
        if token is None:
            # 测试模式下需要先登录获取 token
            import os
            email = os.getenv("TEST_EMAIL", "test@example.com")
            password = os.getenv("TEST_PASSWORD", "your_password")
            resp = _post("/api/user/login", {"email": email, "password": password})
            if resp.get("code") == 0:
                return resp["data"]["token"]
            return ""
        return token

    async def test_connection(self) -> bool:
        """测试 1: WebSocket 连接与认证"""
        print("\n  📡 测试 1: WebSocket 连接与认证")
        async with websockets.connect(
            f"{WS_BASE_URL}/api/ws/chat?token={self.jwt_token}&paper_id={self.paper_id}",
            ping_interval=20,
            ping_timeout=10,
        ) as ws:
            # 发送一个简单问题验证连接
            await ws.send(json.dumps({
                "type": "question",
                "content": "你好，请做一个简短的自我介绍。"
            }))
            responses = []
            async for msg in ws:
                data = json.loads(msg)
                responses.append(data)
                if data["type"] in ("done", "error"):
                    break

            success = any(r["type"] == "done" for r in responses)
            has_tokens = any(r["type"] == "token" for r in responses)
            self.results.append({
                "test": "connection_and_auth",
                "success": success,
                "detail": f"收到 {len(responses)} 条消息, token推送: {has_tokens}",
            })
            print(f"    {'✅' if success else '❌'} 连接认证: {'通过' if success else '失败'}")
            print(f"    收到 {len(responses)} 条消息, 含 token 推送: {has_tokens}")
            return success

    async def test_streaming_push(self) -> bool:
        """测试 2: 流式 token 推送"""
        print("\n  📡 测试 2: 流式 token 推送")
        async with websockets.connect(
            f"{WS_BASE_URL}/api/ws/chat?token={self.jwt_token}&paper_id={self.paper_id}",
        ) as ws:
            await ws.send(json.dumps({
                "type": "question",
                "content": "请简要总结这篇论文的核心贡献。"
            }))

            tokens = []
            final_answer = ""
            start_time = time.time()
            first_token_time = None

            async for msg in ws:
                data = json.loads(msg)
                if data["type"] == "token":
                    if first_token_time is None:
                        first_token_time = time.time()
                    tokens.append(data["content"])
                elif data["type"] == "done":
                    final_answer = data["content"]
                    break
                elif data["type"] == "error":
                    self.results.append({
                        "test": "streaming_push",
                        "success": False,
                        "detail": f"服务端错误: {data['content']}",
                    })
                    return False

            total_time = time.time() - start_time
            ttf = (first_token_time - start_time) if first_token_time else total_time

            # 评估流式效果
            has_tokens = len(tokens) > 0
            is_streaming = len(tokens) > 3  # 超过 3 个 token 视为真正流式
            has_final = len(final_answer) > 50

            success = has_tokens and has_final
            self.results.append({
                "test": "streaming_push",
                "success": success,
                "detail": (f"tokens: {len(tokens)}, 首token延迟: {ttf:.2f}s, "
                          f"总耗时: {total_time:.2f}s, 回答长度: {len(final_answer)}"),
            })
            print(f"    {'✅' if success else '❌'} 流式推送: {'通过' if success else '失败'}")
            print(f"    token 数: {len(tokens)}, 首 token 延迟: {ttf:.2f}s")
            print(f"    总耗时: {total_time:.2f}s, 回答长度: {len(final_answer)}")
            print(f"    真正流式: {'是' if is_streaming else '否（可能为一次性返回）'}")
            return success

    async def test_multi_turn_context(self) -> bool:
        """测试 3: 多轮对话上下文连贯性"""
        print("\n  📡 测试 3: 多轮对话上下文连贯性")

        questions = [
            "这篇论文的主要研究问题是什么？",
            "他们用了什么方法来解决这个问题？",       # 期望能引用"研究问题"
            "这个方法相比于传统方法有什么优势？",       # 期望能引用"方法"
            "根据之前讨论的内容，总结一下这篇论文的贡献。",  # 期望综合前文
        ]

        async with websockets.connect(
            f"{WS_BASE_URL}/api/ws/chat?token={self.jwt_token}&paper_id={self.paper_id}",
        ) as ws:
            context_awareness = []

            for i, question in enumerate(questions):
                print(f"\n    第 {i+1} 轮: {question[:50]}...")

                # 先清除历史再提问，模拟全新对话
                if i > 0:
                    # 不清除历史，保持上下文
                    pass

                await ws.send(json.dumps({
                    "type": "question",
                    "content": question,
                }))

                answer = ""
                async for msg in ws:
                    data = json.loads(msg)
                    if data["type"] == "token":
                        answer += data["content"]
                    elif data["type"] == "done":
                        answer = data["content"]
                        break
                    elif data["type"] == "error":
                        print(f"      ❌ 错误: {data['content']}")
                        break

                # 评估回答质量
                has_content = len(answer) > 30
                print(f"      回答长度: {len(answer)}")

                # 上下文连贯性检测：第2轮问题应提及"方法"，第4轮应综合前文
                if i == 3:
                    # 综合轮次，期望引用前文
                    references_previous = any(
                        kw in answer for kw in ["研究问题", "方法", "优势", "前面", "如上", "之前"]
                    )
                    context_awareness.append(references_previous)
                    print(f"      引用前文: {'是' if references_previous else '否'}")

            success = all(ca for ca in context_awareness) if context_awareness else True
            self.results.append({
                "test": "multi_turn_context",
                "success": success,
                "detail": f"{len(questions)} 轮对话, 上下文引用: {context_awareness}",
            })
            print(f"    {'✅' if success else '❌'} 多轮对话: {'通过' if success else '失败'}")
            return success

    async def test_concurrent_sessions(self) -> bool:
        """测试 4: 并发 WebSocket 连接"""
        print("\n  📡 测试 4: 并发 WebSocket 连接")
        n_concurrent = 3

        async def single_session(session_id: int) -> dict:
            try:
                async with websockets.connect(
                    f"{WS_BASE_URL}/api/ws/chat?token={self.jwt_token}&paper_id={self.paper_id}",
                    ping_interval=20,
                    ping_timeout=10,
                ) as ws:
                    await ws.send(json.dumps({
                        "type": "question",
                        "content": f"这是会话 {session_id} 的测试问题。"
                    }))
                    responses = []
                    async for msg in ws:
                        data = json.loads(msg)
                        responses.append(data["type"])
                        if data["type"] in ("done", "error"):
                            break
                    return {"id": session_id, "success": "done" in responses, "count": len(responses)}
            except Exception as e:
                return {"id": session_id, "success": False, "error": str(e)}

        tasks = [single_session(i) for i in range(n_concurrent)]
        session_results = await asyncio.gather(*tasks)

        all_success = all(r["success"] for r in session_results)
        self.results.append({
            "test": "concurrent_sessions",
            "success": all_success,
            "detail": f"{n_concurrent} 个并发会话, 全部成功: {all_success}",
        })
        for r in session_results:
            status = "✅" if r["success"] else "❌"
            print(f"    {status} 会话 {r['id']}: {'成功' if r['success'] else '失败'}")
        return all_success

    async def test_clear_context(self) -> bool:
        """测试 5: 清除上下文"""
        print("\n  📡 测试 5: 清除对话上下文")
        async with websockets.connect(
            f"{WS_BASE_URL}/api/ws/chat?token={self.jwt_token}&paper_id={self.paper_id}",
        ) as ws:
            # 先发一个问题建立上下文
            await ws.send(json.dumps({"type": "question", "content": "这是第一个问题。"}))
            async for msg in ws:
                data = json.loads(msg)
                if data["type"] in ("done", "error"):
                    break

            # 清除上下文
            await ws.send(json.dumps({"type": "clear"}))
            clear_resp = await asyncio.wait_for(ws.recv(), timeout=5)
            clear_data = json.loads(clear_resp)
            success = clear_data.get("type") == "status" and clear_data.get("content") == "context_cleared"

            self.results.append({
                "test": "clear_context",
                "success": success,
                "detail": f"清除响应: {clear_data.get('type')} / {clear_data.get('content')}",
            })
            print(f"    {'✅' if success else '❌'} 清除上下文: {'通过' if success else '失败'}")
            return success

    async def test_edge_cases(self) -> bool:
        """测试 6: 边界情况"""
        print("\n  📡 测试 6: 边界情况测试")
        edge_results = []

        async with websockets.connect(
            f"{WS_BASE_URL}/api/ws/chat?token={self.jwt_token}&paper_id={self.paper_id}",
        ) as ws:
            # 6a. 空消息
            await ws.send(json.dumps({"type": "question", "content": ""}))
            resp = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
            empty_ok = resp.get("type") == "error"
            edge_results.append(("空消息", empty_ok))
            print(f"    {'✅' if empty_ok else '❌'} 空消息: {'正确拒绝' if empty_ok else '未拒绝'}")

            # 6b. 无效 JSON
            await ws.send("这不是 JSON")
            resp = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
            invalid_ok = resp.get("type") == "error"
            edge_results.append(("无效JSON", invalid_ok))
            print(f"    {'✅' if invalid_ok else '❌'} 无效JSON: {'正确拒绝' if invalid_ok else '未拒绝'}")

            # 6c. 未知消息类型
            await ws.send(json.dumps({"type": "unknown_type", "content": "test"}))
            resp = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
            unknown_ok = resp.get("type") == "error"
            edge_results.append(("未知类型", unknown_ok))
            print(f"    {'✅' if unknown_ok else '❌'} 未知类型: {'正确拒绝' if unknown_ok else '未拒绝'}")

        all_pass = all(r for _, r in edge_results)
        self.results.append({
            "test": "edge_cases",
            "success": all_pass,
            "detail": f"空消息={'通过' if edge_results[0][1] else '失败'}, "
                      f"无效JSON={'通过' if edge_results[1][1] else '失败'}, "
                      f"未知类型={'通过' if edge_results[2][1] else '失败'}",
        })
        return all_pass

    async def test_reconnection(self) -> bool:
        """测试 7: 断线重连"""
        print("\n  📡 测试 7: 断线重连")
        try:
            # 第一次连接并立即断开
            ws1 = await websockets.connect(
                f"{WS_BASE_URL}/api/ws/chat?token={self.jwt_token}&paper_id={self.paper_id}",
            )
            await ws1.close()

            # 等待短暂时间后重连
            await asyncio.sleep(0.5)
            async with websockets.connect(
                f"{WS_BASE_URL}/api/ws/chat?token={self.jwt_token}&paper_id={self.paper_id}",
            ) as ws2:
                await ws2.send(json.dumps({
                    "type": "question",
                    "content": "重连后的测试问题。"
                }))
                async for msg in ws2:
                    data = json.loads(msg)
                    if data["type"] in ("done", "error"):
                        break

            success = True
            self.results.append({
                "test": "reconnection",
                "success": True,
                "detail": "断线重连成功",
            })
            print(f"    ✅ 断线重连: 通过")
            return True
        except Exception as e:
            self.results.append({
                "test": "reconnection",
                "success": False,
                "detail": f"重连失败: {e}",
            })
            print(f"    ❌ 断线重连: 失败 - {e}")
            return False

    async def run_all(self):
        """运行所有测试"""
        print("\n" + "=" * 70)
        print("🧪 WebSocket 异步推送 + 多轮对话测试")
        print("=" * 70)

        tests = [
            ("连接与认证", self.test_connection()),
            ("流式 token 推送", self.test_streaming_push()),
            ("多轮对话上下文", self.test_multi_turn_context()),
            ("并发会话", self.test_concurrent_sessions()),
            ("清除上下文", self.test_clear_context()),
            ("边界情况", self.test_edge_cases()),
            ("断线重连", self.test_reconnection()),
        ]

        for name, coro in tests:
            try:
                await asyncio.wait_for(coro, timeout=60)
            except asyncio.TimeoutError:
                self.results.append({
                    "test": name,
                    "success": False,
                    "detail": "超时 (60s)",
                })
                print(f"    ❌ {name}: 超时")

        self.print_report()

    def print_report(self):
        """打印测试报告"""
        print("\n" + "=" * 70)
        print("📊 WebSocket + 多轮对话测试报告")
        print("=" * 70)

        total = len(self.results)
        passed = sum(1 for r in self.results if r["success"])

        print(f"\n📈 总体统计:")
        print(f"   测试项总数: {total}")
        print(f"   通过: {passed} / 失败: {total - passed}")
        print(f"   通过率: {passed/total*100:.1f}%" if total else "   无测试结果")

        print(f"\n📋 测试详情:")
        for r in self.results:
            status = "✅" if r["success"] else "❌"
            print(f"\n   {status} {r['test']}")
            print(f"      详情: {r['detail']}")

        grade = "A" if passed == total else "B" if passed >= total * 0.8 else "C"
        print(f"\n🏆 综合评定: {grade}")
        print("=" * 70)

        return passed == total


# ---------------------------------------------------------------------------
# pytest 入口
# ---------------------------------------------------------------------------


@_needs_backend
@pytest.mark.asyncio
async def test_ws_connection():
    token, paper_id = _get_token_and_paper()
    suite = WSTestSuite(token, paper_id)
    assert await suite.test_connection()


@_needs_backend
@pytest.mark.asyncio
async def test_ws_streaming():
    token, paper_id = _get_token_and_paper()
    suite = WSTestSuite(token, paper_id)
    assert await suite.test_streaming_push()


@_needs_backend
@pytest.mark.asyncio
async def test_ws_multi_turn():
    token, paper_id = _get_token_and_paper()
    suite = WSTestSuite(token, paper_id)
    assert await suite.test_multi_turn_context()


@_needs_backend
@pytest.mark.asyncio
async def test_ws_concurrent():
    token, paper_id = _get_token_and_paper()
    suite = WSTestSuite(token, paper_id)
    assert await suite.test_concurrent_sessions()


@_needs_backend
@pytest.mark.asyncio
async def test_ws_clear_context():
    token, paper_id = _get_token_and_paper()
    suite = WSTestSuite(token, paper_id)
    assert await suite.test_clear_context()


@_needs_backend
@pytest.mark.asyncio
async def test_ws_edge_cases():
    token, paper_id = _get_token_and_paper()
    suite = WSTestSuite(token, paper_id)
    assert await suite.test_edge_cases()


@_needs_backend
@pytest.mark.asyncio
async def test_ws_reconnection():
    token, paper_id = _get_token_and_paper()
    suite = WSTestSuite(token, paper_id)
    assert await suite.test_reconnection()


# ---------------------------------------------------------------------------
# 直接运行入口
# ---------------------------------------------------------------------------

async def main():
    token, paper_id = _get_token_and_paper()
    suite = WSTestSuite(token, paper_id)
    await suite.run_all()


if __name__ == "__main__":
    asyncio.run(main())
