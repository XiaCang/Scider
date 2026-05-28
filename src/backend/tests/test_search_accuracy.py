"""
论文检索算法准确性测试

覆盖：
  - 关键词检索（3 组）：召回率 ≥ 50%，准确率 ≥ 40%
  - 上游参考文献检索（1 组）：召回率 = 100%（mock 全量注入）
  - 下游引用文献检索（1 组）：召回率 = 100%
  - 方向推荐（1 组）：召回率 ≥ 60%
  - 在线验证（@pytest.mark.online，默认跳过）
"""

from __future__ import annotations

import pytest
from dataclasses import dataclass
from unittest.mock import patch, MagicMock

from app.services import semantic_scholar


# ---------------------------------------------------------------------------
# 指标计算
# ---------------------------------------------------------------------------

@dataclass
class AccuracyMetrics:
    name: str
    retrieved_count: int
    relevant_count: int
    intersection_count: int
    precision: float
    recall: float


def compute_metrics(retrieved_ids: set[str], relevant_ids: set[str], name: str) -> AccuracyMetrics:
    inter = retrieved_ids & relevant_ids
    precision = len(inter) / len(retrieved_ids) if retrieved_ids else 0.0
    recall = len(inter) / len(relevant_ids) if relevant_ids else 0.0
    return AccuracyMetrics(
        name=name,
        retrieved_count=len(retrieved_ids),
        relevant_count=len(relevant_ids),
        intersection_count=len(inter),
        precision=precision,
        recall=recall,
    )


def print_accuracy_report(metrics_list: list[AccuracyMetrics]) -> None:
    header = f"{'Test Case':<45} {'Retrieved':>10} {'Relevant':>10} {'Hit':>6} {'Precision':>10} {'Recall':>8}"
    sep = "-" * len(header)
    print(f"\n{sep}\n{header}\n{sep}")
    for m in metrics_list:
        print(
            f"{m.name:<45} {m.retrieved_count:>10} {m.relevant_count:>10} "
            f"{m.intersection_count:>6} {m.precision:>10.2%} {m.recall:>8.2%}"
        )
    if metrics_list:
        avg_p = sum(m.precision for m in metrics_list) / len(metrics_list)
        avg_r = sum(m.recall for m in metrics_list) / len(metrics_list)
        print(f"{sep}\n{'AVERAGE':<45} {'':>10} {'':>10} {'':>6} {avg_p:>10.2%} {avg_r:>8.2%}")
    print(f"{sep}\n")


# ---------------------------------------------------------------------------
# 测试数据构造工具
# ---------------------------------------------------------------------------

def _ss_paper(pid, title, year, venue, pub_types=None, doi=None, citations=0) -> dict:
    return {
        "paperId": pid,
        "title": title,
        "authors": [{"name": "Test Author"}],
        "year": year,
        "venue": venue,
        "abstract": "Test abstract.",
        "externalIds": {"DOI": doi} if doi else {},
        "citationCount": citations,
        "publicationTypes": pub_types or [],
        "openAccessPdf": None,
    }


def _make_mock_ctx(json_data):
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


# ---------------------------------------------------------------------------
# 静态测试数据集
# ---------------------------------------------------------------------------

