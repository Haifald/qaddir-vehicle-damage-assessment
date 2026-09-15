from __future__ import annotations

import logging

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from .config import Settings
from .cv import ImageValidationError, PipelineUnavailableError, UltralyticsCVPipeline
from .llm import OpenAIReportGenerator
from .schemas import (
    CVRecord,
    HealthComponent,
    HealthResponse,
    VerificationRequest,
    VerificationResult,
)
from .service import AssessmentService
from .verification import verify_record


logger = logging.getLogger(__name__)
settings = Settings.from_env()
cv_pipeline = UltralyticsCVPipeline(settings)
report_generator = OpenAIReportGenerator(settings)
service = AssessmentService(settings, cv_pipeline, report_generator)

app = FastAPI(
    title="Qaddir Assessment API",
    version="0.1.0",
    description="Verified application boundary for Qaddir's CV and LLM pipeline.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.exception_handler(RequestValidationError)
async def request_validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "code": "invalid_request",
            "message": "The request is missing required or valid fields.",
            "issues": exc.errors(),
        },
    )


@app.exception_handler(ImageValidationError)
async def image_validation_handler(_: Request, exc: ImageValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"code": "invalid_image", "message": str(exc)},
    )


@app.exception_handler(PipelineUnavailableError)
async def pipeline_unavailable_handler(_: Request, exc: PipelineUnavailableError) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={"code": "cv_pipeline_unavailable", "message": str(exc)},
    )


@app.exception_handler(Exception)
async def unexpected_error_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled API error", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={
            "code": "server_error",
            "message": "The assessment service encountered an unexpected error.",
        },
    )


@app.get("/api/v1/health", response_model=HealthResponse)
def health() -> HealthResponse:
    cv_ready, cv_detail = cv_pipeline.readiness()
    prompt_ready, prompt_detail = report_generator.prompt_loader.readiness()
    llm_ready, llm_detail = report_generator.readiness()
    thresholds_ready = settings.thresholds.calibrated
    components = {
        "cv": HealthComponent(ready=cv_ready, detail=cv_detail),
        "verification": HealthComponent(
            ready=thresholds_ready,
            detail=(
                "Production thresholds are configured."
                if thresholds_ready
                else "Production thresholds are not calibrated/configured."
            ),
        ),
        "prompt": HealthComponent(ready=prompt_ready, detail=prompt_detail),
        "llm": HealthComponent(ready=llm_ready, detail=llm_detail),
    }
    return HealthResponse(
        status="ready" if all(item.ready for item in components.values()) else "configuration_required",
        components=components,
    )


@app.post("/api/v1/assess")
async def assess(image: UploadFile = File(...)):
    content = await image.read()
    return service.assess(content, image.filename or "uploaded-image", image.content_type)


@app.post("/api/v1/verify", response_model=VerificationResult)
def verify(request: VerificationRequest) -> VerificationResult:
    try:
        record = CVRecord.model_validate(request.record)
    except ValidationError as exc:
        return VerificationResult(
            status="rejected",
            llm_eligible=False,
            issues=[
                {
                    "code": "invalid_structure",
                    "message": error["msg"],
                    "path": ".".join(str(value) for value in error["loc"]),
                    "level": "error",
                }
                for error in exc.errors()
            ],
        )
    return verify_record(record, settings.thresholds)
