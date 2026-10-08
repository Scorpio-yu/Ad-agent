@echo off
title 广告合规审核 Agent

echo ============================================
echo   广告合规审核 Agent
echo ============================================
echo.

:: Activate venv
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo [错误] 没有找到虚拟环境，请先双击 setup.bat 完成安装！
    pause
    exit /b 1
)

:: Check .env
if not exist .env (
    echo [错误] 没有找到 .env 文件！
    echo 请参考 .env.example 创建 .env，填入你的 API Key。
    pause
    exit /b 1
)

echo 正在启动服务...
echo.
echo 启动后请打开浏览器，访问 http://localhost:8000
echo 按 Ctrl+C 可以停止服务
echo ============================================
echo.

uvicorn src.api.app:app --host 0.0.0.0 --port 8000
pause
