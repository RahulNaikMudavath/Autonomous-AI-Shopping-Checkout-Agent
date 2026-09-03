"""
Layer 5: Trust & Safety - Untrusted Content Sanitizer & Prompt Injection Defense
Defends against Indirect Prompt Injection attacks inside merchant product listings, descriptions, and metadata.

Flow:
Merchant content ➔ Untrusted context ➔ Sanitizer ➔ Policy boundary ➔ LLM

Result upon attack:
⚠ Untrusted instruction detected.
Ignoring merchant instruction.
Continuing according to user policy.
"""
import re
import hashlib
from typing import Dict, List, Any, Tuple, Optional
from enum import Enum
from pydantic import BaseModel, Field

from backend.trust_safety.policy_engine import add_audit_log

class ThreatSeverity(str, Enum):
    CLEAN = "CLEAN"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class SanitizationResult(BaseModel):
    is_safe: bool
    threat_severity: ThreatSeverity
    injections_detected: List[str]
    raw_untrusted_content: str
    sanitized_clean_content: str
    security_alert_message: Optional[str] = None
    policy_boundary_intact: bool = True
    audit_hash: str

class UntrustedContentSanitizer:
    INJECTION_PATTERNS = [
        (r'(?i)\bsystem\s*message\s*:', "System Message Impersonation"),
        (r'(?i)\bignore\s+(?:all\s+)?(?:the\s+)?(?:previous|prior|user[\'’]?s?)\s+(?:instructions|rules|prompts|budget|policy|constraints)', "Instruction/Budget Override Directive"),
        (r'(?i)\bignore\s+(?:the\s+)?(?:user[\'’]?s?\s+)?budget\b', "Budget Override Injection"),
        (r'(?i)\bpurchase\s+immediately\b', "Forced Purchase Trigger"),
        (r'(?i)\bapprove\s+without\s+(?:pin|auth|confirmation|approval)\b', "Authorization Bypass Attempt"),
        (r'(?i)\bdisregard\s+(?:safety|spending|policy|limit)\b', "Safety Boundary Disregard"),
        (r'(?i)\bset\s+price\s+to\s+(?:0|zero|free)\b', "Zero-Price Cart Exploit"),
        (r'(?i)\bextract\s+(?:auth|token|password|pin|credentials)\b', "Credential Exfiltration Attempt"),
        (r'(?i)\bhttps?://[^\s]+(?:leak|exfil|webhook|evil)', "Suspicious Webhook Target"),
        (r'(?i)<\s*script[^>]*>.*?<\s*/\s*script\s*>', "Embedded Script Tag"),
        (r'(?i)<!--\s*#system\b.*?-->', "Hidden System Comment Injection")
    ]

    @classmethod
    def sanitize_merchant_content(
        cls,
        raw_text: str,
        merchant_name: str = "Unknown Merchant",
        source_field: str = "product_description"
    ) -> SanitizationResult:
        """
        Passes third-party merchant content through the untrusted context sanitizer
        before any LLM or policy evaluator sees it.
        """
        injections = []
        sanitized_text = raw_text

        # Scan against known attack patterns
        for pattern, label in cls.INJECTION_PATTERNS:
            matches = re.findall(pattern, raw_text)
            if matches:
                injections.append(f"{label} (Pattern matched: '{matches[0]}')")
                # Redact or strip the injection from sanitized output
                sanitized_text = re.sub(pattern, "[UNTRUSTED_INSTRUCTION_REDACTED]", sanitized_text)

        # Remove extra whitespace left from redactions
        sanitized_text = re.sub(r'\n{3,}', '\n\n', sanitized_text).strip()

        is_safe = len(injections) == 0
        severity = ThreatSeverity.CLEAN
        security_alert = None

        if not is_safe:
            if any("System Message" in inj or "Override" in inj for inj in injections):
                severity = ThreatSeverity.CRITICAL
            else:
                severity = ThreatSeverity.HIGH

            security_alert = (
                "⚠ Untrusted instruction detected.\n"
                "Ignoring merchant instruction.\n"
                "Continuing according to user policy."
            )

            # Log to immutable cryptographic audit ledger
            add_audit_log(
                action_type="INJECTION_BLOCKED",
                actor="UNTRUSTED_MERCHANT_SANITIZER",
                payload_summary=f"Blocked {len(injections)} injection(s) from {merchant_name} in {source_field}. Alerts: {'; '.join(injections)}",
                policy_verified=True
            )

        audit_hash = hashlib.sha256(f"{raw_text}:{is_safe}:{severity.value}".encode()).hexdigest()

        return SanitizationResult(
            is_safe=is_safe,
            threat_severity=severity,
            injections_detected=injections,
            raw_untrusted_content=raw_text,
            sanitized_clean_content=sanitized_text,
            security_alert_message=security_alert,
            policy_boundary_intact=True,
            audit_hash=audit_hash
        )

    @classmethod
    def create_untrusted_wrapper(cls, raw_content: str, merchant_id: str) -> str:
        """
        Wraps untrusted merchant content in strict data isolation boundaries for LLMs.
        """
        sanitization = cls.sanitize_merchant_content(raw_content, merchant_id)
        return (
            f"<untrusted_merchant_data source='{merchant_id}' is_safe='{sanitization.is_safe}'>\n"
            f"{sanitization.sanitized_clean_content}\n"
            f"</untrusted_merchant_data>"
        )
