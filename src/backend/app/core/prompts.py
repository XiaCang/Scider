"""
Prompts — 用于大模型四要素提取的 System / User Prompt 模板。

四要素定义：
  background   —— 研究背景：论文研究的问题领域与动机
  methodology  —— 研究方法：所采用的技术路线、算法或实验设计
  innovation   —— 创新点：相较于已有工作的新贡献或关键突破
  conclusion   —— 研究结论：主要实验结果与最终结论
"""

EXTRACT_SYSTEM_PROMPT = """\
你是一个学术论文分析专家。
你的任务是从用户提供的论文文本中，准确提取以下信息，并以 JSON 格式输出：

**元数据字段：**
- title        （论文标题：从文本中提取，若已有则保持不变）
- authors      （作者列表：逗号分隔的字符串，如 "张三, 李四, Wang Wei"）
- year         （发表年份：整数，如 2024；若无法确定则填 null）
- source       （出处：期刊或会议名称，如 "Nature", "ICML 2024"；若无则填 null）

**四要素字段：**
- background   （研究背景：100 字以内，说明研究领域、问题和动机）
- methodology  （研究方法：100 字以内，说明技术路线、算法或实验设计）
- innovation   （创新点：100 字以内，说明相较于已有工作的新贡献）
- conclusion   （研究结论：100 字以内，说明主要实验结果和最终结论）

输出格式要求：
1. 仅输出一个合法的 JSON 对象，不要包含任何额外说明文字、代码块标记或换行符。
2. 所有字段必须存在；若原文中找不到相关信息，元数据字段填 null，四要素字段填"暂无相关信息"。
3. 每个四要素字段值不超过 200 个字符。

示例输出（格式参考，非真实内容）：
{"title":"...","authors":"...","year":2024,"source":"...","background":"...","methodology":"...","innovation":"...","conclusion":"..."}\
"""

_USER_TEMPLATE = """\
请根据以下论文文本提取四要素：

{text}
"""


QA_SYSTEM_PROMPT = """\
你是一位专业的学术研究助手，专门帮助用户深入理解和分析学术论文。

回答规则：
1. 仅基于所提供的论文正文和用户笔记作答；不得引用外部知识或对原文未提及的内容进行推测。
2. 若提供的内容不足以回答问题，请明确告知："根据现有内容，暂无法回答此问题"，并说明缺失的信息类型。
3. 引用具体段落时，请在括号内注明来源，例如：（论文正文）或（笔记·第X页）。
4. 使用与用户问题相同的语言作答：中文问题用中文回答，英文问题用英文回答。
5. 回答应简洁、精准，避免重复上下文中已明显可见的内容。\
"""

_QA_USER_TEMPLATE = """\
【论文信息】
标题：{title}
{authors_line}\
【论文正文摘录】
{fulltext}

【用户笔记】
{notes}

用户问题：{question}\
"""


def build_qa_user_prompt(
    title: str,
    authors: str | None,
    full_text: str | None,
    notes: list,
    question: str,
    max_chars: int = 6000,
) -> str:
    authors_line = f"作者：{authors}\n" if authors else ""

    if full_text and full_text.strip():
        truncated = full_text[:max_chars]
        if len(full_text) > max_chars:
            truncated += f"\n\n[正文已截断，仅展示前 {max_chars} 个字符]"
        fulltext = truncated
    else:
        fulltext = "（暂无，论文可能尚未完成解析）"

    if notes:
        lines = []
        for note in notes:
            location = f"第 {note.page_number} 页" if note.page_number else "位置不详"
            if note.selected_text:
                preview = note.selected_text[:120] + ("…" if len(note.selected_text) > 120 else "")
                lines.append(f"• [{location}] 选中原文：「{preview}」\n  笔记：{note.content}")
            else:
                lines.append(f"• [{location}] {note.content}")
        notes_str = "\n".join(lines)
    else:
        notes_str = "（暂无笔记）"

    return _QA_USER_TEMPLATE.format(
        title=title,
        authors_line=authors_line,
        fulltext=fulltext,
        notes=notes_str,
        question=question,
    )


GRAPH_QA_SYSTEM_PROMPT = """\
你是一位学术研究助手，基于用户提供的知识图谱中的论文集合回答问题。

回答规则：
1. 仅基于所提供的论文信息作答，不引用外部知识。
2. 回答中引用论文时，使用「《论文标题》」格式。
3. 若提供的内容不足以回答，明确告知并说明原因。
4. 使用与用户问题相同的语言作答。
5. 回答简洁精准，重点突出跨论文的关联与规律。\
"""

_GRAPH_QA_USER_TEMPLATE = """\
【知识图谱包含的论文集合】
{papers_summary}

{history}

用户问题：{question}\
"""


def build_graph_qa_user_prompt(
    papers: list[dict],
    question: str,
    history: list | None = None,
    max_chars_per_paper: int = 300,
    max_total_chars: int = 8000,
) -> str:
    lines = []
    total = 0
    for i, p in enumerate(papers, 1):
        kp = p.get("key_points") or {}
        parts = [f"{i}. 《{p.get('title', '未知标题')}》"]
        if p.get("authors"):
            parts.append(f"   作者：{p['authors']}")
        if p.get("year"):
            parts.append(f"   年份：{p['year']}")
        for label, key in [("背景", "background"), ("方法", "methodology"), ("创新", "innovation"), ("结论", "conclusion")]:
            val = kp.get(key) or ""
            if val:
                parts.append(f"   {label}：{val[:max_chars_per_paper]}")
        block = "\n".join(parts)
        if total + len(block) > max_total_chars:
            lines.append(f"[已截断，共 {len(papers)} 篇论文，仅展示前 {i-1} 篇]")
            break
        lines.append(block)
        total += len(block)

    # 构建对话历史
    history_str = ""
    if history:
        h_lines = []
        for h in history[-10:]:  # 最多保留最近 10 轮
            role_label = "用户" if h.role == "user" else "AI"
            # 截断过长的内容
            content = h.content[:300] + ("…" if len(h.content) > 300 else "")
            h_lines.append(f"{role_label}：{content}")
        if h_lines:
            history_str = "【对话历史】\n" + "\n".join(h_lines)

    return _GRAPH_QA_USER_TEMPLATE.format(
        papers_summary="\n\n".join(lines),
        history=history_str,
        question=question,
    )


def build_user_prompt(paper_text: str, max_chars: int = 8000) -> str:
    """
    构造 User Prompt，对超长文本进行截断以避免超出模型 Context 限制。

    Args:
        paper_text: 论文全文或摘要+正文拼接。
        max_chars:  送入模型的最大字符数（默认 8000）。

    Returns:
        格式化后的 User Prompt 字符串。
    """
    truncated = paper_text[:max_chars]
    if len(paper_text) > max_chars:
        truncated += "\n\n[文本已截断，仅供参考以上部分]"
    return _USER_TEMPLATE.format(text=truncated)
