@echo off
setlocal enabledelayedexpansion
title Ad Compliance Agent - One-Click Setup

echo =============================================
echo   Ad Compliance Agent - One-Click Setup
echo =============================================
echo.

:: [1/5] Check Python
echo [1/5] Checking Python installation...
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo.
    echo Please install Python 3.10+ from:
    echo   https://www.python.org/downloads/
    echo.
    echo IMPORTANT: Check "Add Python to PATH" during installation.
    pause
    exit /b 1
)
python --version
echo.

:: [2/5] Create virtual environment
echo [2/5] Creating virtual environment...
if exist venv (
    echo Virtual environment already exists. Skipping.
) else (
    python -m venv venv
    echo Created.
)
call venv\Scripts\activate.bat
echo.

:: [3/5] Install dependencies
echo [3/5] Installing dependencies (this may take 1-3 minutes)...
pip install --quiet --disable-pip-version-check -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] pip install failed. Check network connection and retry.
    pause
    exit /b 1
)
echo Done.
echo.

:: [4/5] Configure
echo [4/5] Setting up configuration...
if not exist .env (
    copy .env.example .env >nul
    echo.
    echo **********************************************************
    echo   .env file created from .env.example
    echo.
    echo   Open .env in VSCode and set your API keys:
    echo     - OPENAI_API_KEY     (DeepSeek API key)
    echo     - EMBEDDING_MODEL    (online API recommended)
    echo.
    echo   !!! IMPORTANT !!!
    echo   DeepSeek does NOT have an /embeddings endpoint.
    echo   If you use EMBEDDING_MODEL=text-embedding-3-small,
    echo   set EMBEDDING_BASE_URL to an embedding service:
    echo     https://api.siliconflow.cn/v1    (SiliconFlow)
    echo     https://api.openai.com/v1         (OpenAI)
    echo.
    echo   Or use local model:
    echo     EMBEDDING_MODEL=shibing624/text2vec-base-chinese
    echo     EMBEDDING_DEVICE=cpu
    echo **********************************************************
    echo.
) else (
    echo .env already exists. Skipping.
)
echo.

:: [5/5] Build knowledge base
echo [5/5] Building knowledge base... (requires API key to be set)
python scripts/build_knowledge_base.py
if %errorlevel% neq 0 (
    echo.
    echo [WARNING] Knowledge base build failed.
    echo You can retry after setting up .env:
    echo   python scripts/build_knowledge_base.py
) else (
    echo Knowledge base built successfully.
)
echo.

echo =============================================
echo   Setup complete!
echo.
echo   Start the API server:
echo     venv\Scripts\activate
echo     uvicorn src.api.app:app --reload
echo.
echo   Then open http://localhost:8000 in browser
echo.
echo   Or CLI audit:
echo     python scripts/run_audit.py "test ad text"
echo =============================================
pause
