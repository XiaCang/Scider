"""
AI 问答场景化测试 — 统一运行入口

运行所有场景化测试：
  python tests/run_qa_scenario_tests.py

选择性运行：
  python tests/run_qa_scenario_tests.py --qa-only      # 仅运行标准问题集测试
  python tests/run_qa_scenario_tests.py --ws-only       # 仅运行 WebSocket 测试
  python tests/run_qa_scenario_tests.py --task-only     # 仅运行异步任务测试
  python tests/run_qa_scenario_tests.py --all           # 运行全部（默认）
"""

import sys
import subprocess
import time


def print_header(text: str):
    print("\n" + "=" * 70)
    print(f" {text}")
    print("=" * 70)


def run_test(module_name: str, description: str) -> bool:
    print_header(f"运行: {description}")
    start = time.time()
    result = subprocess.run(
        [sys.executable, f"tests/{module_name}"],
        capture_output=False,
        text=True,
    )
    elapsed = time.time() - start
    success = result.returncode == 0
    status = "✅ 通过" if success else "❌ 失败"
    print(f"\n   {status} ({elapsed:.1f}s)")
    return success


def main():
    import argparse
    parser = argparse.ArgumentParser(description="AI 问答场景化测试运行器")
    parser.add_argument("--qa-only", action="store_true", help="仅运行标准问题集测试")
    parser.add_argument("--ws-only", action="store_true", help="仅运行 WebSocket 测试")
    parser.add_argument("--task-only", action="store_true", help="仅运行异步任务测试")
    parser.add_argument("--all", action="store_true", default=True, help="运行全部测试")
    args = parser.parse_args()

    print_header("🧪 AI 问答助手场景化测试套件")

    test_plan = [
        ("test_qa_scenario.py", "标准问题集 × PDF 场景回答相关性"),
        ("test_ws_conversation.py", "WebSocket 流式推送 + 多轮对话"),
        ("test_task_async_push.py", "Celery 异步任务状态轮询"),
    ]

    if args.qa_only:
        test_plan = test_plan[:1]
    elif args.ws_only:
        test_plan = test_plan[1:2]
    elif args.task_only:
        test_plan = test_plan[2:]

    results = []
    for module, desc in test_plan:
        success = run_test(module, desc)
        results.append((desc, success))

    # 汇总
    print_header("📊 测试汇总")
    passed = sum(1 for _, s in results if s)
    total = len(results)
    print(f"\n   总计: {total}  通过: {passed}  失败: {total - passed}")
    for desc, success in results:
        status = "✅" if success else "❌"
        print(f"   {status} {desc}")

    if passed == total:
        print("\n🎉 所有场景化测试通过！")
    else:
        print(f"\n⚠️  共 {total - passed} 项测试未通过，请检查上述报告。")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
