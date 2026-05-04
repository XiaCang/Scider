"""
semantic_scholar.py — Semantic Scholar Graph API 客户端

提供：
  - search_papers()   关键词检索，支持年份/来源类型筛选和排序
  - get_references()  获取某篇论文的参考文献（上游）
  - get_citations()   获取引用某篇论文的文献（下游）

所有请求均通过 _request() 统一处理重试和限流（429）。
"""

import logging
import time
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_BASE = "https://api.semanticscholar.org/graph/v1"
# 检索接口需要的字段（含 publicationTypes 用于来源类型判断）
_SEARCH_FIELDS = "paperId,title,authors,year,venue,abstract,externalIds,citationCount,publicationTypes,openAccessPdf"
# 参考文献/引用接口字段（不需要 publicationTypes）
_REF_FIELDS = "paperId,title,authors,year,venue,abstract,externalIds,citationCount"

_MAX_RETRIES = 5
_RETRY_DELAY = 5   # 首次重试等待秒数，指数退避（无 Key 时 SS 限额严格）
_MIN_INTERVAL = 1.1  # 两次请求之间的最小间隔（秒），避免触发速率限制

# sort 参数 → 用于 Python 排序的字段名（None 表示使用 SS 默认相关度排序）
_SORT_FIELD_MAP = {
    "relevance": None,
    "citations": "citationCount",
    "date": "year",
}


# ---------------------------------------------------------------------------
# 内部工具
# ---------------------------------------------------------------------------

def _headers() -> dict:
    """构造请求头，若配置了 API Key 则附加（提升速率限制）。"""
    h = {"User-Agent": "Scider/1.0 (research assistant)"}
    if settings.SEMANTIC_SCHOLAR_API_KEY:
        h["x-api-key"] = settings.SEMANTIC_SCHOLAR_API_KEY
    return h


def _request(method: str, url: str, **kwargs) -> dict:
    """
    带重试和限流处理的 HTTP 请求封装。

    - 每次请求前等待 _MIN_INTERVAL 秒，避免匿名限额触发 429
    - 遇到 429 时读取 Retry-After 头并等待（指数退避兜底）
    - 其他网络错误按指数退避重试，最多 _MAX_RETRIES 次
    - HTTP 4xx/5xx（非 429）直接抛出 RuntimeError
    """
    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        time.sleep(_MIN_INTERVAL)  # 主动限速，防止匿名 429
        try:
            with httpx.Client(timeout=2000, headers=_headers()) as client:
                r = getattr(client, method)(url, **kwargs)

                if r.status_code == 429:
                    # 优先使用服务端返回的等待时间，兜底用指数退避
                    wait = int(r.headers.get("Retry-After", _RETRY_DELAY * (2 ** attempt)))
                    logger.warning(
                        "SS 429 rate-limited attempt=%d/%d retry_after=%ds url=%s",
                        attempt + 1, _MAX_RETRIES, wait, url,
                    )
                    time.sleep(wait)
                    continue

                r.raise_for_status()
                logger.debug("SS %s %s → %d", method.upper(), url, r.status_code)
                return r.json()

        except httpx.HTTPStatusError as e:
            logger.error("SS HTTP error %s url=%s", e.response.status_code, url)
            raise RuntimeError(str(e)) from e
        except Exception as e:
            wait = _RETRY_DELAY * (2 ** attempt)
            logger.warning(
                "SS request error attempt=%d/%d error=%s retry_in=%ds",
                attempt + 1, _MAX_RETRIES, e, wait,
            )
            last_exc = e
            time.sleep(wait)

    raise RuntimeError(f"Semantic Scholar unreachable after {_MAX_RETRIES} attempts: {last_exc}")


def _source_type(p: dict) -> str:
    """
    根据 venue 字符串和 publicationTypes 推断来源类型。
    返回值：'arXiv' | 'conference' | 'journal' | 'other'
    """
    venue = (p.get("venue") or "").lower()
    pub_types = [t.lower() for t in (p.get("publicationTypes") or [])]

    if "arxiv" in venue or "arxiv" in pub_types:
        return "arXiv"
    if any(k in venue for k in ("conference", "proceedings", "workshop", "symposium")):
        return "conference"
    if any(k in venue for k in ("journal", "transactions", "letters", "review")):
        return "journal"
    if "journalarticle" in pub_types:
        return "journal"
    if "conference" in pub_types:
        return "conference"
    return "other"


