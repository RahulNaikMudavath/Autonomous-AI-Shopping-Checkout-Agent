"""
Phase 5: Autonomous AI Shopping Agent Policy Tools
Sandboxed read-only tools for evaluating proposed purchases against safety and spending guardrails.
Guaranteed safe: No tool in this module can approve purchases, modify policies, execute payments, or place orders.
"""
import logging
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from backend.services.policy_engine import PolicyEngine

logger = logging.getLogger("agentcart.agent.tools.policy")


class PolicyTools:
    """
    Sandboxed policy evaluation tool suite.
    """

    @staticmethod
    def evaluate_purchase_policy(
        db: Session,
        quote_id: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluates an authoritative checkout quote against the active purchase policy.
        Returns the deterministic decision (ALLOW, REQUIRE_AUTHORIZATION, DENY), reason codes, and human explanation.
        """
        eval_res = PolicyEngine.evaluate_quote_against_policy(
            db=db,
            quote_id=quote_id,
            caller_session_id=session_id
        )
        return {
            "decision": eval_res.decision.value,
            "reason_codes": eval_res.reason_codes,
            "human_explanation": eval_res.human_explanation,
            "grand_total": str(eval_res.grand_total),
            "policy_id": eval_res.policy_id,
            "policy_version": eval_res.policy_version,
            "evaluated_at": eval_res.evaluated_at
        }
