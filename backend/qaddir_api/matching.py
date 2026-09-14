from __future__ import annotations

from dataclasses import dataclass

from .schemas import Association, AssociationAlternative, VisualDetection


@dataclass(frozen=True)
class Box:
    left: float
    top: float
    right: float
    bottom: float

    @property
    def area(self) -> float:
        return max(0.0, self.right - self.left) * max(0.0, self.bottom - self.top)


def damage_coverage(damage: Box, part: Box) -> float:
    intersection_width = max(0.0, min(damage.right, part.right) - max(damage.left, part.left))
    intersection_height = max(0.0, min(damage.bottom, part.bottom) - max(damage.top, part.top))
    if damage.area == 0:
        return 0.0
    return min(1.0, intersection_width * intersection_height / damage.area)


def associate_by_overlap(detections: list[VisualDetection]) -> list[Association]:
    """Create provisional links using damage-box coverage by part boxes.

    This is an integration baseline, not a calibrated matching model. Its score
    remains subject to the production threshold and verification layer.
    """

    damages = [item for item in detections if item.kind == "damage"]
    parts = [item for item in detections if item.kind == "part"]
    associations: list[Association] = []

    for damage in damages:
        damage_box = Box(*damage.bbox)
        candidates = sorted(
            (
                (part.id, damage_coverage(damage_box, Box(*part.bbox)))
                for part in parts
            ),
            key=lambda value: value[1],
            reverse=True,
        )
        candidates = [candidate for candidate in candidates if candidate[1] > 0]
        if not candidates:
            associations.append(
                Association(damage_id=damage.id, part_id=None, confidence=0.0, alternatives=[])
            )
            continue
        leader, *remaining = candidates
        associations.append(
            Association(
                damage_id=damage.id,
                part_id=leader[0],
                confidence=round(leader[1], 6),
                alternatives=[
                    AssociationAlternative(part_id=part_id, confidence=round(score, 6))
                    for part_id, score in remaining[:3]
                ],
            )
        )
    return associations
