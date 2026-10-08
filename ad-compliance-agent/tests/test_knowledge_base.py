"""测试知识库模块 — loader / splitter / text cleaning。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_core.documents import Document

from src.knowledge_base.loader import RegulationLoader, _clean_text
from src.knowledge_base.splitter import get_text_splitter


def test_clean_text():
    raw = "\n\n  第一条  广告不得虚假。\n\n\n  第二条  广告应当真实。  \n\n"
    cleaned = _clean_text(raw)
    assert "第一条" in cleaned
    assert "\n\n\n" not in cleaned


def test_loader():
    loader = RegulationLoader()
    docs = loader.load()
    assert isinstance(docs, list)
    for doc in docs:
        assert hasattr(doc, "page_content")
        assert "category" in doc.metadata
        assert doc.metadata["category"] in ("laws", "platform_rules", "cases")


def test_splitter():
    splitter = get_text_splitter(chunk_size=200, chunk_overlap=20)
    doc = Document(
        page_content="第九条 广告不得使用'国家级''最高级''最佳'等用语。",
        metadata={"source": "advertising_law", "category": "laws"},
    )
    chunks = splitter.split_documents([doc])
    assert len(chunks) >= 1
    for chunk in chunks:
        assert len(chunk.page_content) > 0
