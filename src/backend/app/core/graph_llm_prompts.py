"""
LLM Prompts for Graph Structure Generation and Clustering.

用于让 LLM 分析论文集合，生成主题聚类和语义关系边。
"""

GRAPH_CLUSTERING_SYSTEM_PROMPT = """\
你是一个学术论文分析专家，擅长识别研究主题、领域关系和论文之间的语义联系。

你的任务是分析用户提供的论文集合（包含标题、作者、年份和四要素），完成以下工作：

1. **主题聚类**：根据研究领域、方法论、应用场景等维度，将论文分为 2-6 个主题簇（cluster）
   - 每个簇需要一个简洁的中文名称（如"深度学习"、"自然语言处理"、"计算机视觉"）
   - 每篇论文归属到最相关的一个簇

2. **语义关系边**：识别论文之间的语义关系，生成连边
   - 关系类型包括：
     - "extends"（扩展/改进）：B 论文改进或扩展了 A 论文的方法
     - "applies"（应用）：B 论文将 A 论文的方法应用到新场景
     - "compares"（对比）：两篇论文研究相似问题，可对比
     - "related"（相关）：研究主题相关但方向不同
   - 每篇论文最多连接 3-5 条边
   - 优先连接同簇内的论文，但也可跨簇连接

输出格式要求：
- 仅输出一个合法的 JSON 对象，不要包含任何额外说明文字、代码块标记
- JSON 结构如下：

{
  "clusters": [
    {
      "id": "cluster_0",
      "name": "主题名称",
      "description": "主题描述（50字以内）",
      "paper_ids": ["paper_id_1", "paper_id_2"]
    }
  ],
  "edges": [
    {
      "source": "paper_id_1",
      "target": "paper_id_2",
      "relation_type": "extends",
      "reason": "简短说明关系原因（30字以内）"
    }
  ]
}

注意事项：
- 所有 paper_id 必须来自输入的论文列表
- 每篇论文必须且只能属于一个簇
- 边的数量建议为论文数量的 1.5-2 倍
- 关系原因要具体，避免泛泛而谈
"""


def build_graph_clustering_user_prompt(papers: list[dict]) -> str:
    """
    构造 User Prompt，将论文列表格式化为 LLM 可理解的文本。

    Args:
        papers: 论文列表，每篇包含 paper_id, title, authors, year, key_points

    Returns:
        格式化后的 User Prompt 字符串
    """
    if not papers:
        return "论文列表为空，无法进行聚类分析。"

    lines = ["请分析以下论文集合，生成主题聚类和语义关系边：\n"]

    for i, p in enumerate(papers, 1):
        paper_id = p.get("paper_id", "")
        title = p.get("title", "未知标题")
        authors = p.get("authors", "")
        year = p.get("year", "")
        kp = p.get("key_points", {})

        lines.append(f"【论文 {i}】")
        lines.append(f"ID: {paper_id}")
        lines.append(f"标题: {title}")
        if authors:
            lines.append(f"作者: {authors}")
        if year:
            lines.append(f"年份: {year}")

        bg = kp.get("background", "").strip()
        method = kp.get("method", "").strip()
        innov = kp.get("innovation", "").strip()
        concl = kp.get("conclusion", "").strip()

        if bg:
            lines.append(f"研究背景: {bg}")
        if method:
            lines.append(f"研究方法: {method}")
        if innov:
            lines.append(f"创新点: {innov}")
        if concl:
            lines.append(f"研究结论: {concl}")

        lines.append("")

    lines.append(f"共 {len(papers)} 篇论文，请生成聚类和关系边的 JSON 输出。")

    return "\n".join(lines)
