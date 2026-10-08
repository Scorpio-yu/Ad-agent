"""API 路由 — POST /api/v1/audit  + POST /api/v1/audit/stream"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from src.models.schemas import AuditRequest, AuditResponse

router = APIRouter(prefix="/api/v1", tags=["audit"])

_chain = None


def _get_chain():
    global _chain
    if _chain is None:
        from src.chains.audit_chain import AdAuditChain
        _chain = AdAuditChain()
    return _chain


@router.post("/audit", response_model=AuditResponse)
async def audit(request: AuditRequest) -> AuditResponse:
    """提交广告文案进行合规审核。"""
    try:
        result = _get_chain().audit(request.ad_content)
        return AuditResponse(success=True, data=result)
    except Exception as e:
        return AuditResponse(success=False, error=str(e))


@router.post("/audit/stream")
async def audit_stream(request: AuditRequest):
    """流式审核——逐 token 推送 SSE 事件。"""
    chain = _get_chain()
    return StreamingResponse(
        chain.audit_stream(request.ad_content),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
