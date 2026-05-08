"""
test_recommend.py — 测试 /api/discover/recommendations 接口

用法:
    # 测试 401（不传 token）
    python scripts/test_recommend.py --no-auth

    # 正常测试（从环境变量读取凭据，或命令行指定）
    python scripts/test_recommend.py
    python scripts/test_recommend.py --base-url http://localhost:8000
    python scripts/test_recommend.py --email user@example.com --password mypass
    python scripts/test_recommend.py --direction upstream

    # 也可以从 .env 文件读取（与后端共用）
    python scripts/test_recommend.py --env-file src/backend/.env
"""

import argparse
import json
import os
import sys
from pathlib import Path

import httpx


def load_env_file(path: str) -> dict:
    """简易 .env 解析（仅解析 KEY=VALUE 行，忽略注释和空行）。"""
    env = {}
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                env[key.strip()] = val.strip()
    except FileNotFoundError:
        pass
    return env


def _req_json(method: str, url: str, **kwargs) -> tuple[httpx.Response, dict]:
    """发送 HTTP 请求并解析 JSON，失败时给出友好提示并退出。"""
    try:
        resp = getattr(httpx, method)(url, **kwargs)
        data = resp.json()
        return resp, data
    except httpx.RequestError as e:
        print(f"[FAIL] 请求失败: {e}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"[FAIL] 响应不是有效的 JSON (status={resp.status_code})")
        print(f"       响应内容前 200 字符: {resp.text[:200]}")
        sys.exit(1)


def login(base_url: str, email: str, password: str) -> str:
    """登录获取 JWT token。返回 token 字符串。"""
    url = f"{base_url.rstrip('/')}/api/user/login"
    resp, data = _req_json("post", url, json={"email": email, "password": password}, timeout=15)

    if data.get("code") != 0 or not data.get("data"):
        print(f"[FAIL] 登录失败: {data.get('msg', '未知错误')}")
        sys.exit(1)

    token = data["data"].get("token")
    if not token:
        print(f"[FAIL] 登录响应缺少 token: {json.dumps(data, ensure_ascii=False)}")
        sys.exit(1)

    print(f"[OK] 登录成功，用户名: {data['data'].get('userInfo', {}).get('username', '?')}")
    return token


def test_recommendations(base_url: str, token: str = None, direction: str = ""):
    """调用 recommend 接口并验证结果。"""
    url = f"{base_url.rstrip('/')}/api/discover/recommendations"
    params = {}
    if direction:
        params["direction"] = direction

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    resp, data = _req_json("get", url, params=params, headers=headers, timeout=30)

    # ── 打印响应概览 ──
    code = data.get("code")
    msg = data.get("msg", "")
    items = data.get("data", [])

    print(f"\n响应: code={code}, msg={msg!r}, 结果数={len(items) if isinstance(items, list) else 'N/A'}")

    # ── 401 未认证测试 ──
    if not token:
        if resp.status_code == 401 or code == 401:
            print("[PASS] 未认证请求正确返回 401")
        else:
            print(f"[FAIL] 未认证应返回 401，但得到 status={resp.status_code}, code={code}")
        return

    # ── 正常请求验证 ──
    if resp.status_code != 200:
        print(f"[FAIL] 期望 status=200，得到 {resp.status_code}")
        return

    if code != 0:
        print(f"[FAIL] 期望 code=0，得到 {code}: {msg}")
        return

    if not isinstance(items, list):
        print(f"[FAIL] data 应为 list，得到 {type(items).__name__}")
        return

    # ── 逐条验证字段完整性 ──
    required_fields = {"semantic_id", "title", "authors", "year", "doi",
                       "citation_count", "in_library", "reason"}
    optional_fields = {"venue", "source_type", "abstract", "pdf_url"}

    if items:
        print(f"\n--- 结果预览（前 {min(len(items), 5)} 条）---")
        for i, item in enumerate(items[:5], 1):
            missing = required_fields - set(item.keys())
            if missing:
                print(f"  [{i}] ⚠ 缺少字段: {missing}")
            print(f"  [{i}] {item.get('title', '?')[:60]}")
            print(f"       作者: {item.get('authors', '?')[:40]}")
            print(f"       年份: {item.get('year', '?')}  |  引用: {item.get('citation_count', '?')}")
            print(f"       reason: {item.get('reason', '?')}")
            print(f"       in_library: {item.get('in_library', '?')}")
            print()

        # 字段覆盖率统计
        ok_count = sum(1 for item in items if required_fields.issubset(item.keys()))
        total = len(items)
        print(f"--- 字段完整性: {ok_count}/{total} 条所有必填字段齐全 ---")

        if ok_count == total:
            print("[PASS] 所有推荐结果字段完整")
        else:
            print(f"[WARN] {total - ok_count} 条结果缺失必填字段")

        # in_library 必须是 bool
        bad_in_lib = [i for i, item in enumerate(items) if not isinstance(item.get("in_library"), bool)]
        if bad_in_lib:
            print(f"[WARN] {len(bad_in_lib)} 条结果的 in_library 不是 bool: {bad_in_lib}")
    else:
        print("[INFO] 推荐结果为空（文库中可能没有论文）")

    print("\n[PASS] 所有检查完成")


def main():
    parser = argparse.ArgumentParser(description="测试 /api/discover/recommendations 接口")
    parser.add_argument("--base-url", default=os.getenv("BASE_URL", "http://39.107.252.200:8000"),
                        help="后端地址（默认 http://localhost:8000）")
    parser.add_argument("--email", help="登录邮箱")
    parser.add_argument("--password", help="登录密码")
    parser.add_argument("--direction", default="", help="recommend direction 参数（可选）")
    parser.add_argument("--no-auth", action="store_true",
                        help="测试未认证（401）场景，不传 token")
    parser.add_argument("--env-file", default="",
                        help="从 .env 文件读取凭据（如 src/backend/.env）")
    args = parser.parse_args()

    # 从 .env 文件加载
    if args.env_file:
        env = load_env_file(args.env_file)
        args.email = args.email or env.get("TEST_EMAIL")
        args.password = args.password or env.get("TEST_PASSWORD")

    # 从系统环境变量兜底
    args.email = args.email or os.getenv("TEST_EMAIL")
    args.password = args.password or os.getenv("TEST_PASSWORD")

    print(f"[Config] base_url = {args.base_url}")
    print(f"[Config] direction = {args.direction or '(空)'}")
    print(f"[Config] no_auth = {args.no_auth}")

    # 健康检查
    try:
        health = httpx.get(f"{args.base_url.rstrip('/')}/health", timeout=5)
        if health.status_code != 200:
            print(f"[FAIL] 健康检查返回 status={health.status_code}，后端可能未正常启动")
            print(f"       响应: {health.text[:200]}")
            sys.exit(1)
        print(f"[OK] 健康检查通过")
    except httpx.RequestError as e:
        print(f"[FAIL] 无法连接 {args.base_url}: {e}")
        sys.exit(1)

    token = None
    if not args.no_auth:
        if not args.email or not args.password:
            print("[SKIP] 未提供凭据（--email/--password 或环境变量 TEST_EMAIL/TEST_PASSWORD），"
                  "跳过登录，仅测试 401 场景")
        else:
            token = login(args.base_url, args.email, args.password)

    test_recommendations(args.base_url, token=token, direction=args.direction)


if __name__ == "__main__":
    main()
