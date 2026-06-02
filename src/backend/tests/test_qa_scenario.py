"""
AI 问答助手场景化测试：标准问题集 + PDF 场景回答相关性 + 响应速度

测试目标：
  1. 构建覆盖多维度（事实提取、总结归纳、批判分析、交叉引用）的标准问题集
  2. 验证 PDF 全文 + 笔记场景下 LLM 回答的相关性
  3. 测量端到端响应时间，确保满足 SLA
  4. 边界条件测试（空文本、超长文本、无笔记等）

前置条件：
  1. 后端运行在 http://localhost:8000
  2. .env 中设置了 TEST_USER_ID（测试模式）或提供了有效登录凭据
  3. 账号下至少有一篇 CONFIRMED 状态的论文（含 full_text 和 notes）

运行方式：
  pytest tests/test_qa_scenario.py -v --tb=short
  或
  python tests/test_qa_scenario.py
"""

import sys
import json
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Optional

BASE_URL = "http://localhost:8000"
TEST_USER_ID_ENV_VAR = "TEST_USER_ID"

# ---------------------------------------------------------------------------
# 标准问题集 —— 按认知维度分类
# ---------------------------------------------------------------------------

@dataclass
class TestQuestion:
    """单个测试问题"""
    id: str
    question: str
    category: str                # 问题类别
    description: str             # 测试意图
    min_answer_length: int = 50  # 期望回答最小字符数
    requires_source: bool = True # 是否期望返回来源引用
    expected_keywords: list = field(default_factory=list)  # 期望出现的关键词


# 标准问题集
STANDARD_QUESTIONS = [
    # ── 事实提取类 ──
    TestQuestion(
        id="FACT-1",
        question="这篇论文的主要研究问题是什么？",
        category="fact_extraction",
        description="验证能否准确提取研究问题",
        min_answer_length=50,
        expected_keywords=["研究", "问题"],
    ),
    TestQuestion(
        id="FACT-2",
        question="论文提出了什么创新方法？",
        category="fact_extraction",
        description="验证能否提取方法学创新点",
        min_answer_length=50,
        expected_keywords=["方法", "提出"],
    ),
    TestQuestion(
        id="FACT-3",
        question="论文的实验结果如何？主要性能指标是多少？",
        category="fact_extraction",
        description="验证能否提取实验结果数据",
        min_answer_length=80,
    ),
    TestQuestion(
        id="FACT-4",
        question="论文的研究背景是什么？",
        category="fact_extraction",
        description="验证对研究背景的提取能力",
        min_answer_length=50,
    ),

    # ── 总结归纳类 ──
    TestQuestion(
        id="SUMM-1",
        question="请用三句话概括这篇论文的核心贡献。",
        category="summarization",
        description="验证摘要总结能力",
        min_answer_length=100,
    ),
    TestQuestion(
        id="SUMM-2",
        question="这篇论文的应用场景有哪些？",
        category="summarization",
        description="验证能否归纳应用场景",
        min_answer_length=60,
    ),
    TestQuestion(
        id="SUMM-3",
        question="论文中使用了哪些关键技术或算法？",
        category="summarization",
        description="验证技术细节归纳能力",
        min_answer_length=60,
    ),

    # ── 批判分析类 ──
    TestQuestion(
        id="CRIT-1",
        question="这篇论文的局限性是什么？",
        category="critical_analysis",
        description="验证能否识别论文局限性（若有讨论）",
        min_answer_length=50,
    ),
    TestQuestion(
        id="CRIT-2",
        question="论文的实验设计是否合理？为什么？",
        category="critical_analysis",
        description="验证对实验设计的批判性思考",
        min_answer_length=80,
    ),
    TestQuestion(
        id="CRIT-3",
        question="论文的结论是否有足够的数据支撑？",
        category="critical_analysis",
        description="验证对结论可靠性的判断",
        min_answer_length=60,
    ),

    # ── 交叉引用类（依赖于笔记） ──
    TestQuestion(
        id="CROSS-1",
        question="结合我做的笔记，这篇论文和之前阅读的论文有什么联系？",
        category="cross_reference",
        description="验证能否结合笔记进行关联分析",
        min_answer_length=80,
    ),
    TestQuestion(
        id="CROSS-2",
        question="根据论文内容和我的笔记，这个领域下一步的研究方向可能是什么？",
        category="cross_reference",
        description="验证能否综合论文+笔记进行展望",
        min_answer_length=80,
    ),
]