def _fmt(p: dict) -> dict:
    """将 Semantic Scholar 原始论文对象格式化为统一的响应结构。"""
    return {
        "semantic_id": p.get("paperId"),
        "title": p.get("title"),
        "authors": ", ".join(a["name"] for a in (p.get("authors") or [])),
        "year": p.get("year"),
        "venue": p.get("venue"),
        "source_type": _source_type(p),
        "abstract": p.get("abstract"),
        "doi": (p.get("externalIds") or {}).get("DOI"),
        "citation_count": p.get("citationCount"),
        "pdf_url": (p.get("openAccessPdf") or {}).get("url"),
    }


# ---------------------------------------------------------------------------
# 公开接口
# ---------------------------------------------------------------------------

def search_papers(
    query: str,
    offset: int = 0,
    limit: int = 10,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    source_type: Optional[str] = None,  # "conference" | "journal" | "arXiv"
    sort: str = "relevance",            # "relevance" | "citations" | "date"
) -> dict:
    """
    调用 Semantic Scholar /paper/search 接口进行关键词检索。

    年份筛选由 SS API 原生支持；来源类型筛选和非相关度排序在客户端完成。

    Returns:
        {"total": int, "offset": int, "limit": int, "data": [Paper, ...]}
    """
    params: dict = {"query": query, "offset": offset, "limit": limit, "fields": _SEARCH_FIELDS}

    if year_from or year_to:
        lo = str(year_from) if year_from else ""
        hi = str(year_to) if year_to else ""
        params["year"] = f"{lo}-{hi}"
        logger.debug("search year filter=%s", params["year"])

    logger.info("SS search query=%r offset=%d limit=%d source_type=%s sort=%s", query, offset, limit, source_type, sort)
    raw = _request("get", f"{_BASE}/paper/search", params=params)
    items = [_fmt(p) for p in raw.get("data", [])]

    # SS API 不支持按来源类型过滤，在客户端过滤
    if source_type:
        before = len(items)
        items = [p for p in items if p["source_type"].lower() == source_type.lower()]
        logger.debug("source_type filter=%s before=%d after=%d", source_type, before, len(items))

    # 相关度排序由 SS 默认保证；citations/date 在客户端排序
    sort_key = _SORT_FIELD_MAP.get(sort)
    if sort_key:
        items.sort(key=lambda p: (p.get(sort_key) or 0), reverse=True)
        logger.debug("client sort by=%s", sort_key)

    logger.info("SS search done total=%d returned=%d", raw.get("total", 0), len(items))
    return {"total": raw.get("total", 0), "offset": offset, "limit": limit, "data": items}


def get_references(semantic_id: str) -> list[dict]:
    """
    获取论文的参考文献列表（该论文引用的文献，即上游）。

    Args:
        semantic_id: Semantic Scholar Paper ID
    Returns:
        格式化后的论文列表
    """
    logger.info("SS get_references semantic_id=%s", semantic_id)
    raw = _request(
        "get",
        f"{_BASE}/paper/{semantic_id}/references",
        params={"fields": _REF_FIELDS, "limit": 100},
    )
    refs = [_fmt(r["citedPaper"]) for r in raw.get("data", []) if r.get("citedPaper")]
    logger.info("SS get_references done semantic_id=%s count=%d", semantic_id, len(refs))
    return refs


def get_citations(semantic_id: str) -> list[dict]:
    """
    获取引用该论文的文献列表（下游）。

    Args:
        semantic_id: Semantic Scholar Paper ID
    Returns:
        格式化后的论文列表
    """
    logger.info("SS get_citations semantic_id=%s", semantic_id)
    raw = _request(
        "get",
        f"{_BASE}/paper/{semantic_id}/citations",
        params={"fields": _REF_FIELDS, "limit": 100},
    )
    cites = [_fmt(r["citingPaper"]) for r in raw.get("data", []) if r.get("citingPaper")]
    logger.info("SS get_citations done semantic_id=%s count=%d", semantic_id, len(cites))
    return cites
