# TASK-30 — Integration Testing, Failure Handling and Latency Profiling

## Objective

Verify that Qaddir's integrated assessment path behaves predictably for normal and abnormal inputs, returns controlled user-facing failures instead of raw exceptions, and records cold/warm latency for the major runtime stages.

## Automated integration matrix

Run from the repository root:

```bash
PYTHONPATH=backend python -m unittest discover -s backend/tests -v
```

The TASK-30 coverage added in `backend/tests/test_integration.py` covers:

| Case | Expected handling | Test method |
|---|---|---|
| Normal damaged-image record | Structured response; no uncaught exception | Deterministic CV stub + real verification/service flow |
| No damage detected | Empty damage list remains a controlled assessment result | Deterministic CV stub |
| No part detected | Missing part evidence remains a controlled assessment result | Deterministic CV stub |
| Low-confidence result | Verification/report path remains controlled | Deterministic CV stub |
| Corrupt image | HTTP 400 `invalid_image` | Real API + real image validation |
| Missing upload | HTTP 422 `invalid_request` | Real API request validation |
| CV pipeline unavailable | HTTP 503 `cv_pipeline_unavailable` | API failure injection |
| Unexpected backend exception | Generic HTTP 500 without internal exception detail | API failure injection |
| LLM/API failure | Normalized to `ReportGenerationError` / failed report | Provider stub |
| LLM timeout | Normalized to `ReportGenerationError` / failed report | Provider stub |
| LLM rate limit | Normalized to `ReportGenerationError` / failed report | Provider stub |

The deterministic stubs are intentional: they exercise failure-handling branches without requiring a particular model prediction to occur on demand.

## Non-vehicle live spot-check

A non-vehicle input must also be sent through the **real configured CV pipeline** before TASK-30 is closed. A plain generated image is sufficient because it is valid image data but is not a vehicle photograph.

Create the input:

```bash
python - <<'PY'
from PIL import Image
Image.new("RGB", (640, 640), "white").save("/tmp/qaddir_non_vehicle.png")
PY
```

With the API running, call:

```bash
curl -s -X POST \
  -F "image=@/tmp/qaddir_non_vehicle.png;type=image/png" \
  http://127.0.0.1:8000/api/v1/assess
```

**Pass criterion:** the API returns a structured JSON response or a controlled documented error. It must not expose a traceback or crash the server. Record the observed HTTP status and high-level outcome below after the run.

- HTTP status: `PENDING`
- Outcome: `PENDING`

## Latency profiling

Use a real damaged-vehicle image from the planned demo set:

```bash
PYTHONPATH=backend python scripts/profile_pipeline.py /path/to/demo-image.jpg --runs 3
```

The script writes `docs/integration_latency.json` and records:

- image validation
- CV inference + damage-to-part association + structured record creation
- verification
- report generation + output guard, when eligible/configured
- total end-to-end time
- cold run (includes lazy model-load cost)
- warm runs using the already-loaded model objects

The warm-run average is the relevant number for the live-demo interaction after the first request. The cold run is retained to document startup/model-loading cost rather than hiding it.

## Latency result

The measured values are stored in `docs/integration_latency.json` after profiling. Do not copy a latency number into this document until the profiler has been run on the presentation machine/configuration.

If the dominant stage is too slow for the demo, the first optimization should preserve one-time model loading and reuse the same `UltralyticsCVPipeline` instance across requests. The current FastAPI application already creates the pipeline/service at module startup, so profiling should confirm whether additional optimization is actually necessary before changing code.

## Definition-of-Done checklist

- [ ] Full backend test suite passes, including `test_integration.py`.
- [ ] Normal, no-damage, no-part and low-confidence handling paths are covered.
- [ ] Corrupt/missing input and CV/API failures return controlled errors.
- [ ] LLM API failure, timeout and rate-limit paths are covered without live API calls.
- [ ] A real configured pipeline is spot-checked with a non-vehicle image.
- [ ] `docs/integration_latency.json` exists with cold and warm stage/total measurements.
- [ ] Warm latency is reviewed for live-demo acceptability; any required optimization is documented.

TASK-30 should only be moved to **Done** after every box above is supported by an actual test/profile result.