# ---------------------------------------------------------------------------
# HTTP 工具
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
        body_bytes = e.read()
        try:
            return json.loads(body_bytes)
        except json.JSONDecodeError:
            return {"code": e.code, "msg": body_bytes.decode(), "data": None}


def _get(path: str, token: str | None) -> dict:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{BASE_URL}{path}", headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


# ---------------------------------------------------------------------------
# 评分辅助
# ---------------------------------------------------------------------------

def rate_relevance(answer: str, question: TestQuestion) -> dict:
    """
    对回答进行简单的相关性评分。
    返回评分（0-5）和评分理由。
    """
    score = 3  # 默认中等
    details = []

    # 1. 长度检查
    if len(answer) < question.min_answer_length:
        score -= 1
        details.append(f"回答过短 ({len(answer)} < {question.min_answer_length})")
    elif len(answer) > 500:
        score += 0.5
        details.append("回答内容丰富")

    # 2. 关键词匹配
    if question.expected_keywords:
        matched = sum(1 for kw in question.expected_keywords if kw in answer)
        if matched >= len(question.expected_keywords):
            score += 1
            details.append("关键词覆盖完整")
        elif matched > 0:
            score += 0.5
            details.append(f"部分关键词匹配 ({matched}/{len(question.expected_keywords)})")
        else:
            score -= 0.5
            details.append("未匹配到期望关键词")

    # 3. 检查是否有空洞回复
    vague_patterns = ["无法回答", "没有足够信息", "暂无相关信息", "根据现有内容"]
    if any(p in answer for p in vague_patterns):
        score -= 1
        details.append("回答倾向回避/空洞")

    # 4. 引用检查
    if "（论文正文）" in answer or "（笔记" in answer or "(full_text)" in answer.lower():
        score += 0.5
        details.append("包含来源引用")

    score = max(0, min(5, score))
    return {"score": round(score, 1), "details": "; ".join(details)}


# ---------------------------------------------------------------------------
# 测试结果收集
# ---------------------------------------------------------------------------

