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
