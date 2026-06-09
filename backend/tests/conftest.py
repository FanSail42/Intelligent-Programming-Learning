import os
from datetime import datetime

# Must set env before importing app modules
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["APP_ENV"] = "test"
os.environ["LLM_API_KEY"] = ""
os.environ["EMBEDDING_API_KEY"] = ""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings

get_settings.cache_clear()

import app.core.database as db_module
from app.core.database import get_db
from app.core.security import InMemoryRedis, hash_password, set_redis_client
from app.main import app
from app.models import Base
from app.models.course import Course, CourseCreateApproval, CoursePublishApproval, CourseStatus, CourseTeacher
from app.models.material import MaterialType
from app.models.user import User, UserRole, UserStatus
from app.models.warehouse import CourseSubject, MaterialWarehouse, WarehouseKind

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

db_module.engine = engine
db_module.SessionLocal = TestingSessionLocal


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    set_redis_client(InMemoryRedis())
    yield
    Base.metadata.drop_all(bind=engine)
    set_redis_client(None)


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def seed_users(db_session):
    admin = User(
        username="admin",
        password_hash=hash_password("Admin123!"),
        role=UserRole.admin,
        status=UserStatus.active,
    )
    teacher = User(
        username="teacher",
        password_hash=hash_password("Teacher123!"),
        role=UserRole.teacher,
        status=UserStatus.active,
    )
    student = User(
        username="student",
        password_hash=hash_password("Student123!"),
        role=UserRole.student,
        status=UserStatus.active,
    )
    db_session.add_all([admin, teacher, student])
    db_session.commit()
    db_session.refresh(admin)
    db_session.refresh(teacher)
    db_session.refresh(student)
    return {"admin": admin, "teacher": teacher, "student": student}


@pytest.fixture
def seed_warehouses(db_session):
    warehouses = []
    for name, mtype in [("PDF库", MaterialType.pdf), ("TXT库", MaterialType.txt), ("MD库", MaterialType.md)]:
        wh = MaterialWarehouse(
            name=name,
            warehouse_kind=WarehouseKind.file_type,
            material_type=mtype,
            icon="📦",
            color="#409eff",
        )
        db_session.add(wh)
        warehouses.append(wh)
    for name, subject in [
        ("Python课程库", CourseSubject.python),
        ("Java课程库", CourseSubject.java),
        ("Cpp课程库", CourseSubject.cpp),
    ]:
        wh = MaterialWarehouse(
            name=name,
            warehouse_kind=WarehouseKind.course,
            course_subject=subject,
            material_type=MaterialType.pdf,
            icon="📦",
            color="#409eff",
            sort_order=10,
        )
        db_session.add(wh)
        warehouses.append(wh)
    db_session.commit()
    for wh in warehouses:
        db_session.refresh(wh)
    return warehouses


@pytest.fixture
def seed_course(db_session, seed_users):
    teacher = seed_users["teacher"]
    course = Course(
        name="Demo Course",
        description="test",
        teacher_id=teacher.id,
        status=CourseStatus.published,
        create_approval=CourseCreateApproval.approved,
        publish_approval=CoursePublishApproval.approved,
        published_at=datetime.now(),
    )
    db_session.add(course)
    db_session.flush()
    db_session.add(CourseTeacher(course_id=course.id, user_id=teacher.id))
    db_session.commit()
    db_session.refresh(course)
    return course


@pytest.fixture
async def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def login(client: AsyncClient, username: str, password: str) -> dict:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    return body["data"]
