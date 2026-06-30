import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft, Mail, Phone, MapPin, Briefcase, Building,
  Globe, Info, ChevronDown,
} from 'lucide-react';
import { api } from '../lib/api';
import type { CandidateDetailResponse, FieldExplanation } from '../types';

function ConfidenceBar({ value }: { value: number }) {
  const color = value >= 0.8 ? 'var(--color-success)' : value >= 0.5 ? 'var(--color-warning)' : 'var(--color-error)';
  return (
    <div className="confidence-bar w-24">
      <div className="confidence-bar-fill" style={{ width: `${value * 100}%`, background: color }} />
    </div>
  );
}

function FieldRow({ label, value, fieldName, candidateId }: {
  label: string; value: unknown; fieldName?: string; candidateId: string;
}) {
  const [explanation, setExplanation] = useState<FieldExplanation | null>(null);
  const [open, setOpen] = useState(false);

  const loadExplanation = async () => {
    if (!fieldName || explanation) { setOpen(!open); return; }
    try {
      const exp = await api.explainField(candidateId, fieldName);
      setExplanation(exp);
      setOpen(true);
    } catch { setOpen(!open); }
  };

  const displayValue = value === null || value === undefined ? '—'
    : Array.isArray(value) ? value.join(', ') : String(value);

  return (
    <div className="border-b border-[var(--color-border)] last:border-0">
      <div className="flex items-center justify-between py-3 px-4 hover:bg-[var(--color-bg-hover)] transition-colors">
        <div className="flex items-center gap-3 min-w-0">
          <span className="text-sm text-[var(--color-text-muted)] w-40 shrink-0">{label}</span>
          <span className="text-sm font-medium truncate">{displayValue}</span>
        </div>
        {fieldName && (
          <button onClick={loadExplanation} className="text-[var(--color-text-muted)] hover:text-[var(--color-accent-light)] transition-colors shrink-0">
            {open ? <ChevronDown size={16} /> : <Info size={16} />}
          </button>
        )}
      </div>
      {open && explanation && (
        <div className="px-4 pb-3 ml-4 space-y-2 border-l-2 border-[var(--color-accent)]/30">
          <div className="flex items-center gap-3 text-sm">
            <span className="text-[var(--color-text-muted)]">Source:</span>
            <span className="badge badge-high text-xs">{explanation.selected_source}</span>
            <ConfidenceBar value={explanation.confidence} />
            <span className="text-xs text-[var(--color-text-muted)]">{(explanation.confidence * 100).toFixed(0)}%</span>
          </div>
          <p className="text-xs text-[var(--color-text-secondary)]">{explanation.reason}</p>
          {explanation.competing_values.length > 1 && (
            <div className="text-xs space-y-1">
              <span className="text-[var(--color-text-muted)]">Competing values:</span>
              {explanation.competing_values.map((cv, i) => (
                <div key={i} className={`flex gap-2 ${cv.is_selected ? 'text-[var(--color-success)]' : 'text-[var(--color-text-muted)]'}`}>
                  <span>[{cv.source}]</span>
                  <span>{String(cv.value)}</span>
                  {cv.is_selected && <span className="text-[var(--color-success)]">✓</span>}
                </div>
              ))}
            </div>
          )}
          {explanation.normalizations_applied.length > 0 && (
            <p className="text-xs text-[var(--color-text-muted)]">
              Normalizations: {explanation.normalizations_applied.join(', ')}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

export default function CandidateDetail() {
  const { id } = useParams<{ id: string }>();
  const [candidate, setCandidate] = useState<CandidateDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<'profile' | 'metadata' | 'provenance'>('profile');

  useEffect(() => {
    if (!id) return;
    api.getCandidate(id).then(setCandidate).finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="text-center py-20 text-[var(--color-text-muted)]">Loading...</div>;
  if (!candidate) return <div className="text-center py-20 text-[var(--color-error)]">Candidate not found</div>;

  const p = candidate.profile as Record<string, unknown>;
  const m = candidate.metadata as Record<string, unknown>;

  const PROFILE_FIELDS = [
    { label: 'Full Name', key: 'full_name', icon: null },
    { label: 'Email', key: 'email', icon: Mail },
    { label: 'Phone', key: 'phone', icon: Phone },
    { label: 'Location', key: 'location', icon: MapPin },
    { label: 'Current Title', key: 'current_title', icon: Briefcase },
    { label: 'Current Company', key: 'current_company', icon: Building },
    { label: 'Years of Exp', key: 'years_of_experience', icon: null },
    { label: 'Skills', key: 'skills', icon: null },
    { label: 'GitHub', key: 'github_url', icon: Globe },
    { label: 'LinkedIn', key: 'linkedin_url', icon: Globe },
    { label: 'Portfolio', key: 'portfolio_url', icon: Globe },
  ];

  const tabs = [
    { key: 'profile' as const, label: 'Profile' },
    { key: 'metadata' as const, label: 'Metadata' },
    { key: 'provenance' as const, label: 'Provenance' },
  ];

  return (
    <div className="space-y-6">
      <Link to="/candidates" className="inline-flex items-center gap-1.5 text-sm text-[var(--color-text-muted)] hover:text-[var(--color-accent-light)]">
        <ArrowLeft size={16} /> Back to candidates
      </Link>

      {/* Header */}
      <div className="card flex items-center gap-5">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[var(--color-accent)] to-[var(--color-accent-dark)] flex items-center justify-center text-2xl font-bold text-white">
          {(String(p.full_name || '?'))[0]}
        </div>
        <div className="flex-1">
          <h1 className="text-xl font-bold">{String(p.full_name || 'Unknown Candidate')}</h1>
          <p className="text-sm text-[var(--color-text-secondary)]">{String(p.current_title || '')} {p.current_company ? `at ${p.current_company}` : ''}</p>
          <div className="flex items-center gap-4 mt-2">
            <span className={`badge badge-${Number(m.overall_confidence || 0) >= 0.8 ? 'high' : Number(m.overall_confidence || 0) >= 0.5 ? 'medium' : 'low'}`}>
              {(Number(m.overall_confidence || 0) * 100).toFixed(0)}% confidence
            </span>
            <span className="text-xs text-[var(--color-text-muted)]">
              {(m.sources_processed as string[] || []).length} sources
            </span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-[var(--color-bg-secondary)] p-1 rounded-lg w-fit">
        {tabs.map((t) => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={`px-4 py-2 rounded-md text-sm transition-colors ${tab === t.key ? 'bg-[var(--color-bg-card)] text-[var(--color-text-primary)] font-medium' : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]'}`}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {tab === 'profile' && (
        <div className="card p-0 overflow-hidden">
          {PROFILE_FIELDS.map(({ label, key }) => (
            <FieldRow key={key} label={label} value={p[key]} fieldName={key} candidateId={id!} />
          ))}
        </div>
      )}

      {tab === 'metadata' && (
        <div className="card space-y-3">
          {Object.entries(m).map(([k, v]) => (
            <div key={k} className="flex justify-between py-2 border-b border-[var(--color-border)] last:border-0">
              <span className="text-sm text-[var(--color-text-muted)]">{k.replace(/_/g, ' ')}</span>
              <span className="text-sm font-mono">{Array.isArray(v) ? v.join(', ') : String(v)}</span>
            </div>
          ))}
        </div>
      )}

      {tab === 'provenance' && (
        <div className="space-y-3">
          {Object.entries(candidate.provenance).map(([field, prov]) => (
            <div key={field} className="card">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-sm">{field.replace(/_/g, ' ')}</span>
                <div className="flex items-center gap-2">
                  <ConfidenceBar value={prov.confidence} />
                  <span className="text-xs text-[var(--color-text-muted)]">{(prov.confidence * 100).toFixed(0)}%</span>
                </div>
              </div>
              <p className="text-xs text-[var(--color-text-secondary)] mb-2">{prov.reason}</p>
              <div className="flex flex-wrap gap-2">
                {prov.competing_values.map((cv, i) => (
                  <div key={i} className={`text-xs px-2 py-1 rounded ${cv.is_selected ? 'bg-[var(--color-success)]/10 text-[var(--color-success)]' : 'bg-[var(--color-bg-secondary)] text-[var(--color-text-muted)]'}`}>
                    [{cv.source}] {String(cv.value).substring(0, 50)}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
