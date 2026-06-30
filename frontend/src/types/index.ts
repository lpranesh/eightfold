/** API types mirroring backend DTOs. */

export interface TransformResponse {
  candidate_id: string;
  profile: Record<string, unknown>;
  metadata: Record<string, unknown>;
  sources_processed: string[];
  overall_confidence: number;
  overall_confidence_level: string;
  warnings: string[];
  created_at: string;
}

export interface CandidateListItem {
  id: string;
  full_name: string | null;
  email: string | null;
  current_title: string | null;
  sources_count: number;
  overall_confidence: number;
  created_at: string;
}

export interface CandidateListResponse {
  candidates: CandidateListItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface CandidateDetailResponse {
  id: string;
  profile: Record<string, unknown>;
  metadata: Record<string, unknown>;
  provenance: Record<string, FieldProvenance>;
  created_at: string;
  updated_at: string;
}

export interface FieldProvenance {
  field_name: string;
  selected_source: string;
  selected_value: unknown;
  competing_values: CompetingValue[];
  reason: string;
  confidence: number;
  confidence_level: string;
  normalizations_applied: string[];
  agreeing_sources: number;
  total_sources: number;
}

export interface CompetingValue {
  source: string;
  value: unknown;
  is_selected: boolean;
  extraction_method?: string;
  extraction_confidence?: number;
}

export interface HealthResponse {
  status: string;
  version: string;
  database: string;
  timestamp: string;
}

export type SourceType =
  | 'resume'
  | 'recruiter_csv'
  | 'recruiter_notes';

export const SOURCE_TYPE_LABELS: Record<SourceType, string> = {
  resume: 'Resume (PDF)',
  recruiter_csv: 'Recruiter CSV',
  recruiter_notes: 'Recruiter Notes',
};
