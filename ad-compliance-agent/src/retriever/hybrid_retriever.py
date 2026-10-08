"""
混合检索器 — 向量检索 + BM25 关键词检索 + RRF 融合。

RRF (Reciprocal Rank Fusion) 公式：score(d) = Σ 1/(k + rank_i(d))
k 默认 60，两个检索器各取 top_k * pool_factor 条结果，融合后取 top_k。

原理：
- 向量检索：捕获语义相似（"最好" ≈ "最高级"）
- BM25 检索：捕获关键词精确匹配（"广告法第九条" 精确命中）
- RRF：不依赖原始分数绝对值，只关心排名，多种检索方式的排名取调和
"""

from __future__ import annotations

import jieba
from rank_bm25 import BM25Okapi

from src.config import config
from src.knowledge_base.vector_store import similarity_search, get_collection, load_from_disk

# 模块导入时强制加载 Embedding 模型
get_collection()


class HybridRetriever:
    """向量 + BM25 + RRF 混合检索器。"""

    def __init__(self, top_k: int | None = None, pool_factor: int = 2, rrf_k: int = 60):
        self.top_k = top_k or config.RETRIEVER_TOP_K
        self.pool_factor = pool_factor  # 每个检索器的候选池倍数
        self.rrf_k = rrf_k

        # 初始化向量检索
        load_from_disk()

        # 初始化 BM25
        self._corpus: list[str] = []          # 原始文档文本（给 BM25 评分用）
        self._corpus_meta: list[dict] = []    # 对应的 metadata
        self._bm25: BM25Okapi | None = None
        self._build_bm25_index()

    def _build_bm25_index(self):
        """从 Chroma 加载全部文档，用 jieba 分词构建 BM25 索引。"""
        coll = get_collection()
        data = coll.get()
        if not data["ids"]:
            print("  [warn] BM25 index empty: no documents in collection")
            return

        self._corpus = data["documents"] or []
        self._corpus_meta = data["metadatas"] or []

        # jieba 分词 → BM25 的 tokenized corpus
        tokenized = [list(jieba.cut(doc)) for doc in self._corpus]
        self._bm25 = BM25Okapi(tokenized)

    def retrieve(self, query: str) -> list[dict]:
        """混合检索：向量 + BM25 → RRF 融合 → Top-K。"""
        pool_size = self.top_k * self.pool_factor

        # 1. 向量检索
        vec_results = similarity_search(query, k=pool_size)

        # 2. BM25 检索
        bm25_results = self._bm25_search(query, k=pool_size)

        # 3. RRF 融合
        fused = self._rrf_fuse(vec_results, bm25_results)
        return fused[:self.top_k]

    def _bm25_search(self, query: str, k: int) -> list[dict]:
        """BM25 关键词检索。"""
        if self._bm25 is None:
            return []

        tokens = list(jieba.cut(query))
        scores = self._bm25.get_scores(tokens)
        # 按分数降序取 top-k
        indexed = [(i, scores[i]) for i in range(len(scores)) if scores[i] > 0]
        indexed.sort(key=lambda x: x[1], reverse=True)

        results = []
        for idx, score in indexed[:k]:
            meta = self._corpus_meta[idx] if idx < len(self._corpus_meta) else {}
            results.append({
                "content": self._corpus[idx],
                "metadata": meta,
                "bm25_score": round(float(score), 4),
            })
        return results

    def _rrf_fuse(self, vec_results: list[dict], bm25_results: list[dict]) -> list[dict]:
        """RRF 融合两个排序列表。

        每个文档用 (content 前 100 字符) 去重。RRF 分数 = 1/(k + rank);
        如果文档同时出现在两个列表中，分数相加。
        """
        # doc key: content 前 100 字符作为去重标识
        def _key(item: dict) -> str:
            return item["content"][:100]

        rrf_scores: dict[str, float] = {}
        doc_map: dict[str, dict] = {}

        # 向量侧
        for rank, item in enumerate(vec_results):
            k = _key(item)
            score = 1.0 / (self.rrf_k + rank + 1)
            rrf_scores[k] = rrf_scores.get(k, 0.0) + score
            doc_map[k] = item

        # BM25 侧
        for rank, item in enumerate(bm25_results):
            k = _key(item)
            score = 1.0 / (self.rrf_k + rank + 1)
            rrf_scores[k] = rrf_scores.get(k, 0.0) + score
            if k not in doc_map:
                doc_map[k] = item

        # 按 RRF 分数降序排列
        sorted_keys = sorted(rrf_scores, key=lambda k: rrf_scores[k], reverse=True)
        fused = []
        for k in sorted_keys:
            item = doc_map[k].copy()
            item["rrf_score"] = round(rrf_scores[k], 6)
            fused.append(item)

        return fused

    def format_context(self, results: list[dict]) -> str:
        parts = []
        for i, item in enumerate(results, 1):
            source = item["metadata"].get("source", "unknown")
            parts.append(f"[Clause {i} - Source: {source}]\n{item['content']}")
        return "\n\n".join(parts)


# 全局单例
_hybrid_retriever: HybridRetriever | None = None


def get_hybrid_retriever() -> HybridRetriever:
    global _hybrid_retriever
    if _hybrid_retriever is None:
        _hybrid_retriever = HybridRetriever()
    return _hybrid_retriever
