from app.services.chat_suggestions import TRACK_SUGGESTIONS, get_chat_suggestions
from app.services.course_track import course_track_key, resolve_course_code_language


def test_course_track_key():
    assert course_track_key("Java 面向对象编程") == "java"
    assert course_track_key("Python 数据分析") == "python"
    assert course_track_key("C++ 数据结构与算法") == "cpp"


def test_resolve_course_code_language():
    assert resolve_course_code_language("C++ 数据结构与算法") == "C++"
    assert resolve_course_code_language("Java 面向对象编程") == "Java"
    assert resolve_course_code_language("Python 数据分析") == "Python"


def test_track_suggestions_content():
    assert "面向对象三大特性" in TRACK_SUGGESTIONS["java"][0]
    assert "Pandas" in TRACK_SUGGESTIONS["python"][0]
    assert "快排" in TRACK_SUGGESTIONS["cpp"][0]


def test_suggestions_use_seed_course(db_session, seed_course):
    seed_course.name = "Python 数据分析"
    db_session.commit()
    items = get_chat_suggestions(db_session, seed_course.id)
    assert len(items) == 3
    assert "Pandas" in items[0]
