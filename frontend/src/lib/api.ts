/** API client for the backend. */

import type {
  CandidateDetailResponse,
  CandidateListResponse,
  FieldExplanation,
  HealthResponse,
  MetadataResponse,
  ProjectionResponse,
  TransformResponse,
} from '../types';

const API_BASE = '/api';

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, init);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.error || `Request failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  health(): Promise<HealthResponse> {
    return request('/health');
  },

  transform(files: File[], sourceTypes: string[]): Promise<TransformResponse> {
    const form = new FormData();
    files.forEach((f) => form.append('files', f));
    sourceTypes.forEach((t) => form.append('source_types', t));
    return request('/transform', { method: 'POST', body: form });
  },

  listCandidates(limit = 50, offset = 0): Promise<CandidateListResponse> {
    return request(`/candidates?limit=${limit}&offset=${offset}`);
  },

  getCandidate(id: string): Promise<CandidateDetailResponse> {
    return request(`/candidate/${id}`);
  },

  getMetadata(id: string): Promise<MetadataResponse> {
    return request(`/candidate/${id}/metadata`);
  },

  explainField(id: string, fieldName: string): Promise<FieldExplanation> {
    return request(`/candidate/${id}/explain/${fieldName}`);
  },

  project(
    id: string,
    config: {
      include_fields?: string[];
      exclude_fields?: string[];
      rename_fields?: Record<string, string>;
      hide_metadata?: boolean;
    }
  ): Promise<ProjectionResponse> {
    return request(`/candidate/${id}/projection`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
  },
};
