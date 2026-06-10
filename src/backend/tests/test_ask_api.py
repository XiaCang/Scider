"""
集成测试：向本地后端服务测试 AI 问答接口 POST /api/papers/{paper_id}/ask

前置条件：
  1. 后端服务运行在 http://localhost:8000
  2. 方式一（推荐）：在 .env 中设置 TEST_USER_ID=<你的用户ID>，无需登录
  3. 方式二：修改下方 EMAIL / PASSWORD，通过登录获取 token
  4. 账号下至少有一篇已解析完成的论文（status=CONFIRMED）

运行方式：
  python tests/test_ask_api.py
"""

import sys
import json
import urllib.request
import urllib.error

BASE_URL = "http://localhost:8000"

# 方式二：登录认证（如果 .env 中未设置 TEST_USER_ID）
EMAIL = "test@example.com"
PASSWORD = "your_password"


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
        return json.loads(e.read())


def _get(path: str, token: str | None) -> dict:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{BASE_URL}{path}", headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def main():
    # 检查是否启用测试模式
    print("检查后端测试模式...")
    try:
        resp = _get("/health", None)
        if resp.get("status") == "ok":
            print("   后端服务正常")
    except Exception as e:
        print(f"   后端服务未启动: {e}")
        sys.exit(1)

    # 尝试无 token 访问（测试模式下应成功）
    token = None
    try:
        resp = _get("/api/papers/", None)
        if resp.get("code") == 0:
            print("   测试模式已启用（.env 中设置了 TEST_USER_ID）")
            token = "test_mode"
        else:
            print("   测试模式未启用，需要登录")
    except:
        print("   测试模式未启用，需要登录")

    # 如果测试模式未启用，则登录
    if token != "test_mode":
        print("1. 登录...")
        resp = _post("/api/user/login", {"email": EMAIL, "password": PASSWORD})
        if resp.get("code") != 0:
            print(f"   登录失败: {resp.get('msg')}")
            sys.exit(1)
        token = resp["data"]["token"]
        print(f"   登录成功，token: {token[:20]}...")
    else:
        token = None  # 测试模式下不需要 token

    # 2. 获取论文列表，取第一篇
    print("2. 获取论文列表...")
    resp = _get("/api/papers/", token)
    papers = resp.get("data", [])
    if not papers:
        print("   账号下无论文，请先上传并解析一篇论文")
        sys.exit(1)
    paper = papers[0]
    paper_id = paper["id"]
    print(f"   使用论文: [{paper['status']}] {paper['title'][:60]}")

    # 3. 测试问答接口
    questions = [
        "这篇论文的主要研究问题是什么？",
        "论文提出了什么创新方法？",
        "实验结果如何？",
    ]

    print("3. 测试 AI 问答接口...")
    for i, question in enumerate(questions, 1):
        print(f"\n   问题 {i}: {question}")
        resp = _post(f"/api/papers/{paper_id}/ask", {"question": question}, token)
        code = resp.get("code")
        if code == 0:
            answer = resp["data"]["answer"]
            sources = resp["data"]["sources"]
            print(f"   回答: {answer[:200]}{'...' if len(answer) > 200 else ''}")
            print(f"   来源数量: {len(sources)} 条（full_text: {sum(1 for s in sources if s['type']=='full_text')}, notes: {sum(1 for s in sources if s['type']=='note')}）")
        else:
            print(f"   失败 (code={code}): {resp.get('msg')}")

    # 4. 边界测试：空问题（应返回 422）
    print("\n4. 边界测试：空问题...")
    resp = _post(f"/api/papers/{paper_id}/ask", {"question": ""}, token)
    print(f"   空问题响应: code={resp.get('code')}, msg={resp.get('msg', 'N/A')}")

    # 5. 边界测试：不存在的 paper_id（应返回 404）
    print("5. 边界测试：不存在的 paper_id...")
    resp = _post("/api/papers/nonexistent_id_12345/ask", {"question": "test"}, token)
    print(f"   不存在论文响应: code={resp.get('code')}, msg={resp.get('msg', 'N/A')}")

    print("\n测试完成。")


if __name__ == "__main__":
    main()
