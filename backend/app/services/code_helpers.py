import json
from enum import Enum
from typing import Any

from app.schemas.code_analysis import AnalysisResultData


def enum_to_str(value: Any) -> str:
    if isinstance(value, Enum):
        return value.value
    return str(value)


def parse_result_json(raw: Any) -> dict | None:
    if raw is None:
        return None
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return None
        return parsed if isinstance(parsed, dict) else None
    return None


def extract_summary(raw: Any) -> str | None:
    data = parse_result_json(raw)
    if not data:
        return None
    summary = data.get("summary")
    if isinstance(summary, str):
        return summary
    return None


def validate_result_data(raw: Any) -> AnalysisResultData | None:
    data = parse_result_json(raw)
    if not data:
        return None
    try:
        return AnalysisResultData.model_validate(data)
    except Exception:
        return None
