"""
广告法规检索器 — 基于 Chroma 向量相似度检索相关法规条款。

重要：必须在导入 langchain_openai 之前加载 SentenceTransformer 模型，
否则 Windows 下会 segfault。此处通过模块级预加载保证顺序。
"""

from __future__ import annotations

from src.config import config
from src.knowledge_base.vector_store import similarity_search, load_from_disk, get_collection

# 模块导入时强制加载 Embedding 模型，确保在 audit_chain 中 import langchain_openai 之前完成
get_collection()


class AdRegulationRetriever:
    """检索与广告文本最相关的法规条款。"""

    def __init__(self, top_k: int | None = None):
        self.top_k = top_k or config.RETRIEVER_TOP_K
        loaded = load_from_disk()
        if not loaded:
            print("  [warn] knowledge base is empty, run build_knowledge_base.py first")

    def retrieve(self, query: str) -> list[dict]:
        return similarity_search(query, k=self.top_k)

    def format_context(self, results: list[dict]) -> str:
        parts = []
        for i, item in enumerate(results, 1):
            source = item["metadata"].get("source", "unknown")
            parts.append(f"[Clause {i} - Source: {source}]\n{item['content']}")
        return "\n\n".join(parts)
