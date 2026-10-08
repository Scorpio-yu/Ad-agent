"""
法规文档加载器 — 从 data/laws、data/platform_rules、data/cases 三个目录批量加载。
每个目录对应一个知识类别，自动附加到 Document 元数据中。
"""

from pathlib import Path

from langchain_core.documents import Document

from src.config import config

CATEGORY_MAP = {
    config.LAWS_DIR: "laws",
    config.PLATFORM_RULES_DIR: "platform_rules",
    config.CASES_DIR: "cases",
}


def _clean_text(text: str) -> str:
    """基础文本清洗：去除多余空行、统一换行。"""
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def _load_dir(dir_path: str) -> list[Document]:
    """加载单个目录下所有 .txt / .md 文件。"""
    docs = []
    root = Path(dir_path)
    category = CATEGORY_MAP.get(dir_path, "unknown")

    if not root.exists():
        return docs

    for file_path in root.rglob("*"):
        if file_path.suffix not in (".txt", ".md"):
            continue
        if file_path.name.startswith("."):
            continue

        raw = file_path.read_text(encoding="utf-8")
        text = _clean_text(raw)
        if not text:
            continue

        docs.append(Document(
            page_content=text,
            metadata={
                "source": file_path.stem,
                "category": category,
                "file_path": str(file_path.relative_to(root)),
            },
        ))
    return docs


class RegulationLoader:
    """从三个知识类别目录批量加载法规文档。"""

    def __init__(self):
        self.dirs = [config.LAWS_DIR, config.PLATFORM_RULES_DIR, config.CASES_DIR]

    def load(self) -> list[Document]:
        all_docs = []
        for d in self.dirs:
            docs = _load_dir(d)
            if docs:
                category = CATEGORY_MAP.get(d, "unknown")
                print(f"  [{category}] 加载 {len(docs)} 份文档")
            all_docs.extend(docs)
        return all_docs
