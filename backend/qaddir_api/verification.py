from __future__ import annotations

from collections import Counter

from .config import DAMAGE_CLASSES, PART_CLASSES, Thresholds
from .schemas import (
    CVRecord,
    VerificationIssue,
    VerificationResult,
    VerificationStatus,
)


STRICT_PART_COMPATIBILITY = {
    "glass_shatter": {"front_glass", "back_glass"},
    "lamp_broken": {"front_light", "back_light"},
    "tire_flat": {"wheel"},
}


def _issue(code: str, message: str, *, path: str | None = None, error: bool = False) -> VerificationIssue:
    return VerificationIssue(
        code=code,
        message=message,
        path=path,
        level="error" if error else "review",
    )


def verify_record(record: CVRecord, thresholds: Thresholds) -> VerificationResult:
    issues: list[VerificationIssue] = []
    errors: list[VerificationIssue] = []

    damage_ids = [item.id for item in record.damage_detections]
    part_ids = [item.id for item in record.part_detections]
    damage_by_id = {item.id: item for item in record.damage_detections}
    part_by_id = {item.id: item for item in record.part_detections}

    for duplicate in _duplicates(damage_ids):
        errors.append(_issue("duplicate_damage_id", f"Damage id '{duplicate}' is duplicated.", error=True))
    for duplicate in _duplicates(part_ids):
        errors.append(_issue("duplicate_part_id", f"Part id '{duplicate}' is duplicated.", error=True))

    for index, detection in enumerate(record.damage_detections):
        if detection.class_name not in DAMAGE_CLASSES:
            errors.append(
                _issue(
                    "unsupported_damage_class",
                    f"'{detection.class_name}' is not a supported damage class.",
                    path=f"damage_detections.{index}.class",
                    error=True,
                )
            )
    for index, detection in enumerate(record.part_detections):
        if detection.class_name not in PART_CLASSES:
            errors.append(
                _issue(
                    "unsupported_part_class",
                    f"'{detection.class_name}' is not a supported vehicle-part class.",
                    path=f"part_detections.{index}.class",
                    error=True,
                )
            )

    association_damage_ids: list[str] = []
    for index, association in enumerate(record.associations):
        association_damage_ids.append(association.damage_id)
        damage = damage_by_id.get(association.damage_id)
        part = part_by_id.get(association.part_id) if association.part_id else None
        if damage is None:
            errors.append(
                _issue(
                    "unknown_damage_reference",
                    f"Association references unknown damage id '{association.damage_id}'.",
                    path=f"associations.{index}.damage_id",
                    error=True,
                )
            )
        if association.part_id is not None and part is None:
            errors.append(
                _issue(
                    "unknown_part_reference",
                    f"Association references unknown part id '{association.part_id}'.",
                    path=f"associations.{index}.part_id",
                    error=True,
                )
            )
        alternative_ids = [alternative.part_id for alternative in association.alternatives]
        if len(alternative_ids) != len(set(alternative_ids)):
            errors.append(
                _issue(
                    "duplicate_alternative_candidate",
                    "An association contains the same alternative part more than once.",
                    path=f"associations.{index}.alternatives",
                    error=True,
                )
            )
        for alternative_index, alternative in enumerate(association.alternatives):
            if alternative.part_id not in part_by_id:
                errors.append(
                    _issue(
                        "unknown_alternative_reference",
                        f"Alternative references unknown part id '{alternative.part_id}'.",
                        path=f"associations.{index}.alternatives.{alternative_index}.part_id",
                        error=True,
                    )
                )
            if alternative.confidence > association.confidence:
                errors.append(
                    _issue(
                        "alternative_exceeds_leader",
                        "An alternative association score cannot exceed the leading score.",
                        path=f"associations.{index}.alternatives.{alternative_index}.confidence",
                        error=True,
                    )
                )
            if damage and alternative.part_id in part_by_id:
                alternative_part = part_by_id[alternative.part_id]
                allowed_parts = STRICT_PART_COMPATIBILITY.get(damage.class_name)
                if allowed_parts and alternative_part.class_name not in allowed_parts:
                    errors.append(
                        _issue(
                            "contradictory_alternative",
                            f"{damage.class_name} cannot be associated with {alternative_part.class_name} in the supported taxonomy.",
                            path=f"associations.{index}.alternatives.{alternative_index}",
                            error=True,
                        )
                    )
        if association.part_id and association.part_id in alternative_ids:
            errors.append(
                _issue(
                    "duplicate_association_candidate",
                    "The leading part also appears in association alternatives.",
                    path=f"associations.{index}",
                    error=True,
                )
            )
        if damage and part:
            allowed_parts = STRICT_PART_COMPATIBILITY.get(damage.class_name)
            if allowed_parts and part.class_name not in allowed_parts:
                errors.append(
                    _issue(
                        "contradictory_association",
                        f"{damage.class_name} cannot be associated with {part.class_name} in the supported taxonomy.",
                        path=f"associations.{index}",
                        error=True,
                    )
                )

    for duplicate in _duplicates(association_damage_ids):
        errors.append(
            _issue(
                "duplicate_damage_association",
                f"Damage id '{duplicate}' has more than one association record.",
                error=True,
            )
        )

    associated_damage_ids = set(association_damage_ids)
    for damage_id in damage_ids:
        if damage_id not in associated_damage_ids:
            issues.append(
                _issue(
                    "missing_damage_association",
                    f"Damage detection '{damage_id}' has no association record.",
                    path=f"damage_detections.{damage_id}",
                )
            )

    if not record.image.usable and (
        record.damage_detections or record.part_detections or record.associations
    ):
        errors.append(
            _issue(
                "unusable_image_has_detections",
                "An unusable image cannot contain inference results.",
                path="image.usable",
                error=True,
            )
        )

    if errors:
        return VerificationResult(
            status=VerificationStatus.REJECTED,
            llm_eligible=False,
            issues=errors + issues,
        )

    if not record.image.usable:
        issues.append(
            _issue(
                "image_unusable",
                record.image.quality_note or "The image did not pass input quality checks.",
                path="image.usable",
            )
        )

    if not thresholds.calibrated:
        issues.append(
            _issue(
                "thresholds_not_calibrated",
                "Production confidence thresholds are not configured; automated reporting is disabled.",
            )
        )
    else:
        assert thresholds.damage_report is not None
        assert thresholds.damage_hedge is not None
        assert thresholds.part_report is not None
        assert thresholds.association_state is not None
        assert thresholds.association_ambiguity is not None
        for detection in record.damage_detections:
            if detection.confidence < thresholds.damage_report:
                issues.append(
                    _issue(
                        "low_damage_confidence",
                        f"Damage detection '{detection.id}' is below the reporting threshold.",
                        path=f"damage_detections.{detection.id}.confidence",
                    )
                )
            elif detection.confidence < thresholds.damage_hedge:
                issues.append(
                    _issue(
                        "damage_confidence_hedge_band",
                        f"Damage detection '{detection.id}' is in the hedge band and requires manual review.",
                        path=f"damage_detections.{detection.id}.confidence",
                    )
                )
        for association in record.associations:
            if association.part_id is None:
                issues.append(
                    _issue(
                        "unmatched_damage",
                        f"Damage detection '{association.damage_id}' is not linked to a vehicle part.",
                        path=f"associations.{association.damage_id}",
                    )
                )
                continue
            part = part_by_id[association.part_id]
            if part.confidence < thresholds.part_report:
                issues.append(
                    _issue(
                        "low_part_confidence",
                        f"Part detection '{part.id}' is below the reporting threshold.",
                        path=f"part_detections.{part.id}.confidence",
                    )
                )
            if association.confidence < thresholds.association_state:
                issues.append(
                    _issue(
                        "low_association_confidence",
                        f"The part link for damage '{association.damage_id}' is below the reporting threshold.",
                        path=f"associations.{association.damage_id}.confidence",
                    )
                )
            if association.alternatives:
                strongest_alternative = max(
                    alternative.confidence for alternative in association.alternatives
                )
                confidence_gap = association.confidence - strongest_alternative
                if confidence_gap < thresholds.association_ambiguity:
                    issues.append(
                        _issue(
                            "ambiguous_part_association",
                            f"The part link for damage '{association.damage_id}' is too close to an alternative candidate and requires manual review.",
                            path=f"associations.{association.damage_id}.alternatives",
                        )
                    )

    status = VerificationStatus.MANUAL_REVIEW if issues else VerificationStatus.VERIFIED
    return VerificationResult(
        status=status,
        llm_eligible=status is VerificationStatus.VERIFIED,
        issues=issues,
    )


def _duplicates(values: list[str]) -> list[str]:
    return sorted(value for value, count in Counter(values).items() if count > 1)
