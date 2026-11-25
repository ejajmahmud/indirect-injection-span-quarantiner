"""Core indirect prompt-injection detector and nonce-fenced data quarantiner."""
import re
import secrets
from typing import Any, Dict, List


class InjectionQuarantiner:
    """Detects imperative prompt-injection lines in untrusted tool text and fences payloads."""

    INJECTION_PATTERNS = [
        re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions", re.I),
        re.compile(r"(reveal|print|exfiltrate|send)\s+(your\s+)?(system\s+prompt|api\s+key|secret|env)", re.I),
        re.compile(r"you\s+are\s+now\s+(in\s+)?developer\s+mode", re.I),
        re.compile(r"override\s+safety\s+(rules|policy|guardrails)", re.I),
    ]

    def sanitize(self, untrusted_text: str, source: str = "external_tool") -> Dict[str, Any]:
        redacted_lines: List[int] = []
        clean_lines: List[str] = []

        for idx, line in enumerate(untrusted_text.splitlines(), 1):
            matched = any(p.search(line) for p in self.INJECTION_PATTERNS)
            if matched:
                redacted_lines.append(idx)
                clean_lines.append(f"[QUARANTINED_INJECTION_LINE_{idx}]")
            else:
                clean_lines.append(line)

        nonce = secrets.token_hex(6)
        fenced = f"<untrusted_data source=\"{source}\" nonce=\"{nonce}\">\n" + "\n".join(clean_lines) + f"\n</untrusted_data nonce=\"{nonce}\">"
        risk_score = min(100, len(redacted_lines) * 45)
        return {
            "risk_score": risk_score,
            "quarantined": len(redacted_lines) > 0,
            "redacted_lines": redacted_lines,
            "nonce": nonce,
            "fenced_payload": fenced,
        }
