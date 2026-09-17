import type { ApiError, AssessmentResponse, HealthResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

// CPU inference on both models can be slow; stop waiting well after a normal run.
const ASSESS_TIMEOUT_MS = 180_000;

/**
 * Failed API call. `message` is the backend's raw message (possibly empty) and
 * must not be shown directly; map it through `describeError` in `lib/errors.ts`.
 */
export class ApiRequestError extends Error implements ApiError {
  readonly code: string;
  readonly status: number | null;

  constructor(code: string, message = "", status: number | null = null) {
    super(message);
    this.name = "ApiRequestError";
    this.code = code;
    this.status = status;
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isHealthResponse(payload: unknown): payload is HealthResponse {
  return isRecord(payload) && typeof payload.status === "string" && isRecord(payload.components);
}

function isAssessmentResponse(payload: unknown): payload is AssessmentResponse {
  if (!isRecord(payload) || typeof payload.analysis_id !== "string") return false;
  const { cv_output: cv, verification, report } = payload;
  return (
    isRecord(cv) &&
    isRecord(cv.image) &&
    Array.isArray(cv.damage_detections) &&
    Array.isArray(cv.part_detections) &&
    Array.isArray(cv.associations) &&
    isRecord(verification) &&
    typeof verification.status === "string" &&
    Array.isArray(verification.issues) &&
    isRecord(report) &&
    typeof report.status === "string"
  );
}

async function request(path: string, init: RequestInit, timeoutMs?: number): Promise<Response> {
  const controller = new AbortController();
  const timer = timeoutMs === undefined ? undefined : setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(`${API_BASE}${path}`, { ...init, signal: controller.signal });
  } catch {
    throw new ApiRequestError(controller.signal.aborted ? "timeout" : "network_error");
  } finally {
    clearTimeout(timer);
  }
}

async function parseResponse<T>(response: Response, isValid: (payload: unknown) => payload is T): Promise<T> {
  const payload: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const fallbackCode = response.status >= 500 ? "server_error" : "request_failed";
    const code = isRecord(payload) && typeof payload.code === "string" ? payload.code : fallbackCode;
    const message = isRecord(payload) && typeof payload.message === "string" ? payload.message : "";
    throw new ApiRequestError(code, message, response.status);
  }
  if (!isValid(payload)) {
    throw new ApiRequestError("invalid_response", "", response.status);
  }
  return payload;
}

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await request("/api/v1/health", { cache: "no-store" });
  return parseResponse(response, isHealthResponse);
}

export async function assessImage(file: File): Promise<AssessmentResponse> {
  const body = new FormData();
  body.append("image", file);
  const response = await request("/api/v1/assess", { method: "POST", body }, ASSESS_TIMEOUT_MS);
  return parseResponse(response, isAssessmentResponse);
}