class TestResults:
    def __init__(self):
        self.questions: list[dict] = []
        self.boundary_tests: list[dict] = []
        self.timing_results: list[float] = []

    def add_question_result(self, q: TestQuestion, answer: str, sources: list,
                            elapsed: float, success: bool, error_msg: str = ""):
        relevance = rate_relevance(answer, q) if success else {"score": 0, "details": error_msg}
        self.questions.append({
            "id": q.id,
            "category": q.category,
            "question": q.question,
            "description": q.description,
            "success": success,
            "answer_preview": answer[:200] + ("..." if len(answer) > 200 else ""),
            "answer_length": len(answer),
            "sources_count": len(sources) if sources else 0,
            "elapsed_seconds": round(elapsed, 2),
            "relevance_score": relevance["score"],
            "relevance_details": relevance["details"],
            "error": error_msg,
        })
        self.timing_results.append(elapsed)

    def add_boundary_result(self, name: str, status_code: int, response: dict, elapsed: float):
        self.boundary_tests.append({
            "name": name,
            "status_code": status_code,
            "response": response,
            "elapsed_seconds": round(elapsed, 2),
        })

    def print_report(self):
        """打印详细测试报告"""
        print("\n" + "=" * 70)
        print("📊 AI 问答场景化测试报告")
        print("=" * 70)

        # 总体统计
        total = len(self.questions)
        success = sum(1 for q in self.questions if q["success"])
        avg_time = sum(self.timing_results) / len(self.timing_results) if self.timing_results else 0
        avg_score = sum(q["relevance_score"] for q in self.questions) / total if total else 0

        print(f"\n📈 总体统计:")
        print(f"   问题总数: {total}")
        print(f"   成功: {success} / 失败: {total - success}")
        print(f"   平均响应时间: {avg_time:.2f}s")
        print(f"   平均相关性评分: {avg_score:.2f} / 5.0")

        # SLA 达标率
        sla_targets = [
            ("≤ 5秒", 5),
            ("≤ 10秒", 10),
            ("≤ 30秒", 30),
        ]
        print(f"\n⏱ 响应时间 SLA:")
        for label, threshold in sla_targets:
            count = sum(1 for t in self.timing_results if t <= threshold)
            pct = count / len(self.timing_results) * 100
            bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
            print(f"   {label}: {bar} {pct:.0f}% ({count}/{len(self.timing_results)})")

        # 按类别统计
        print(f"\n📂 按类别统计:")
        categories = {}
        for q in self.questions:
            cat = q["category"]
            if cat not in categories:
                categories[cat] = {"total": 0, "success": 0, "scores": [], "times": []}
            categories[cat]["total"] += 1
            if q["success"]:
                categories[cat]["success"] += 1
            categories[cat]["scores"].append(q["relevance_score"])
            categories[cat]["times"].append(q["elapsed_seconds"])

        cat_names = {
            "fact_extraction": "事实提取",
            "summarization": "总结归纳",
            "critical_analysis": "批判分析",
            "cross_reference": "交叉引用",
        }
        for cat, stats in sorted(categories.items()):
            avg_s = sum(stats["scores"]) / len(stats["scores"]) if stats["scores"] else 0
            avg_t = sum(stats["times"]) / len(stats["times"]) if stats["times"] else 0
            name = cat_names.get(cat, cat)
            print(f"   {name}: {stats['success']}/{stats['total']} 通过 | "
                  f"平均评分 {avg_s:.1f} | 平均响应 {avg_t:.2f}s")

        # 逐题详情
        print(f"\n📋 逐题详情:")
        for q in self.questions:
            status = "✅" if q["success"] else "❌"
            bar = "█" * int(q["relevance_score"] * 4) + "░" * (20 - int(q["relevance_score"] * 4))
            print(f"\n   {status} [{q['id']}] {q['question'][:60]}")
            print(f"      类别: {q['category']} | 时间: {q['elapsed_seconds']:.2f}s | "
                  f"评分: {q['relevance_score']}/5.0")
            print(f"      相关度: {bar}")
            print(f"      回答预览: {q['answer_preview']}")
            if q["error"]:
                print(f"      错误: {q['error']}")

        # 边界测试
        if self.boundary_tests:
            print(f"\n🧪 边界测试:")
            for bt in self.boundary_tests:
                status = "✅" if bt["status_code"] in (200, 400, 404, 422) else "❌"
                print(f"   {status} {bt['name']}: {bt['status_code']} ({bt['elapsed_seconds']:.2f}s)")

        # 综合评分
        print(f"\n🏆 综合评分:")
        final_score = (success / total * 40 if total else 0) + min(avg_score * 10, 40) + max(0, 20 - avg_time)
        final_score = min(100, final_score)
        grade = "A" if final_score >= 90 else "B" if final_score >= 75 else "C" if final_score >= 60 else "D"
        print(f"   得分: {final_score:.1f}/100 (等级 {grade})")
        print(f"   通过率: {success}/{total} + 相关性: {avg_score:.1f}/5 + 速度: {avg_time:.1f}s")
        print("=" * 70)


