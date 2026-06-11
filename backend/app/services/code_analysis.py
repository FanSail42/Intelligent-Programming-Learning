import json
import re
from pathlib import Path

import structlog
import yaml

from app.core.config import get_settings
from app.models.code import CodeLanguage
from app.schemas.code_analysis import AnalysisResultData
from app.services.chunking import estimate_tokens
from app.services.llm_service import invoke_llm, validate_user_input

settings = get_settings()
logger = structlog.get_logger(__name__)

SUPPORTED_LANGUAGES = {lang.value for lang in CodeLanguage}

_LANGUAGE_ALIASES = {
    "c++": CodeLanguage.cpp.value,
    "cplusplus": CodeLanguage.cpp.value,
}


def load_code_prompts() -> dict:
    prompt_path = Path(__file__).resolve().parents[2] / "prompts" / "code_analysis.yaml"
    if prompt_path.exists():
        return yaml.safe_load(prompt_path.read_text(encoding="utf-8"))
    return {}


def validate_language(language: str) -> CodeLanguage:
    normalized = language.strip().lower()
    normalized = _LANGUAGE_ALIASES.get(normalized, normalized)
    if normalized not in SUPPORTED_LANGUAGES:
        supported = "C、C++、Python、Java"
        raise ValueError(f"当前仅支持语言: {supported}")
    return CodeLanguage(normalized)


def prepare_source_code(source_code: str) -> tuple[str, bool]:
    max_chars = settings.code_max_source_chars
    if len(source_code) <= max_chars:
        return source_code, False
    return source_code[:max_chars], True


def build_analysis_messages(language: str, source_code: str, truncated: bool) -> list[dict]:
    prompts = load_code_prompts()
    system = prompts.get("system", "你是编程助教，只输出 JSON。")
    user_tpl = prompts.get(
        "user_template",
        "语言：{language}\n代码：\n{source_code}",
    )
    user_content = user_tpl.format(language=language, source_code=source_code)
    if truncated:
        user_content += "\n\n（注：代码过长已截断，仅分析可见部分）"
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_content},
    ]


def _extract_json(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return json.loads(cleaned)


def _split_crammed_clauses(text: str) -> str:
    """Break long single-line explanations into readable clauses."""
    if not text or "\n" in text:
        return text
    if len(text) < 80:
        return text
    parts = re.split(r"(?<=[。！？；])\s*", text)
    if len(parts) <= 1:
        return text
    return "\n".join(p.strip() for p in parts if p.strip())


def _normalize_result(result: AnalysisResultData) -> AnalysisResultData:
    result.summary = _split_crammed_clauses(result.summary)
    for level in (result.levels.syntax, result.levels.semantic, result.levels.runtime):
        for issue in level.issues:
            issue.message = _split_crammed_clauses(issue.message)
            if issue.hint:
                issue.hint = _split_crammed_clauses(issue.hint)
            if issue.explanation:
                issue.explanation = _split_crammed_clauses(issue.explanation)
        level.suggestions = [
            _split_crammed_clauses(s) for s in level.suggestions if s.strip()
        ]
    result.examples = [_split_crammed_clauses(ex) for ex in result.examples if ex.strip()]
    return result


def parse_analysis_result(raw: str) -> AnalysisResultData:
    data = _extract_json(raw)
    result = AnalysisResultData.model_validate(data)
    return _normalize_result(result)


def demo_analysis_result(language: str, source_code: str, truncated: bool) -> AnalysisResultData:
    lines = source_code.splitlines()
    syntax_issues = []
    for idx, line in enumerate(lines, start=1):
        if line.rstrip() != line and line.strip():
            syntax_issues.append(
                {
                    "line": idx,
                    "message": "行尾存在多余空白",
                    "hint": "删除行尾空格保持缩进整洁",
                }
            )
        if "elif" in line and not line.startswith(" ") and idx > 1:
            syntax_issues.append(
                {
                    "line": idx,
                    "message": "elif 缩进可能不正确",
                    "hint": "elif 应与同级 if 对齐",
                }
            )

    semantic_score = "ok"
    semantic_issues = []
    if "while True" in source_code or "while(1)" in source_code:
        semantic_score = "warning"
        semantic_issues.append(
            {
                "message": "可能存在无法结束的循环",
                "explanation": "while True 需要明确的 break 条件，否则逻辑上可能永不结束",
            }
        )

    runtime_score = "ok"
    runtime_issues = []
    if "[" in source_code and "]" in source_code:
        runtime_score = "warning"
        runtime_issues.append(
            {
                "message": "注意列表/数组下标访问",
                "explanation": "越界访问会引发 IndexError，提交前检查索引范围",
            }
        )

    summary = "（演示模式：未配置 LLM_API_KEY）已对代码进行基础静态分析。"
    if truncated:
        summary += " 代码过长已截断分析。"

    return AnalysisResultData(
        summary=summary,
        levels={
            "syntax": {
                "score": "error" if syntax_issues else "ok",
                "issues": syntax_issues[:5],
                "suggestions": ["检查缩进与括号配对"] if syntax_issues else [],
            },
            "semantic": {
                "score": semantic_score,
                "issues": semantic_issues,
                "suggestions": ["为循环添加明确退出条件"] if semantic_issues else [],
            },
            "runtime": {
                "score": runtime_score,
                "issues": runtime_issues,
                "stderr_hint": None,
            },
        },
        fixed_code=None,
        examples=["对比正确缩进与错误缩进的 if/elif 结构"],
        truncated=truncated,
    )


async def analyze_source_code(
    *,
    user_id: int,
    language: str,
    source_code: str,
) -> AnalysisResultData:
    validate_user_input(source_code)
    prepared, truncated = prepare_source_code(source_code)
    messages = build_analysis_messages(language, prepared, truncated)

    raw = await invoke_llm(messages)
    if not raw:
        result = demo_analysis_result(language, prepared, truncated)
        await _log_invoke(user_id, estimate_tokens(prepared))
        return result

    try:
        result = parse_analysis_result(raw)
        result.truncated = truncated
        await _log_invoke(user_id, estimate_tokens(prepared))
        return result
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("code_analysis_parse_failed", error=str(exc))
        raise ValueError("AI 返回格式无法解析，请稍后重试") from exc


async def _log_invoke(user_id: int, tokens: int) -> None:
    from app.services.llm_service import log_llm_invoke
    from app.services.runtime_ai_config import get_cached_runtime_ai_config

    await log_llm_invoke(
        user_id=user_id,
        scene="code_analysis",
        model=get_cached_runtime_ai_config().llm_model,
        tokens=tokens,
    )
