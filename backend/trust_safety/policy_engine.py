"""
Layer 5: Trust & Safety - Policy Guardrails, Prompt Injection Defense & Cryptographic Audit
Enforces user spending constraints, authorization boundaries, and tamper-evident audit logging.
"""
import hashlib
import json
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from backend.schemas import (
    SpendingPolicy, PolicyCheckResult, PromptInjectionScanResult, AuditBlock, Product
)

# Global Active Policy
CURRENT_POLICY = SpendingPolicy(
    max_budget_limit_inr=150000.0,
    single_item_approval_threshold_inr=50000.0,
    daily_velocity_limit_inr=200000.0,
    allowed_categories=["laptops", "gpus", "monitors", "electronics", "accessories"],
    blocked_merchants=[],
    trusted_merchants_only=True,
    auto_approve_under_threshold=True,
    prompt_injection_defense_enabled=True
)

# Cryptographic Audit Ledger (Append-only blockchain-style ledger)
AUDIT_LEDGER: List[AuditBlock] = []

# Genesis Hash
GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

def get_current_policy() -> SpendingPolicy:
    return CURRENT_POLICY

def update_policy(new_policy: SpendingPolicy) -> SpendingPolicy:
    global CURRENT_POLICY
    CURRENT_POLICY = new_policy
    add_audit_log(
        action_type="POLICY_UPDATE",
        actor="USER",
        payload_summary=f"Updated policy: Max Budget ₹{new_policy.max_budget_limit_inr:,.0f}, Approval Threshold ₹{new_policy.single_item_approval_threshold_inr:,.0f}",
        policy_verified=True
    )
    return CURRENT_POLICY

def evaluate_spending_policy(product: Product, user_max_budget: Optional[float] = None) -> PolicyCheckResult:
    """
    Evaluates product purchase against active spending policies and human-in-the-loop triggers.
    """
    violations = []
    warnings = []
    requires_human_approval = False
    
    # 1. Check Global Ceiling
    effective_budget = user_max_budget if user_max_budget else CURRENT_POLICY.max_budget_limit_inr
    if product.price_inr > effective_budget:
        violations.append(
            f"Price ₹{product.price_inr:,.2f} exceeds effective budget ceiling ₹{effective_budget:,.2f}"
        )
        
    # 2. Check Single-Item Human-in-the-Loop Threshold
    if product.price_inr >= CURRENT_POLICY.single_item_approval_threshold_inr:
        requires_human_approval = True
        warnings.append(
            f"High-value purchase (₹{product.price_inr:,.2f} >= ₹{CURRENT_POLICY.single_item_approval_threshold_inr:,.2f} threshold). Requires explicit User Authorization."
        )
        
    # 3. Check Category Whitelist
    if product.category.lower() not in [c.lower() for c in CURRENT_POLICY.allowed_categories]:
        violations.append(f"Category '{product.category}' is not in allowed categories.")
        
    # 4. Check Merchant Blocklist
    if product.merchant_id in CURRENT_POLICY.blocked_merchants:
        violations.append(f"Merchant '{product.merchant_name}' ({product.merchant_id}) is blocked by user policy.")

    passed = len(violations) == 0
    return PolicyCheckResult(
        passed=passed,
        requires_human_approval=requires_human_approval,
        policy_violations=violations,
        warning_notes=warnings,
        spending_ceiling_ok=passed,
        single_item_threshold_triggered=requires_human_approval,
        merchant_trusted=product.merchant_id not in CURRENT_POLICY.blocked_merchants
    )

# Prompt Injection Attack Patterns
INJECTION_SIGNATURES = [
    r"ignore\s+(previous|all|the\s+above)\s+instructions",
    r"disregard\s+(all\s+prior|safety)\s+rules",
    r"you\s+are\s+now\s+in\s+(developer|unrestricted|god)\s+mode",
    r"system\s*override",
    r"bypass\s+(spending\s+limit|policy|approval|budget)",
    r"ship\s+to\s+attacker",
    r"transfer\s+(funds|crypto|bitcoin|eth)",
    r"do\s+not\s+ask\s+for\s+confirmation",
    r"secretly\s+purchase",
    r"<script.*?>",
    r"javascript:"
]

