import json
import structlog
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.deps import CurrentUser, DbSession
from app.core.exceptions import ERR_NOT_FOUND, BusinessException
from app.core.rate_limit import check_llm_rate_limit
from app.models.chat import ChatMessage, ChatSession, MessageCitation, MessageRole
from app.models.course import Course
from app.models.learning import KnowledgePoint
from app.models.material import CourseMaterial, MaterialChunk
from app.models.user import User, UserRole
from app.schemas.chat import MessageCreate, MessageOut, SessionCreate, SessionOut
from app.schemas.response import success
from app.services.chunking import estimate_tokens
from app.services.course_access import ensure_chat_access, ensure_student_enrolled
from app.services.llm_service import (
    build_rag_prompt,
    log_llm_invoke,
    stream_llm,
    validate_user_input,
)
from app.services.runtime_ai_config import get_cached_runtime_ai_config
from app.services.chat_suggestions import get_chat_suggestions
from app.services.course_track import resolve_code_fence_tag, resolve_course_code_language
from app.services.learning_events import after_chat_no_context
from app.services.rag import retrieve_chunks
from app.services.rag_relevance import filter_relevant_hits

router = APIRouter(prefix="/chat", tags=["chat"])
settings = get_settings()
logger = structlog.get_logger(__name__)
DEFAULT_SESSION_TITLE = "新对话"
SESSION_TITLE_MAX_LEN = 10
CITATION_DISPLAY_LIMIT = 3


def _material_display_name(name: str | None) -> str:
    if not name:
        return "课程资料"
    stem = name.rsplit(".", 1)[0] if "." in name else name
    return stem.strip() or "课程资料"


def _top_citations_from_hits(hits: list) -> list[dict]:
    """Deduplicate by material, keep top-N by retrieval score."""
    seen_materials: set[int] = set()
    result: list[dict] = []
    for hit in hits:
        material_id = getattr(hit, "material_id", None) or hit.chunk_id
        if material_id in seen_materials:
            continue
        seen_materials.add(material_id)
        result.append(
            {
                "chunk_id": hit.chunk_id,
                "material_name": _material_display_name(
                    getattr(hit, "material_name", None)
                ),
            }
        )
        if len(result) >= CITATION_DISPLAY_LIMIT:
            break
    return result


def _enrich_stored_citations(db: Session, citations: list[MessageCitation]) -> list[dict]:
    if not citations:
        return []
    chunk_ids = [c.chunk_id for c in citations]
    chunks = (
        db.query(MaterialChunk)
        .filter(MaterialChunk.id.in_(chunk_ids), MaterialChunk.deleted == 0)
        .all()
    )
    chunk_map = {c.id: c for c in chunks}
    material_ids = {c.material_id for c in chunks}
    materials = (
        db.query(CourseMaterial)
        .filter(CourseMaterial.id.in_(material_ids), CourseMaterial.deleted == 0)
        .all()
        if material_ids
        else []
    )
    material_map = {m.id: m.original_name for m in materials}

    seen_materials: set[int] = set()
    result: list[dict] = []
    for cite in citations:
        chunk = chunk_map.get(cite.chunk_id)
        material_id = chunk.material_id if chunk else cite.chunk_id
        if material_id in seen_materials:
            continue
        seen_materials.add(material_id)
        material_name = (
            _material_display_name(material_map.get(chunk.material_id))
            if chunk
            else "课程资料"
        )
        result.append({"chunk_id": cite.chunk_id, "material_name": material_name})
        if len(result) >= CITATION_DISPLAY_LIMIT:
            break
    return result


def summarize_session_title(content: str, max_len: int = SESSION_TITLE_MAX_LEN) -> str:
    text = " ".join(content.strip().split())
    if not text:
        return DEFAULT_SESSION_TITLE
    return text if len(text) <= max_len else text[:max_len]


def _get_session(db: Session, session_id: int, user: User) -> ChatSession:
    session = (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id, ChatSession.deleted == 0)
        .first()
    )
    if not session:
        raise BusinessException(ERR_NOT_FOUND, "会话不存在")
    if user.role == UserRole.student and session.user_id != user.id:
        raise BusinessException(ERR_NOT_FOUND, "会话不存在")
    return session


def _load_session_history(
    db: Session,
    session_id: int,
    before_message_id: int,
) -> list[dict]:
    rows = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.session_id == session_id,
            ChatMessage.deleted == 0,
            ChatMessage.id < before_message_id,
            ChatMessage.role.in_([MessageRole.user, MessageRole.assistant]),
        )
        .order_by(ChatMessage.id.asc())
        .all()
    )
    max_messages = settings.chat_history_max_turns * 2
    if max_messages > 0 and len(rows) > max_messages:
        rows = rows[-max_messages:]
    return [{"role": row.role.value, "content": row.content} for row in rows]


