from __future__ import annotations

from uuid import uuid4

from .config import Settings
from .cv import UltralyticsCVPipeline, validate_image
from .llm import OpenAIReportGenerator, PromptUnavailableError, ReportGenerationError
from .report_guard import UnsafeReportError, validate_report
from .schemas import AssessmentResponse, ReportResult, VerificationStatus
from .verification import verify_record


DISCLAIMER = (
    "AI-assisted preliminary result only. A qualified human assessor remains "
    "responsible for the final decision."
)


class AssessmentService:
    def __init__(
        self,
        settings: Settings,
        cv_pipeline: UltralyticsCVPipeline | None = None,
        report_generator: OpenAIReportGenerator | None = None,
    ):
        self.settings = settings
        self.cv_pipeline = cv_pipeline or UltralyticsCVPipeline(settings)
        self.report_generator = report_generator or OpenAIReportGenerator(settings)

    def assess(self, content: bytes, filename: str, content_type: str | None) -> AssessmentResponse:
        prepared = validate_image(content, filename, content_type, self.settings)
        inference = self.cv_pipeline.infer(prepared)
        verification = verify_record(inference.record, self.settings.thresholds)

        if verification.status is VerificationStatus.REJECTED:
            report = ReportResult(
                status="blocked",
                message="The CV record failed verification and was not sent to the LLM.",
            )
        elif verification.status is VerificationStatus.MANUAL_REVIEW:
            report = ReportResult(
                status="blocked",
                message=(
                    "The structured findings require manual review and were not sent to the LLM."
                ),
            )
        elif not verification.llm_eligible:
            report = ReportResult(
                status="blocked",
                message="This record is not eligible for automated report generation.",
            )
        else:
            report = self._generate_report(inference.record)

        recommendation = (
            "Manual review required before any assessment conclusion."
            if verification.status is not VerificationStatus.VERIFIED
            else "Qualified assessor review required before any final decision."
        )
        return AssessmentResponse(
            analysis_id=str(uuid4()),
            cv_output=inference.record,
            visual_detections=inference.visual_detections,
            overlay_data_url=inference.overlay_data_url,
            verification=verification,
            severity=None,
            report=report,
            recommendation=recommendation,
            disclaimer=DISCLAIMER,
        )

    def _generate_report(self, record):
        ready, detail = self.report_generator.readiness()
        if not ready:
            return ReportResult(status="unavailable", message=detail)
        try:
            text = self.report_generator.generate(record)
            validate_report(text, record)
            return ReportResult(status="generated", text=text)
        except UnsafeReportError as exc:
            return ReportResult(
                status="failed",
                message=f"The generated report failed the output safety check: {exc}",
            )
        except (PromptUnavailableError, ReportGenerationError) as exc:
            return ReportResult(status="failed", message=str(exc))
