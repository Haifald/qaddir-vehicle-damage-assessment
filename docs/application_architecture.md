# Application Architecture

## Request flow

```text
Next.js upload UI
        |
        v
FastAPI image validation
        |
        v
Ultralytics damage + part adapters
        |
        v
Provisional overlap association
        |
        v
Structured CV record (Ruba contract)
        |
        v
Verification layer ----> rejected/manual review: show structured findings, no report
        |
        | verified only
        v
Frozen Prompt V2 + verified JSON
        |
        v
OpenAI Responses API
        |
        v
Output safety guard -------------------> failed: suppress report
        |
        v
API response and assessor-facing UI
```

## Responsibilities

| Area | Location | Responsibility |
|---|---|---|
| Frontend | `frontend/` | Upload, progress, structured findings, readiness, error and review states |
| API | `backend/qaddir_api/main.py` | HTTP boundary, validation errors, health and assessment routes |
| CV | `backend/qaddir_api/cv.py` | Image checks, model loading, inference normalization, visual overlay |
| Matching | `backend/qaddir_api/matching.py` | Provisional damage-box coverage association with alternatives |
| Contract | `backend/qaddir_api/schemas.py` | Typed version of the provisional Ruba JSON input |
| Verification | `backend/qaddir_api/verification.py` | Closed sets, references, contradictions, confidence policy, manual review |
| LLM | `backend/qaddir_api/llm.py` | Run the teammate's manifest verifier, read the frozen prompt, inject configured thresholds, send verified JSON |
| Output guard | `backend/qaddir_api/report_guard.py` | Suppress reports that introduce obvious unsupported claims |
| Orchestration | `backend/qaddir_api/service.py` | Preserve stage ordering and assemble the public response |

## API endpoints

- `GET /api/v1/health` loads both configured CV models, validates their class
  vocabularies, checks explicit inference configuration, and reports readiness
  independently for CV, thresholds, the frozen prompt, and the LLM provider.
- `POST /api/v1/assess` accepts one `image` multipart field and runs the pipeline.
- `POST /api/v1/verify` accepts `{ "record": <CV JSON> }` for contract testing
  without invoking an LLM.
- Interactive OpenAPI documentation is available at `/docs` while the API runs.

## Deliberate limitations

- Severity is `null` and displayed as “Not assessed” because neither current CV
  model produces severity and Prompt V2 expressly forbids inventing it.
- The UI has no sample-result mode. Missing models return a professional 503
  error, not simulated detections.
- The association score is box coverage, not a learned or calibrated confidence.
  Uncalibrated thresholds keep report generation disabled by default.
- Hedge-band detections and associations whose lead over the strongest
  alternative is below `QADDIR_T_ASSOC_AMBIG` require manual review. Only a
  `verified` record is eligible for LLM report generation.
- Images and overlays are held for the request only and are returned as a data
  URL. They are not persisted by this implementation.

## LLM evaluation boundary

The application intentionally retains its OpenAI Responses gateway. Ruba's
frozen Prompt V2 was evaluated only on Claude Sonnet 5 (`claude-sonnet-5`). Its
evaluation evidence therefore does not transfer automatically to an OpenAI
model. Before presentation use, the frozen prompt and fixtures must be
re-evaluated against the exact configured `QADDIR_LLM_MODEL`; the frozen prompt
itself must not be modified as part of that evaluation.
