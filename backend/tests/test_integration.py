from __future__ import annotations

import io
import sys
import types
from pathlib import Path
from unittest import TestCase, mock

from fastapi.testclient import TestClient
from PIL import Image

from qaddir_api import main as api_main
from qaddir_api.config import Settings, Thresholds
from qaddir_api.cv import InferenceOutput, PipelineUnavailableError
from qaddir_api.llm import OpenAIReportGenerator, ReportGenerationError
from qaddir_api.schemas import CVRecord
from qaddir_api.service import AssessmentService


CALIBRATED = Thresholds(
    damage_report=0.4,
    damage_hedge=0.7,
    part_report=0.5,
    association_state=0.6,
    association_ambiguity=0.1,
)


def make_settings() -> Settings:
    return Settings(
        damage_model_path=None,
        part_model_path=None,
        cv_confidence=None,
        cv_image_size=None,
        cv_device=None,
        prompt_path=Path("unused-prompt.md"),
        llm_api_key="test-key",
        llm_model="test-model",
        thresholds=CALIBRATED,
        min_image_side=1,
    )


def png_bytes(size: tuple[int, int] = (8, 8)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, "white").save(buffer, format="PNG")
    return buffer.getvalue()


def make_record(
    *,
    damage_confidence: float = 0.95,
    include_damage: bool = True,
    include_part: bool = True,
) -> CVRecord:
    damage_detections = []
    part_detections = []
    associations = []

    if include_damage:
        damage_detections.append(
            {"id": "d1", "class": "dent", "confidence": damage_confidence}
        )
    if include_part:
        part_detections.append(
            {"id": "p1", "class": "front_door", "confidence": 0.95}
        )
    if include_damage:
        associations.append(
            {
                "damage_id": "d1",
                "part_id": "p1" if include_part else None,
                "confidence": 0.95 if include_part else 0.0,
                "alternatives": [],
            }
        )

    return CVRecord.model_validate(
        {
            "image": {"id": "test.png", "usable": True, "quality_note": None},
            "damage_detections": damage_detections,
            "part_detections": part_detections,
            "associations": associations,
        }
    )


class StubCVPipeline:
    def __init__(self, record: CVRecord):
        self.record = record

    def infer(self, _prepared):
        return InferenceOutput(
            record=self.record,
            visual_detections=[],
            overlay_data_url=None,
        )


class SafeReportGenerator:
    def readiness(self):
        return True, "ready"

    def generate(self, record: CVRecord) -> str:
        if record.damage_detections:
            return "A dent was detected."
        return "No damage was detected."


class FailingReportGenerator:
    def __init__(self, message: str = "The report service could not generate a response."):
        self.message = message

    def readiness(self):
        return True, "ready"

    def generate(self, _record: CVRecord) -> str:
        raise ReportGenerationError(self.message)


class IntegrationHandlingTests(TestCase):
    def service_for(self, record: CVRecord, report_generator=None) -> AssessmentService:
        return AssessmentService(
            make_settings(),
            cv_pipeline=StubCVPipeline(record),
            report_generator=report_generator or SafeReportGenerator(),
        )

    def test_normal_damaged_vehicle_completes_without_exception(self):
        result = self.service_for(make_record()).assess(
            png_bytes(), "test.png", "image/png"
        )
        self.assertEqual(result.cv_output.damage_detections[0].class_name, "dent")
        self.assertIn(result.report.status, {"generated", "blocked", "unavailable"})

    def test_no_damage_result_is_controlled(self):
        result = self.service_for(
            make_record(include_damage=False, include_part=True)
        ).assess(png_bytes(), "test.png", "image/png")
        self.assertEqual(result.cv_output.damage_detections, [])
        self.assertIn(result.report.status, {"generated", "blocked", "unavailable"})

    def test_no_part_result_is_controlled(self):
        result = self.service_for(
            make_record(include_damage=True, include_part=False)
        ).assess(png_bytes(), "test.png", "image/png")
        self.assertEqual(result.cv_output.part_detections, [])
        self.assertIn(result.report.status, {"generated", "blocked", "unavailable"})

    def test_low_confidence_result_is_controlled(self):
        result = self.service_for(make_record(damage_confidence=0.45)).assess(
            png_bytes(), "test.png", "image/png"
        )
        self.assertIn(result.verification.status.value, {"verified", "manual_review", "rejected"})
        self.assertIn(result.report.status, {"generated", "blocked", "unavailable"})

    def test_report_generation_failure_becomes_failed_report(self):
        result = self.service_for(
            make_record(), FailingReportGenerator()
        ).assess(png_bytes(), "test.png", "image/png")
        self.assertEqual(result.report.status, "failed")
        self.assertIn("could not generate", result.report.message or "")


class APIFailureHandlingTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(api_main.app, raise_server_exceptions=False)

    def test_corrupt_file_returns_controlled_400(self):
        response = self.client.post(
            "/api/v1/assess",
            files={"image": ("broken.png", b"not-an-image", "image/png")},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "invalid_image")

    def test_missing_upload_returns_controlled_422(self):
        response = self.client.post("/api/v1/assess")
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], "invalid_request")

    def test_pipeline_unavailable_returns_controlled_503(self):
        with mock.patch.object(
            api_main.service,
            "assess",
            side_effect=PipelineUnavailableError("CV models are unavailable."),
        ):
            response = self.client.post(
                "/api/v1/assess",
                files={"image": ("test.png", png_bytes(), "image/png")},
            )
        self.assertEqual(response.status_code, 503)
        body = response.json()
        self.assertEqual(body["code"], "cv_pipeline_unavailable")
        self.assertNotIn("Traceback", body["message"])

    def test_unexpected_exception_returns_generic_500_without_internal_detail(self):
        with mock.patch.object(
            api_main.service,
            "assess",
            side_effect=RuntimeError("internal-secret-detail"),
        ):
            response = self.client.post(
                "/api/v1/assess",
                files={"image": ("test.png", png_bytes(), "image/png")},
            )
        self.assertEqual(response.status_code, 500)
        body = response.json()
        self.assertEqual(body["code"], "server_error")
        self.assertNotIn("internal-secret-detail", body["message"])
        self.assertNotIn("Traceback", body["message"])


class LLMProviderFailureTests(TestCase):
    def test_provider_failure_timeout_and_rate_limit_are_normalized(self):
        record = make_record()
        generator = OpenAIReportGenerator(make_settings())

        failure_cases = {
            "api_failure": RuntimeError("provider unavailable"),
            "timeout": TimeoutError("provider timed out"),
            "rate_limit": RuntimeError("429 rate limit"),
        }

        for name, provider_error in failure_cases.items():
            with self.subTest(name=name):
                class FakeResponses:
                    def create(self, **_kwargs):
                        raise provider_error

                class FakeClient:
                    def __init__(self, **_kwargs):
                        self.responses = FakeResponses()

                fake_openai = types.SimpleNamespace(OpenAI=FakeClient)
                with (
                    mock.patch.dict(sys.modules, {"openai": fake_openai}),
                    mock.patch.object(generator, "readiness", return_value=(True, "ready")),
                    mock.patch.object(
                        generator.prompt_loader,
                        "load_system_prompt",
                        return_value="system prompt",
                    ),
                ):
                    with self.assertRaises(ReportGenerationError) as context:
                        generator.generate(record)

                self.assertEqual(
                    str(context.exception),
                    "The report service could not generate a response.",
                )
