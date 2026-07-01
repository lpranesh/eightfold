export interface TransformResponse {
  profile: Record<string, unknown>;
  metadata: Record<string, unknown> | null;
  provenance: Record<string, FieldProvenance> | null;
  warnings: string[];
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
}

export interface CompetingValue {
  source: string;
  value: unknown;
  confidence: number;
}
