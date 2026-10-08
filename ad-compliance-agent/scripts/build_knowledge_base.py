"""
知识库构建 — 从 data/laws、data/platform_rules、data/cases 读取文档，
清洗 -> 切分 -> 向量化 -> 写入 Chroma，最终保存到磁盘 JSON。
用法：python scripts/build_knowledge_base.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.knowledge_base.loader import RegulationLoader
from src.knowledge_base.splitter import get_text_splitter
from src.knowledge_base.vector_store import (
    add_documents,
    save_to_disk,
    delete_collection,
)


def main():
    print("=" * 50)
    print("  Ad Compliance Knowledge Base Builder")
    print("=" * 50)

    # 1. Load
    print("\n[1/3] Loading regulation documents...")
    loader = RegulationLoader()
    raw_docs = loader.load()
    print(f"  Total: {len(raw_docs)} documents")

    if not raw_docs:
        print("  [WARN] No documents found in data/laws/ data/platform_rules/ data/cases/")
        return

    # 2. Split
    print("\n[2/3] Splitting documents...")
    splitter = get_text_splitter()
    chunks = splitter.split_documents(raw_docs)
    print(f"  Total: {len(chunks)} chunks")

    # 3. Build
    print("\n[3/3] Building vector database...")
    delete_collection()
    add_documents(chunks)
    save_to_disk()
    print(f"  [OK] Done, {len(chunks)} vectors persisted")


if __name__ == "__main__":
    main()
