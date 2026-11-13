"""Stores report chunks in Chroma and searches them.

Every chunk is tagged with user_id and report_id, and every search filters on
user_id, so one user can never retrieve another user's report.
"""
import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.core.config import settings
from app.rag.chunker import biomarker_summary, split_text
from app.rag.embeddings import GeminiEmbeddings

COLLECTION_NAME = "report_chunks"

_store: Chroma | None = None


def get_store() -> Chroma:
    global _store
    if _store is None:
        client = chromadb.PersistentClient(
            path=settings.CHROMA_DIR,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        _store = Chroma(
            client=client,
            collection_name=COLLECTION_NAME,
            embedding_function=GeminiEmbeddings(),
        )
    return _store


def _where(user_id: int, report_id: int | None = None) -> dict:
    if report_id is None:
        return {"user_id": user_id}
    return {"$and": [{"user_id": user_id}, {"report_id": report_id}]}


def is_indexed(user_id: int, report_id: int) -> bool:
    found = get_store().get(where=_where(user_id, report_id), limit=1)
    return len(found["ids"]) > 0


def index_report(report, biomarkers) -> int:
    """(Re)build the stored chunks of one report. Returns how many were stored."""
    store = get_store()

    old_ids = store.get(where=_where(report.user_id, report.id))["ids"]
    if old_ids:
        store.delete(ids=old_ids)

    base_meta = {
        "user_id": report.user_id,
        "report_id": report.id,
        "report_name": report.report_name,
        "report_date": str(report.report_date),
    }

    texts: list[str] = []
    metadatas: list[dict] = []
    ids: list[str] = []

    for i, chunk in enumerate(split_text(report.raw_text)):
        texts.append(chunk)
        metadatas.append({**base_meta, "kind": "text"})
        ids.append(f"r{report.id}-text-{i}")

    texts.append(biomarker_summary(report.report_name, report.report_date, biomarkers))
    metadatas.append({**base_meta, "kind": "biomarkers"})
    ids.append(f"r{report.id}-biomarkers")

    store.add_texts(texts=texts, metadatas=metadatas, ids=ids)
    return len(texts)


def search(query: str, user_id: int, report_id: int | None = None, k: int = 6) -> list[Document]:
    """Most relevant chunks for a question, limited to this user (and report)."""
    return get_store().similarity_search(query, k=k, filter=_where(user_id, report_id))
