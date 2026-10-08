# 广告合规审核 Agent

基于 **LangChain + RAG + Chroma** 的广告合规智能审核系统。

输入广告文案 → 自动检索《广告法》《互联网广告管理办法》及相关案例 → LLM 审核 → 输出结构化 JSON 报告（违规类型、风险关键词、法规依据、修改建议）。

## 技术栈

| 层级 | 技术 |
|------|------|
| LLM | DeepSeek / GPT-4o（OpenAI 兼容 API，可切换） |
| RAG 框架 | LangChain |
| 向量数据库 | Chroma |
| Embedding | 在线 API（text-embedding-3-small）/ 本地中文模型 |
| 检索 | 混合检索 = 向量相似度 + BM25 关键词 + RRF 融合 |
| API | FastAPI + Uvicorn + SSE 流式输出 |
| 前端 | 纯 HTML/CSS/JS，暗色主题聊天界面 |

---

## 快速开始（3 种方式）

### 方式一：setup.bat / setup.sh 一键安装（推荐）

**Windows** — 双击 `setup.bat`  
**Mac/Linux** — `bash setup.sh`

脚本自动完成：检测 Python → 创建 venv → 安装依赖 → 创建 `.env` → 构建知识库。

启动：
```bash
# Windows
venv\Scripts\activate
uvicorn src.api.app:app --reload

# Mac/Linux
source venv/bin/activate
uvicorn src.api.app:app --reload
```

浏览器打开 `http://localhost:8000` 即可使用。

### 方式二：Docker

```bash
# 1. 配置 API Key
cp .env.example .env
# 编辑 .env 填入 OPENAI_API_KEY

# 2. 启动
docker compose up
```

浏览器打开 `http://localhost:8000`。

### 方式三：手动安装

```bash
# 1. 虚拟环境
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置
cp .env.example .env
# 编辑 .env 填入 API Key

# 4. 构建知识库
python scripts/build_knowledge_base.py

# 5. 启动
uvicorn src.api.app:app --reload
```

---

## 配置说明

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `OPENAI_API_KEY` | LLM API Key | `sk-your-key-here` |
| `OPENAI_BASE_URL` | LLM API 地址 | `https://api.deepseek.com/v1` |
| `LLM_MODEL` | 模型名称 | `deepseek-chat` |
| `LLM_TEMPERATURE` | 生成温度 | `0.1` |
| `EMBEDDING_MODEL` | Embedding 模型 | `text-embedding-3-small` |
| `EMBEDDING_API_KEY` | 独立的 Embedding API Key（可不设） | 复用 `OPENAI_API_KEY` |
| `EMBEDDING_BASE_URL` | 独立的 Embedding API 地址（可不设） | 复用 `OPENAI_BASE_URL` |
| `CHROMA_COLLECTION_NAME` | Chroma 集合名 | `ad_regulations` |
| `RETRIEVER_TOP_K` | 检索返回条数 | `5` |

### ⚠️ DeepSeek 用户注意

DeepSeek **不提供 /embeddings 接口**。使用在线 embedding 时，需将 `EMBEDDING_BASE_URL` 设为支持 embeddings 的服务：

```
# siliconflow（国内可用）
EMBEDDING_BASE_URL=https://api.siliconflow.cn/v1
EMBEDDING_API_KEY=sk-your-siliconflow-key

# 或者直接用 OpenAI
EMBEDDING_BASE_URL=https://api.openai.com/v1
EMBEDDING_API_KEY=sk-your-openai-key
```

### 切换本地 embedding 模型

编辑 `.env`：
```
EMBEDDING_MODEL=shibing624/text2vec-base-chinese
EMBEDDING_DEVICE=cpu
HF_ENDPOINT=https://hf-mirror.com
```

首次运行会自动下载约 400MB 模型文件。之后设 `HF_HUB_OFFLINE=1` 可跳过联网校验。

---

## API

### 非流式审核

```bash
curl -X POST http://localhost:8000/api/v1/audit \
  -H "Content-Type: application/json" \
  -d '{"ad_content": "全网最低价，绝对正品，假一赔十"}'
```

### 流式审核（SSE）

```bash
curl -X POST http://localhost:8000/api/v1/audit/stream \
  -H "Content-Type: application/json" \
  -d '{"ad_content": "全网最低价，绝对正品，假一赔十"}'
```

### CLI

```bash
python scripts/run_audit.py "全网最低价，绝对正品，假一赔十"
```

---

## 输出示例

```json
{
  "is_violation": true,
  "violation_type": "绝对化用语",
  "risk_level": "high",
  "risk_keywords": ["全网最低价", "绝对正品"],
  "violation_clauses": [
    {
      "law": "中华人民共和国广告法",
      "article": "第九条 第三项",
      "content": "广告不得使用\"国家级\"、\"最高级\"、\"最佳\"等用语"
    }
  ],
  "reason": "\"全网最低价\"属于绝对化价格承诺，\"绝对正品\"使用绝对化用语，均违反广告法第九条",
  "suggestion": "修改为：\"价格实惠，品质有保障，支持专柜验货\""
}
```

---

## 项目结构

```
ad-compliance-agent/
├── config/
│   └── settings.yaml           # 默认参数
├── data/                       # 法规知识库原始文档
│   ├── laws/
│   ├── platform_rules/
│   ├── cases/
│   └── chroma_db/              # 向量库持久化数据
├── scripts/
│   ├── build_knowledge_base.py
│   └── run_audit.py
├── src/
│   ├── config.py               # 统一配置管理
│   ├── api/                    # FastAPI 接口
│   ├── chains/                 # RAG 审核链路
│   ├── embedding/              # Embedding 工厂
│   ├── knowledge_base/         # 文档加载/切片/向量库
│   ├── models/                 # Pydantic 数据模型
│   ├── prompts/                # Prompt 模板
│   ├── retriever/              # 混合检索器
│   └── frontend/               # 前端聊天界面
├── tests/
├── Dockerfile
├── docker-compose.yml
├── setup.bat                   # Windows 一键安装
├── setup.sh                    # Mac/Linux 一键安装
└── requirements.txt
```

## 违规类型（6 类）

虚假广告 · 绝对化用语 · 误导性对比 · 贬低竞争对手 · 必要信息缺失 · 公序良俗