def scan_for_prompt_injection(user_input: str) -> PromptInjectionScanResult:
    """
    Scans natural language queries and external strings for adversarial jailbreaks or prompt injections.
    """
    if not CURRENT_POLICY.prompt_injection_defense_enabled:
        return PromptInjectionScanResult(
            is_malicious=False,
            threat_level="safe",
            detected_patterns=[],
            sanitized_input=user_input
        )
        
    detected = []
    for pattern in INJECTION_SIGNATURES:
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            detected.append(match.group(0))
            
    is_malicious = len(detected) > 0
    threat_level = "critical" if any("bypass" in d.lower() or "ignore" in d.lower() for d in detected) else ("medium" if is_malicious else "safe")
    
    # Sanitization
    sanitized = user_input
    for d in detected:
        sanitized = re.sub(re.escape(d), "[REDACTED_SECURITY_THREAT]", sanitized, flags=re.IGNORECASE)
        
    if is_malicious:
        add_audit_log(
            action_type="INJECTION_BLOCKED",
            actor="AGENT",
            payload_summary=f"Blocked prompt injection attempt. Detected: {', '.join(detected)}",
            policy_verified=False
        )
        
    return PromptInjectionScanResult(
        is_malicious=is_malicious,
        threat_level=threat_level,
        detected_patterns=detected,
        sanitized_input=sanitized
    )

def calculate_block_hash(
    index: int,
    timestamp: str,
    action_type: str,
    actor: str,
    payload_summary: str,
    previous_hash: str
) -> str:
    raw_data = f"{index}|{timestamp}|{action_type}|{actor}|{payload_summary}|{previous_hash}"
    return hashlib.sha256(raw_data.encode("utf-8")).hexdigest()

def add_audit_log(
    action_type: Optional[str] = None,
    actor: str = "AGENT",
    payload_summary: str = "",
    policy_verified: bool = True,
    action: Optional[str] = None,
    status: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> AuditBlock:
    """
    Appends a cryptographically verified SHA-256 block to the immutable audit ledger.
    """
    final_action = action_type or action or "SYSTEM_EVENT"
    final_summary = payload_summary or (str(details) if details else "")
    final_verified = policy_verified if status is None else (status == "PASSED")

    index = len(AUDIT_LEDGER)
    timestamp = datetime.now(timezone.utc).isoformat()
    previous_hash = AUDIT_LEDGER[-1].current_hash if AUDIT_LEDGER else GENESIS_HASH
    
    current_hash = calculate_block_hash(
        index=index,
        timestamp=timestamp,
        action_type=final_action,
        actor=actor,
        payload_summary=final_summary,
        previous_hash=previous_hash
    )
    
    block = AuditBlock(
        block_index=index,
        timestamp=timestamp,
        action_type=final_action,
        actor=actor,
        payload_summary=final_summary,
        previous_hash=previous_hash,
        current_hash=current_hash,
        policy_verified=final_verified
    )
    AUDIT_LEDGER.append(block)
    return block

def get_audit_ledger() -> List[AuditBlock]:
    return AUDIT_LEDGER

def verify_audit_ledger_integrity() -> Dict[str, Any]:
    """
    Verifies that no block in the audit ledger has been tampered with.
    """
    if not AUDIT_LEDGER:
        return {"valid": True, "total_blocks": 0, "message": "Ledger is empty"}
        
    for i, block in enumerate(AUDIT_LEDGER):
        expected_prev = GENESIS_HASH if i == 0 else AUDIT_LEDGER[i-1].current_hash
        if block.previous_hash != expected_prev:
            return {
                "valid": False,
                "broken_block_index": i,
                "message": f"Previous hash mismatch at block {i}"
            }
            
        recalculated_hash = calculate_block_hash(
            index=block.block_index,
            timestamp=block.timestamp,
            action_type=block.action_type,
            actor=block.actor,
            payload_summary=block.payload_summary,
            previous_hash=block.previous_hash
        )
        if recalculated_hash != block.current_hash:
            return {
                "valid": False,
                "broken_block_index": i,
                "message": f"Hash corruption detected at block {i}"
            }
            
    return {
        "valid": True,
        "total_blocks": len(AUDIT_LEDGER),
        "message": f"All {len(AUDIT_LEDGER)} blocks cryptographically verified intact"
    }

# Initialize with System Start block
if not AUDIT_LEDGER:
    add_audit_log(
        action_type="SYSTEM_INIT",
        actor="AGENT",
        payload_summary="AgentCart Trust & Safety Engine initialized with active policies.",
        policy_verified=True
    )
