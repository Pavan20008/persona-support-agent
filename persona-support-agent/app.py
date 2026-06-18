"""Main Streamlit web UI for the persona-adaptive customer support agent."""

import os
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")
if not os.environ.get("GEMINI_API_KEY"):
    try:
        os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
    except (KeyError, FileNotFoundError, AttributeError):
        pass

from src.classifier import classify_customer_persona
from src.config import GEMINI_API_KEY, RETRIEVAL_CONFIDENCE_THRESHOLD, TOP_K
from src.generator import generate_adaptive_response
from src.rag_pipeline import LocalRAGPipeline

st.set_page_config(
    page_title="Adsparkx Support Agent",
    page_icon="🤖",
    layout="wide",
)

TEST_SCENARIOS = [
    {
        "label": "Frustrated User — Cookie issue",
        "message": (
            "Where is the guide to clear cookies? It's been an hour and nothing "
            "is loading on your interface!"
        ),
    },
    {
        "label": "Technical Expert — Bearer token",
        "message": (
            "What are the header parameter requirements for your bearer token "
            "auth implementation?"
        ),
    },
    {
        "label": "Business Executive — Billing timeline",
        "message": (
            "Our operational uptime is decreasing. We need a timeline of when "
            "billing disputes are resolved."
        ),
    },
    {
        "label": "Technical Expert — Database errors",
        "message": (
            "I'm experiencing an issue with your database integration that's "
            "causing internal errors."
        ),
    },
    {
        "label": "Escalation — Duplicate charges",
        "message": (
            "My billing statement has unexpected duplicate charges. "
            "I demand an immediate refund!"
        ),
    },
]


@st.cache_resource
def get_rag_pipeline() -> LocalRAGPipeline:
    pipeline = LocalRAGPipeline()
    if pipeline.is_index_empty():
        with st.spinner("Indexing knowledge base documents (first run only)..."):
            stats = pipeline.ingest_data_directory()
            st.session_state["ingest_stats"] = stats
    return pipeline