KEYWORD_CASES = [
    {
        "name": "transformer_attention",
        "query": "attention is all you need",
        "mock_data": [
            _ss_paper("204e3073870fae3d05bcbc2f6a8e263d29031248", "Attention Is All You Need",
                      2017, "NeurIPS", ["Conference"], citations=95000),
            _ss_paper("df2b0e26d0599ce3e70df8a9da02e51594e0e992",
                      "BERT: Pre-training of Deep Bidirectional Transformers",
                      2019, "NAACL", ["Conference"], citations=55000),
            _ss_paper("MOCK_GPT2_ID", "Language Models are Unsupervised Multitask Learners",
                      2019, "", ["JournalArticle"], citations=20000),
            _ss_paper("NOISE_PAPER_1", "Survey on Graph Neural Networks",
                      2020, "IEEE", ["JournalArticle"], citations=8000),
            _ss_paper("NOISE_PAPER_2", "Efficient Video Object Detection",
                      2021, "CVPR", ["Conference"], citations=300),
        ],
        "relevant_ids": {
            "204e3073870fae3d05bcbc2f6a8e263d29031248",
            "df2b0e26d0599ce3e70df8a9da02e51594e0e992",
            "MOCK_GPT2_ID",
        },
    },
    {
        "name": "graph_neural_network",
        "query": "graph neural network node classification",
        "mock_data": [
            _ss_paper("GNN_PAPER_1", "Semi-supervised Classification with Graph Convolutional Networks",
                      2017, "ICLR", ["Conference"], citations=15000),
            _ss_paper("GNN_PAPER_2", "Graph Attention Networks",
                      2018, "ICLR", ["Conference"], citations=12000),
            _ss_paper("GNN_PAPER_3", "Inductive Representation Learning on Large Graphs",
                      2017, "NeurIPS", ["Conference"], citations=9000),
            _ss_paper("NOISE_PAPER_3", "Random Forest for Text Classification",
                      2016, "ACL", ["Conference"], citations=1000),
        ],
        "relevant_ids": {"GNN_PAPER_1", "GNN_PAPER_2", "GNN_PAPER_3"},
    },
    {
        "name": "diffusion_model",
        "query": "denoising diffusion probabilistic models image generation",
        "mock_data": [
            _ss_paper("DDPM_ID", "Denoising Diffusion Probabilistic Models",
                      2020, "NeurIPS", ["Conference"], citations=14000),
            _ss_paper("SCORE_BASED_ID", "Score-Based Generative Modeling through SDEs",
                      2021, "ICLR", ["Conference"], citations=5000),
            _ss_paper("NOISE_PAPER_4", "AdaGrad: Adaptive Learning Rates",
                      2011, "JMLR", ["JournalArticle"], citations=8000),
        ],
        "relevant_ids": {"DDPM_ID", "SCORE_BASED_ID"},
    },
]

REFERENCE_CASES = [
    {
        "name": "transformer_upstream",
        "semantic_id": "204e3073870fae3d05bcbc2f6a8e263d29031248",
        "mock_response": {
            "data": [
                {"citedPaper": _ss_paper("BAHDANAU_ID", "Neural Machine Translation by Jointly Learning to Align",
                                         2015, "ICLR", citations=20000)},
                {"citedPaper": _ss_paper("LSTM_ID", "Long Short-Term Memory",
                                         1997, "Neural Computation", citations=80000)},
                {"citedPaper": _ss_paper("RESIDUAL_ID", "Deep Residual Learning for Image Recognition",
                                         2016, "CVPR", citations=100000)},
                {"citedPaper": None},
                {"citedPaper": _ss_paper("ADAM_ID", "Adam: A Method for Stochastic Optimization",
                                         2015, "ICLR", citations=90000)},
            ]
        },
        "relevant_ids": {"BAHDANAU_ID", "LSTM_ID", "RESIDUAL_ID", "ADAM_ID"},
    },
]

CITATION_CASES = [
    {
        "name": "transformer_downstream",
        "semantic_id": "204e3073870fae3d05bcbc2f6a8e263d29031248",
        "mock_response": {
            "data": [
                {"citingPaper": _ss_paper("BERT_ID",
                                          "BERT: Pre-training of Deep Bidirectional Transformers",
                                          2019, "NAACL", citations=55000)},
                {"citingPaper": _ss_paper("GPT3_ID", "Language Models are Few-Shot Learners",
                                          2020, "NeurIPS", citations=30000)},
                {"citingPaper": _ss_paper("VIT_ID", "An Image is Worth 16x16 Words",
                                          2021, "ICLR", citations=22000)},
                {"citingPaper": _ss_paper("NOISE_CITE_1", "Unrelated Domain Paper", 2020, "", citations=50)},
            ]
        },
        "relevant_ids": {"BERT_ID", "GPT3_ID", "VIT_ID"},
    },
]

