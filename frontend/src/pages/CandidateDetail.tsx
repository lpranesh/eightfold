import { useState } from 'react';
import { Link, useLocation, Navigate } from 'react-router-dom';
import {
  ArrowLeft, Mail, Phone, MapPin, Briefcase, Building,
  Globe, Info, ChevronDown,
} from 'lucide-react';
import type { TransformResponse } from '../types';

function ConfidenceBar({ value }: { value: number }) {
  const color = value >= 0.8 ? 'var(--color-success)' : value >= 0.5 ? 'var(--color-warning)' : 'var(--color-error)';
  return (
    <div className="confidence-bar w-24">
      <div className="confidence-bar-fill" style={{ width: `${value * 100}%`, background: color }} />
    </div>
  );
}

function FieldRow({ label, value, explanation }: {
  label: string; value: unknown; explanation?: any;
}) {
  const [open, setOpen] = useState(false);

  const displayValue = value === null || value === undefined ? '—'
    : Array.isArray(value) ? value.join(', ') : String(value);

  return (
    <div className="border-b border-[var(--color-border)] last:border-0">
      <div className="flex items-center justify-between py-3 px-4 hover:bg-[var(--color-bg-hover)] transition-colors">
        <div className="flex items-center gap-3 min-w-0">
          <span className="text-sm text-[var(--color-text-muted)] w-40 shrink-0">{label}</span>
          <span className="text-sm font-medium truncate">{displayValue}</span>
        </div>
        {explanation && (
          <button onClick={() => setOpen(!open)} className="text-[var(--color-text-muted)] hover:text-[var(--color-accent-light)] transition-colors shrink-0">
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
          {explanation.competing_values?.length > 1 && (
            <div className="text-xs space-y-1">
              <span className="text-[var(--color-text-muted)]">Competing values:</span>
              {explanation.competing_values.map((cv: any, i: number) => (
                <div key={i} className={`flex gap-2 text-[var(--color-text-muted)]`}>
                  <span>[{cv.source}]</span>
                  <span>{String(cv.value)}</span>
                </div>
              ))}
            </div>
          )}
          {explanation.normalizations_applied?.length > 0 && (
            <p className="text-xs text-[var(--color-text-muted)]">
              Normalizations: {explanation.normalizations_applied.join(', ')}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

export default function Result() {
  const location = useLocation();
  const [tab, setTab] = useState<'profile' | 'metadata'>('profile');

  const result = location.state?.result as TransformResponse;

  if (!result) {
    return <Navigate to="/upload" replace />;
  }

  const p = result.profile as Record<string, unknown>;
  const m = result.metadata as Record<string, unknown>;
  const prov = result.provenance as Record<string, any>;

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
  ];

  return (
    <div className="space-y-6">
      <Link to="/upload" className="inline-flex items-center gap-1.5 text-sm text-[var(--color-text-muted)] hover:text-[var(--color-accent-light)]">
        <ArrowLeft size={16} /> Transform another
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
            <span className={`badge badge-${Number(m?.overall_confidence || 0) >= 0.8 ? 'high' : Number(m?.overall_confidence || 0) >= 0.5 ? 'medium' : 'low'}`}>
              {(Number(m?.overall_confidence || 0) * 100).toFixed(0)}% confidence
            </span>
            <span className="text-xs text-[var(--color-text-muted)]">
              {(m?.sources_processed as string[] || []).length} sources
            </span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-[var(--color-bg-secondary)] p-1 rounded-lg w-fit">
        {tabs.map((t) => (
          <button key={t.key} onClick={() => setTab(t.key as any)}
            className={`px-4 py-2 rounded-md text-sm transition-colors ${tab === t.key ? 'bg-[var(--color-bg-card)] text-[var(--color-text-primary)] font-medium' : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]'}`}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {tab === 'profile' && (
        <div className="card p-0 overflow-hidden">
          {PROFILE_FIELDS.map(({ label, key }) => (
            <FieldRow key={key} label={label} value={p[key]} explanation={prov?.[key]} />
          ))}
        </div>
      )}

      {tab === 'metadata' && m && (
        <div className="card space-y-3">
          {Object.entries(m).map(([k, v]) => (
            <div key={k} className="flex justify-between py-2 border-b border-[var(--color-border)] last:border-0">
              <span className="text-sm text-[var(--color-text-muted)]">{k.replace(/_/g, ' ')}</span>
              <span className="text-sm font-mono">{Array.isArray(v) ? v.join(', ') : String(v)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
