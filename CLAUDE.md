# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 当前进展

- 2025-05-25：项目初始化完成，目录结构已建立
- 2025-05-25：完成 `/init` 全项目代码分析，CLAUDE.md 现已包含完整架构、数据流、关键设计决策
- 2025-05-25：知识库已预构建（`data/chroma_db/kb_dump.json`，7个文档块），可直接运行审核
- 2025-05-26：**彻底移除 Stop hook**——用户级 `~/.claude/settings.json` 和项目级 `.claude/settings.local.json` 两处均删除，不再自动提示更新 CLAUDE.md。保存完全手动化。
- 2025-05-26：**初始化 Auto Memory 系统**——`C:\Users\24945\.claude\projects\D--vs---AI-Agent\memory\` 下创建 3 条记忆（user_preferences / feedback_manual_save / project_architecture）+ MEMORY.md 索引
- 2025-05-26：**安装 22 个 Skills**——从 mattpocock/skills 仓库克隆并安装 engineering / productivity / misc 类技能到 `.claude/skills/`
- 2025-05-26：**运行测试通过**——解决 greenlet==2.0.2 编译兼容问题，CLI 审核 "全网最低价，绝对正品，假一赔十" 正确识别为绝对化用语违规
- 2025-05-26：**新增前端聊天界面**——纯 HTML/CSS/JS，暗色主题，`src/frontend/` 下 3 个文件，FastAPI 挂载静态文件，浏览器打开 `localhost:8000` 即可使用
- 2026-06-24：**实现流式输出 SSE**——`POST /api/v1/audit/stream`，逐 token 推送 + 前端 `fetch` + `ReadableStream` 逐字渲染，`src/frontend/index.html` 新增 streaming 模板
- 2026-06-24：**换中文 Embedding 模型**——`all-MiniLM-L6-v2` → `shibing624/text2vec-base-chinese`（本地已缓存），知识库已重建（7 chunks）。同时修复 huggingface 网络问题：`vector_store.py` 在 `import chromadb` 前设 `HF_HUB_OFFLINE=1` + `TRANSFORMERS_OFFLINE=1` + `HF_ENDPOINT` 镜像
- 2026-06-24：**待完成——混合检索**（向量 + BM25 + Reranker），下次继续
- 2026-06-25：**完成混合检索**——新增 `src/retriever/hybrid_retriever.py`，向量检索 + BM25 关键词检索 + RRF 融合。JM25 用 jieba 分词建索引，RRF 两个排序列表融合取 Top-5。`AdAuditChain` 已切换为 `HybridRetriever`。端到端测试通过（混合检索 + 中文 Embedding + SSE 流式，29.5s/265 tokens）。三个高优先级优化全部完成。

## 保存策略
- 完全手动保存：用户说"保存进展"或"更新 CLAUDE.md"时才写入，任何 hook 都不会自动触发

## 常用命令

```bash
# 构建/重建知识库（修改 data/ 下的法律条文后必须执行）
python scripts/build_knowledge_base.py

# CLI 审核广告文案
python scripts/run_audit.py "你的广告文案"

# 启动 API 服务
python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload

# 运行全部测试
pytest tests/ -v

# 运行单个测试文件
pytest tests/test_audit_chain.py -v
```

## 项目概述

广告合规检测 Agent，RAG + LLM 架构。输入广告文案 → 向量检索相关法规条文 → LLM 审核 → 输出结构化 JSON 审核报告（违规类型、风险等级、相关条款、修改建议）。

**技术栈**: LangChain + Chroma（向量库）+ FastAPI + Pydantic v2 + sentence-transformers（embedding）+ DeepSeek（LLM，OpenAI 兼容 API）

## 架构与数据流

### RAG 管线（核心流程）

```
广告文案输入
  → AdRegulationRetriever.retrieve() → Chroma 相似度检索 top-5 法规片段
  → format_context() → 编号的法规文本
  → SystemMessage (角色+输出格式约束) + HumanMessage (法规上下文 + 广告原文)
  → ChatOpenAI (DeepSeek) → JSON 响应
  → _parse_response() → 去 markdown 包裹 → json.loads()
