"""
测试 Semantic Scholar 上下游（参考文献/引证文献）服务。

用法（从 src/backend 目录运行）：
    python -m scripts.test_citation

可传入论文标题或 DOI 作为参数：
    python -m scripts.test_citation "K-Search: LLM Kernel Generation via Co-Evolving Intrinsic World Model"
    python -m scripts.test_citation "DOI:10.48550/arXiv.2406.06754"
"""

import sys
import os
from pathlib import Path

# 确保可以导入 backend 模块
backend_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_root))

from app.services import semantic_scholar


def resolve_semantic_id(title_or_doi: str) -> str | None:
    """模拟后端 _resolve_semantic_id 逻辑：有 DOI 前缀则直查，否则按标题搜索。"""
    if title_or_doi.startswith("DOI:"):
        print(f"[resolve] 直接用 DOI 标识: {title_or_doi}")
        return title_or_doi

    print(f"[resolve] 无 DOI，按标题搜索: {title_or_doi[:60]}...")
    result = semantic_scholar.search_papers(title_or_doi, limit=3)
    papers = result.get("data", [])
    if not papers:
        print("[resolve] 未搜索到任何论文")
        return None

    for i, p in enumerate(papers):
        print(f"  [{i}] {p.get('title', 'N/A')}  (semantic_id={p.get('semantic_id')})")

    s2_id = papers[0].get("semantic_id")
    if s2_id:
        print(f"[resolve] 命中第一篇: semantic_id={s2_id}")
        return s2_id

    print("[resolve] 搜索结果缺少 semantic_id")
    return None


def main():
    # 从命令行参数获取论文标识，默认使用测试标题
    paper = sys.argv[1] if len(sys.argv) > 1 else (
        "K-Search: LLM Kernel Generation via Co-Evolving Intrinsic World Model"
    )

    print("=" * 60)
    print("Semantic Scholar 上下游服务测试")
    print("=" * 60)

    # Step 1: 解析出 Semantic Scholar ID
    print(f"\n▶ Step 1: 解析论文标识")
    print(f"   输入: {paper}")
    semantic_id = resolve_semantic_id(paper)
    if not semantic_id:
        print("✗ 无法获取 Semantic Scholar ID，终止测试")
        sys.exit(1)
    print(f"  ✓ 得到 semantic_id: {semantic_id}")

    # Step 2: 获取参考文献（上游）
    print(f"\n▶ Step 2: 获取参考文献 (upstream / references)")
    try:
        refs = semantic_scholar.get_references(semantic_id)
        print(f"  ✓ 获取到 {len(refs)} 篇参考文献")
        for i, ref in enumerate(refs[:5], 1):
            print(f"    [{i}] {ref.get('title', 'N/A')}")
            print(f"        作者: {ref.get('authors', 'N/A')[:40]}")
            print(f"        年份: {ref.get('year')}  引用: {ref.get('citation_count')}")
        if len(refs) > 5:
            print(f"    ... 还有 {len(refs) - 5} 篇")
    except Exception as e:
        print(f"  ✗ 获取参考文献失败: {e}")

    # Step 3: 获取引证文献（下游）
    print(f"\n▶ Step 3: 获取引证文献 (downstream / citations)")
    try:
        cites = semantic_scholar.get_citations(semantic_id)
        print(f"  ✓ 获取到 {len(cites)} 篇引证文献")
        for i, cite in enumerate(cites[:5], 1):
            print(f"    [{i}] {cite.get('title', 'N/A')}")
            print(f"        作者: {cite.get('authors', 'N/A')[:40]}")
            print(f"        年份: {cite.get('year')}  引用: {cite.get('citation_count')}")
        if len(cites) > 5:
            print(f"    ... 还有 {len(cites) - 5} 篇")
    except Exception as e:
        print(f"  ✗ 获取引证文献失败: {e}")

    print(f"\n{'=' * 60}")
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
