from __future__ import annotations

import json
from typing import Any

from google import genai
from google.genai import types

from src.config import (
    CLASSIFIER_TEMPERATURE,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    PERSONAS,
)
from src.escalator import detect_sensitive_topic
from src.gemini_utils import call_gemini_with_backoff, is_gemini_quota_error

TECHNICAL_HINTS = [
    "api",
    "token",
    "bearer",
    "header",
    "401",
    "403",
    "database",
    "integration",
    "config",
    "endpoint",
    "webhook",
    "oauth",
    "sso",
    "error code",
    "logs",
    "implementation",
]
FRUSTRATED_HINTS = [
    "frustrated",
    "hour",
    "waiting",
    "nothing",
    "loading",
    "help",
    "urgent",
    "asap",
    "terrible",
    "awful",
    "demand",
]
BUSINESS_HINTS = [
    "timeline",
    "uptime",
    "roi",
    "business",
    "operational",
    "executive",
    "sla",
    "contract",
    "disputes",
    "billing statement",
]


def _get_client() -> genai.Client:
    if not GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY is not set. Copy .env.example to .env and add your key."
        )
    return genai.Client(api_key=GEMINI_API_KEY)


def classify_customer_persona_heuristic(user_message: str) -> dict[str, Any]:
    """Rule-based fallback when the Gemini API is unavailable."""
    lowered = user_message.lower()
    scores = {
        "Technical Expert": sum(1 for hint in TECHNICAL_HINTS if hint in lowered),
        "Frustrated User": sum(1 for hint in FRUSTRATED_HINTS if hint in lowered)
        + (2 if "!" in user_message else 0),
        "Business Executive": sum(1 for hint in BUSINESS_HINTS if hint in lowered),
    }
    persona = max(scores, key=scores.get)
    if scores[persona] == 0:
        persona = "Frustrated User"

    return {
        "persona": persona,
        "confidence": 0.55,
        "reasoning": (
            "Heuristic fallback used because the Gemini API quota was exceeded."
        ),
        "sensitive_topic": detect_sensitive_topic(user_message),
        "fallback": True,
    }


def classify_customer_persona(user_message: str) -> dict[str, Any]:
    """
    Analyze the user's message and classify it into one of three personas.
    Returns persona, confidence, reasoning, and sensitive_topic flag.
    """
    client = _get_client()

    system_instruction = (
        "You are an advanced classification engine. Analyze the sentiment, "
        "vocabulary, and tone of an incoming support message and classify it "
        "into exactly one of three customer personas:\n"
        "1. 'Technical Expert': Uses jargon, asks about APIs/code/configs.\n"
        "2. 'Frustrated User': Uses emotional language, exclamation marks, "
        "or mentions urgency.\n"
        "3. 'Business Executive': Focuses on business impact, ROI, timelines, "
        "and brevity.\n\n"
        "Also detect whether the message involves sensitive topics such as "
        "billing disputes, refund demands, legal concerns, or account modifications.\n\n"
        "Provide your evaluation strictly in the requested JSON structure."
    )

    response_schema = {
        "type": "OBJECT",
        "properties": {
            "persona": {
                "type": "STRING",
                "enum": PERSONAS,
            },
            "confidence": {"type": "NUMBER"},
            "reasoning": {"type": "STRING"},
            "sensitive_topic": {"type": "BOOLEAN"},
        },
        "required": ["persona", "confidence", "reasoning", "sensitive_topic"],
    }

    def _call():
        return client.models.generate_content(
            model=GEMINI_MODEL,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=response_schema,
                temperature=CLASSIFIER_TEMPERATURE,
            ),
        )

    try:
        response = call_gemini_with_backoff(_call)
        return json.loads(response.text)
    except Exception as exc:
        if is_gemini_quota_error(exc):
            return classify_customer_persona_heuristic(user_message)
        raise


if __name__ == "__main__":
    test_msg = (
        "Our production API key stopped working with a 401 Unauthorized block. "
        "Check our logs immediately."
    )
    result = classify_customer_persona(test_msg)
    print(json.dumps(result, indent=2))
