from __future__ import annotations

import re

from .schemas import CVRecord


class UnsafeReportError(ValueError):
    pass


PROHIBITED_PATTERNS = (
    r"\b(?:minor|moderate|severe|significant|extensive|cosmetic|structural)\b",
    r"\b(?:repair|repairable|repaired|repairing|respray|respraying|buffed|buffing|panel beating)\b",
    r"\b(?:replace|replacement)\b(?!\s+image)",
    r"(?:\$|\bSAR\b|\bUSD\b|\briyals?\b|\bcost\b)",
    r"\b(?:safe|unsafe|roadworthy|liability|fault|collision caused)\b",
)

DAMAGE_RENDERINGS = {
    "dent": ("dent",),
    "scratch": ("scratch",),
    "crack": ("crack",),
    "glass_shatter": ("shattered glass",),
    "lamp_broken": ("broken lamp",),
    "tire_flat": ("flat tyre", "flat tire"),
}
PART_RENDERINGS = {
    value: value.replace("_", " ")
    for value in (
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
    )
}


def validate_report(report: str, record: CVRecord) -> None:
    lowered = report.lower()
    lowered = lowered.replace("not an assessment of severity, repair requirements or cost", "")
    for pattern in PROHIBITED_PATTERNS:
        if re.search(pattern, lowered, flags=re.IGNORECASE):
            raise UnsafeReportError("The generated report contains a prohibited unsupported claim.")

    allowed_damage = {item.class_name for item in record.damage_detections}
    allowed_parts = {item.class_name for item in record.part_detections}
    for class_name, renderings in DAMAGE_RENDERINGS.items():
        if any(rendering in lowered for rendering in renderings) and class_name not in allowed_damage:
            raise UnsafeReportError(f"The report introduced unsupported damage class '{class_name}'.")
    for class_name, rendering in PART_RENDERINGS.items():
        if rendering in lowered and class_name not in allowed_parts:
            raise UnsafeReportError(f"The report introduced unsupported vehicle part '{class_name}'.")
