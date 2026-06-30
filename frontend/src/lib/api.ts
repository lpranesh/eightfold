/** API client for the backend. */

import type { HealthResponse, TransformResponse } from '../types';

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

  transform(files: File[], githubUrl?: string, linkedinUrl?: string, projection?: Record<string, any>): Promise<TransformResponse> {
    const form = new FormData();
    files.forEach((f) => form.append('files', f));
    if (githubUrl) form.append('github_url', githubUrl);
    if (linkedinUrl) form.append('linkedin_url', linkedinUrl);
    if (projection) form.append('projection_json', JSON.stringify(projection));
    
    return request('/transform', { method: 'POST', body: form });
  },
};
