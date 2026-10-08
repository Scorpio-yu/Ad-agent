"""
统一配置 — 从 .env 和 config/settings.yaml 加载。
优先级：环境变量 > .env 文件 > settings.yaml 默认值
"""

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"


def _load_yaml() -> dict:
    yaml_path = PROJECT_ROOT / "config" / "settings.yaml"
    with open(yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


_yaml = _load_yaml()


class Config:
    # ===== 数据目录 =====
    LAWS_DIR: str = os.getenv("LAWS_DIR", str(DATA_DIR / "laws"))
    PLATFORM_RULES_DIR: str = os.getenv("PLATFORM_RULES_DIR", str(DATA_DIR / "platform_rules"))
    CASES_DIR: str = os.getenv("CASES_DIR", str(DATA_DIR / "cases"))

    # ===== LLM（OpenAI 兼容接口，支持 DeepSeek / Qwen / 智谱） =====
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    LLM_MODEL: str = os.getenv("LLM_MODEL", _yaml["audit"]["model"])
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", _yaml["audit"]["temperature"]))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", _yaml["audit"]["max_tokens"]))

    # ===== Embedding =====
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-zh-v1.5")
    EMBEDDING_DEVICE: str = os.getenv("EMBEDDING_DEVICE", "cpu")
    # 独立的 embedding API 配置（不设则默认复用 OPENAI_API_KEY / OPENAI_BASE_URL）
    EMBEDDING_API_KEY: str = os.getenv("EMBEDDING_API_KEY", "")
    EMBEDDING_BASE_URL: str = os.getenv("EMBEDDING_BASE_URL", "")

    @property
    def is_api_embedding(self) -> bool:
        """是否使用在线 API embedding（显式配置 > 自动检测模型名前缀）。"""
        if self.EMBEDDING_PROVIDER:
            return self.EMBEDDING_PROVIDER == "api"
        return self.EMBEDDING_MODEL.startswith("text-embedding")

    # ===== HuggingFace 配置（仅本地模型需要）=====
    HF_ENDPOINT: str = os.getenv("HF_ENDPOINT", "https://hf-mirror.com")
    HF_HUB_OFFLINE: bool = os.getenv("HF_HUB_OFFLINE", "1").lower() in ("1", "true", "yes")
    TRANSFORMERS_OFFLINE: bool = os.getenv("TRANSFORMERS_OFFLINE", "1").lower() in ("1", "true", "yes")

    # ===== Chroma =====
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", str(DATA_DIR / "chroma_db"))
    CHROMA_COLLECTION_NAME: str = os.getenv("CHROMA_COLLECTION_NAME", "ad_regulations")

    # ===== 切片参数 =====
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", _yaml["knowledge_base"]["chunk_size"]))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", _yaml["knowledge_base"]["chunk_overlap"]))

    # ===== 检索 =====
    RETRIEVER_TOP_K: int = int(os.getenv("RETRIEVER_TOP_K", _yaml["retriever"]["top_k"]))


config = Config()
