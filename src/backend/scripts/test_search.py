"""
测试 Semantic Scholar 论文搜索服务。

用法（从 src/backend 目录运行）：
    python -m scripts.test_search
    python -m scripts.test_search "transformer attention" --limit 5 --year-from 2023
"""

import argparse
import sys
from pathlib import Path

# 确保可以导入 backend 模块
backend_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_root))

from app.services import semantic_scholar


def fmt(p: dict) -> str:
    """格式化单篇论文信息为一行摘要。"""
    parts = [
        f"  [{p.get('year', '????')}] {p.get('title', 'N/A')}",
    ]
    authors = p.get("authors", "")
    if authors:
        # 取前两个作者 + et al.
        author_list = authors.split(", ")
        author_str = author_list[0]
        if len(author_list) > 2:
            author_str += " et al."
        elif len(author_list) == 2:
            author_str += f" & {author_list[1]}"
        parts.append(f"      作者: {author_str}")
    if p.get("venue"):
        parts.append(f"      来源: {p['venue']}")
    if p.get("citation_count"):
        parts.append(f"      引用: {p['citation_count']}")
    if p.get("source_type"):
        parts.append(f"      类型: {p['source_type']}")
    if p.get("abstract"):
        abstract_preview = p["abstract"][:120].replace("\n", " ") + ("..." if len(p["abstract"]) > 120 else "")
        parts.append(f"      摘要: {abstract_preview}")
    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser(description="测试 Semantic Scholar 论文搜索")
    parser.add_argument("query", nargs="?", default="K-Search LLM kernel generation",
                        help="搜索关键词")
    parser.add_argument("--limit", type=int, default=5, help="返回结果数")
    parser.add_argument("--offset", type=int, default=0, help="分页偏移")
    parser.add_argument("--year-from", type=int, default=None, help="年份下限")
    parser.add_argument("--year-to", type=int, default=None, help="年份上限")
    parser.add_argument("--source-type", choices=["conference", "journal", "arXiv"], default=None,
                        help="来源类型筛选")
    parser.add_argument("--sort", choices=["relevance", "citations", "date"], default="relevance",
                        help="排序方式")
    args = parser.parse_args()

    print("=" * 60)
    print("Semantic Scholar 论文搜索测试")
    print("=" * 60)
    print(f"\n查询: {args.query}")
    print(f"参数: limit={args.limit} offset={args.offset} "
          f"year={args.year_from or ''}-{args.year_to or ''} "
          f"source_type={args.source_type or '全部'} "
          f"sort={args.sort}")

    # 执行搜索
    print(f"\n▶ 正在搜索...")
    try:
        result = semantic_scholar.search_papers(
            args.query,
            offset=args.offset,
            limit=args.limit,
            year_from=args.year_from,
            year_to=args.year_to,
            source_type=args.source_type,
            sort=args.sort,
        ) 
    except RuntimeError as e:
        print(f"\n✗ 搜索失败: {e}")
        sys.exit(1)

    total = result.get("total", 0)
    papers = result.get("data", [])

    print(f"\n✓ 搜索完成: 共 {total} 条结果，返回 {len(papers)} 条")
    print()

    if not papers:
        print("(无匹配结果)")
    else:
        for i, paper in enumerate(papers, 1):
            print(f"── [{i}/{len(papers)}] ─{'─' * 50}")
            print(fmt(paper))
            print()

    # 简单统计
    if papers:
        years = [p.get("year") for p in papers if p.get("year")]
        if years:
            print(f"  年份范围: {min(years)} – {max(years)}")
        venues = [p.get("venue") for p in papers if p.get("venue")]
        if venues:
            print(f"  来源分布: {', '.join(set(venues))}")
        types = [p.get("source_type") for p in papers if p.get("source_type")]
        if types:
            from collections import Counter
            type_counts = Counter(types)
            print(f"  类型分布: {', '.join(f'{k}={v}' for k, v in type_counts.items())}")

    print(f"\n{'=' * 60}")
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
