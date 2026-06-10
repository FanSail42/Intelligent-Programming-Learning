from app.models.code import AnalysisResult, AnalysisStatus
from app.models.learning import WrongQuestionSourceType
from app.services.wrong_book_analysis import (
    build_item_detail,
    detect_category,
)


def test_detect_category_semantic_error():
    analysis = AnalysisResult(
        submission_id=1,
        status=AnalysisStatus.done,
        result_json={
            "summary": "x",
            "levels": {
                "syntax": {"score": "ok", "issues": []},
                "semantic": {"score": "error", "issues": [{"message": "bad loop"}]},
                "runtime": {"score": "ok", "issues": []},
            },
        },
    )
    assert detect_category("code_submission", analysis=analysis) == "semantic_error"


def test_build_item_detail_chat():
    detail = build_item_detail("chat_message")
    assert detail["category"] == "chat_no_context"
    assert detail["review_tip"]
