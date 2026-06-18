from __future__ import annotations

from typing import Any

from google import genai
from google.genai import types

from src.config import GEMINI_API_KEY, GEMINI_MODEL, GENERATOR_TEMPERATURE
from src.escalator import generate_handoff_summary, should_escalate
from src.gemini_utils import call_gemini_with_backoff, is_gemini_quota_error


def _get_client() -> genai.Client:
    if not GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY is not set. Copy .env.example to .env and add your key."
        )
    return genai.Client(api_key=GEMINI_API_KEY)


def _fallback_response(persona: str, context_chunks: list[dict[str, Any]]) -> str:
    """Build a grounded response from retrieved docs when Gemini is unavailable."""
    if not context_chunks:
        return (
            "I couldn't find relevant documentation for your request. "
            "Please try rephrasing your question or contact support directly."
        )

    bullets = "\n".join(
        f"- {chunk['text'].strip()[:350]}{'...' if len(chunk['text']) > 350 else ''}"
        for chunk in context_chunks[:2]
    )

    if persona == "Frustrated User":
        intro = (
            "I'm sorry you're running into this — here's what our documentation says:"
        )
    elif persona == "Technical Expert":
        intro = "From our technical documentation:"
    else:
        intro = "Summary from our knowledge base:"

    return (
        f"{intro}\n\n{bullets}\n\n"
        "_Note: Gemini API quota was exceeded, so this answer was assembled "
        "directly from retrieved docs._"
    )


def _persona_instructions(persona: str) -> str:
    if persona == "Technical Expert":
        return (
            "You are a Senior Systems Engineer. Provide clear root-cause analysis, "
            "configuration specifications, and precise API pathways or code blocks. "
            "Keep technical descriptions exact and structured."
        )
    if persona == "Frustrated User":
        return (
            "You are a deeply empathetic, reassuring Customer Care Specialist. "
            "Begin with a warm, genuine validation of their difficulty. Use "
            "straightforward, reassuring, and simple action-oriented bullet steps. "
            "Avoid confusing jargon."
        )
    return (
        "You are a concise Client Relations Director. Focus on direct business "
        "outcomes, impact summaries, and timelines for resolution. Keep responses "
        "extremely brief, professional, and skip unnecessary configuration details."
    )


def generate_adaptive_response(
    user_query: str,
    persona: str,
    context_chunks: list[dict[str, Any]],
    classifier_result: dict[str, Any] | None = None,
    frustration_count: int = 0,
    conversation_history: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """
    Generate a persona-adaptive response grounded in retrieved documents.
    Escalates when confidence is low or sensitive topics are detected.
    """
    escalate, reason = should_escalate(
        user_query,
        context_chunks,
        classifier_result=classifier_result,
        frustration_count=frustration_count,
    )

    if escalate:
        return {
            "escalated": True,
            "escalation_reason": reason,
            "response": (
                "I apologize, but I am unable to safely resolve this request on my own. "
                "I am connecting you with a live human support specialist who can help "
                "you directly."
            ),
            "handoff_summary": generate_handoff_summary(
                user_query,
                persona,
                context_chunks,
                reason,
                conversation_history=conversation_history,
            ),
        }

    context_text = "\n\n".join(
        f"Source [{chunk['source']}]: {chunk['text']}" for chunk in context_chunks
    )
    full_system_prompt = (
        f"{_persona_instructions(persona)}\n\n"
        "CRITICAL RULES:\n"
        "- Base your response ONLY on the provided context.\n"
        "- Do not hallucinate or assume facts not found in the documents.\n"
        "- If the context is insufficient, say so clearly.\n\n"
        f"FACTUAL CONTEXT DOCUMENTS:\n{context_text}"
    )

    client = _get_client()

    def _call():
        return client.models.generate_content(
            model=GEMINI_MODEL,
            contents=user_query,
            config=types.GenerateContentConfig(
                system_instruction=full_system_prompt,
                temperature=GENERATOR_TEMPERATURE,
            ),
        )

    try:
        response = call_gemini_with_backoff(_call)
        return {
            "escalated": False,
            "escalation_reason": None,
            "response": response.text,
            "handoff_summary": None,
            "fallback": False,
        }
    except Exception as exc:
        if is_gemini_quota_error(exc):
            return {
                "escalated": False,
                "escalation_reason": None,
                "response": _fallback_response(persona, context_chunks),
                "handoff_summary": None,
                "fallback": True,
            }
        raise
