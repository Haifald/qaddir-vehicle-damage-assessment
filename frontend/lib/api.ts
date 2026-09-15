import type { ApiError, AssessmentResponse, HealthResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function parseResponse<T>(response: Response): Promise<T> {
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(payload.message ?? "The assessment service is unavailable.") as Error & ApiError;
    error.code = payload.code ?? "request_failed";
    throw error;
  }
  return payload as T;
}

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE}/api/v1/health`, { cache: "no-store" });
  return parseResponse<HealthResponse>(response);
}

export async function assessImage(file: File): Promise<AssessmentResponse> {
  const body = new FormData();
  body.append("image", file);
  const response = await fetch(`${API_BASE}/api/v1/assess`, { method: "POST", body });
  return parseResponse<AssessmentResponse>(response);
}
