"""
文档切分 — RecursiveCharacterTextSplitter 按中文语义切分。
"""

from __future__ import annotations

from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import config

_CHINESE_SEPARATORS = ["\n\n", "\n", "。", "；", "，", " "]


def get_text_splitter(
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size or config.CHUNK_SIZE,
        chunk_overlap=chunk_overlap or config.CHUNK_OVERLAP,
        separators=_CHINESE_SEPARATORS,
    )
