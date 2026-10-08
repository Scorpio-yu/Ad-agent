"""
命令行审核工具。
用法：python scripts/run_audit.py "广告文案"
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.chains.audit_chain import AdAuditChain


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_audit.py \"ad content\"")
        print("Example: python scripts/run_audit.py \"Best product ever!\"")
        return

    ad_content = sys.argv[1]
    chain = AdAuditChain()

    print("Auditing...")
    result = chain.audit(ad_content)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