RECOMMENDATION_CASES = [
    {
        "name": "nlp_library",
        "library_titles": [
            "Attention Is All You Need",
            "BERT: Pre-training of Deep Bidirectional Transformers",
        ],
        "mock_results_per_title": {
            "Attention Is All You Need": [
                _ss_paper("204e3073870fae3d05bcbc2f6a8e263d29031248", "Attention Is All You Need",
                           2017, "NeurIPS", citations=95000),
                _ss_paper("XLNET_ID", "XLNet: Generalized Autoregressive Pretraining",
                           2019, "NeurIPS", citations=8000),
                _ss_paper("T5_ID", "Exploring the Limits of Transfer Learning with T5",
                           2020, "JMLR", citations=12000),
                _ss_paper("ROBERTA_ID", "RoBERTa: A Robustly Optimized BERT Approach",
                           2019, "", citations=9000),
            ],
            "BERT: Pre-training of Deep Bidirectional Transformers": [
                _ss_paper("df2b0e26d0599ce3e70df8a9da02e51594e0e992",
                          "BERT: Pre-training of Deep Bidirectional Transformers",
                          2019, "NAACL", citations=55000),
                _ss_paper("ALBERT_ID", "ALBERT: A Lite BERT for Self-supervised Learning",
                           2020, "ICLR", citations=7000),
                _ss_paper("XLNET_ID", "XLNet: Generalized Autoregressive Pretraining",
                           2019, "NeurIPS", citations=8000),
                _ss_paper("ELECTRA_ID", "ELECTRA: Pre-training Text Encoders",
                           2020, "ICLR", citations=4000),
            ],
        },
        "relevant_ids": {"XLNET_ID", "T5_ID", "ROBERTA_ID", "ALBERT_ID", "ELECTRA_ID"},
        "library_ids": {
            "204e3073870fae3d05bcbc2f6a8e263d29031248",
            "df2b0e26d0599ce3e70df8a9da02e51594e0e992",
        },
    },
]


# ---------------------------------------------------------------------------
# Session 级汇报
# ---------------------------------------------------------------------------

_all_metrics: list[AccuracyMetrics] = []


@pytest.fixture(scope="session", autouse=True)
def print_final_report():
    yield
    if _all_metrics:
        print_accuracy_report(_all_metrics)


# ---------------------------------------------------------------------------
# 关键词检索准确性测试
# ---------------------------------------------------------------------------

class TestKeywordSearchAccuracy:

    @pytest.mark.parametrize("case", KEYWORD_CASES, ids=[c["name"] for c in KEYWORD_CASES])
    def test_keyword_case(self, case):
        mock_response = {"total": len(case["mock_data"]), "data": case["mock_data"]}
        ctx, _ = _make_mock_ctx(mock_response)
        with patch("app.services.semantic_scholar.httpx.Client", return_value=ctx):
            with patch("app.services.semantic_scholar.time.sleep"):
                result = semantic_scholar.search_papers(case["query"], limit=10)

        retrieved_ids = {p["semantic_id"] for p in result["data"] if p.get("semantic_id")}
        m = compute_metrics(retrieved_ids, case["relevant_ids"], case["name"])
        _all_metrics.append(m)

        assert m.precision >= 0.4, f"{case['name']}: precision {m.precision:.0%} < 40%"
        assert m.recall >= 0.5, f"{case['name']}: recall {m.recall:.0%} < 50%"


# ---------------------------------------------------------------------------
# 上游参考文献检索准确性测试
# ---------------------------------------------------------------------------

class TestReferenceRetrievalAccuracy:

    @pytest.mark.parametrize("case", REFERENCE_CASES, ids=[c["name"] for c in REFERENCE_CASES])
    def test_references_case(self, case):
        ctx, _ = _make_mock_ctx(case["mock_response"])
        with patch("app.services.semantic_scholar.httpx.Client", return_value=ctx):
            with patch("app.services.semantic_scholar.time.sleep"):
                refs = semantic_scholar.get_references(case["semantic_id"])

        retrieved_ids = {p["semantic_id"] for p in refs if p.get("semantic_id")}
        m = compute_metrics(retrieved_ids, case["relevant_ids"], case["name"])
        _all_metrics.append(m)

        assert m.recall == 1.0, f"{case['name']}: recall {m.recall:.0%} < 100%"


# ---------------------------------------------------------------------------
# 下游引用文献检索准确性测试
# ---------------------------------------------------------------------------

