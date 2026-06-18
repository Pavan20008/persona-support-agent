from __future__ import annotations

import random
import time
from pathlib import Path
from typing import Any

import chromadb
from google import genai
from google.genai import types
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from src.config import (
    CHROMA_DIR,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    COLLECTION_NAME,
    DATA_DIR,
    EMBEDDING_DIMENSIONALITY,
    EMBEDDING_MODEL,
    GEMINI_API_KEY,
    TOP_K,
)


class LocalRAGPipeline:
    """Document ingestion, embedding, and cosine similarity retrieval."""

    def __init__(self, db_dir: str | Path | None = None):
        if not GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY is not set. Copy .env.example to .env and add your key."
            )
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.db_dir = Path(db_dir or CHROMA_DIR)
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_client = chromadb.PersistentClient(path=str(self.db_dir))
        self.collection = self.chroma_client.get_or_create_collection(
            name=COLLECTION_NAME
        )
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        )

    def call_gemini_with_backoff(self, func, *args, max_retries: int = 5, **kwargs):
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                if attempt == max_retries - 1:
                    raise exc
                sleep_time = (2**attempt) + random.uniform(0, 1)
                time.sleep(sleep_time)

    def get_embedding(self, text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> list[float]:
        def _call():
            return self.client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=text,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=EMBEDDING_DIMENSIONALITY,
                ),
            )

        response = self.call_gemini_with_backoff(_call)
        return response.embeddings[0].values

    @staticmethod
    def _read_file(path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            reader = PdfReader(str(path))
            pages = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
            return "\n".join(pages)
        return path.read_text(encoding="utf-8")

    def ingest_document(self, doc_name: str, content: str) -> int:
        """Split a document and add chunks to the vector database."""
        chunks = self.splitter.split_text(content)
        if not chunks:
            return 0

        for idx, chunk in enumerate(chunks):
            embedding = self.get_embedding(chunk, task_type="RETRIEVAL_DOCUMENT")
            chunk_id = f"{doc_name}_chunk_{idx}"
            self.collection.upsert(
                ids=[chunk_id],
                embeddings=[embedding],
                metadatas=[{"source": doc_name, "chunk_index": idx}],
                documents=[chunk],
            )
        return len(chunks)

    def ingest_data_directory(self, data_dir: Path | None = None) -> dict[str, int]:
        """Ingest all supported files from the knowledge base directory."""
        directory = data_dir or DATA_DIR
        stats: dict[str, int] = {}
        supported = {".txt", ".md", ".pdf"}

        for path in sorted(directory.iterdir()):
            if path.is_file() and path.suffix.lower() in supported:
                content = self._read_file(path)
                stats[path.name] = self.ingest_document(path.name, content)
        return stats

    def is_index_empty(self) -> bool:
        return self.collection.count() == 0

    def retrieve_context(self, query: str, top_k: int = TOP_K) -> list[dict[str, Any]]:
        """Perform semantic search and return ranked context chunks."""
        query_vector = self.get_embedding(query, task_type="RETRIEVAL_QUERY")
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
        )

        retrieved_items: list[dict[str, Any]] = []
        if not results or not results.get("documents") or not results["documents"][0]:
            return retrieved_items

        distances = results.get("distances", [[]])[0]
        for i, document in enumerate(results["documents"][0]):
            metadata = results["metadatas"][0][i]
            distance = distances[i] if i < len(distances) else 1.0
            retrieved_items.append(
                {
                    "text": document,
                    "source": metadata.get("source", "unknown"),
                    "chunk_index": metadata.get("chunk_index", i),
                    "score": max(0.0, 1.0 - distance),
                }
            )
        return retrieved_items
