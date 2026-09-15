from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ImageEvidence(StrictModel):
    id: str = Field(min_length=1, max_length=200)
    usable: bool
    quality_note: str | None = Field(default=None, max_length=500)


class DamageDetection(StrictModel):
    id: str = Field(min_length=1, max_length=80)
    class_name: str = Field(alias="class", min_length=1, max_length=80)
    confidence: float = Field(ge=0, le=1)


class PartDetection(StrictModel):
    id: str = Field(min_length=1, max_length=80)
    class_name: str = Field(alias="class", min_length=1, max_length=80)
    confidence: float = Field(ge=0, le=1)


class AssociationAlternative(StrictModel):
    part_id: str = Field(min_length=1, max_length=80)
    confidence: float = Field(ge=0, le=1)


class Association(StrictModel):
    damage_id: str = Field(min_length=1, max_length=80)
    part_id: str | None = Field(default=None, max_length=80)
    confidence: float = Field(ge=0, le=1)
    alternatives: list[AssociationAlternative] = Field(default_factory=list, max_length=20)


class CVRecord(StrictModel):
    """The provisional Ruba-branch LLM input contract, preserved verbatim."""

    image: ImageEvidence
    damage_detections: list[DamageDetection] = Field(max_length=100)
    part_detections: list[PartDetection] = Field(max_length=100)
    associations: list[Association] = Field(max_length=100)


class VisualDetection(StrictModel):
    id: str
    kind: Literal["damage", "part"]
    class_name: str
    confidence: float
    bbox: tuple[float, float, float, float]


class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    MANUAL_REVIEW = "manual_review"
    REJECTED = "rejected"


class VerificationIssue(StrictModel):
    code: str
    message: str
    path: str | None = None
    level: Literal["review", "error"]


class VerificationResult(StrictModel):
    status: VerificationStatus
    llm_eligible: bool
    issues: list[VerificationIssue]


class ReportResult(StrictModel):
    status: Literal["generated", "unavailable", "blocked", "failed"]
    text: str | None = None
    message: str | None = None


class AssessmentResponse(StrictModel):
    analysis_id: str
    cv_output: CVRecord
    visual_detections: list[VisualDetection]
    overlay_data_url: str | None
    verification: VerificationResult
    severity: None = None
    report: ReportResult
    recommendation: str
    disclaimer: str


class HealthComponent(StrictModel):
    ready: bool
    detail: str


class HealthResponse(StrictModel):
    status: Literal["ready", "configuration_required"]
    components: dict[str, HealthComponent]


class VerificationRequest(StrictModel):
    record: dict[str, Any]
