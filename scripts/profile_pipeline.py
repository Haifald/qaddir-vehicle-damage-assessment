from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from time import perf_counter

from qaddir_api.config import Settings
from qaddir_api.cv import UltralyticsCVPipeline, validate_image
from qaddir_api.llm import OpenAIReportGenerator
from qaddir_api.report_guard import validate_report
from qaddir_api.schemas import VerificationStatus
from qaddir_api.verification import verify_record


def milliseconds(start: float) -> float:
    return round((perf_counter() - start) * 1000, 2)


def profile_once(
    *,
    content: bytes,
    filename: str,
    content_type: str,
    settings: Settings,
    cv_pipeline: UltralyticsCVPipeline,
    report_generator: OpenAIReportGenerator,
) -> dict:
    total_start = perf_counter()

    stage_start = perf_counter()
    prepared = validate_image(content, filename, content_type, settings)
    validation_ms = milliseconds(stage_start)

    stage_start = perf_counter()
    inference = cv_pipeline.infer(prepared)
    cv_pipeline_ms = milliseconds(stage_start)

    stage_start = perf_counter()
    verification = verify_record(inference.record, settings.thresholds)
    verification_ms = milliseconds(stage_start)

    report_ms = None
    report_status = "skipped"
    report_detail = None

    if verification.status is VerificationStatus.VERIFIED and verification.llm_eligible:
        ready, detail = report_generator.readiness()
        if ready:
            stage_start = perf_counter()
            try:
                text = report_generator.generate(inference.record)
                validate_report(text, inference.record)
                report_status = "generated"
            except Exception as exc:  # profiling records the controlled stage outcome
                report_status = "failed"
                report_detail = type(exc).__name__
            report_ms = milliseconds(stage_start)
        else:
            report_status = "unavailable"
            report_detail = detail
    else:
        report_status = "blocked"
        report_detail = verification.status.value

    return {
        "validation_ms": validation_ms,
        "cv_inference_association_structure_ms": cv_pipeline_ms,
        "verification_ms": verification_ms,
        "report_generation_and_guard_ms": report_ms,
        "total_ms": milliseconds(total_start),
        "verification_status": verification.status.value,
        "report_status": report_status,
        "report_detail": report_detail,
        "damage_count": len(inference.record.damage_detections),
        "part_count": len(inference.record.part_detections),
        "association_count": len(inference.record.associations),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Profile Qaddir end-to-end latency using the configured local models."
    )
    parser.add_argument("image", type=Path, help="Path to a real image used for the demo path")
    parser.add_argument("--runs", type=int, default=3, help="Number of runs; first run is cold")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/integration_latency.json"),
        help="JSON file to write",
    )
    args = parser.parse_args()

    if args.runs < 2:
        raise SystemExit("Use at least 2 runs so cold and warm latency are both recorded.")
    if not args.image.is_file():
        raise SystemExit(f"Image not found: {args.image}")

    settings = Settings.from_env()
    cv_pipeline = UltralyticsCVPipeline(settings)
    report_generator = OpenAIReportGenerator(settings)

    cv_ready, cv_detail = cv_pipeline.readiness()
    if not cv_ready:
        raise SystemExit(f"CV pipeline is not ready: {cv_detail}")

    content = args.image.read_bytes()
    suffix = args.image.suffix.lower()
    content_type = "image/png" if suffix == ".png" else "image/jpeg"

    runs = []
    for index in range(args.runs):
        result = profile_once(
            content=content,
            filename=args.image.name,
            content_type=content_type,
            settings=settings,
            cv_pipeline=cv_pipeline,
            report_generator=report_generator,
        )
        result["run"] = index + 1
        result["mode"] = "cold" if index == 0 else "warm"
        runs.append(result)

    warm_runs = runs[1:]
    numeric_keys = [
        "validation_ms",
        "cv_inference_association_structure_ms",
        "verification_ms",
        "total_ms",
    ]
    warm_average = {
        key: round(statistics.mean(item[key] for item in warm_runs), 2)
        for key in numeric_keys
    }
    report_values = [
        item["report_generation_and_guard_ms"]
        for item in warm_runs
        if item["report_generation_and_guard_ms"] is not None
    ]
    warm_average["report_generation_and_guard_ms"] = (
        round(statistics.mean(report_values), 2) if report_values else None
    )

    output = {
        "image": args.image.name,
        "runs": runs,
        "warm_average_ms": warm_average,
        "configuration": {
            "cv_confidence": settings.cv_confidence,
            "cv_image_size": settings.cv_image_size,
            "cv_device": settings.cv_device,
            "thresholds_configured": settings.thresholds.calibrated,
            "llm_configured": bool(settings.llm_api_key and settings.llm_model),
            "damage_model": (
                settings.damage_model_path.name if settings.damage_model_path else None
            ),
            "part_model": settings.part_model_path.name if settings.part_model_path else None,
        },
        "notes": [
            "Run 1 is cold and includes any one-time lazy model loading cost.",
            "Warm averages use runs 2..N on the same pipeline instance.",
            "CV stage includes damage inference, part inference, association, and structured-record creation.",
            "Report latency is null when verification blocks the LLM or the LLM is not configured.",
        ],
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))
    print(f"\nSaved latency profile to {args.output}")


if __name__ == "__main__":
    main()
