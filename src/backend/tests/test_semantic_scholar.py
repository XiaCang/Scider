"""
Unit tests for app.services.semantic_scholar

覆盖：
  - 基础检索（分页信封、参数传递、字段格式化）
  - 年份筛选（year_from / year_to）
  - 来源类型筛选（source_type，客户端过滤）
  - 排序（citations / date，客户端排序）
  - 来源类型推断（_source_type）
  - 429 限流重试
  - 超过最大重试次数后抛出 RuntimeError
  - get_references / get_citations
"""

import pytest
from unittest.mock import patch, MagicMock
from app.services import semantic_scholar


# ---------------------------------------------------------------------------
# 测试数据
# ---------------------------------------------------------------------------

def _paper(pid, title, year, venue, pub_types=None, doi=None, citations=0):
    return {
        "paperId": pid,
        "title": title,
        "authors": [{"name": "Author"}],
        "year": year,
        "venue": venue,
        "abstract": "abstract",
        "externalIds": {"DOI": doi} if doi else {},
        "citationCount": citations,
        "publicationTypes": pub_types or [],
    }


PAPERS = [
    _paper("p1", "Transformer", 2017, "NeurIPS", ["Conference"], "10.1/t", 90000),
    _paper("p2", "BERT",        2019, "ACL",     ["Conference"], "10.1/b", 50000),
    _paper("p3", "GPT-4",       2023, "arXiv",   ["JournalArticle"], "10.1/g", 10000),
    _paper("p4", "Old Paper",   2010, "Nature",  ["JournalArticle"], "10.1/o", 500),
]

MOCK_RESPONSE = {"total": len(PAPERS), "data": PAPERS}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _mock_ctx(json_data):
    """返回一个模拟 httpx.Client 上下文管理器，固定返回 json_data。"""
    resp = MagicMock()
    resp.status_code = 200
    resp.headers = {}
    resp.raise_for_status.return_value = None
    resp.json.return_value = json_data

    client = MagicMock()
    client.get.return_value = resp

    ctx = MagicMock()
    ctx.__enter__.return_value = client
    ctx.__exit__.return_value = False
    return ctx, client


@pytest.fixture
def patch_search():
    """仅激活 mock，不返回 client（用于不需要检查调用参数的测试）。"""
    ctx, _ = _mock_ctx(MOCK_RESPONSE)
    with patch("app.services.semantic_scholar.httpx.Client", return_value=ctx):
        yield


@pytest.fixture
def mock_search():
    """激活 mock 并返回 client（用于需要检查 call_args 的测试）。"""
    ctx, client = _mock_ctx(MOCK_RESPONSE)
    with patch("app.services.semantic_scholar.httpx.Client", return_value=ctx):
        yield client


# ---------------------------------------------------------------------------
# 基础检索
# ---------------------------------------------------------------------------

@pytest.mark.usefixtures("patch_search")
def test_search_pagination_envelope():
    result = semantic_scholar.search_papers("transformer")
    assert result["total"] == len(PAPERS)
    assert result["offset"] == 0
    assert result["limit"] == 10


def test_search_passes_params(mock_search):
    semantic_scholar.search_papers("attention", offset=20, limit=5)
    _, kw = mock_search.get.call_args
    p = kw["params"]
    assert p["query"] == "attention"
    assert p["offset"] == 20
    assert p["limit"] == 5


@pytest.mark.usefixtures("patch_search")
def test_fmt_fields():
    result = semantic_scholar.search_papers("test")
    p = result["data"][0]
    assert p["semantic_id"] == "p1"
    assert p["authors"] == "Author"
    assert p["doi"] == "10.1/t"
    assert p["citation_count"] == 90000


# ---------------------------------------------------------------------------
# 年份筛选
# ---------------------------------------------------------------------------

def test_year_filter_both(mock_search):
    semantic_scholar.search_papers("x", year_from=2018, year_to=2022)
    _, kw = mock_search.get.call_args
    assert kw["params"]["year"] == "2018-2022"


def test_year_filter_from_only(mock_search):
    semantic_scholar.search_papers("x", year_from=2020)
    _, kw = mock_search.get.call_args
    assert kw["params"]["year"] == "2020-"


def test_year_filter_to_only(mock_search):
    semantic_scholar.search_papers("x", year_to=2019)
    _, kw = mock_search.get.call_args
    assert kw["params"]["year"] == "-2019"


def test_no_year_filter_no_param(mock_search):
    semantic_scholar.search_papers("x")
    _, kw = mock_search.get.call_args
    assert "year" not in kw["params"]


