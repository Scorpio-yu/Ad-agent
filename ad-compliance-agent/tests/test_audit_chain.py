"""测试审核链路 — JSON 解析与输出 Schema。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.chains.audit_chain import AdAuditChain

REQUIRED_KEYS = {
    "is_violation", "violation_type", "risk_level",
    "risk_keywords", "violation_clauses", "reason", "suggestion",
}


def test_parse_valid_json():
    chain = AdAuditChain()
    raw = '{"is_violation": true, "risk_level": "high"}'
    parsed = chain._parse_response(raw)
    assert parsed["is_violation"] is True


def test_parse_markdown_wrapped_json():
    chain = AdAuditChain()
    raw = '```json\n{"is_violation": false}\n```'
    parsed = chain._parse_response(raw)
    assert parsed["is_violation"] is False


def test_parse_invalid_json_fallback():
    chain = AdAuditChain()
    parsed = chain._parse_response("not valid json")
    assert "JSON parse failed" in parsed["reason"]


def test_output_has_all_keys():
    chain = AdAuditChain()
    result = chain.audit("测试广告")
    for key in REQUIRED_KEYS:
        assert key in result, f"缺少字段: {key}"
