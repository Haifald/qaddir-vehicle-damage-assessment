import io
from pathlib import Path
from unittest import TestCase

from PIL import Image

from qaddir_api.config import Settings, Thresholds
from qaddir_api.cv import InferenceOutput
from qaddir_api.schemas import CVRecord
from qaddir_api.service import AssessmentService


CALIBRATED = Thresholds(
    damage_report=0.4,
    damage_hedge=0.7,
    part_report=0.5,
    association_state=0.6,
    association_ambiguity=0.1,
)


class StubCVPipeline:
    def __init__(self, record):
        self.record = record

    def infer(self, _prepared):
        return InferenceOutput(
            record=self.record,
            visual_detections=[],
            overlay_data_url=None,
        )


class FailingReportGenerator:
    def readiness(self):
        raise AssertionError("A manual-review record must not reach the report generator")


class AssessmentServiceTests(TestCase):
    def test_manual_review_keeps_findings_visible_and_does_not_call_llm(self):
        record = CVRecord.model_validate(
            {
                "image": {"id": "test.png", "usable": True, "quality_note": None},
                "damage_detections": [{"id": "d1", "class": "dent", "confidence": 0.5}],
                "part_detections": [
                    {"id": "p1", "class": "front_door", "confidence": 0.8}
                ],
                "associations": [
                    {
                        "damage_id": "d1",
                        "part_id": "p1",
                        "confidence": 0.8,
                        "alternatives": [],
                    }
                ],
            }
        )
        service = AssessmentService(
            Settings(
                damage_model_path=None,
                part_model_path=None,
                cv_confidence=None,
                cv_image_size=None,
                cv_device=None,
                prompt_path=Path("unused-prompt.md"),
                llm_api_key=None,
                llm_model=None,
                thresholds=CALIBRATED,
                min_image_side=1,
            ),
            cv_pipeline=StubCVPipeline(record),
            report_generator=FailingReportGenerator(),
        )
        image = io.BytesIO()
        Image.new("RGB", (1, 1), "white").save(image, format="PNG")

        result = service.assess(image.getvalue(), "test.png", "image/png")

        self.assertEqual(result.verification.status, "manual_review")
        self.assertFalse(result.verification.llm_eligible)
        self.assertEqual(result.report.status, "blocked")
        self.assertEqual(result.cv_output.damage_detections[0].class_name, "dent")