# ---------------------------------------------------------------------------
# 来源类型筛选（客户端）
# ---------------------------------------------------------------------------

@pytest.mark.usefixtures("patch_search")
def test_source_type_conference():
    result = semantic_scholar.search_papers("x", source_type="conference")
    types = {p["source_type"] for p in result["data"]}
    assert types == {"conference"}


@pytest.mark.usefixtures("patch_search")
def test_source_type_arxiv():
    result = semantic_scholar.search_papers("x", source_type="arXiv")
    assert all(p["source_type"] == "arXiv" for p in result["data"])


@pytest.mark.usefixtures("patch_search")
def test_source_type_journal():
    result = semantic_scholar.search_papers("x", source_type="journal")
    assert all(p["source_type"] == "journal" for p in result["data"])


# ---------------------------------------------------------------------------
# 来源类型推断
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("venue,pub_types,expected", [
    ("arXiv",           [],                  "arXiv"),
    ("NeurIPS",         ["Conference"],      "conference"),
    ("ICML proceedings",[], "conference"),
    ("Nature journal",  [],                  "journal"),
    ("",                ["JournalArticle"],  "journal"),
    ("",                [],                  "other"),
])
def test_source_type_inference(venue, pub_types, expected):
    p = {"venue": venue, "publicationTypes": pub_types}
    assert semantic_scholar._source_type(p) == expected


# ---------------------------------------------------------------------------
# 排序（客户端）
# ---------------------------------------------------------------------------

@pytest.mark.usefixtures("patch_search")
def test_sort_by_citations():
    result = semantic_scholar.search_papers("x", sort="citations")
    counts = [p["citation_count"] for p in result["data"]]
    assert counts == sorted(counts, reverse=True)


@pytest.mark.usefixtures("patch_search")
def test_sort_by_date():
    result = semantic_scholar.search_papers("x", sort="date")
    years = [p["year"] for p in result["data"]]
    assert years == sorted(years, reverse=True)


# ---------------------------------------------------------------------------
# 重试与限流
# ---------------------------------------------------------------------------

def test_retry_429_then_success():
    ok_resp = MagicMock()
    ok_resp.status_code = 200
    ok_resp.headers = {}
    ok_resp.raise_for_status.return_value = None
    ok_resp.json.return_value = MOCK_RESPONSE

    rate_resp = MagicMock()
    rate_resp.status_code = 429
    rate_resp.headers = {"Retry-After": "0"}

    client = MagicMock()
    client.get.side_effect = [rate_resp, ok_resp]

    ctx = MagicMock()
    ctx.__enter__.return_value = client
    ctx.__exit__.return_value = False

    with patch("app.services.semantic_scholar.httpx.Client", return_value=ctx):
        with patch("app.services.semantic_scholar.time.sleep"):
            result = semantic_scholar.search_papers("retry")
    assert result["total"] == len(PAPERS)


def test_raises_after_max_retries():
    rate_resp = MagicMock()
    rate_resp.status_code = 429
    rate_resp.headers = {"Retry-After": "0"}

    client = MagicMock()
    client.get.return_value = rate_resp

    ctx = MagicMock()
    ctx.__enter__.return_value = client
    ctx.__exit__.return_value = False

    with patch("app.services.semantic_scholar.httpx.Client", return_value=ctx):
        with patch("app.services.semantic_scholar.time.sleep"):
            with pytest.raises(RuntimeError, match="unreachable"):
                semantic_scholar.search_papers("fail")


# ---------------------------------------------------------------------------
# get_references / get_citations
# ---------------------------------------------------------------------------

REF_RESPONSE = {
    "data": [
        {"citedPaper": _paper("r1", "Ref Paper", 2015, "ICML", doi="10.1/r")},
        {"citedPaper": None},  # 应被过滤掉
    ]
}

CITE_RESPONSE = {
    "data": [
        {"citingPaper": _paper("c1", "Citing Paper", 2021, "ICLR", doi="10.1/c")},
    ]
}


def test_get_references():
    ctx, _ = _mock_ctx(REF_RESPONSE)
    with patch("app.services.semantic_scholar.httpx.Client", return_value=ctx):
        refs = semantic_scholar.get_references("p1")
    assert len(refs) == 1
    assert refs[0]["semantic_id"] == "r1"


def test_get_citations():
    ctx, _ = _mock_ctx(CITE_RESPONSE)
    with patch("app.services.semantic_scholar.httpx.Client", return_value=ctx):
        cites = semantic_scholar.get_citations("p1")
    assert len(cites) == 1
    assert cites[0]["semantic_id"] == "c1"
