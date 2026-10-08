"""
Pydantic 数据模型 — 输入/输出 Schema。
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class ViolationClause(BaseModel):
    """违规涉及的法条。"""
    law: str = Field(description="法规名称")
    article: str = Field(description="条款编号")
    content: str = Field(description="条款原文摘要")


class AuditResult(BaseModel):
    """LLM 返回的结构化审核结果。"""
    is_violation: bool = Field(description="是否违规")
    violation_type: str = Field(default="", description="违规类型")
    risk_level: str = Field(description="high / medium / low / none")
    risk_keywords: List[str] = Field(description="风险关键词")
    violation_clauses: List[ViolationClause] = Field(description="违规依据法规条款")
    reason: str = Field(description="判定理由")
    suggestion: str = Field(description="修改建议，合规时为空")


class AuditRequest(BaseModel):
    """API 请求体。"""
    ad_content: str = Field(
        description="广告文案",
        min_length=1,
        max_length=5000,
        examples=["某某面膜，三天美白，效果最好！"],
    )


class AuditResponse(BaseModel):
    """API 响应体。"""
    success: bool
    data: Optional[AuditResult] = None
    error: Optional[str] = None
