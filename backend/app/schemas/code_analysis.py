from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class CodeIssue(BaseModel):
    line: int | None = None
    message: str
    hint: str | None = None
    explanation: str | None = None


class LevelAnalysis(BaseModel):
    score: Literal["ok", "warning", "error"] = "ok"
    issues: list[CodeIssue] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    stderr_hint: str | None = None


class AnalysisLevels(BaseModel):
    syntax: LevelAnalysis = Field(default_factory=LevelAnalysis)
    semantic: LevelAnalysis = Field(default_factory=LevelAnalysis)
    runtime: LevelAnalysis = Field(default_factory=LevelAnalysis)


class AnalysisResultData(BaseModel):
    summary: str = ""
    levels: AnalysisLevels = Field(default_factory=AnalysisLevels)
    fixed_code: str | None = None
    examples: list[str] = Field(default_factory=list)
    truncated: bool = False


class CodeSubmitRequest(BaseModel):
    language: str = Field(default="python", max_length=16)
    source_code: str = Field(min_length=1, max_length=65536)


class SubmissionOut(BaseModel):
    id: int
    course_id: int | None = None
    language: str
    source_code: str
    version: int
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalysisOut(BaseModel):
    status: str
    result: AnalysisResultData | None = None
    error_message: str | None = None


class SubmitResultOut(BaseModel):
    submission: SubmissionOut
    analysis: AnalysisOut


class SubmissionListItem(BaseModel):
    id: int
    course_id: int | None = None
    language: str
    version: int
    status: str
    summary: str | None = None
    created_at: datetime
