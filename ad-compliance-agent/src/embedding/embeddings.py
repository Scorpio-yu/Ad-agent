"""
Embedding 工厂 — 支持本地 HuggingFace 模型和在线 API 两套方案。
    本地：BAAI/bge-large-zh-v1.5 (免费，中文效果优秀)
    在线：OpenAI text-embedding-3-small
"""

from __future__ import annotations

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings

from src.config import config


class EmbeddingFactory:
    """根据配置创建 Embedding 实例。"""

    @staticmethod
    def create() -> HuggingFaceEmbeddings | OpenAIEmbeddings:
        model = config.EMBEDDING_MODEL

        if config.is_api_embedding:
            return OpenAIEmbeddings(
                model=model,
                openai_api_key=config.EMBEDDING_API_KEY or config.OPENAI_API_KEY,
                openai_api_base=config.EMBEDDING_BASE_URL or config.OPENAI_BASE_URL,
            )

        return HuggingFaceEmbeddings(
            model_name=model,
            model_kwargs={"device": config.EMBEDDING_DEVICE},
            encode_kwargs={"normalize_embeddings": True},
        )
