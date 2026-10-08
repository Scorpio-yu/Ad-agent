"""
FastAPI 应用入口。
启动方式：uvicorn src.api.app:app --reload
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.api.routes import router

app = FastAPI(
    title="广告合规审核 Agent",
    description="基于 LangChain + RAG 的广告合规智能审核系统",
    version="0.1.0",
)

app.include_router(router)

# 挂载前端静态文件
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

# 根路径重定向到前端页面
from fastapi.responses import FileResponse

@app.get("/")
async def root():
    index_path = frontend_dir / "index.html"
    return FileResponse(str(index_path))
