import structlog
from chromadb.errors import InvalidArgumentError
from sqlalchemy.orm import Session

from app.models.material import CourseMaterial, MaterialChunk
from app.services.embedding import embed_texts
from app.services.vector_store import VectorHit, get_vector_store

logger = structlog.get_logger(__name__)


async def retrieve_chunks(
    db: Session,
    *,
    course_id: int,
    query: str,
    top_k: int = 5,
) -> list[VectorHit]:
    embeddings = await embed_texts([query])
    if not embeddings:
        return []
    try:
        hits = get_vector_store().query(
            course_id=course_id,
            query_embedding=embeddings[0],
            top_k=top_k,
        )
    except InvalidArgumentError as exc:
        logger.warning(
            "vector_query_dimension_mismatch",
            course_id=course_id,
            error=str(exc),
        )
        return []
    except Exception as exc:
        logger.warning("vector_query_failed", course_id=course_id, error=str(exc))
        return []
    if not hits:
        return []

    chunk_ids = [h.chunk_id for h in hits]
    chunks = (
        db.query(MaterialChunk)
        .filter(
            MaterialChunk.id.in_(chunk_ids),
            MaterialChunk.deleted == 0,
            MaterialChunk.course_id == course_id,
        )
        .all()
    )
    chunk_map = {c.id: c for c in chunks}
    material_ids = {c.material_id for c in chunks}
    materials = (
        db.query(CourseMaterial)
        .filter(
            CourseMaterial.id.in_(material_ids),
            CourseMaterial.deleted == 0,
        )
        .all()
        if material_ids
        else []
    )
    material_map = {m.id: m.original_name for m in materials}
    enriched: list[VectorHit] = []
    for hit in hits:
        chunk = chunk_map.get(hit.chunk_id)
        if chunk:
            enriched.append(
                VectorHit(
                    chunk_id=chunk.id,
                    course_id=course_id,
                    text=chunk.text,
                    page=chunk.source_page,
                    score=hit.score,
                    material_id=chunk.material_id,
                    material_name=material_map.get(chunk.material_id),
                )
            )
    return enriched
