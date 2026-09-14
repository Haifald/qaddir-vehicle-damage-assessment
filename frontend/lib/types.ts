export type VerificationStatus = "verified" | "manual_review" | "rejected";

export interface Detection {
  id: string;
  class: string;
  confidence: number;
}

export interface Association {
  damage_id: string;
  part_id: string | null;
  confidence: number;
  alternatives: Array<{ part_id: string; confidence: number }>;
}

export interface CVRecord {
  image: { id: string; usable: boolean; quality_note: string | null };
  damage_detections: Detection[];
  part_detections: Detection[];
  associations: Association[];
}

export interface AssessmentResponse {
  analysis_id: string;
  cv_output: CVRecord;
  visual_detections: Array<{
    id: string;
    kind: "damage" | "part";
    class_name: string;
    confidence: number;
    bbox: [number, number, number, number];
  }>;
  overlay_data_url: string | null;
  verification: {
    status: VerificationStatus;
    llm_eligible: boolean;
    issues: Array<{ code: string; message: string; path: string | null; level: "review" | "error" }>;
  };
  severity: null;
  report: {
    status: "generated" | "unavailable" | "blocked" | "failed";
    text: string | null;
    message: string | null;
  };
  recommendation: string;
  disclaimer: string;
}

export interface HealthResponse {
  status: "ready" | "configuration_required";
  components: Record<string, { ready: boolean; detail: string }>;
}

export interface ApiError {
  code: string;
  message: string;
}
