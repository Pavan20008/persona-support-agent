# persona-support-agent
# Persona-Adaptive Customer Support Agent

An intelligent customer support agent that classifies user communication style, retrieves answers from a local knowledge base via RAG, adapts responses to three personas, and escalates to human agents when confidence is low or topics are sensitive.

Built for the **Adsparkx AI Assignment**.

## Architecture

```
[User Message] ──> [Persona Classifier] ──> [Persona Tag: Tech/Frustrated/Exec]
                        │
                        ▼
                [Vector Database] ──> [Cosine Similarity Search] ──> [Top-K Chunks]
                        │
                        ▼
            [Adaptive Prompt Engine] ──> (Retrieval Quality Check)
                        │                                  │
                        │ (Sufficient Info Found)          │ (Confidence Low / Sensitive Issue)
                        ▼                                  ▼
             [Generate Adaptive Response]         [Escalate to Human Agent]
                                                           │
                                                           ▼
                                                [Generate Handoff JSON]
```

## Features

- **Persona classification** — Technical Expert, Frustrated User, Business Executive
- **RAG pipeline** — ChromaDB + Gemini `gemini-embedding-001` embeddings
- **LLM** — `gemini-2.5-flash` for classification and generation (override with `GEMINI_MODEL`)
- **Adaptive responses** — Persona-specific system prompts grounded in retrieved docs
- **Escalation engine** — Low retrieval confidence, sensitive topics, repeated frustration
- **Streamlit UI** — Interactive chat with test scenarios and handoff JSON display

## Project Structure

```
persona-support-agent/
├── data/                    # Knowledge base (txt, md, pdf)
├── src/
│   ├── config.py            # Thresholds and settings
│   ├── classifier.py        # Persona detection
│   ├── rag_pipeline.py      # Chunking, embedding, retrieval
│   ├── generator.py         # Adaptive LLM responses
│   └── escalator.py         # Escalation logic & handoff JSON
├── scripts/
│   └── generate_pdf.py      # Creates password_reset_guide.pdf
├── app.py                   # Streamlit web UI
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

### 1. Prerequisites

- Python 3.11+
- [Google Gemini API key](https://aistudio.google.com/app/apikey)

### 2. Install

```bash
cd persona-support-agent
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env and set your GEMINI_API_KEY
# Optional: GEMINI_MODEL=gemini-2.5-flash (default; do not use gemini-2.0-flash — shut down 2026-06-01)
```

### 4. Generate the PDF knowledge base file

```bash
python scripts/generate_pdf.py
```

### 5. Run the app

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

## Knowledge Base

The `data/` folder contains 16 support articles covering:

- API troubleshooting and authentication
- Billing, refunds, and SLA timelines
- Password reset (PDF), cookie clearing, 2FA
- Database integration, webhooks, SSO, rate limits

On first launch, documents are chunked (500 chars, 50 overlap), embedded with Gemini, and stored in `./chroma_db/`. Subsequent runs reuse the persistent index.

## Escalation Triggers

| Trigger | Condition |
|---------|-----------|
| Low retrieval confidence | Top cosine similarity score < 0.45 |
| Sensitive topics | Billing, refunds, legal, account deletion |
| Repeated frustration | 2+ consecutive Frustrated User turns |

Escalations produce structured JSON handoff data for human agents.

## Test Scenarios

Use the sidebar buttons or paste these messages:

| # | Message | Expected |
|---|---------|----------|
| 1 | Cookie loading frustration | Frustrated User — empathetic bullet steps |
| 2 | Bearer token header requirements | Technical Expert — detailed HTTP headers |
| 3 | Billing dispute timeline | Business Executive — brief, business-focused |
| 4 | Database integration errors | Technical Expert — step-by-step resolution |
| 5 | Duplicate charges / refund demand | Escalation + handoff JSON |

## Deployment (Streamlit Cloud)

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect the repo, set main file to `app.py`
4. Add `GEMINI_API_KEY` under **Secrets**:

```toml
GEMINI_API_KEY = "your_key_here"
```

## Tech Stack

| Library | Purpose |
|---------|---------|
| google-genai | Gemini LLM + embeddings |
| streamlit | Web UI |
| chromadb | Local vector store |
| langchain-text-splitters | RecursiveCharacterTextSplitter |
| pypdf | PDF parsing |
| python-dotenv | Environment variables |

## License

MIT — for assignment submission purposes.
