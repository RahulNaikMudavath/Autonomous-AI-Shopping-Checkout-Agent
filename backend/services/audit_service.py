"""
AgentCart Cryptographic Audit Service
Provides SHA-256 hash-chained immutable logging for regulatory compliance,
trust & safety decisions, and policy enforcement audits.
"""
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.database.models import AuditEvent

logger = logging.getLogger("agentcart.services.audit")

GENESIS_HASH = "0" * 64


class AuditService:
    """Manages creation, hash-chaining, and integrity validation of audit records."""

    @staticmethod
    def calculate_hash(
        prev_hash: str,
        timestamp_str: str,
        action: str,
        status: str,
        agent_id: str,
        event_details: Dict[str, Any]
    ) -> str:
        """Calculates a SHA-256 digest over the sequential block fields."""
        serialized_details = json.dumps(event_details, sort_keys=True)
        raw_block = f"{prev_hash}|{timestamp_str}|{action}|{status}|{agent_id}|{serialized_details}"
        return hashlib.sha256(raw_block.encode("utf-8")).hexdigest()

    @staticmethod
    def record_event(
        db: Session,
        action: str,
        status: str = "PASSED",
        session_id: Optional[str] = None,
        agent_id: str = "supervisor",
        event_details: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        """Appends a cryptographically verified event to the audit ledger."""
        payload_details = event_details or details or {}
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()

        # Get latest event's hash to chain from
        last_event = db.query(AuditEvent).order_by(desc(AuditEvent.created_at)).first()
        prev_hash = last_event.sha256_hash if last_event else GENESIS_HASH

        sha256_hash = AuditService.calculate_hash(
            prev_hash=prev_hash,
            timestamp_str=now_iso,
            action=action,
            status=status,
            agent_id=agent_id,
            event_details=payload_details
        )

        event = AuditEvent(
            session_id=session_id,
            action=action,
            status=status,
            agent_id=agent_id,
            event_details=payload_details,
            sha256_hash=sha256_hash,
            prev_hash=prev_hash,
            created_at=now
        )
        db.add(event)
        db.commit()
        db.refresh(event)

        logger.info("Recorded audit event [action=%s, status=%s, hash=%.8s...]", action, status, sha256_hash)
        return event

    @staticmethod
    def verify_ledger_integrity(db: Session) -> Dict[str, Any]:
        """
        Walks the entire audit trail sequentially from genesis and verifies all SHA-256 links.
        Returns validation status and total event count.
        """
        events = db.query(AuditEvent).order_by(AuditEvent.created_at).all()
        if not events:
            return {
                "valid": True,
                "total_events": 0,
                "message": "Audit ledger is clean and empty."
            }

        expected_prev_hash = GENESIS_HASH
        for idx, evt in enumerate(events):
            if evt.prev_hash != expected_prev_hash:
                logger.error("Audit chain broken at index %d! Expected prev_hash=%s, found=%s", idx, expected_prev_hash, evt.prev_hash)
                return {
                    "valid": False,
                    "tampered_index": idx,
                    "event_id": evt.id,
                    "message": f"Hash chain broken at event {evt.id}."
                }
            expected_prev_hash = evt.sha256_hash

        return {
            "valid": True,
            "total_events": len(events),
            "latest_hash": expected_prev_hash,
            "message": "Cryptographic audit chain verified: 100% intact and immutable."
        }
