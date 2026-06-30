import { useState, useEffect } from 'react';
import { api } from '../lib/api';
import type { CandidateListItem, ProjectionResponse } from '../types';

export default function ProjectionPlayground() {
  const [candidates, setCandidates] = useState<CandidateListItem[]>([]);
  const [selectedId, setSelectedId] = useState('');
  const [includeFields, setIncludeFields] = useState('');
  const [excludeFields, setExcludeFields] = useState('');
  const [renameFields, setRenameFields] = useState('');
  const [hideMetadata, setHideMetadata] = useState(false);
  const [result, setResult] = useState<ProjectionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.listCandidates(50).then((r) => setCandidates(r.candidates)).catch(() => {});
  }, []);

  const applyProjection = async () => {
    if (!selectedId) { setError('Select a candidate'); return; }
    setLoading(true); setError(null);
    try {
      const config: Record<string, unknown> = { hide_metadata: hideMetadata };
      if (includeFields.trim()) config.include_fields = includeFields.split(',').map((s) => s.trim());
      if (excludeFields.trim()) config.exclude_fields = excludeFields.split(',').map((s) => s.trim());
      if (renameFields.trim()) {
        const renames: Record<string, string> = {};
        renameFields.split(',').forEach((pair) => {
          const [from, to] = pair.split(':').map((s) => s.trim());
          if (from && to) renames[from] = to;
        });
        config.rename_fields = renames;
      }
      const res = await api.project(selectedId, config);
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Projection failed');
    } finally {
      setLoading(false);
    }
  };

  const FIELDS = [
    'full_name', 'email', 'phone', 'location', 'current_title',
    'current_company', 'skills', 'experience', 'education',
    'years_of_experience', 'github_url', 'linkedin_url', 'summary',
  ];

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold">Projection Playground</h1>
        <p className="text-[var(--color-text-secondary)] mt-1">
          Create customized views of candidate profiles without modifying the canonical data
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Config */}
        <div className="space-y-4">
          <div className="card space-y-4">
            <h2 className="font-semibold">Configuration</h2>

            <div>
              <label className="text-sm text-[var(--color-text-muted)] block mb-1">Candidate</label>
              <select value={selectedId} onChange={(e) => setSelectedId(e.target.value)} className="input-field">
                <option value="">Select a candidate...</option>
                {candidates.map((c) => (
                  <option key={c.id} value={c.id}>{c.full_name || c.email || c.id}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-sm text-[var(--color-text-muted)] block mb-1">Include Fields (comma-separated)</label>
              <input value={includeFields} onChange={(e) => setIncludeFields(e.target.value)}
                placeholder="full_name, email, skills" className="input-field" />
            </div>

            <div>
              <label className="text-sm text-[var(--color-text-muted)] block mb-1">Exclude Fields (comma-separated)</label>
              <input value={excludeFields} onChange={(e) => setExcludeFields(e.target.value)}
                placeholder="phone, summary" className="input-field" />
            </div>

            <div>
              <label className="text-sm text-[var(--color-text-muted)] block mb-1">Rename Fields (from:to, comma-separated)</label>
              <input value={renameFields} onChange={(e) => setRenameFields(e.target.value)}
                placeholder="full_name:name, current_title:role" className="input-field" />
            </div>

            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={hideMetadata} onChange={(e) => setHideMetadata(e.target.checked)} />
              Hide metadata
            </label>

            <button onClick={applyProjection} disabled={loading || !selectedId} className="btn-primary w-full">
              {loading ? 'Applying...' : 'Apply Projection'}
            </button>
          </div>

          <div className="card">
            <h3 className="text-sm font-semibold text-[var(--color-text-muted)] mb-2">Available Fields</h3>
            <div className="flex flex-wrap gap-1.5">
              {FIELDS.map((f) => (
                <span key={f} className="text-xs px-2 py-1 rounded bg-[var(--color-bg-secondary)] text-[var(--color-text-secondary)] font-mono">
                  {f}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Result */}
        <div>
          {error && (
            <div className="p-3 rounded-lg bg-[var(--color-error)]/10 text-[var(--color-error)] text-sm mb-4">{error}</div>
          )}
          {result && (
            <div className="card">
              <h2 className="font-semibold mb-3">Projected Profile</h2>
              <pre className="text-sm font-mono text-[var(--color-text-secondary)] overflow-auto max-h-[500px] p-4 bg-[var(--color-bg-secondary)] rounded-lg">
                {JSON.stringify(result.projected_profile, null, 2)}
              </pre>
            </div>
          )}
          {!result && !error && (
            <div className="card text-center py-12 text-[var(--color-text-muted)]">
              Configure and apply a projection to see results
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
