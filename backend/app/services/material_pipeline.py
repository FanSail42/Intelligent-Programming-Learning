import asyncio
import time

import structlog
from sqlalchemy.orm import Session

from app.core.security import get_redis
from app.models.material import CourseMaterial, MaterialChunk, MaterialStatus
from app.services.chunking import chunk_blocks
from app.services.document_parser import parse_document
from app.services.embedding import embed_texts
from app.services.vector_store import get_vector_store

logger = structlog.get_logger(__name__)


def _set_material_status_cache(material_id: int, status: str) -> None:
    get_redis().set(f"material:status:{material_id}", status, ex=86400)


def _publish_status(material_id: int, status: MaterialStatus) -> None:
    _set_material_status_cache(material_id, status.value)


def _commit_status(
    db: Session,
    material: CourseMaterial,
    status: MaterialStatus,
    *,
    error: str | None = None,
    persist: bool = True,
) -> None:
    _publish_status(material.id, status)
    if not persist:
        return
    material.status = status
    if error is not None:
        material.error_message = error
    elif status != MaterialStatus.failed:
        material.error_message = None
    db.commit()


def _find_ready_clone_source(db: Session, material: CourseMaterial) -> CourseMaterial | None:
    return (
        db.query(CourseMaterial)
        .filter(
            CourseMaterial.file_path == material.file_path,
            CourseMaterial.status == MaterialStatus.ready,
            CourseMaterial.deleted == 0,
            CourseMaterial.id != material.id,
        )
        .order_by(CourseMaterial.id.asc())
        .first()
    )


def _clone_from_ready_source(
    db: Session,
    material: CourseMaterial,
    source: CourseMaterial,
) -> int:
    source_chunks = (
        db.query(MaterialChunk)
        .filter(
            MaterialChunk.material_id == source.id,
            MaterialChunk.deleted == 0,
        )
        .order_by(MaterialChunk.seq)
        .all()
    )
    if not source_chunks:
        raise ValueError("源资料尚未生成分块，无法克隆")

    db.query(MaterialChunk).filter(MaterialChunk.material_id == material.id).update(
        {"deleted": 1}
    )
    get_vector_store().delete_by_material(material.id)

    source_ids = [f"chunk_{row.id}" for row in source_chunks]
    embedding_map = get_vector_store().fetch_embeddings(source_ids)
    if len(embedding_map) != len(source_ids):
        raise ValueError("源资料向量不完整，改为完整处理")

    new_rows: list[MaterialChunk] = []
    for src in source_chunks:
        row = MaterialChunk(
            material_id=material.id,
            course_id=material.course_id,
            seq=src.seq,
            text=src.text,
            source_page=src.source_page,
            token_count=src.token_count,
        )
        db.add(row)
        new_rows.append(row)
    db.commit()
    for row in new_rows:
        db.refresh(row)

    ids = [f"chunk_{row.id}" for row in new_rows]
    texts = [row.text for row in new_rows]
    embeddings = [embedding_map[f"chunk_{src.id}"] for src in source_chunks]
    metadatas = [
        {
            "chunk_id": row.id,
            "course_id": material.course_id,
            "material_id": material.id,
            "page": row.source_page if row.source_page is not None else -1,
        }
        for row in new_rows
    ]
    get_vector_store().upsert_chunks(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )
    return len(new_rows)


async def process_material_async(material_id: int) -> None:
    await asyncio.to_thread(process_material, material_id)


def process_material(material_id: int) -> None:
    from app.core.database import SessionLocal

    db = SessionLocal()
    started = time.perf_counter()
    try:
        material = (
            db.query(CourseMaterial)
            .filter(CourseMaterial.id == material_id, CourseMaterial.deleted == 0)
            .first()
        )
        if not material:
            return

        try:
            clone_source = _find_ready_clone_source(db, material)
            if clone_source is not None:
                _commit_status(db, material, MaterialStatus.chunking, persist=False)
                t0 = time.perf_counter()
                chunk_count = _clone_from_ready_source(db, material, clone_source)
                clone_ms = int((time.perf_counter() - t0) * 1000)
                _commit_status(db, material, MaterialStatus.ready)
                logger.info(
                    "material_cloned",
                    material_id=material_id,
                    source_material_id=clone_source.id,
                    chunks=chunk_count,
                    clone_ms=clone_ms,
                    total_ms=int((time.perf_counter() - started) * 1000),
                )
                return

            _commit_status(db, material, MaterialStatus.parsing, persist=False)
            t0 = time.perf_counter()
            blocks = parse_document(material.file_path, material.type)
            parse_ms = int((time.perf_counter() - t0) * 1000)

            _commit_status(db, material, MaterialStatus.chunking, persist=False)
            db.query(MaterialChunk).filter(
                MaterialChunk.material_id == material.id
            ).update({"deleted": 1})
            get_vector_store().delete_by_material(material.id)

            pieces = chunk_blocks(blocks)
            for seq, (text, page, token_count) in enumerate(pieces):
                db.add(
                    MaterialChunk(
                        material_id=material.id,
                        course_id=material.course_id,
                        seq=seq,
                        text=text,
                        source_page=page,
                        token_count=token_count,
                    )
                )
            db.commit()
            chunk_rows = (
                db.query(MaterialChunk)
                .filter(
                    MaterialChunk.material_id == material.id,
                    MaterialChunk.deleted == 0,
                )
                .order_by(MaterialChunk.seq)
                .all()
            )

            embed_ms = 0
            chroma_ms = 0
            _commit_status(db, material, MaterialStatus.embedding, persist=False)
            if chunk_rows:
                texts = [r.text for r in chunk_rows]
                t0 = time.perf_counter()
                embeddings = asyncio.run(embed_texts(texts))
                embed_ms = int((time.perf_counter() - t0) * 1000)
                ids = [f"chunk_{r.id}" for r in chunk_rows]
                metadatas = [
                    {
                        "chunk_id": r.id,
                        "course_id": material.course_id,
                        "material_id": material.id,
                        "page": r.source_page if r.source_page is not None else -1,
                    }
                    for r in chunk_rows
                ]
                t0 = time.perf_counter()
                get_vector_store().upsert_chunks(
                    ids=ids,
                    embeddings=embeddings,
                    documents=texts,
                    metadatas=metadatas,
                )
                chroma_ms = int((time.perf_counter() - t0) * 1000)

            _commit_status(db, material, MaterialStatus.ready)
            logger.info(
                "material_processed",
                material_id=material_id,
                chunks=len(chunk_rows),
                parse_ms=parse_ms,
                embed_ms=embed_ms,
                chroma_ms=chroma_ms,
                total_ms=int((time.perf_counter() - started) * 1000),
            )
        except Exception as exc:
            db.rollback()
            material = db.query(CourseMaterial).filter(CourseMaterial.id == material_id).first()
            if material:
                _commit_status(db, material, MaterialStatus.failed, error=str(exc))
            raise
    finally:
        db.close()