def _soft_delete_session(db: Session, session_id: int) -> None:
    message_ids = [
        row.id
        for row in db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id, ChatMessage.deleted == 0)
        .all()
    ]
    if message_ids:
        db.query(MessageCitation).filter(
            MessageCitation.message_id.in_(message_ids),
            MessageCitation.deleted == 0,
        ).update({"deleted": 1}, synchronize_session=False)
        db.query(ChatMessage).filter(ChatMessage.id.in_(message_ids)).update(
            {"deleted": 1}, synchronize_session=False
        )
    db.query(ChatSession).filter(ChatSession.id == session_id).update({"deleted": 1})


@router.post("/sessions")
def create_session(body: SessionCreate, db: DbSession, user: CurrentUser):
    if user.role == UserRole.student:
        ensure_student_enrolled(db, user, body.course_id)
    else:
        ensure_chat_access(db, user, body.course_id)

    session = ChatSession(
        user_id=user.id,
        course_id=body.course_id,
        title=body.title,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return success(SessionOut.model_validate(session).model_dump(mode="json"))


@router.get("/suggestions")
def chat_suggestions(
    db: DbSession,
    user: CurrentUser,
    course_id: int = Query(...),
):
    if user.role == UserRole.student:
        ensure_student_enrolled(db, user, course_id)
    else:
        ensure_chat_access(db, user, course_id)
    return success(get_chat_suggestions(db, course_id))


@router.get("/sessions")
def list_sessions(
    db: DbSession,
    user: CurrentUser,
    course_id: int = Query(...),
):
    if user.role == UserRole.student:
        ensure_student_enrolled(db, user, course_id)
    else:
        ensure_chat_access(db, user, course_id)

    query = db.query(ChatSession).filter(
        ChatSession.course_id == course_id,
        ChatSession.deleted == 0,
    )
    if user.role == UserRole.student:
        query = query.filter(ChatSession.user_id == user.id)

    rows = query.order_by(ChatSession.id.desc()).all()
    updated = False
    for session in rows:
        if session.title != DEFAULT_SESSION_TITLE:
            continue
        first_user = (
            db.query(ChatMessage)
            .filter(
                ChatMessage.session_id == session.id,
                ChatMessage.deleted == 0,
                ChatMessage.role == MessageRole.user,
            )
            .order_by(ChatMessage.id.asc())
            .first()
        )
        if first_user:
            session.title = summarize_session_title(first_user.content)
            updated = True
    if updated:
        db.commit()
    return success([SessionOut.model_validate(s).model_dump(mode="json") for s in rows])


@router.get("/sessions/{session_id}/messages")
def list_session_messages(
    session_id: int,
    db: DbSession,
    user: CurrentUser,
):
    session = _get_session(db, session_id, user)
    ensure_chat_access(db, user, session.course_id)

    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id, ChatMessage.deleted == 0)
        .order_by(ChatMessage.id.asc())
        .all()
    )

    assistant_ids = [m.id for m in rows if m.role == MessageRole.assistant]
    cite_map: dict[int, list[dict]] = {mid: [] for mid in assistant_ids}
    if assistant_ids:
        citations = (
            db.query(MessageCitation)
            .filter(
                MessageCitation.message_id.in_(assistant_ids),
                MessageCitation.deleted == 0,
            )
            .all()
        )
        for msg_id in assistant_ids:
            msg_cites = [c for c in citations if c.message_id == msg_id]
            cite_map[msg_id] = _enrich_stored_citations(db, msg_cites)

    result: list[dict] = []
    for msg in rows:
        if msg.role not in (MessageRole.user, MessageRole.assistant):
            continue
        citations = cite_map.get(msg.id, [])
        context_relevant = bool(citations) if msg.role == MessageRole.assistant else None
        item = MessageOut(
            id=msg.id,
            role=msg.role.value,
            content=msg.content,
            created_at=msg.created_at,
            citations=citations,
            no_context=None,
            context_relevant=context_relevant,
        )
        result.append(item.model_dump(mode="json"))

    return success(result)


@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: int,
    db: DbSession,
    user: CurrentUser,
):
    session = _get_session(db, session_id, user)
    ensure_chat_access(db, user, session.course_id)
    _soft_delete_session(db, session_id)
    db.commit()
    return success(None, message="已删除")