# ---------------------------------------------------------------------------
# 主测试流程
# ---------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("🧪 AI 问答助手场景化测试")
    print("   标准问题集 × PDF 场景回答相关性 × 响应速度")
    print("=" * 70)

    results = TestResults()

    # ── 步骤 1: 健康检查 ──
    print("\n1️⃣  健康检查...")
    try:
        resp = _get("/health", None)
        if resp.get("status") == "ok":
            print("    ✅ 后端服务正常")
        else:
            print(f"    ❌ 后端状态异常: {resp}")
            sys.exit(1)
    except Exception as e:
        print(f"    ❌ 后端服务未启动: {e}")
        sys.exit(1)

    # ── 步骤 2: 认证 ──
    print("\n2️⃣  认证...")
    token = None
    try:
        resp = _get("/api/papers/", None)
        if resp.get("code") == 0:
            print("    ✅ 测试模式已启用（无需 token）")
            token = None
        else:
            print("    ⚠️  测试模式未启用，尝试登录...")
            # 从环境变量或配置读取
            import os
            email = os.getenv("TEST_EMAIL", "test@example.com")
            password = os.getenv("TEST_PASSWORD", "your_password")
            resp = _post("/api/user/login", {"email": email, "password": password})
            if resp.get("code") != 0:
                print(f"    ❌ 登录失败: {resp.get('msg')}")
                sys.exit(1)
            token = resp["data"]["token"]
            print(f"    ✅ 登录成功")
    except Exception as e:
        print(f"    ❌ 认证失败: {e}")
        sys.exit(1)

    # ── 步骤 3: 获取论文 ──
    print("\n3️⃣  获取论文列表...")
    resp = _get("/api/papers/", token)
    papers = resp.get("data", [])
    if not papers:
        print("    ❌ 账号下无论文，请先上传并解析一篇论文")
        sys.exit(1)

    # 筛选 CONFIRMED 论文
    confirmed = [p for p in papers if p.get("status") == "CONFIRMED"]
    if not confirmed:
        print("    ⚠️  无 CONFIRMED 论文，使用第一篇论文")
        paper = papers[0]
    else:
        paper = confirmed[0]

    paper_id = paper["id"]
    print(f"    ✅ 使用论文: [{paper.get('status', '?')}] {paper['title'][:60]}...")

    # ── 步骤 4: 执行标准问题集测试 ──
    print(f"\n4️⃣  执行标准问题集测试 ({len(STANDARD_QUESTIONS)} 题)...")
    for i, q in enumerate(STANDARD_QUESTIONS, 1):
        print(f"\n    [{i}/{len(STANDARD_QUESTIONS)}] [{q.id}] ({q.category}) {q.question[:60]}...")
        start = time.time()
        resp = _post(f"/api/papers/{paper_id}/ask", {"question": q.question}, token)
        elapsed = time.time() - start

        code = resp.get("code")
        if code == 0:
            answer = resp.get("data", {}).get("answer", "")
            sources = resp.get("data", {}).get("sources", [])
            results.add_question_result(q, answer, sources, elapsed, success=True)
            print(f"       ✅ {elapsed:.2f}s | 回答长度: {len(answer)} | 来源: {len(sources)}")
        else:
            results.add_question_result(q, "", [], elapsed, success=False,
                                        error_msg=resp.get("msg", "未知错误"))
            print(f"       ❌ ({resp.get('code')}): {resp.get('msg')}")

    # ── 步骤 5: 边界测试 ──
    print(f"\n5️⃣  边界测试...")

    # 5a. 空问题
    start = time.time()
    resp = _post(f"/api/papers/{paper_id}/ask", {"question": ""}, token)
    elapsed = time.time() - start
    results.add_boundary_result("空问题", resp.get("code", 0), resp, elapsed)
    print(f"    {'✅' if resp.get('code') in (0, 400, 422) else '❌'} 空问题: code={resp.get('code')} ({elapsed:.2f}s)")

    # 5b. 不存在的论文
    start = time.time()
    resp = _post("/api/papers/nonexistent_id_12345/ask", {"question": "test"}, token)
    elapsed = time.time() - start
    results.add_boundary_result("不存在论文", resp.get("code", 0), resp, elapsed)
    print(f"    {'✅' if resp.get('code') in (404, 401) else '❌'} 不存在论文: code={resp.get('code')} ({elapsed:.2f}s)")

    # 5c. 超长问题（超过 2000 字）
    long_question = "请回答" + "测试" * 1500
    start = time.time()
    resp = _post(f"/api/papers/{paper_id}/ask", {"question": long_question}, token)
    elapsed = time.time() - start
    results.add_boundary_result("超长问题", resp.get("code", 0), resp, elapsed)
    print(f"    {'✅' if resp.get('code') in (0, 400, 422) else '❌'} 超长问题: code={resp.get('code')} ({elapsed:.2f}s)")

    # 5d. 特殊字符问题
    special_question = "!@#$%^&*()_+{}:\"<>?/.,';][=-`~"
    start = time.time()
    resp = _post(f"/api/papers/{paper_id}/ask", {"question": special_question}, token)
    elapsed = time.time() - start
    results.add_boundary_result("特殊字符", resp.get("code", 0), resp, elapsed)
    print(f"    {'✅' if resp.get('code') == 0 else '❌'} 特殊字符: code={resp.get('code')} ({elapsed:.2f}s)")

    # ── 步骤 6: 打印报告 ──
    results.print_report()

    # ── 返回测试结果 ──
    success_rate = sum(1 for q in results.questions if q["success"]) / len(results.questions) if results.questions else 0
    return success_rate >= 0.7  # 70% 通过率视为合格


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
