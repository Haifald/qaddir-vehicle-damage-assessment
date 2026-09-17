"""TASK-35 integrated end-to-end system evaluation.

Runs every held-out image through the real assessment service (validation, CV
inference, damage-to-part association, verification and the report gate) and
writes a machine-readable scorecard plus per-image predictions.

Measures:

- damage detection at the deployed operating point (class-aware and
  class-agnostic precision/recall at IoU 0.5) against YOLO box labels
- optional dataset-level mAP on the same labelled subset (``--map``)
- damage-to-part association behaviour; accuracy only when a human-verified
  reference sheet is supplied (``--matching-reference``)
- verification and report-gate outcomes
- end-to-end latency, failures and controlled handling of invalid inputs

The language model is never called unless ``--allow-llm`` is passed.

Usage, from the repository root:

    PYTHONPATH=backend python scripts/evaluate_system.py \\
        --env-file .env \\
        --images <CarDD_YOLO>/images/test \\
        --labels <CarDD_YOLO>/labels/test \\
        --data-yaml <CarDD_YOLO>/data.yaml \\
        --out docs/evaluation --map

Outputs never contain absolute paths or secrets.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import platform
import random
import statistics
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

IOU_THRESHOLD = 0.5
SAMPLE_SEED = 35
SAMPLE_SIZE = 60
IMAGE_SUFFIXES = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
SAMPLE_FIELDS = [
    "sample_id",
    "image",
    "damage_id",
    "damage_class",
    "damage_confidence",
    "damage_bbox_xyxy",
    "predicted_part_id",
    "predicted_part_class",
    "overlap_score",
    "alternatives",
    "reference_part_class",
    "reviewer",
    "notes",
]


# --------------------------------------------------------------------------- setup


def load_env_file(path: Path) -> None:
    """Load KEY=VALUE lines without overriding the environment. Values are never printed."""
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


class DisabledReportGenerator:
    """Stands in for the LLM so an evaluation run can never call a provider by accident."""

    def readiness(self) -> tuple[bool, str]:
        return False, "Report generation disabled for this evaluation run."

    def generate(self, record):  # pragma: no cover - unreachable while readiness is False
        raise RuntimeError("Report generation is disabled for this evaluation run.")


def sha256_prefix(path: Path | None, length: int = 16) -> str | None:
    if path is None or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()[:length]


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round(fraction * (len(ordered) - 1))))
    return round(ordered[index], 2)


def ratio(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 4) if denominator else None


# ------------------------------------------------------------------------- labels


def load_class_names(data_yaml: Path) -> dict[int, str]:
    import yaml

    from qaddir_api.cv import normalise_class_name

    names = yaml.safe_load(data_yaml.read_text(encoding="utf-8"))["names"]
    if isinstance(names, list):
        names = dict(enumerate(names))
    return {int(index): normalise_class_name(str(name)) for index, name in names.items()}


def load_ground_truth(label_path: Path, width: int, height: int, names: dict[int, str]) -> list[dict]:
    boxes = []
    for line in label_path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if len(fields) != 5:
            raise ValueError(f"{label_path.name}: expected YOLO box rows with 5 fields")
        class_id, cx, cy, w, h = int(fields[0]), *map(float, fields[1:])
        boxes.append(
            {
                "class": names[class_id],
                "bbox": (
                    (cx - w / 2) * width,
                    (cy - h / 2) * height,
                    (cx + w / 2) * width,
                    (cy + h / 2) * height,
                ),
            }
        )
    return boxes


def iou(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    intersection = ix * iy
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - intersection
    return intersection / union if union > 0 else 0.0


def match_detections(predictions: list[dict], truths: list[dict], *, class_aware: bool) -> tuple[list[bool], list[bool]]:
    """Greedy confidence-ordered matching. Returns (prediction is TP, truth is matched)."""
    prediction_hit = [False] * len(predictions)
    truth_hit = [False] * len(truths)
    for p_index in sorted(range(len(predictions)), key=lambda i: -predictions[i]["confidence"]):
        prediction = predictions[p_index]
        best, best_iou = None, IOU_THRESHOLD
        for t_index, truth in enumerate(truths):
            if truth_hit[t_index] or (class_aware and truth["class"] != prediction["class"]):
                continue
            overlap = iou(prediction["bbox"], truth["bbox"])
            if overlap >= best_iou:
                best, best_iou = t_index, overlap
        if best is not None:
            prediction_hit[p_index] = True
            truth_hit[best] = True
    return prediction_hit, truth_hit


# ------------------------------------------------------------------------ images


def discover_images(images_dir: Path) -> tuple[list[Path], list[str]]:
    """Return unique images (by content) and the names skipped as byte-identical duplicates.

    Canonical names are visited first so a browser-style copy such as ``003703(1).jpg``
    is the one skipped, not the original that its label file is named after.
    """
    seen: dict[str, str] = {}
    unique, duplicates = [], []
    for path in sorted(images_dir.iterdir(), key=lambda item: ("(" in item.stem, item.name)):
        if path.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest in seen:
            duplicates.append(path.name)
            continue
        seen[digest] = path.name
        unique.append(path)
    return unique, duplicates


def robustness_probes(service, settings) -> list[dict]:
    from PIL import Image

    from qaddir_api.cv import ImageValidationError

    def encoded(image, fmt: str) -> bytes:
        buffer = io.BytesIO()
        image.save(buffer, format=fmt)
        return buffer.getvalue()

    probes = [
        ("non_vehicle_blank_image", encoded(Image.new("RGB", (640, 640), "white"), "PNG"), "image/png"),
        (
            "below_minimum_size",
            encoded(Image.new("RGB", (settings.min_image_side // 2,) * 2, "gray"), "JPEG"),
            "image/jpeg",
        ),
        ("corrupt_bytes", b"not an image" * 64, "image/jpeg"),
        ("unsupported_content_type", encoded(Image.new("RGB", (640, 640), "white"), "PNG"), "image/gif"),
    ]
    results = []
    for name, content, content_type in probes:
        try:
            response = service.assess(content, f"{name}.bin", content_type)
            results.append(
                {
                    "probe": name,
                    "outcome": "structured_response",
                    "image_usable": response.cv_output.image.usable,
                    "damage_detections": len(response.cv_output.damage_detections),
                    "verification_status": response.verification.status.value,
                    "report_status": response.report.status,
                }
            )
        except ImageValidationError:
            results.append({"probe": name, "outcome": "controlled_rejection", "error": "invalid_image"})
        except Exception as exc:  # recorded, never raised: the point is to observe handling
            results.append({"probe": name, "outcome": "uncontrolled_exception", "error": type(exc).__name__})
    return results


# ---------------------------------------------------------------------- matching


def build_matching_sample(damage_rows: list[dict]) -> list[dict]:
    """Deterministic, class-stratified sample of correctly detected damages for human reference labelling."""
    by_class: dict[str, list[dict]] = defaultdict(list)
    for row in damage_rows:
        by_class[row["damage_class"]].append(row)
    rng = random.Random(SAMPLE_SEED)
    for rows in by_class.values():
        rows.sort(key=lambda row: (row["image"], row["damage_id"]))
        rng.shuffle(rows)
    sample: list[dict] = []
    while len(sample) < SAMPLE_SIZE and any(by_class.values()):
        for cls in sorted(by_class):
            if by_class[cls] and len(sample) < SAMPLE_SIZE:
                sample.append(by_class[cls].pop())
    for index, row in enumerate(sample, start=1):
        row["sample_id"] = f"m{index:03d}"
    return sample


def sample_has_reference(path: Path) -> bool:
    if not path.is_file():
        return False
    with path.open(newline="", encoding="utf-8") as handle:
        return any((row.get("reference_part_class") or "").strip() for row in csv.DictReader(handle))


def score_matching_reference(path: Path) -> dict:
    """Score a human-verified sheet. `none` in reference_part_class means no part should be linked."""
    with path.open(newline="", encoding="utf-8") as handle:
        rows = [row for row in csv.DictReader(handle) if (row.get("reference_part_class") or "").strip()]
    per_class: dict[str, Counter] = defaultdict(Counter)
    errors = []
    for row in rows:
        predicted = (row["predicted_part_class"] or "none").strip()
        reference = row["reference_part_class"].strip()
        correct = predicted == reference
        per_class[row["damage_class"]]["correct" if correct else "incorrect"] += 1
        if not correct:
            errors.append({"sample_id": row["sample_id"], "damage_class": row["damage_class"], "predicted": predicted, "reference": reference, "notes": row.get("notes", "")})
    correct = sum(counter["correct"] for counter in per_class.values())
    return {
        "verified_instances": len(rows),
        "accuracy": ratio(correct, len(rows)),
        "per_damage_class": {cls: {"n": sum(c.values()), "accuracy": ratio(c["correct"], sum(c.values()))} for cls, c in sorted(per_class.items())},
        "errors": errors,
    }


# ---------------------------------------------------------------------------- mAP


def dataset_map(settings, labelled: list[tuple[Path, Path]], data_yaml_names: dict[int, str]) -> dict:
    """Standard Ultralytics box mAP on the labelled subset, in a temporary dataset of symlinks."""
    from ultralytics import YOLO

    from qaddir_api.cv import normalise_class_name

    model = YOLO(str(settings.damage_model_path))
    model_names = {int(k): normalise_class_name(v) for k, v in model.names.items()}
    if model_names != data_yaml_names:
        raise SystemExit("Model class order does not match the label class order; refusing to compute mAP.")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "images" / "test").mkdir(parents=True)
        (root / "labels" / "test").mkdir(parents=True)
        for image, label in labelled:
            (root / "images" / "test" / image.name).symlink_to(image.resolve())
            (root / "labels" / "test" / f"{image.stem}.txt").symlink_to(label.resolve())
        yaml_path = root / "data.yaml"
        yaml_path.write_text(
            json.dumps({"path": str(root), "train": "images/test", "val": "images/test", "test": "images/test", "names": model.names}),
            encoding="utf-8",
        )
        metrics = model.val(
            data=str(yaml_path),
            split="test",
            imgsz=settings.cv_image_size,
            device=settings.cv_device,
            batch=8,
            plots=False,
            verbose=False,
            project=str(root / "runs"),
            name="val",
        )
    box = metrics.box
    return {
        "images": len(labelled),
        "precision": round(float(box.mp), 4),
        "recall": round(float(box.mr), 4),
        "map50": round(float(box.map50), 4),
        "map50_95": round(float(box.map), 4),
        "per_class_map50_95": {model_names[i]: round(float(v), 4) for i, v in enumerate(box.maps)},
        "note": "Ultralytics defaults (conf 0.001); comparable to the notebook test run, not to the operating point.",
    }


# --------------------------------------------------------------------------- main


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--images", type=Path, required=True)
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--data-yaml", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("docs/evaluation"))
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--map", action="store_true", help="also compute dataset-level mAP on the labelled subset")
    parser.add_argument("--matching-reference", type=Path, help="human-verified matching sheet to score")
    parser.add_argument("--allow-llm", action="store_true", help="let eligible records call the configured LLM")
    args = parser.parse_args()

    if args.env_file:
        load_env_file(args.env_file)
    # Ultralytics otherwise pip-installs optional packages into the environment during val().
    os.environ.setdefault("YOLO_AUTOINSTALL", "false")

    from PIL import Image

    from qaddir_api.config import Settings
    from qaddir_api.cv import UltralyticsCVPipeline
    from qaddir_api.service import AssessmentService

    settings = Settings.from_env()
    names = load_class_names(args.data_yaml)
    cv_pipeline = UltralyticsCVPipeline(settings)

    load_start = perf_counter()
    ready, _ = cv_pipeline.readiness()
    model_load_ms = round((perf_counter() - load_start) * 1000, 2)
    if not ready:
        raise SystemExit("CV pipeline is not ready; check the model paths and CV settings.")

    report_generator = None if args.allow_llm else DisabledReportGenerator()
    service = AssessmentService(settings, cv_pipeline, report_generator)  # type: ignore[arg-type]

    images, duplicates = discover_images(args.images)
    args.out.mkdir(parents=True, exist_ok=True)

    counts = {k: Counter() for k in ("tp", "fp", "fn", "gt", "pred")}
    agnostic = Counter()
    fn_kind = Counter()
    image_level = Counter()
    latencies: list[float] = []
    failures: list[dict] = []
    verification_status = Counter()
    report_status = Counter()
    issue_images = Counter()
    rejection_reasons = Counter()
    llm_eligible = 0
    association_stats = Counter()
    leader_scores: list[float] = []
    sample_candidates: list[dict] = []
    labelled_pairs: list[tuple[Path, Path]] = []

    with (args.out / "predictions.jsonl").open("w", encoding="utf-8") as predictions_out:
        for path in images:
            content = path.read_bytes()
            start = perf_counter()
            try:
                response = service.assess(content, path.name, IMAGE_SUFFIXES[path.suffix.lower()])
            except Exception as exc:
                failures.append({"image": path.name, "error": type(exc).__name__})
                continue
            elapsed = round((perf_counter() - start) * 1000, 2)
            latencies.append(elapsed)

            cv = response.cv_output
            verification = response.verification
            verification_status[verification.status.value] += 1
            report_status[response.report.status] += 1
            llm_eligible += int(verification.llm_eligible)
            codes = sorted({issue.code for issue in verification.issues})
            for code in codes:
                issue_images[code] += 1
            if verification.status.value == "rejected":
                for code in {issue.code for issue in verification.issues if issue.level == "error"}:
                    rejection_reasons[code] += 1

            parts = {part.id: part for part in cv.part_detections}
            visuals = {item.id: item for item in response.visual_detections}
            associations = {item.damage_id: item for item in cv.associations}
            predictions = [
                {"id": d.id, "class": d.class_name, "confidence": d.confidence, "bbox": tuple(visuals[d.id].bbox)}
                for d in cv.damage_detections
            ]

            damage_records = []
            for prediction in predictions:
                association = associations.get(prediction["id"])
                linked = association is not None and association.part_id in parts
                association_stats["damages"] += 1
                association_stats["linked" if linked else "unlinked"] += 1
                if association and association.alternatives:
                    association_stats["with_alternatives"] += 1
                    if any(abs(alt.confidence - association.confidence) < 1e-9 for alt in association.alternatives):
                        association_stats["tied_leader"] += 1
                if linked:
                    leader_scores.append(association.confidence)
                damage_records.append(
                    {
                        "id": prediction["id"],
                        "class": prediction["class"],
                        "confidence": round(prediction["confidence"], 4),
                        "bbox_xyxy": [round(v, 1) for v in prediction["bbox"]],
                        "part_id": association.part_id if association else None,
                        "part_class": parts[association.part_id].class_name if linked else None,
                        "overlap_score": round(association.confidence, 4) if association else None,
                        "alternatives": [
                            {"part_class": parts[alt.part_id].class_name if alt.part_id in parts else None, "overlap_score": round(alt.confidence, 4)}
                            for alt in (association.alternatives if association else [])
                        ],
                    }
                )

            label_path = args.labels / f"{path.stem}.txt"
            labelled = label_path.is_file()
            detection_eval = None
            if labelled:
                labelled_pairs.append((path, label_path))
                with Image.open(io.BytesIO(content)) as image:
                    width, height = image.size
                truths = load_ground_truth(label_path, width, height, names)
                hits, truth_hits = match_detections(predictions, truths, class_aware=True)
                agnostic_hits, agnostic_truth_hits = match_detections(predictions, truths, class_aware=False)
                for truth in truths:
                    counts["gt"][truth["class"]] += 1
                for prediction, hit in zip(predictions, hits):
                    counts["pred"][prediction["class"]] += 1
                    counts["tp" if hit else "fp"][prediction["class"]] += 1
                for truth, hit, agnostic_hit in zip(truths, truth_hits, agnostic_truth_hits):
                    if not hit:
                        counts["fn"][truth["class"]] += 1
                        fn_kind["wrong_class" if agnostic_hit else "missed"] += 1
                agnostic["tp"] += sum(agnostic_hits)
                agnostic["pred"] += len(predictions)
                agnostic["gt"] += len(truths)
                image_level["labelled"] += 1
                image_level["any_correct_detection"] += int(any(hits))
                image_level["no_detections"] += int(not predictions)
                for record, hit in zip(damage_records, hits):
                    record["true_positive"] = hit
                    if hit:
                        sample_candidates.append(
                            {
                                "image": path.name,
                                "damage_id": record["id"],
                                "damage_class": record["class"],
                                "damage_confidence": record["confidence"],
                                "damage_bbox_xyxy": " ".join(str(v) for v in record["bbox_xyxy"]),
                                "predicted_part_id": record["part_id"] or "",
                                "predicted_part_class": record["part_class"] or "none",
                                "overlap_score": record["overlap_score"] if record["overlap_score"] is not None else "",
                                "alternatives": "; ".join(f"{a['part_class']}:{a['overlap_score']}" for a in record["alternatives"]),
                                "reference_part_class": "",
                                "reviewer": "",
                                "notes": "",
                            }
                        )
                detection_eval = {"ground_truth": len(truths), "true_positives": sum(hits)}

            predictions_out.write(
                json.dumps(
                    {
                        "image": path.name,
                        "labelled": labelled,
                        "latency_ms": elapsed,
                        "image_usable": cv.image.usable,
                        "damages": damage_records,
                        "parts": [{"id": p.id, "class": p.class_name, "confidence": round(p.confidence, 4)} for p in cv.part_detections],
                        "verification_status": verification.status.value,
                        "llm_eligible": verification.llm_eligible,
                        "issue_codes": codes,
                        "report_status": response.report.status,
                        "detection_eval": detection_eval,
                    }
                )
                + "\n"
            )

    classes = sorted(set(names.values()))
    per_class = {}
    for cls in classes:
        tp, fp, fn = counts["tp"][cls], counts["fp"][cls], counts["fn"][cls]
        precision, recall = ratio(tp, tp + fp), ratio(tp, tp + fn)
        f1 = round(2 * precision * recall / (precision + recall), 4) if precision and recall else None
        per_class[cls] = {"ground_truth": counts["gt"][cls], "predictions": counts["pred"][cls], "tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}
    tp_all, fp_all, fn_all = (sum(counts[k].values()) for k in ("tp", "fp", "fn"))

    sample_path = args.out / "matching_reference_sample.csv"
    if sample_has_reference(sample_path):
        sample_note = "existing sheet contains reference labels; not overwritten"
    else:
        sample = build_matching_sample(sample_candidates)
        with sample_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=SAMPLE_FIELDS)
            writer.writeheader()
            writer.writerows(sample)
        sample_note = f"{len(sample)} correctly detected damage instances written for human verification"

    summary = {
        "task": "TASK-35 integrated end-to-end system evaluation",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "configuration": {
            "damage_model": settings.damage_model_path.name,
            "damage_model_sha256_prefix": sha256_prefix(settings.damage_model_path),
            "part_model": settings.part_model_path.name,
            "part_model_sha256_prefix": sha256_prefix(settings.part_model_path),
            "cv_confidence": settings.cv_confidence,
            "cv_image_size": settings.cv_image_size,
            "cv_device": settings.cv_device,
            "thresholds_calibrated": settings.thresholds.calibrated,
            "llm_called": bool(args.allow_llm),
            "platform": f"{platform.system()} {platform.machine()}, Python {platform.python_version()}",
        },
        "dataset": {
            "images_found": len(images) + len(duplicates),
            "duplicate_files_skipped": len(duplicates),
            "unique_images_evaluated": len(images),
            "labelled_images": image_level["labelled"],
            "unlabelled_images": len(images) - image_level["labelled"],
        },
        "damage_detection_operating_point": {
            "iou_threshold": IOU_THRESHOLD,
            "class_aware": {"tp": tp_all, "fp": fp_all, "fn": fn_all, "precision": ratio(tp_all, tp_all + fp_all), "recall": ratio(tp_all, tp_all + fn_all)},
            "class_agnostic": {"precision": ratio(agnostic["tp"], agnostic["pred"]), "recall": ratio(agnostic["tp"], agnostic["gt"])},
            "missed_ground_truth": {"not_localised": fn_kind["missed"], "localised_with_wrong_class": fn_kind["wrong_class"]},
            "per_class": per_class,
            "images": {
                "labelled": image_level["labelled"],
                "with_at_least_one_correct_detection": image_level["any_correct_detection"],
                "with_no_damage_detections": image_level["no_detections"],
            },
        },
        "damage_to_part_association": {
            "damage_detections": association_stats["damages"],
            "linked_to_a_part": association_stats["linked"],
            "not_linked": association_stats["unlinked"],
            "with_alternatives": association_stats["with_alternatives"],
            "leader_tied_with_alternative": association_stats["tied_leader"],
            "median_leader_overlap_score": round(statistics.median(leader_scores), 4) if leader_scores else None,
            "reference_sample": sample_note,
            "accuracy": score_matching_reference(args.matching_reference) if args.matching_reference else None,
        },
        "verification_and_report_gate": {
            "verification_status": dict(verification_status),
            "llm_eligible": llm_eligible,
            "report_status": dict(report_status),
            "images_with_issue_code": dict(sorted(issue_images.items())),
            "rejected_images_by_error_code": dict(sorted(rejection_reasons.items())),
        },
        "runtime": {
            "model_load_and_readiness_ms": model_load_ms,
            "completed": len(latencies),
            "failed": len(failures),
            "failures": failures,
            "latency_ms": {
                "mean": round(statistics.fmean(latencies), 2) if latencies else None,
                "p50": percentile(latencies, 0.50),
                "p90": percentile(latencies, 0.90),
                "p95": percentile(latencies, 0.95),
                "max": round(max(latencies), 2) if latencies else None,
            },
            "note": "Warm, in-process service.assess(): validation, inference, association, overlay rendering, verification, report gate. Excludes HTTP transport.",
        },
        "robustness_probes": robustness_probes(service, settings),
    }
    if args.map:
        summary["damage_detection_dataset_map"] = dataset_map(settings, labelled_pairs, names)

    (args.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Evaluated {len(latencies)} images ({len(failures)} failed). Results written to {args.out}/")


if __name__ == "__main__":
    main()
