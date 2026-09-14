from __future__ import annotations

import base64
import io
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import DAMAGE_CLASSES, PART_CLASSES, Settings
from .matching import associate_by_overlap
from .schemas import CVRecord, DamageDetection, ImageEvidence, PartDetection, VisualDetection


class ImageValidationError(ValueError):
    pass


class PipelineUnavailableError(RuntimeError):
    pass


@dataclass(frozen=True)
class PreparedImage:
    image: Any
    image_id: str
    usable: bool
    quality_note: str | None


@dataclass(frozen=True)
class InferenceOutput:
    record: CVRecord
    visual_detections: list[VisualDetection]
    overlay_data_url: str | None


def validate_image(content: bytes, filename: str, content_type: str | None, settings: Settings) -> PreparedImage:
    if not content:
        raise ImageValidationError("The uploaded image is empty.")
    if len(content) > settings.max_image_bytes:
        raise ImageValidationError(
            f"The image exceeds the {settings.max_image_bytes // (1024 * 1024)} MB upload limit."
        )
    allowed_types = {"image/jpeg", "image/png", "image/webp"}
    if content_type not in allowed_types:
        raise ImageValidationError("Upload a JPEG, PNG, or WebP image.")
    try:
        from PIL import Image

        image = Image.open(io.BytesIO(content))
        image.verify()
        image = Image.open(io.BytesIO(content)).convert("RGB")
    except Exception as exc:
        raise ImageValidationError("The file is not a readable image.") from exc

    shortest_side = min(image.size)
    usable = shortest_side >= settings.min_image_side
    note = None if usable else f"Image is too small; the shortest side must be at least {settings.min_image_side}px."
    return PreparedImage(
        image=image,
        image_id=Path(filename or "uploaded-image").name,
        usable=usable,
        quality_note=note,
    )


