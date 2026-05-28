import re
from typing import List

import bleach

ALLOWED_TAGS = [
    "p",
    "br",
    "strong",
    "em",
    "ul",
    "ol",
    "li",
    "a",
    "code",
    "pre",
    "h1",
    "h2",
    "h3",
    "img",
]
ALLOWED_ATTRS = {
    "a": ["href", "title", "rel"],
    "img": ["src", "alt", "title", "width", "height"],
}


def sanitize_html(raw_html: str) -> str:
    """使用 bleach 清洗 HTML，返回安全的 HTML 字符串。"""
    if not raw_html:
        return ""
    cleaned = bleach.clean(raw_html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)
    # 强制给外链 a 添加 rel="nofollow" target="_blank"
    cleaned = re.sub(r'<a([^>]+?)href=[\"\'](http[^\"\']+)[\"\']([^>]*)>',
                     r'<a\1href="\2" rel="nofollow" target="_blank"\3>',
                     cleaned, flags=re.IGNORECASE)
    return cleaned


def html_to_text(html: str) -> str:
    """从 HTML 抽取纯文本，压缩空白，用作全文索引或展示摘要。"""
    if not html:
        return ""
    text = bleach.clean(html, tags=[], strip=True)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_image_srcs(html: str) -> List[str]:
    """从 HTML 中提取所有 <img> 的 src（按出现顺序）。"""
    if not html:
        return []
    # 简单正则提取 src，配合 bleach 保证已清洗
    pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
    return re.findall(pattern, html, flags=re.IGNORECASE)
