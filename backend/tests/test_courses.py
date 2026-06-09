import pytest



from tests.conftest import login





@pytest.mark.asyncio

async def test_teacher_create_course(client, seed_users):

    tokens = await login(client, "teacher", "Teacher123!")

    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.post(

        "/api/v1/courses",

        headers=headers,

        json={"name": "New Course", "description": "desc"},

    )

    body = resp.json()

    assert body["code"] == 0

    assert body["data"]["status"] == "draft"

    assert body["data"]["create_approval"] == "pending"

    assert body["data"]["teacher_name"] == "teacher"





@pytest.mark.asyncio

async def test_student_cannot_create_course(client, seed_users):

    tokens = await login(client, "student", "Student123!")

    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.post(

        "/api/v1/courses",

        headers=headers,

        json={"name": "Hack Course"},

    )

    assert resp.json()["code"] == 40301





@pytest.mark.asyncio

async def test_student_join_course(client, seed_users, seed_course):

    tokens = await login(client, "student", "Student123!")

    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.post(

        f"/api/v1/courses/{seed_course.id}/join",

        headers=headers,

    )

    assert resp.json()["code"] == 0



    my = await client.get("/api/v1/courses/my", headers=headers)

    courses = my.json()["data"]["list"]

    assert len(courses) == 1

    assert courses[0]["id"] == seed_course.id





@pytest.mark.asyncio

async def test_student_join_draft_course_fails(client, seed_users, db_session, seed_course):

    from app.models.course import CourseStatus



    seed_course.status = CourseStatus.draft

    db_session.commit()



    tokens = await login(client, "student", "Student123!")

    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.post(

        f"/api/v1/courses/{seed_course.id}/join",

        headers=headers,

    )

    assert resp.json()["code"] == 40001





@pytest.mark.asyncio

async def test_admin_create_course_without_teacher_fails(client, seed_users):

    tokens = await login(client, "admin", "Admin123!")

    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.post(

        "/api/v1/courses",

        headers=headers,

        json={"name": "Admin Course", "description": "desc"},

    )

    assert resp.json()["code"] == 40001





@pytest.mark.asyncio

async def test_admin_create_course_with_teacher(client, seed_users):

    tokens = await login(client, "admin", "Admin123!")

    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.post(

        "/api/v1/courses",

        headers=headers,

        json={

            "name": "Admin Course",

            "description": "desc",

            "teacher_id": seed_users["teacher"].id,

        },

    )

    body = resp.json()

    assert body["code"] == 0

    assert body["data"]["teacher_id"] == seed_users["teacher"].id

    assert body["data"]["teacher_name"] == "teacher"

    assert body["data"]["create_approval"] == "approved"





@pytest.mark.asyncio

async def test_teacher_publish_requires_approval(client, seed_users):

    tokens = await login(client, "teacher", "Teacher123!")

    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    create = await client.post(

        "/api/v1/courses",

        headers=headers,

        json={"name": "Pending Course", "description": "desc"},

    )

    course_id = create.json()["data"]["id"]



    resp = await client.put(

        f"/api/v1/courses/{course_id}",

        headers=headers,

        json={"status": "published"},

    )

    assert resp.json()["code"] == 40001





@pytest.mark.asyncio

async def test_teacher_publish_workflow(client, seed_users):

    teacher_tokens = await login(client, "teacher", "Teacher123!")

    teacher_headers = {"Authorization": f"Bearer {teacher_tokens['access_token']}"}

    admin_tokens = await login(client, "admin", "Admin123!")

    admin_headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}



    create = await client.post(

        "/api/v1/courses",

        headers=teacher_headers,

        json={"name": "Workflow Course", "description": "desc"},

    )

    course_id = create.json()["data"]["id"]



    approve_create = await client.post(

        f"/api/v1/courses/{course_id}/approve-create",

        headers=admin_headers,

        json={"approved": True},

    )

    assert approve_create.json()["data"]["create_approval"] == "approved"



    request_publish = await client.post(

        f"/api/v1/courses/{course_id}/request-publish",

        headers=teacher_headers,

    )

    assert request_publish.json()["data"]["publish_approval"] == "pending"



    approve_publish = await client.post(

        f"/api/v1/courses/{course_id}/approve-publish",

        headers=admin_headers,

        json={"approved": True},

    )

    data = approve_publish.json()["data"]

    assert data["status"] == "published"

    assert data["published_at"] is not None





@pytest.mark.asyncio

async def test_teacher_list_courses(client, seed_users, seed_course):

    tokens = await login(client, "teacher", "Teacher123!")

    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.get("/api/v1/courses?page_num=1&page_size=10", headers=headers)

    body = resp.json()

    assert body["code"] == 0

    assert body["data"]["total"] >= 1


@pytest.mark.asyncio
async def test_admin_list_courses_search(client, seed_users, seed_course):
    tokens = await login(client, "admin", "Admin123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    resp = await client.get(
        "/api/v1/courses",
        headers=headers,
        params={
            "name": "Demo",
            "teacher_name": "teacher",
            "status": "published",
            "page_num": 1,
            "page_size": 10,
        },
    )
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["total"] >= 1
    assert body["data"]["list"][0]["teacher_name"] == "teacher"


@pytest.mark.asyncio
async def test_student_my_courses_search(client, seed_users, seed_course):
    tokens = await login(client, "student", "Student123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    await client.post(f"/api/v1/courses/{seed_course.id}/join", headers=headers)

    resp = await client.get(
        "/api/v1/courses/my",
        headers=headers,
        params={"name": "Demo", "teacher_name": "teacher", "status": "published"},
    )
    body = resp.json()
    assert body["code"] == 0
    assert len(body["data"]["list"]) == 1
    assert body["data"]["list"][0]["teacher_name"] == "teacher"
    assert body["data"]["list"][0]["published_at"] is not None


@pytest.mark.asyncio
async def test_student_browse_courses(client, seed_users, seed_course):
    tokens = await login(client, "student", "Student123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.get(
        "/api/v1/courses/browse",
        headers=headers,
        params={"name": "Demo", "teacher_name": "teacher"},
    )
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["total"] >= 1
    assert body["data"]["list"][0]["enrolled"] is False

    await client.post(f"/api/v1/courses/{seed_course.id}/join", headers=headers)

    resp2 = await client.get(
        "/api/v1/courses/browse",
        headers=headers,
        params={"course_id": str(seed_course.id)},
    )
    assert resp2.json()["data"]["list"][0]["enrolled"] is True


@pytest.mark.asyncio
async def test_student_leave_course(client, seed_users, seed_course):
    tokens = await login(client, "student", "Student123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    await client.post(f"/api/v1/courses/{seed_course.id}/join", headers=headers)
    leave = await client.post(f"/api/v1/courses/{seed_course.id}/leave", headers=headers)
    assert leave.json()["code"] == 0

    my = await client.get("/api/v1/courses/my", headers=headers)
    assert my.json()["data"]["total"] == 0