@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: int,
    body: MessageCreate,
    db: DbSession,
    user: CurrentUser,
):
    session = _get_session(db, session_id, user)
    ensure_chat_access(db, user, session.course_id)

    try:
        validate_user_input(body.content)
    except ValueError as exc:
        raise BusinessException(40001, str(exc)) from exc

    check_llm_rate_limit(user.id)

    user_msg = ChatMessage(
        session_id=session.id,
        role=MessageRole.user,
        content=body.content,
        token_count=estimate_tokens(body.content),
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    session_title = session.title
    if session.title == DEFAULT_SESSION_TITLE:
        prior_user_count = (
            db.query(ChatMessage)
            .filter(
                ChatMessage.session_id == session.id,
                ChatMessage.deleted == 0,
                ChatMessage.id < user_msg.id,
                ChatMessage.role == MessageRole.user,
            )
            .count()
        )
        if prior_user_count == 0:
            session.title = summarize_session_title(body.content)
            session_title = session.title
            db.commit()
            db.refresh(session)

    try:
        raw_hits = await retrieve_chunks(db, course_id=session.course_id, query=body.content)
    except Exception as exc:
        logger.warning("rag_retrieve_failed", course_id=session.course_id, error=str(exc))
        raw_hits = []
    relevant_hits = filter_relevant_hits(body.content, raw_hits)
    context_relevant = len(relevant_hits) > 0
    history = _load_session_history(db, session.id, user_msg.id)
    course = (
        db.query(Course)
        .filter(Course.id == session.course_id, Course.deleted == 0)
        .first()
    )
    course_name = course.name if course else ""
    messages = build_rag_prompt(
        relevant_hits,
        body.content,
        history=history,
        code_language=resolve_course_code_language(course_name),
        code_fence_tag=resolve_code_fence_tag(course_name),
    )
    no_context = len(raw_hits) == 0
    hit_data = _top_citations_from_hits(relevant_hits) if context_relevant else []

    async def event_stream() -> AsyncIterator[str]:
        from app.core.database import SessionLocal

        full_parts: list[str] = []
        citations: list[dict] = []
        try:
            async for chunk in stream_llm(messages):
                if chunk.kind == "reasoning":
                    payload = json.dumps(
                        {"reasoning_delta": chunk.text, "done": False},
                        ensure_ascii=False,
                    )
                else:
                    full_parts.append(chunk.text)
                    payload = json.dumps(
                        {"delta": chunk.text, "done": False},
                        ensure_ascii=False,
                    )
                yield f"event: message\ndata: {payload}\n\n"

            full_text = "".join(full_parts)
            save_db = SessionLocal()
            try:
                assistant_msg = ChatMessage(
                    session_id=session.id,
                    role=MessageRole.assistant,
                    content=full_text,
                    token_count=estimate_tokens(full_text),
                )
                save_db.add(assistant_msg)
                save_db.commit()
                save_db.refresh(assistant_msg)

                citations = []
                for item in hit_data:
                    cite = MessageCitation(
                        message_id=assistant_msg.id,
                        chunk_id=item["chunk_id"],
                        source_page=None,
                    )
                    save_db.add(cite)
                    citations.append(item)
                save_db.commit()
                if not context_relevant:
                    kp = (
                        save_db.query(KnowledgePoint)
                        .filter(
                            KnowledgePoint.course_id == session.course_id,
                            KnowledgePoint.deleted == 0,
                        )
                        .order_by(KnowledgePoint.sort_order.asc())
                        .first()
                    )
                    after_chat_no_context(
                        save_db,
                        user_id=user.id,
                        course_id=session.course_id,
                        session_id=session.id,
                        message_id=assistant_msg.id,
                        kp_id=kp.id if kp else None,
                    )
                    save_db.commit()
            finally:
                save_db.close()

            await log_llm_invoke(
                user_id=user.id,
                scene="chat_rag",
                model=get_cached_runtime_ai_config().llm_model,
                tokens=estimate_tokens(full_text),
            )

            final_payload = json.dumps(
                {
                    "delta": "",
                    "done": True,
                    "citations": citations if context_relevant else [],
                    "no_context": no_context,
                    "context_relevant": context_relevant,
                    "session_title": session_title,
                },
                ensure_ascii=False,
            )
            yield f"event: message\ndata: {final_payload}\n\n"
        except Exception as exc:
            err = json.dumps({"code": 50001, "message": str(exc)}, ensure_ascii=False)
            yield f"event: error\ndata: {err}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
