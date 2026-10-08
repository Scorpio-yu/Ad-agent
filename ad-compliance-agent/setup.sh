#!/bin/bash
set -e

echo "============================================="
echo "  Ad Compliance Agent - One-Click Setup"
echo "============================================="
echo

# [1/5] Check Python
echo "[1/5] Checking Python installation..."
if ! command -v python3 &>/dev/null; then
    echo "[ERROR] Python 3 not found!"
    echo "Please install Python 3.10+ from https://www.python.org/downloads/"
    exit 1
fi
python3 --version
echo

# [2/5] Create virtual environment
echo "[2/5] Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists. Skipping."
else
    python3 -m venv venv
    echo "Created."
fi
source venv/bin/activate
echo

# [3/5] Install dependencies
echo "[3/5] Installing dependencies..."
pip install --quiet --disable-pip-version-check -r requirements.txt
echo "Done."
echo

# [4/5] Configure
echo "[4/5] Setting up configuration..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ""
    echo "**********************************************************"
    echo "  .env file created from .env.example"
    echo ""
    echo "  Edit .env to set your API keys:"
    echo "    - OPENAI_API_KEY     (DeepSeek API key)"
    echo "    - EMBEDDING_MODEL    (online API recommended)"
    echo ""
    echo "  !!! IMPORTANT !!!"
    echo "  DeepSeek does NOT have an /embeddings endpoint."
    echo "  If using EMBEDDING_MODEL=text-embedding-3-small,"
    echo "  set EMBEDDING_BASE_URL to a compatible service."
    echo "**********************************************************"
    echo ""
else
    echo ".env already exists. Skipping."
fi
echo

# [5/5] Build knowledge base
echo "[5/5] Building knowledge base..."
python scripts/build_knowledge_base.py || echo "[WARNING] KB build failed. Set up .env and retry."
echo

echo "============================================="
echo "  Setup complete!"
echo ""
echo "  Start server:  source venv/bin/activate"
echo "                 uvicorn src.api.app:app --reload"
echo ""
echo "  Open http://localhost:8000 in browser"
echo "============================================="
