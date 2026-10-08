#!/bin/bash
set -e

echo "============================================="
echo "  Ad Compliance Agent - Docker"
echo "============================================="

if [ ! -f "data/chroma_db/kb_dump.json" ]; then
    echo "[1/2] Building knowledge base..."
    python scripts/build_knowledge_base.py
    echo "Knowledge base built."
else
    echo "[1/2] Knowledge base already exists. Skipping build."
fi

echo "[2/2] Starting API server on port 8000..."
exec uvicorn src.api.app:app --host 0.0.0.0 --port 8000
