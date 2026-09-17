import { ApiRequestError } from "./api";

export interface UserFacingError {
  code: string;
  title: string;
  message: string;
  note: string | null;
}

type ErrorCopy = Omit<UserFacingError, "code">;

const NO_RESULT = "No assessment result was generated.";

// Fixed copy per error code. Backend messages can carry exception text, model
// paths or provider configuration, so they are never rendered verbatim, with
// the one exception of `invalid_image`, whose messages are authored for users.
const ERROR_COPY: Record<string, ErrorCopy> = {
  no_image: {
    title: "No image selected",
    message: "Choose a vehicle image before running analysis.",
    note: null,
  },
  invalid_image: {
    title: "Image could not be used",
    message: "Upload a readable JPEG, PNG or WebP image of 10 MB or less.",
    note: null,
  },
  invalid_request: {
    title: "Upload could not be read",
    message: "The request did not include a valid image upload. Select the image again and retry.",
    note: NO_RESULT,
  },
  cv_pipeline_unavailable: {
    title: "CV pipeline not configured",
    message: "The computer-vision models are not ready, so the image could not be analyzed.",
    note: NO_RESULT,
  },
  network_error: {
    title: "Assessment service unreachable",
    message: "Qaddir could not reach the assessment service. Check that the API is running, then try again.",
    note: NO_RESULT,
  },
  timeout: {
    title: "Assessment timed out",
    message: "The assessment took too long to complete and was stopped. Try again in a moment.",
    note: NO_RESULT,
  },
  server_error: {
    title: "Assessment service error",
    message: "The assessment service encountered an unexpected error.",
    note: NO_RESULT,
  },
  invalid_response: {
    title: "Unexpected response",
    message: "The assessment service returned a response this page could not read.",
    note: NO_RESULT,
  },
};

const FALLBACK_COPY: ErrorCopy = {
  title: "Analysis could not continue",
  message: "The assessment request did not complete. Try again in a moment.",
  note: NO_RESULT,
};

export function clientError(code: string, message: string): UserFacingError {
  const copy = ERROR_COPY[code] ?? FALLBACK_COPY;
  return { code, ...copy, message };
}

export function describeError(error: unknown): UserFacingError {
  if (!(error instanceof ApiRequestError)) {
    return { code: "unknown", ...FALLBACK_COPY };
  }
  const copy = ERROR_COPY[error.code] ?? FALLBACK_COPY;
  const message = error.code === "invalid_image" && error.message.trim() ? error.message : copy.message;
  return { code: error.code, ...copy, message };
}
