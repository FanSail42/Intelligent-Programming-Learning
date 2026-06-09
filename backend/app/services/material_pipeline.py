import asyncio

from sqlalchemy.orm import Session

from app.core.security import get_redis
from app.models.material import CourseMaterial, MaterialChunk, MaterialStatus
from app.services.chunking import chunk_blocks
from app.services.document_parser import parse_document
from app.services.embedding import embed_texts
from app.services.vector_store import get_vector_store


def _set_material_status_cache(material_id: int, status: str) -> None:
    get_redis().set(f"material:status:{material_id}", status, ex=86400)


def _update_status(db: Session, material: CourseMaterial, status: MaterialStatus, error: str | None = None) -> None:
    material.status = status
    if error:
        material.error_message = error
    db.commit()
    _set_material_status_cache(material.id, status.value)


async def process_material_async(material_id: int) -> None:
    await asyncio.to_thread(process_material, material_id)


def process_material(material_id: int) -> None:
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        material = (
            db.query(CourseMaterial)
            .filter(CourseMaterial.id == material_id, CourseMaterial.deleted == 0)
            .first()
        )
        if not material:
            return

        try:
            _update_status(db, material, MaterialStatus.parsing)
            blocks = parse_document(material.file_path, material.type)

            _update_status(db, material, MaterialStatus.chunking)
            db.query(MaterialChunk).filter(
                MaterialChunk.material_id == material.id
            ).update({"deleted": 1})
            get_vector_store().delete_by_material(material.id)

            pieces = chunk_blocks(blocks)
            chunk_rows: list[MaterialChunk] = []
            for seq, (text, page, token_count) in enumerate(pieces):
                row = MaterialChunk(
                    material_id=material.id,
                    course_id=material.course_id,
                    seq=seq,
                    text=text,
                    source_page=page,
                    token_count=token_count,
                )
                db.add(row)
                chunk_rows.append(row)
            db.commit()
            for row in chunk_rows:
                db.refresh(row)

            _update_status(db, material, MaterialStatus.embedding)
            if chunk_rows:
                texts = [r.text for r in chunk_rows]
                embeddings = asyncio.run(embed_texts(texts))
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
                get_vector_store().upsert_chunks(
                    ids=ids,
                    embeddings=embeddings,
                    documents=texts,
                    metadatas=metadatas,
                )

            _update_status(db, material, MaterialStatus.ready)
        except Exception as exc:
            db.rollback()
            material = db.query(CourseMaterial).filter(CourseMaterial.id == material_id).first()
            if material:
                _update_status(db, material, MaterialStatus.failed, str(exc))
            raise
    finally:
        db.close()
