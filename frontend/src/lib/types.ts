/** Shared API types (mirror of the backend Pydantic schemas). */

export type AnalysisMode = "identify" | "find_exact";

export type AnalysisStatus =
  | "pending"
  | "processing"
  | "completed"
  | "failed"
  | "deleted";

export type ConfidenceBand =
  | "exact_gps"
  | "strong"
  | "probable"
  | "approximate"
  | "weak"
  | "unknown";

export interface ImageRead {
  mime_type: string;
  byte_size: number;
  width: number | null;
  height: number | null;
}

export interface AnalysisRead {
  id: string;
  mode: AnalysisMode;
  status: AnalysisStatus;
  hint: string | null;
  confidence: number | null;
  confidence_band: ConfidenceBand | null;
  created_at: string;
  image: ImageRead | null;
  error: { code: string; message: string } | null;
}

export interface ApiError {
  error: { code: string; message: string; details?: unknown };
}
