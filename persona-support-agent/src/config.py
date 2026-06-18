import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CHROMA_DIR = PROJECT_ROOT / "chroma_db"

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
# gemini-2.0-flash was shut down 2026-06-01; override via GEMINI_MODEL in .env if needed.
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSIONALITY = 768

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K = 3

RETRIEVAL_CONFIDENCE_THRESHOLD = 0.45
CLASSIFIER_TEMPERATURE = 0.1
GENERATOR_TEMPERATURE = 0.2

MAX_RETRIES = 5
COLLECTION_NAME = "support_kb"

SENSITIVE_KEYWORDS = [
    "refund",
    "chargeback",
    "legal",
    "lawsuit",
    "attorney",
    "lawyer",
    "duplicate charge",
    "unauthorized charge",
    "account deletion",
    "delete my account",
    "close my account",
    "gdpr erasure",
    "data breach",
]

PERSONAS = ["Technical Expert", "Frustrated User", "Business Executive"]
