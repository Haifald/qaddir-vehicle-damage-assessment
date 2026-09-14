from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]

DAMAGE_CLASSES = frozenset(
    {"dent", "scratch", "crack", "glass_shatter", "lamp_broken", "tire_flat"}
)
PART_CLASSES = frozenset(
    {
        "back_bumper",
        "back_door",
        "back_glass",
        "back_light",
        "front_bumper",
        "front_door",
        "front_glass",
        "front_light",
        "hood",
        "side_mirror",
        "trunk_or_tailgate",
        "truck_bed",
        "wheel",
    }
)


def _optional_float(name: str) -> float | None:
    value = os.getenv(name)
    if value is None or not value.strip():
        return None
    parsed = float(value)
    if not 0 <= parsed <= 1:
        raise ValueError(f"{name} must be between 0 and 1")
    return parsed


def _optional_positive_int(name: str) -> int | None:
    value = os.getenv(name)
    if value is None or not value.strip():
        return None
    parsed = int(value)
    if parsed <= 0:
        raise ValueError(f"{name} must be greater than zero")
    return parsed


def _optional_text(name: str) -> str | None:
    value = os.getenv(name)
    if value is None or not value.strip():
        return None
    return value.strip()


def _path_from_env(name: str, default: str | None = None) -> Path | None:
    value = os.getenv(name, default)
    if not value:
        return None
    path = Path(value)
    return path if path.is_absolute() else REPOSITORY_ROOT / path


@dataclass(frozen=True)
class Thresholds:
    damage_report: float | None
    damage_hedge: float | None
    part_report: float | None
    association_state: float | None
    association_ambiguity: float | None

    def __post_init__(self) -> None:
        if (
            self.damage_report is not None
            and self.damage_hedge is not None
            and self.damage_hedge < self.damage_report
        ):
            raise ValueError("QADDIR_T_DAMAGE_HEDGE must be at least QADDIR_T_DAMAGE_REPORT")

    @property
    def calibrated(self) -> bool:
        return all(
            value is not None
            for value in (
                self.damage_report,
                self.damage_hedge,
                self.part_report,
                self.association_state,
                self.association_ambiguity,
            )
        )

    def as_prompt_values(self) -> dict[str, float]:
        if not self.calibrated:
            raise RuntimeError("Production thresholds have not been configured")
        return {
            "T_DAMAGE_REPORT": self.damage_report,
            "T_DAMAGE_HEDGE": self.damage_hedge,
            "T_PART_REPORT": self.part_report,
            "T_ASSOC_STATE": self.association_state,
            "T_ASSOC_AMBIG": self.association_ambiguity,
        }


@dataclass(frozen=True)
class Settings:
    damage_model_path: Path | None
    part_model_path: Path | None
    cv_confidence: float | None
    cv_image_size: int | None
    cv_device: str | None
    prompt_path: Path
    llm_api_key: str | None
    llm_model: str | None
    thresholds: Thresholds
    max_image_bytes: int = 10 * 1024 * 1024
    min_image_side: int = 320
    cors_origins: tuple[str, ...] = ("http://localhost:3000",)

    @classmethod
    def from_env(cls) -> "Settings":
        origins = tuple(
            value.strip()
            for value in os.getenv("QADDIR_CORS_ORIGINS", "http://localhost:3000").split(",")
            if value.strip()
        )
        return cls(
            damage_model_path=_path_from_env("QADDIR_DAMAGE_MODEL_PATH"),
            part_model_path=_path_from_env("QADDIR_PART_MODEL_PATH"),
            cv_confidence=_optional_float("QADDIR_CV_CONFIDENCE"),
            cv_image_size=_optional_positive_int("QADDIR_CV_IMAGE_SIZE"),
            cv_device=_optional_text("QADDIR_CV_DEVICE"),
            prompt_path=_path_from_env(
                "QADDIR_LLM_PROMPT_PATH", "prompts/production/prompt_production.md"
            )
            or REPOSITORY_ROOT / "prompts/production/prompt_production.md",
            llm_api_key=os.getenv("OPENAI_API_KEY"),
            llm_model=os.getenv("QADDIR_LLM_MODEL"),
            thresholds=Thresholds(
                damage_report=_optional_float("QADDIR_T_DAMAGE_REPORT"),
                damage_hedge=_optional_float("QADDIR_T_DAMAGE_HEDGE"),
                part_report=_optional_float("QADDIR_T_PART_REPORT"),
                association_state=_optional_float("QADDIR_T_ASSOC_STATE"),
                association_ambiguity=_optional_float("QADDIR_T_ASSOC_AMBIG"),
            ),
            max_image_bytes=int(os.getenv("QADDIR_MAX_IMAGE_BYTES", 10 * 1024 * 1024)),
            min_image_side=int(os.getenv("QADDIR_MIN_IMAGE_SIDE", 320)),
            cors_origins=origins,
        )