class UltralyticsCVPipeline:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._damage_model: Any | None = None
        self._part_model: Any | None = None

    def readiness(self) -> tuple[bool, str]:
        paths = (self.settings.damage_model_path, self.settings.part_model_path)
        if any(path is None for path in paths):
            return False, "Production damage and part model paths are not both configured."
        missing = [str(path) for path in paths if path is not None and not path.is_file()]
        if missing:
            return False, "Configured model file is missing: " + ", ".join(missing)
        try:
            self._load_models()
        except PipelineUnavailableError as exc:
            return False, str(exc)

        inference_settings = {
            "QADDIR_CV_CONFIDENCE": self.settings.cv_confidence,
            "QADDIR_CV_IMAGE_SIZE": self.settings.cv_image_size,
            "QADDIR_CV_DEVICE": self.settings.cv_device,
        }
        unconfigured = [name for name, value in inference_settings.items() if value is None]
        if unconfigured:
            return (
                False,
                "Production models load and their class vocabularies match, but CV inference "
                "configuration is incomplete: " + ", ".join(unconfigured),
            )
        return (
            True,
            "Production models load and their class vocabularies match. "
            f"Inference uses confidence={self.settings.cv_confidence}, "
            f"image_size={self.settings.cv_image_size}, device={self.settings.cv_device}.",
        )

    def infer(self, prepared: PreparedImage) -> InferenceOutput:
        if not prepared.usable:
            return InferenceOutput(
                record=CVRecord(
                    image=ImageEvidence(
                        id=prepared.image_id,
                        usable=False,
                        quality_note=prepared.quality_note,
                    ),
                    damage_detections=[],
                    part_detections=[],
                    associations=[],
                ),
                visual_detections=[],
                overlay_data_url=None,
            )

        ready, detail = self.readiness()
        if not ready:
            raise PipelineUnavailableError(detail)
        self._load_models()
        predict_options = {
            "conf": self.settings.cv_confidence,
            "imgsz": self.settings.cv_image_size,
            "device": self.settings.cv_device,
            "verbose": False,
        }
        damage_result = self._damage_model.predict(prepared.image, **predict_options)[0]
        part_result = self._part_model.predict(
            prepared.image,
            **predict_options,
            retina_masks=True,
        )[0]
        damage_visuals = self._extract(damage_result, "damage", "d", DAMAGE_CLASSES)
        part_visuals = self._extract(part_result, "part", "p", PART_CLASSES)
        visuals = damage_visuals + part_visuals
        associations = associate_by_overlap(visuals)
        record = CVRecord(
            image=ImageEvidence(id=prepared.image_id, usable=True, quality_note=None),
            damage_detections=[
                DamageDetection(id=item.id, **{"class": item.class_name}, confidence=item.confidence)
                for item in damage_visuals
            ],
            part_detections=[
                PartDetection(id=item.id, **{"class": item.class_name}, confidence=item.confidence)
                for item in part_visuals
            ],
            associations=associations,
        )
        return InferenceOutput(
            record=record,
            visual_detections=visuals,
            overlay_data_url=self._render_overlay(prepared.image, visuals),
        )

    def _load_models(self) -> None:
        if self._damage_model is not None and self._part_model is not None:
            return
        try:
            from ultralytics import YOLO

            damage_model = YOLO(str(self.settings.damage_model_path))
            part_model = YOLO(str(self.settings.part_model_path))
            self._assert_class_names(damage_model.names, DAMAGE_CLASSES, "damage")
            self._assert_class_names(part_model.names, PART_CLASSES, "part")
            self._damage_model = damage_model
            self._part_model = part_model
        except PipelineUnavailableError:
            raise
        except Exception as exc:
            raise PipelineUnavailableError(f"The CV models could not be loaded: {exc}") from exc

    @staticmethod
    def _assert_class_names(names: dict[int, str] | list[str], expected: frozenset[str], label: str) -> None:
        actual = set(names.values() if isinstance(names, dict) else names)
        if actual != expected:
            raise PipelineUnavailableError(
                f"The configured {label} model has classes {sorted(actual)}, expected {sorted(expected)}."
            )

    @staticmethod
    def _extract(result: Any, kind: str, prefix: str, allowed: frozenset[str]) -> list[VisualDetection]:
        boxes = result.boxes
        names = result.names
        detections: list[VisualDetection] = []
        if boxes is None:
            return detections
        for index, (xyxy, confidence, class_id) in enumerate(
            zip(boxes.xyxy.cpu().tolist(), boxes.conf.cpu().tolist(), boxes.cls.cpu().tolist()),
            start=1,
        ):
            class_name = names[int(class_id)]
            if class_name not in allowed:
                raise PipelineUnavailableError(
                    f"The {kind} model returned unsupported class '{class_name}'."
                )
            detections.append(
                VisualDetection(
                    id=f"{prefix}{index}",
                    kind=kind,
                    class_name=class_name,
                    confidence=round(float(confidence), 6),
                    bbox=tuple(round(float(value), 2) for value in xyxy),
                )
            )
        return detections

    @staticmethod
    def _render_overlay(image: Any, detections: list[VisualDetection]) -> str:
        from PIL import ImageDraw, ImageFont

        rendered = image.copy()
        draw = ImageDraw.Draw(rendered)
        font = ImageFont.load_default(size=14)
        colors = {"damage": "#dc5f50", "part": "#1c7c75"}
        for detection in detections:
            color = colors[detection.kind]
            draw.rectangle(detection.bbox, outline=color, width=3)
            label = f"{detection.class_name.replace('_', ' ')} {detection.confidence:.0%}"
            left, top, _, _ = detection.bbox
            text_box = draw.textbbox((left, top), label, font=font)
            draw.rectangle(text_box, fill=color)
            draw.text((left, top), label, fill="white", font=font)
        output = io.BytesIO()
        rendered.save(output, format="JPEG", quality=88)
        encoded = base64.b64encode(output.getvalue()).decode("ascii")
        return f"data:image/jpeg;base64,{encoded}"
