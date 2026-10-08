"""测试检索器。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.retriever.base_retriever import AdRegulationRetriever


def test_retrieve_format():
    retriever = AdRegulationRetriever(top_k=3)
    results = retriever.retrieve("面膜三天美白")
    assert isinstance(results, list)
    for item in results:
        assert "content" in item
        assert "metadata" in item
        assert "distance" in item


def test_format_context():
    retriever = AdRegulationRetriever()
    sample = [
        {
            "content": "广告不得含有虚假或者引人误解的内容。",
            "metadata": {"source": "advertising_law", "category": "laws"},
            "score": 0.95,
        }
    ]
    ctx = retriever.format_context(sample)
    assert "advertising_law" in ctx
    assert "虚假" in ctx
