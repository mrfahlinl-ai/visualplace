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

export interface ExifRead {
  has_gps: boolean;
  gps_valid: boolean | null;
  gps_latitude: number | null;
  gps_longitude: number | null;
  captured_at: string | null;
  camera_make: string | null;
  camera_model: string | null;
}

export interface ImageRead {
  mime_type: string;
  byte_size: number;
  width: number | null;
  height: number | null;
  exif: ExifRead | null;
}

export interface LocationRead {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  address: string | null;
  city: string | null;
  country: string | null;
  country_code: string | null;
  place_type: string | null;
  website: string | null;
}

export type EvidenceKind = "match" | "contradiction";

export interface EvidenceRead {
  category: string;
  kind: EvidenceKind;
  description: string;
  weight: number | null;
}

export type CandidateSource = "ai" | "map" | "search" | "exif";

export interface CandidateRead {
  id: string;
  name: string;
  latitude: number | null;
  longitude: number | null;
  city: string | null;
  country: string | null;
  country_code: string | null;
  place_type: string | null;
  source: CandidateSource;
  score: number;
  rank: number | null;
  radius_m: number | null;
  evidence: EvidenceRead[];
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
  final_location: LocationRead | null;
  candidates: CandidateRead[];
  explanation: string[];
  error: { code: string; message: string } | null;
}

export interface ApiError {
  error: { code: string; message: string; details?: unknown };
}
