"""
Chroma 向量库封装。
Windows 下 PersistentClient 子进程与 langchain_openai 冲突导致 segfault，
因此日常查询使用 EphemeralClient，数据通过 JSON 从磁盘加载/保存。

Embedding 支持双模式（由 EMBEDDING_PROVIDER 或模型名前缀控制）：
  - 在线 API：EMBEDDING_PROVIDER=api 或模型名以 "text-embedding" 开头
  - 本地模型：EMBEDDING_PROVIDER=local 或模型名不以 "text-embedding" 开头
"""

from __future__ import annotations

import json
import os

# 先加载配置，再根据 embedding 模式决定是否设置 HuggingFace 环境变量
# 必须在 import chromadb 之前执行——sentence-transformers 导入时会读这些变量
from src.config import config

_model = config.EMBEDDING_MODEL
if not config.is_api_embedding:
    # 本地模型模式：设置 HF 镜像 + 离线，避免直连 huggingface.co 超时
    if config.HF_ENDPOINT:
        os.environ.setdefault("HF_ENDPOINT", config.HF_ENDPOINT)
    if config.HF_HUB_OFFLINE:
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
    if config.TRANSFORMERS_OFFLINE:
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import chromadb

_client: chromadb.ClientAPI | None = None
_collection: chromadb.Collection | None = None
_embedding_fn = None


def _get_embedding_fn():
    """根据 EMBEDDING_MODEL 配置返回对应的 Chroma embedding function。"""
    global _embedding_fn
    if _embedding_fn is None:
        model = config.EMBEDDING_MODEL

        if config.is_api_embedding:
            # API-based embeddings（OpenAI 兼容接口）
            from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
            _embedding_fn = OpenAIEmbeddingFunction(
                api_key=config.EMBEDDING_API_KEY or config.OPENAI_API_KEY,
                api_base=config.EMBEDDING_BASE_URL or config.OPENAI_BASE_URL,
                model_name=model,
            )
        else:
            # 本地 embeddings（sentence-transformers / HuggingFace）
            from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
            _embedding_fn = SentenceTransformerEmbeddingFunction(
                model_name=model,
                device=config.EMBEDDING_DEVICE,
            )
    return _embedding_fn


def get_collection() -> chromadb.Collection:
    global _client, _collection
    if _client is None:
        _client = chromadb.EphemeralClient()
    if _collection is None:
        ef = _get_embedding_fn()
        _collection = _client.get_or_create_collection(
            name=config.CHROMA_COLLECTION_NAME,
            embedding_function=ef,
        )
    return _collection


def add_documents(documents: list) -> None:
    coll = get_collection()
    start = coll.count()
    ids = [f"doc_{start + i}" for i in range(len(documents))]
    texts = [d.page_content for d in documents]
    metadatas = [d.metadata for d in documents]
    coll.add(ids=ids, documents=texts, metadatas=metadatas)


def similarity_search(query: str, k: int = 5) -> list[dict]:
    coll = get_collection()
    results = coll.query(query_texts=[query], n_results=k)
    items = []
    if results["documents"] and results["documents"][0]:
        for i, doc in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][i] if results["metadatas"] else {}
            dist = results["distances"][0][i] if results["distances"] else 0
            items.append({"content": doc, "metadata": meta, "distance": round(dist, 4)})
    return items


# ---- 磁盘持久化 ----
# 知识库数据序列化为 JSON 保存/加载，绕过 PersistentClient 子进程问题

DUMP_PATH = os.path.join(config.CHROMA_PERSIST_DIR, "kb_dump.json")


def save_to_disk():
    """将当前 Collection 数据导出到 JSON 文件。"""
    coll = get_collection()
    data = coll.get()
    if not data["ids"]:
        return
    os.makedirs(config.CHROMA_PERSIST_DIR, exist_ok=True)
    payload = {
        "ids": data["ids"],
        "documents": data["documents"],
        "metadatas": data["metadatas"],
    }
    with open(DUMP_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    print(f"  [persist] saved {len(data['ids'])} records to {DUMP_PATH}")


def load_from_disk() -> bool:
    """从 JSON 文件加载数据到 EphemeralClient。"""
    if not os.path.exists(DUMP_PATH):
        return False
    with open(DUMP_PATH, "r", encoding="utf-8") as f:
        payload = json.load(f)
    if not payload["ids"]:
        return False
    coll = get_collection()
    if coll.count() > 0:
        return True  # already loaded
    coll.add(
        ids=payload["ids"],
        documents=payload["documents"],
        metadatas=payload["metadatas"],
    )
    return True


def delete_collection() -> None:
    global _client, _collection
    if _client is not None:
        try:
            _client.delete_collection(config.CHROMA_COLLECTION_NAME)
        except Exception:
            pass
    _collection = None
    if os.path.exists(DUMP_PATH):
        os.remove(DUMP_PATH)