```

### 模块依赖图（导入顺序敏感）

```
config.py (加载 .env + settings.yaml 单例)
  ├── embedding/embeddings.py    (EmbeddingFactory - 给 LangChain 用)
  ├── knowledge_base/loader.py   (RegulationLoader - 加载 txt/md 法律条文)
  ├── knowledge_base/splitter.py (中文优化的文本切分器)
  ├── knowledge_base/vector_store.py (Chroma 封装, EphemeralClient + JSON 持久化)
  │     └── 导入时预热 SentenceTransformer 模型
  ├── retriever/base_retriever.py (AdRegulationRetriever)
  │     └── 导入时强制 get_collection() 在 langchain_openai 之前加载
  ├── chains/audit_chain.py (AdAuditChain - 核心审核管线)
  │     ├── prompts/templates.py (SYSTEM_PROMPT + USER_PROMPT_TEMPLATE)
  │     └── models/schemas.py   (Pydantic 模型)
  └── api/routes.py (FastAPI: POST /api/v1/audit)
```

### 知识库构建流程（离线，数据变更后执行）

```
data/laws/*.txt + data/platform_rules/*.txt + data/cases/*.txt
  → RegulationLoader → [Document]
  → get_text_splitter() (中文分隔符: \n\n, \n, 。, ；, ，, 空格)
  → add_documents() → Chroma EphemeralClient
  → save_to_disk() → data/chroma_db/kb_dump.json
```

## 关键设计决策与注意事项

### 1. Windows 兼容：EphemeralClient + JSON 持久化
**这是最重要的架构约束。** Windows 上 `chromadb.PersistentClient` 子进程与 `langchain_openai` 存在 segfault 冲突。解决方案：
- 运行时使用 `chromadb.EphemeralClient`
- 数据通过 `save_to_disk()` / `load_from_disk()` 手动序列化到 `kb_dump.json`
- 修改法规数据后必须运行 `build_knowledge_base.py` 重新生成 JSON

### 2. 导入顺序必须严格
`chromadb` / SentenceTransformer 必须在 `langchain_openai` 之前初始化，否则可能 segfault。`base_retriever.py` 模块级调用 `get_collection()` 确保此顺序。**不要在 retriever 之前 import audit_chain 或任何触发 langchain_openai 导入的模块。**

### 3. 两套独立的 embedding 机制
- **LangChain 侧**: `EmbeddingFactory.create()` → `HuggingFaceEmbeddings` 或 `OpenAIEmbeddings`（给 LangChain workflow 用）
- **Chroma 侧**: `SentenceTransformerEmbeddingFunction`（Chroma 自己的 `query()` 需要原生 embedding function）

两者通过 `config.EMBEDDING_MODEL` 共用同一个模型名。当前环境用 `all-MiniLM-L6-v2`。

### 4. 不走 LangChain 高层抽象
项目没有用 `RetrievalQA` 或 LCEL chain，而是在 `AdAuditChain.audit()` 中手动编排检索→拼接提示词→调 LLM→解析 JSON 全流程，以保持完全控制。

### 5. 配置优先级
环境变量 > `.env` 文件 > `config/settings.yaml` 默认值。`src/config.py` 中 `Config` 类是模块级单例。

### 6. API 端点
单一端点 `POST /api/v1/audit`，请求体 `{"ad_content": "..."}` (1-5000 字符)，返回 `AuditResponse`（含 `success`, `data: AuditResult`, `error`）。

### 7. LLM JSON 解析容错
`_parse_response()` 会先去掉 markdown 代码块包裹（```json ... ```），再 `json.loads()`。解析失败时返回 fallback dict（`is_violation=False`, `risk_level="none"`）而非抛异常。

## 数据文件

| 路径 | 内容 |
|------|------|
| `data/laws/advertising_law.txt` | 广告法核心条款（第4/8/9/12/13/16/17/18/28条） |
| `data/platform_rules/internet_ad_rules.txt` | 互联网广告管理办法（第6/8/10/16条） |
| `data/cases/violation_cases.txt` | 5个违规案例 + 2个合规案例（参考） |
| `data/chroma_db/kb_dump.json` | 预构建的 Chroma 知识库（7个文档块） |

## 违规类型（6类）

虚假广告、绝对化用语、误导性对比、贬低竞争对手、必要信息缺失、公序良俗
