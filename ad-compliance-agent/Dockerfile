FROM python:3.12-slim

WORKDIR /app

# 系统依赖（chromadb 需要 build-essential 编译 C++ 扩展）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制源码
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY config/ ./config/
COPY data/ ./data/

# 默认使用在线 API embedding
ENV EMBEDDING_MODEL=text-embedding-3-small

EXPOSE 8000

# 首次启动：构建知识库 → 启动 API
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

CMD ["./entrypoint.sh"]
