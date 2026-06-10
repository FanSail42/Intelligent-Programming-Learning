from app.services.code_helpers import extract_summary, enum_to_str, parse_result_json, validate_result_data


def test_enum_to_str():
    from app.models.code import CodeLanguage

    assert enum_to_str(CodeLanguage.python) == "python"
    assert enum_to_str("java") == "java"


def test_parse_result_json_string():
    data = parse_result_json('{"summary":"hi"}')
    assert data == {"summary": "hi"}


def test_extract_summary_ignores_invalid():
    assert extract_summary(["bad"]) is None
    assert extract_summary('{"summary":"ok"}') == "ok"


def test_validate_result_data_invalid():
    assert validate_result_data(["bad"]) is None