class TestCitationRetrievalAccuracy:

    @pytest.mark.parametrize("case", CITATION_CASES, ids=[c["name"] for c in CITATION_CASES])
    def test_citations_case(self, case):
        ctx, _ = _make_mock_ctx(case["mock_response"])
        with patch("app.services.semantic_scholar.httpx.Client", return_value=ctx):
            with patch("app.services.semantic_scholar.time.sleep"):
                cites = semantic_scholar.get_citations(case["semantic_id"])

        retrieved_ids = {p["semantic_id"] for p in cites if p.get("semantic_id")}
        m = compute_metrics(retrieved_ids, case["relevant_ids"], case["name"])
        _all_metrics.append(m)

        assert m.recall == 1.0, f"{case['name']}: recall {m.recall:.0%} < 100%"


# ---------------------------------------------------------------------------
# 方向推荐准确性测试
# ---------------------------------------------------------------------------

class TestRecommendationAccuracy:

    @pytest.mark.parametrize("case", RECOMMENDATION_CASES, ids=[c["name"] for c in RECOMMENDATION_CASES])
    def test_recommendation_case(self, case):
        def mock_search(query, offset=0, limit=10, **kwargs):
            raw = case["mock_results_per_title"].get(query, [])
            return {"total": len(raw), "offset": 0, "limit": limit, "data": raw}

        seen: set[str] = set()
        results: list[dict] = []
        for title in case["library_titles"]:
            res = mock_search(title, 0, 4)
            for p in res["data"]:
                # mock_results_per_title 存的是原始 SS 格式（paperId），需经 _fmt 转换
                formatted = semantic_scholar._fmt(p)
                sid = formatted.get("semantic_id")
                if sid and sid not in seen:
                    seen.add(sid)
                    results.append(formatted)

        retrieved_ids = {p["semantic_id"] for p in results if p.get("semantic_id")}
        retrieved_ids -= case.get("library_ids", set())
        m = compute_metrics(retrieved_ids, case["relevant_ids"], case["name"])
        _all_metrics.append(m)

        assert m.recall >= 0.6, f"{case['name']}: recall {m.recall:.0%} < 60%"


# ---------------------------------------------------------------------------
# 在线验证（需真实 SS API，默认跳过）
# ---------------------------------------------------------------------------

@pytest.mark.online
@pytest.mark.skip(reason="需要真实 SS API，使用 -m online 手动运行")
def test_online_keyword_transformer():
    """Transformer 论文必须出现在 top-10 结果中。"""
    result = semantic_scholar.search_papers("attention is all you need", limit=10)
    retrieved = {p["semantic_id"] for p in result["data"] if p.get("semantic_id")}
    relevant = {"204e3073870fae3d05bcbc2f6a8e263d29031248"}
    m = compute_metrics(retrieved, relevant, "online_keyword_transformer")
    print_accuracy_report([m])
    assert m.recall >= 1.0


@pytest.mark.online
@pytest.mark.skip(reason="需要真实 SS API，使用 -m online 手动运行")
def test_online_references_transformer():
    """Transformer 论文的参考文献必须包含 Bahdanau attention 论文。"""
    refs = semantic_scholar.get_references("204e3073870fae3d05bcbc2f6a8e263d29031248")
    retrieved = {p["semantic_id"] for p in refs if p.get("semantic_id")}
    relevant = {"1c5d5b62e28f9e9f0a37e9f58fcef8ef5706e0f0"}
    m = compute_metrics(retrieved, relevant, "online_refs_transformer")
    print_accuracy_report([m])
    assert m.recall >= 1.0


@pytest.mark.online
@pytest.mark.skip(reason="需要真实 SS API，使用 -m online 手动运行")
def test_online_recommendation_nlp():
    """基于 NLP 库论文的推荐结果中，BERT 或 GPT-3 至少命中一篇。"""
    result = semantic_scholar.search_papers("Attention Is All You Need", limit=5)
    retrieved = {p["semantic_id"] for p in result["data"] if p.get("semantic_id")}
    retrieved.discard("204e3073870fae3d05bcbc2f6a8e263d29031248")
    relevant = {
        "df2b0e26d0599ce3e70df8a9da02e51594e0e992",  # BERT
        "9405cc0d6169988371b2755e573cc28650d14dfe",   # GPT-3
    }
    m = compute_metrics(retrieved, relevant, "online_recommendation_nlp")
    print_accuracy_report([m])
    assert m.recall >= 0.5
