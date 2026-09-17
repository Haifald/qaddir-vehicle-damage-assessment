export type VerificationStatus = "verified" | "manual_review" | "rejected";

export interface Detection {
  id: string;
  class: string;
  confidence: number;
}

export interface AssociationAlternative {
  part_id: string;
  confidence: number;
}

export interface Association {
  damage_id: string;
  part_id: string | null;
  confidence: number;
  alternatives: AssociationAlternative[];
}

export interface CVRecord {
  image: { id: string; usable: boolean; quality_note: string | null };
  damage_detections: Detection[];
  part_detections: Detection[];
  associations: Association[];
}

export interface VisualDetection {
  id: string;
  kind: "damage" | "part";
  class_name: string;
  confidence: number;
  bbox: [number, number, number, number];
}

export interface VerificationIssue {
  code: string;
  message: string;
  path: string | null;
  level: "review" | "error";
}

export interface VerificationResult {
  status: VerificationStatus;
  llm_eligible: boolean;
  issues: VerificationIssue[];
}

export type ReportStatus = "generated" | "unavailable" | "blocked" | "failed";

export interface ReportResult {
  status: ReportStatus;
  text: string | null;
  message: string | null;
}

export interface AssessmentResponse {
  analysis_id: string;
  cv_output: CVRecord;
  visual_detections: VisualDetection[];
  overlay_data_url: string | null;
  verification: VerificationResult;
  severity: null;
  report: ReportResult;
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
