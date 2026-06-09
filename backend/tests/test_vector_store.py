import tempfile

from app.services.embedding import _local_embed
from app.services.vector_store import VectorStore


def test_vector_store_course_isolation():
    chroma_dir = tempfile.mkdtemp()
    store = VectorStore(persist_dir=chroma_dir, embed_dim=384)

    emb1 = _local_embed("python variable scope in course 1")
    emb2 = _local_embed("java class definition in course 2")

    store.upsert_chunks(
        ids=["chunk_1", "chunk_2"],
        embeddings=[emb1, emb2],
        documents=["python scope", "java class"],
        metadatas=[
            {"chunk_id": 1, "course_id": 1, "material_id": 1, "page": 1},
            {"chunk_id": 2, "course_id": 2, "material_id": 2, "page": 1},
        ],
    )

    hits = store.query(course_id=1, query_embedding=emb1, top_k=5)
    assert len(hits) == 1
    assert hits[0].course_id == 1
    assert hits[0].chunk_id == 1
