"""
RAG 广告合规审核链 — 核心审核流程。
链路：用户输入广告文案 → 检索法规 → 组装 Prompt → 调用 LLM → 解析 JSON

注意：必须先导入 retriever（触发 chromadb 初始化），再导入 langchain_openai，
否则在部分环境下会 segfault。
"""

import json

# chromadb 相关必须先于 langchain_openai 导入
from src.config import config
from src.retriever.hybrid_retriever import HybridRetriever
from src.prompts.templates import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage


class AdAuditChain:
    """广告合规审核主流程。"""

    def __init__(self):
        self.retriever = HybridRetriever()
        self.llm = ChatOpenAI(
            model=config.LLM_MODEL,
            temperature=config.LLM_TEMPERATURE,
            max_tokens=config.LLM_MAX_TOKENS,
            openai_api_key=config.OPENAI_API_KEY,
            openai_api_base=config.OPENAI_BASE_URL,
        )

    def _build_messages(self, ad_content: str) -> tuple[list, str]:
        """构建检索 + Prompt 组装（audit 和 audit_stream 共用）。"""
        results = self.retriever.retrieve(ad_content)
        regulation_context = self.retriever.format_context(results)
        user_message = USER_PROMPT_TEMPLATE.format(
            regulation_context=regulation_context,
            ad_content=ad_content,
        )
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_message),
        ]
        return messages, regulation_context

    def audit(self, ad_content: str) -> dict:
        messages, _ = self._build_messages(ad_content)
        response = self.llm.invoke(messages)
        return self._parse_response(response.content)

    def audit_stream(self, ad_content: str):
        """流式审核，逐 token yield SSE 事件。"""
        messages, _ = self._build_messages(ad_content)
        full_text = ""
        for chunk in self.llm.stream(messages):
            token = chunk.content if hasattr(chunk, "content") and chunk.content else ""
            if token:
                full_text += token
                yield f"data: {json.dumps({'token': token})}\n\n"
        # 发送完成信号 + 解析结果
        result = self._parse_response(full_text)
        yield f"data: {json.dumps({'done': True, 'result': result})}\n\n"
        yield "data: [DONE]\n\n"

    def _parse_response(self, raw: str) -> dict:
        raw = raw.strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            lines = [l for l in lines if not l.startswith("```")]
            raw = "\n".join(lines)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {
                "is_violation": False,
                "violation_type": "",
                "risk_level": "none",
                "risk_keywords": [],
                "violation_clauses": [],
                "reason": f"JSON parse failed, raw: {raw[:500]}",
                "suggestion": "",
            }
