"""Gemini embeddings, wrapped so LangChain's Chroma store can use them."""
from google import genai
from google.genai import types
from langchain_core.embeddings import Embeddings

from app.core.config import settings

_client: genai.Client | None = None


def get_client() -> genai.Client:
    """One shared Gemini client (same library and key as explanation_service)."""
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


class GeminiEmbeddings(Embeddings):
    def __init__(self, model: str | None = None):
        self.model = model or settings.EMBEDDING_MODEL

    def _embed(self, texts: list[str], task_type: str) -> list[list[float]]:
        vectors: list[list[float]] = []
        for i in range(0, len(texts), 100):  # the API accepts limited batch sizes
            batch = texts[i : i + 100]
            response = get_client().models.embed_content(
                model=self.model,
                contents=batch,
                config=types.EmbedContentConfig(task_type=task_type),
            )
            vectors.extend(list(e.values) for e in response.embeddings)
        return vectors

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return self._embed(texts, "RETRIEVAL_DOCUMENT")

    def embed_query(self, text: str) -> list[float]:
        return self._embed([text], "RETRIEVAL_QUERY")[0]
