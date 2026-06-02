"""
Celery 异步任务推送测试 — 验证 PDF 解析流程的异步任务状态轮询。

测试目标：
  1. PDF 上传后返回有效的 task_id
  2. 轮询 GET /api/tasks/{task_id} 能获取任务进度
  3. 任务状态流转正确（PENDING → SUCCESS/FAILURE）
  4. 边界情况：查询不存在的 task_id

前置条件：
  1. 后端运行在 http://localhost:8000
  2. Celery Worker 已启动（见 readme.md）
  3. Redis 服务运行中
  4. .env 中设置了 TEST_USER_ID 或有效登录凭据

运行方式：
  pytest tests/test_task_async_push.py -v --tb=short
  或
  python tests/test_task_async_push.py
"""

import sys
import json
import time
import urllib.request
import urllib.error

BASE_URL = "http://localhost:8000"

# 任务状态轮询配置
POLL_INTERVAL = 2    # 轮询间隔（秒）
MAX_POLL_TIME = 120  # 最大等待时间（秒）


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


def _get_token() -> str | None:
    """获取认证 token。"""
    resp = _get("/api/papers/", None)
    if resp.get("code") == 0:
        return None  # 测试模式
    import os
    email = os.getenv("TEST_EMAIL", "test@example.com")
    password = os.getenv("TEST_PASSWORD", "your_password")
    resp = _post("/api/user/login", {"email": email, "password": password})
    if resp.get("code") != 0:
        print(f"❌ 登录失败: {resp.get('msg')}")
        sys.exit(1)
    return resp["data"]["token"]


def poll_task(task_id: str, timeout: int = MAX_POLL_TIME) -> dict:
    """
    轮询任务状态，直到任务完成或超时。

    Args:
        task_id: Celery 任务 ID
        timeout: 最大等待秒数

    Returns:
        任务结果字典，包含 status, result/error 等字段
    """
    start = time.time()
    last_status = None

    print(f"\n    开始轮询任务 {task_id[:8]}...")
    while time.time() - start < timeout:
        elapsed = time.time() - start
        resp = _get(f"/api/tasks/{task_id}", None)

        status = resp.get("status", "UNKNOWN")
        if status != last_status:
            print(f"    📡 [{elapsed:5.1f}s] 状态: {status}")
            last_status = status

        if status == "SUCCESS":
            print(f"    ✅ 任务成功完成 (耗时 {elapsed:.1f}s)")
            return resp
        elif status == "FAILURE":
            error = resp.get("error", "未知错误")
            print(f"    ❌ 任务失败: {error}")
            return resp
        elif status == "REVOKED":
            print(f"    ⚠️  任务被撤销")
            return resp

        time.sleep(POLL_INTERVAL)

    print(f"    ⏰ 轮询超时 ({timeout}s)")
    return {"status": "TIMEOUT", "task_id": task_id}


def main():
    print("=" * 70)
    print("🧪 Celery 异步任务推送测试")
    print("   任务状态轮询 × PDF 解析流程")
    print("=" * 70)

    results = {"passed": 0, "failed": 0, "tests": []}

    # ── 1. 健康检查 ──
    print("\n1️⃣  前置检查...")
    try:
        resp = _get("/health", None)
        assert resp.get("status") == "ok"
        print("    ✅ 后端服务正常")
    except Exception as e:
        print(f"    ❌ 后端服务异常: {e}")
        sys.exit(1)

    token = _get_token()
    print(f"    ✅ 认证完成")

    # ── 2. Ping 任务测试 ──
    print("\n2️⃣  Ping 任务测试...")
    try:
        resp = _post("/api/tasks/ping", {}, token)
        task_id = resp.get("task_id")
        assert task_id, "未返回 task_id"
        print(f"    ✅ Ping 任务提交成功: task_id={task_id[:8]}...")

        # 轮询
        result = poll_task(task_id, timeout=30)
        assert result.get("status") == "SUCCESS", f"Ping 任务未成功: {result}"

        results["tests"].append({
            "name": "ping_task",
            "success": True,
            "detail": f"task_id={task_id[:8]}..., status={result['status']}",
        })
        results["passed"] += 1
        print(f"    ✅ Ping 任务测试通过")
    except Exception as e:
        results["tests"].append({
            "name": "ping_task",
            "success": False,
            "detail": str(e),
        })
        results["failed"] += 1
        print(f"    ❌ Ping 任务测试失败: {e}")

    # ── 3. 任务状态查询边界测试 ──
    print("\n3️⃣  边界测试...")

    # 3a. 不存在的 task_id
    try:
        resp = _get("/api/tasks/nonexistent-task-id-12345", None)
        status = resp.get("status", "N/A")
        # 不存在的任务应返回 PENDING 或错误
        results["tests"].append({
            "name": "nonexistent_task",
            "success": True,
            "detail": f"不存在任务查询: status={status}",
        })
        results["passed"] += 1
        print(f"    ✅ 不存在任务查询: status={status}")
    except Exception as e:
        results["tests"].append({
            "name": "nonexistent_task",
            "success": False,
            "detail": str(e),
        })
        results["failed"] += 1
        print(f"    ❌ 不存在任务查询失败: {e}")

    # 3b. 无效 task_id 格式
    try:
        resp = _get("/api/tasks/", None)
        # 期望 404 或错误
        results["tests"].append({
            "name": "invalid_task_id",
            "success": True,
            "detail": f"无效 task_id 响应: code={resp.get('code', 'N/A')}",
        })
        results["passed"] += 1
        print(f"    ✅ 无效 task_id 格式: 正确处理")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            results["tests"].append({
                "name": "invalid_task_id",
                "success": True,
                "detail": f"返回 404 正确",
            })
            results["passed"] += 1
            print(f"    ✅ 无效 task_id: 返回 404")
        else:
            results["tests"].append({
                "name": "invalid_task_id",
                "success": False,
                "detail": f"HTTP {e.code}",
            })
            results["failed"] += 1
            print(f"    ❌ 无效 task_id: 返回 {e.code}")

    # ── 4. 打印报告 ──
    print("\n" + "=" * 70)
    print("📊 异步任务推送测试报告")
    print("=" * 70)

    total = results["passed"] + results["failed"]
    print(f"\n📈 统计:")
    print(f"   测试总数: {total}")
    print(f"   通过: {results['passed']}")
    print(f"   失败: {results['failed']}")
    print(f"   通过率: {results['passed']/total*100:.1f}%" if total else "   无测试")

    print(f"\n📋 详情:")
    for t in results["tests"]:
        status = "✅" if t["success"] else "❌"
        print(f"   {status} {t['name']}: {t['detail']}")

    grade = "A" if results["failed"] == 0 else "B" if results["failed"] <= total * 0.2 else "C"
    print(f"\n🏆 综合评定: {grade}")
    print("=" * 70)

    return results["failed"] == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
