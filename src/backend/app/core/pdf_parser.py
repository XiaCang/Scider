"""
PDF Parser — 基于 PyMuPDF 提取论文纯文本。

所有提取任务在本模块中完成，上层 Celery 任务只需要调一个函数即可。
"""

import logging

logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_path: str, max_chars: int = 0) -> str:
    """
    从 PDF 文件中提取纯文本。

    Args:
        pdf_path: PDF 文件的绝对路径。
        max_chars: 最大字符数（0 表示不限制）。

    Returns:
        提取出的纯文本字符串。如果提取结果为空则返回空字符串。
    """
    import fitz  # PyMuPDF

    try:
        doc = fitz.open(pdf_path)
    except Exception as exc:
        logger.error("无法打开 PDF 文件 %s: %s", pdf_path, exc)
        return ""

    pages_text: list[str] = []
    total = 0

    for page_num, page in enumerate(doc, start=1):
        text = page.get_text()
        if not text:
            continue
        if max_chars > 0:
            remaining = max_chars - total
            if remaining <= 0:
                break
            pages_text.append(text[:remaining])
            total += len(text[:remaining])
        else:
            pages_text.append(text)
            total += len(text)

    doc.close()

    result = "\n".join(pages_text).strip()
    logger.info(
        "PDF 文本提取完成: pages=%d, chars=%d, path=%s",
        len(pages_text),
        len(result),
        pdf_path,
    )
    return result
