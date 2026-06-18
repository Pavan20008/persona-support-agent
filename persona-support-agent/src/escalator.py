from __future__ import annotations

import json
from typing import Any

from src.config import RETRIEVAL_CONFIDENCE_THRESHOLD, SENSITIVE_KEYWORDS


def detect_sensitive_topic(user_message: str, classifier_sensitive: bool = False) -> bool:
    """Detect billing, legal, refund, or account-modification issues."""
    if classifier_sensitive:
        return True

    lowered = user_message.lower()
    return any(keyword in lowered for keyword in SENSITIVE_KEYWORDS)


def should_escalate(
    user_message: str,
    context_chunks: list[dict[str, Any]],
    classifier_result: dict[str, Any] | None = None,
    frustration_count: int = 0,
) -> tuple[bool, str]:
    """
    Determine whether the conversation should be escalated to a human agent.
    Returns (should_escalate, reason).
    """
    classifier_result = classifier_result or {}
    best_score = max((chunk["score"] for chunk in context_chunks), default=0.0)

    if not context_chunks or best_score < RETRIEVAL_CONFIDENCE_THRESHOLD:
        return True, "low_retrieval_confidence"

    if detect_sensitive_topic(
        user_message,
        classifier_sensitive=classifier_result.get("sensitive_topic", False),
    ):
        return True, "sensitive_topic"

    if (
        classifier_result.get("persona") == "Frustrated User"
        and frustration_count >= 2
    ):
        return True, "repeated_frustration"

    return False, ""


def generate_handoff_summary(
    user_query: str,
    persona: str,
    context_chunks: list[dict[str, Any]],
    escalation_reason: str,
    conversation_history: list[dict[str, str]] | None = None,
) -> str:
    """Compile structured JSON handoff data for a human support specialist."""
    best_score = max((chunk["score"] for chunk in context_chunks), default=0.0)
    handoff_data = {
        "escalation_reason": escalation_reason,
        "persona": persona,
        "detected_issue": user_query,
        "retrieved_sources": [chunk["source"] for chunk in context_chunks],
        "confidence_score": round(best_score, 4),
        "conversation_turns": len(conversation_history or []),
        "attempted_context_snippets": [
            chunk["text"][:200] + ("..." if len(chunk["text"]) > 200 else "")
            for chunk in context_chunks[:3]
        ],
        "recommended_action": _recommended_action(escalation_reason),
    }
    return json.dumps(handoff_data, indent=2)


def _recommended_action(reason: str) -> str:
    actions = {
        "low_retrieval_confidence": (
            "Review knowledge base gaps, verify customer intent, and provide "
            "a documented resolution path."
        ),
        "sensitive_topic": (
            "Route to billing or account specialist. Verify charges, refund "
            "eligibility, and legal/compliance requirements before responding."
        ),
        "repeated_frustration": (
            "Prioritize empathetic human outreach, acknowledge prior failed "
            "attempts, and provide a concrete resolution timeline."
        ),
    }
    return actions.get(reason, "Contact the customer directly with a tailored resolution.")
