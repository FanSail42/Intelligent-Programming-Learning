TRACK_CODE_LANGUAGE: dict[str, str] = {
    "java": "Java",
    "python": "Python",
    "cpp": "C++",
}

TRACK_CODE_FENCE: dict[str, str] = {
    "java": "java",
    "python": "python",
    "cpp": "cpp",
}


def course_track_key(course_name: str) -> str | None:
    lowered = course_name.lower()
    if "java" in lowered or "面向对象" in course_name:
        return "java"
    if "python" in lowered or "数据分析" in course_name:
        return "python"
    if (
        "c++" in lowered
        or "cpp" in lowered
        or "数据结构" in course_name
        or ("算法" in course_name and "c" in lowered)
    ):
        return "cpp"
    return None


def resolve_course_code_language(course_name: str) -> str:
    track = course_track_key(course_name)
    if track:
        return TRACK_CODE_LANGUAGE[track]
    return "Python"


def resolve_code_fence_tag(course_name: str) -> str:
    track = course_track_key(course_name)
    if track:
        return TRACK_CODE_FENCE[track]
    return "python"
