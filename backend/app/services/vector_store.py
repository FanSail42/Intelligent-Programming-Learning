from dataclasses import dataclass
from typing import Any

import chromadb
import structlog
from chromadb.config import Settings as ChromaSettings

from app.core.config import get_settings
from app.services.embedding import LOCAL_EMBED_DIM

settings = get_settings()
logger = structlog.get_logger(__name__)
COLLECTION_NAME = "course_chunks"


def resolve_embedding_dimensions() -> int:
    if settings.embedding_api_key or settings.llm_api_key:
        return settings.embedding_dimensions
    return LOCAL_EMBED_DIM


def collection_name_for_dim(dim: int) -> str:
    return f"{COLLECTION_NAME}_{dim}"


@dataclass
class VectorHit:
    chunk_id: int
    course_id: int
    text: str
    page: int | None
    score: float


class VectorStore:
    def __init__(self, persist_dir: str | None = None, *, embed_dim: int | None = None) -> None:
        path = persist_dir or settings.chroma_persist_dir
        self.embed_dim = embed_dim if embed_dim is not None else resolve_embedding_dimensions()
        self._client = chromadb.PersistentClient(
            path=path,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=collection_name_for_dim(self.embed_dim),
            metadata={"hnsw:space": "cosine"},
        )

    def upsert_chunks(
        self,
        *,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None:
        self._collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def delete_by_material(self, material_id: int) -> None:
        self._collection.delete(where={"material_id": material_id})

    def query(
        self,
        *,
        course_id: int,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[VectorHit]:
        result = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where={"course_id": course_id},
            include=["documents", "metadatas", "distances"],
        )
        hits: list[VectorHit] = []
        if not result["ids"] or not result["ids"][0]:
            return hits
        for i, doc_id in enumerate(result["ids"][0]):
            meta = result["metadatas"][0][i]
            distance = result["distances"][0][i]
            hits.append(
                VectorHit(
                    chunk_id=int(meta["chunk_id"]),
                    course_id=int(meta["course_id"]),
                    text=result["documents"][0][i],
                    page=meta.get("page"),
                    score=1 - distance,
                )
            )
        return hits


_vector_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store


def set_vector_store(store: VectorStore | None) -> None:
    global _vector_store
    _vector_store = store