def init_session_state() -> None:
    defaults = {
        "messages": [],
        "frustration_count": 0,
        "last_persona": None,
        "status_message": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _format_gemini_error(exc: Exception) -> str:
    message = str(exc)
    if "limit: 0" in message and "gemini-2.0-flash" in message:
        return (
            "The configured Gemini model is no longer available (gemini-2.0-flash was "
            "shut down). Set GEMINI_MODEL=gemini-2.5-flash in your .env file and restart."
        )
    if "RESOURCE_EXHAUSTED" in message or "429" in message:
        return (
            "Gemini API quota exceeded. Check usage at https://ai.dev/rate-limit, "
            "wait for the daily limit to reset, or enable billing on your Google AI project."
        )
    return f"Gemini API error: {message}"


def process_message(user_message: str, pipeline: LocalRAGPipeline) -> bool:
    """Process a user message. Returns True on success, False on failure."""
    st.session_state.status_message = None
    st.session_state.messages.append({"role": "user", "content": user_message})

    try:
        with st.spinner("Classifying persona..."):
            classification = classify_customer_persona(user_message)
    except Exception as exc:
        st.session_state.messages.pop()
        st.session_state.status_message = ("error", _format_gemini_error(exc))
        return False

    persona = classification.get("persona", "Frustrated User")
    if persona == "Frustrated User":
        st.session_state.frustration_count += 1
    else:
        st.session_state.frustration_count = 0
    st.session_state.last_persona = persona

    with st.spinner("Retrieving relevant documentation..."):
        context_chunks = pipeline.retrieve_context(user_message, top_k=TOP_K)

    try:
        with st.spinner("Generating adaptive response..."):
            result = generate_adaptive_response(
                user_query=user_message,
                persona=persona,
                context_chunks=context_chunks,
                classifier_result=classification,
                frustration_count=st.session_state.frustration_count,
                conversation_history=st.session_state.messages,
            )
    except Exception as exc:
        st.session_state.messages.pop()
        st.session_state.status_message = ("error", _format_gemini_error(exc))
        return False

    if classification.get("fallback") or result.get("fallback"):
        st.session_state.status_message = (
            "warning",
            "Gemini API quota exceeded — using fallback mode. Responses are built "
            "from heuristics and retrieved docs. Check usage at "
            "https://ai.dev/rate-limit or wait for your daily limit to reset.",
        )

    assistant_payload = {
        "role": "assistant",
        "content": result["response"],
        "persona": persona,
        "classification": classification,
        "context_chunks": context_chunks,
        "escalated": result["escalated"],
        "escalation_reason": result.get("escalation_reason"),
        "handoff_summary": result.get("handoff_summary"),
    }
    st.session_state.messages.append(assistant_payload)
    return True


def render_sidebar() -> None:
    st.sidebar.title("Support Agent")
    st.sidebar.markdown(
        "Persona-adaptive RAG-powered customer support with human escalation."
    )

    if not GEMINI_API_KEY:
        st.sidebar.error("Set GEMINI_API_KEY in your .env file to enable the agent.")
    else:
        st.sidebar.success("API key configured")

    if st.session_state.get("ingest_stats"):
        with st.sidebar.expander("Knowledge base index"):
            for doc, chunks in st.session_state["ingest_stats"].items():
                st.write(f"- {doc}: {chunks} chunks")

    st.sidebar.markdown("---")
    st.sidebar.subheader("Test Scenarios")
    for scenario in TEST_SCENARIOS:
        if st.sidebar.button(scenario["label"], use_container_width=True):
            st.session_state["pending_scenario"] = scenario["message"]
            st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.caption(f"Retrieval threshold: {RETRIEVAL_CONFIDENCE_THRESHOLD}")
    if st.sidebar.button("Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.frustration_count = 0
        st.session_state.last_persona = None
        st.session_state.status_message = None
        st.rerun()


def render_chat(pipeline: LocalRAGPipeline) -> None:
    st.title("Adsparkx Persona-Adaptive Support Agent")
    st.caption(
        "Messages are classified by persona, grounded in your knowledge base, "
        "and escalated when confidence is low or topics are sensitive."
    )

    status = st.session_state.get("status_message")
    if status:
        level, message = status
        if level == "error":
            st.error(message)
        else:
            st.warning(message)

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant":
                cols = st.columns(3)
                cols[0].caption(f"Persona: **{message.get('persona', 'N/A')}**")
                if message.get("escalated"):
                    cols[1].error(f"Escalated: {message.get('escalation_reason')}")
                else:
                    cols[1].success("Resolved by agent")

                if message.get("context_chunks"):
                    with st.expander("Retrieved context"):
                        for chunk in message["context_chunks"]:
                            st.markdown(
                                f"**{chunk['source']}** (score: {chunk['score']:.3f})"
                            )
                            st.text(chunk["text"][:400] + "...")

                if message.get("handoff_summary"):
                    with st.expander("Human handoff JSON"):
                        st.code(message["handoff_summary"], language="json")

                classification = message.get("classification")
                if classification:
                    with st.expander("Classification details"):
                        st.json(classification)

    pending = st.session_state.pop("pending_scenario", None)
    if pending:
        if not GEMINI_API_KEY:
            st.session_state.status_message = (
                "error",
                "Configure GEMINI_API_KEY in .env before chatting.",
            )
        elif process_message(pending, pipeline):
            st.rerun()

    if prompt := st.chat_input("Describe your support issue..."):
        if not GEMINI_API_KEY:
            st.session_state.status_message = (
                "error",
                "Configure GEMINI_API_KEY in .env before chatting.",
            )
        elif process_message(prompt, pipeline):
            st.rerun()


def main() -> None:
    init_session_state()
    render_sidebar()

    try:
        pipeline = get_rag_pipeline()
    except ValueError as exc:
        st.error(str(exc))
        st.info("Copy `.env.example` to `.env` and add your Gemini API key.")
        return

    render_chat(pipeline)


if __name__ == "__main__":
    main()
