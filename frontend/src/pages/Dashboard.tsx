import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Users, Upload, TrendingUp, Shield, ArrowRight } from 'lucide-react';
import { api } from '../lib/api';
import type { CandidateListItem, HealthResponse } from '../types';

export default function Dashboard() {
  const [candidates, setCandidates] = useState<CandidateListItem[]>([]);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.allSettled([
      api.listCandidates(5),
      api.health(),
    ]).then(([candResult, healthResult]) => {
      if (candResult.status === 'fulfilled') setCandidates(candResult.value.candidates);
      if (healthResult.status === 'fulfilled') setHealth(healthResult.value);
      setLoading(false);
    });
  }, []);

  const avgConfidence = candidates.length
    ? candidates.reduce((s, c) => s + c.overall_confidence, 0) / candidates.length
    : 0;

  const stats = [
    { label: 'Total Candidates', value: candidates.length, icon: Users, color: 'var(--color-accent)' },
    { label: 'Avg Confidence', value: `${(avgConfidence * 100).toFixed(0)}%`, icon: TrendingUp, color: 'var(--color-success)' },
    { label: 'System Status', value: health?.status === 'ok' ? 'Healthy' : 'Unknown', icon: Shield, color: health?.status === 'ok' ? 'var(--color-success)' : 'var(--color-warning)' },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-[var(--color-text-secondary)] mt-1">
          Multi-source candidate data transformation overview
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {stats.map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="card flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ background: `${color}15` }}>
              <Icon size={22} style={{ color }} />
            </div>
            <div>
              <p className="text-2xl font-bold">{loading ? '—' : value}</p>
              <p className="text-sm text-[var(--color-text-muted)]">{label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <Link to="/upload" className="card group cursor-pointer flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-lg bg-[var(--color-accent)]/10 flex items-center justify-center">
              <Upload size={20} className="text-[var(--color-accent-light)]" />
            </div>
            <div>
              <h3 className="font-semibold">Upload Sources</h3>
              <p className="text-sm text-[var(--color-text-muted)]">Transform candidate data from multiple sources</p>
            </div>
          </div>
          <ArrowRight size={18} className="text-[var(--color-text-muted)] group-hover:text-[var(--color-accent-light)] transition-colors" />
        </Link>
        <Link to="/candidates" className="card group cursor-pointer flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-lg bg-[var(--color-success)]/10 flex items-center justify-center">
              <Users size={20} className="text-[var(--color-success)]" />
            </div>
            <div>
              <h3 className="font-semibold">View Candidates</h3>
              <p className="text-sm text-[var(--color-text-muted)]">Browse transformed candidate profiles</p>
            </div>
          </div>
          <ArrowRight size={18} className="text-[var(--color-text-muted)] group-hover:text-[var(--color-success)] transition-colors" />
        </Link>
      </div>

      {/* Recent Candidates */}
      {candidates.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold mb-4">Recent Candidates</h2>
          <div className="space-y-2">
            {candidates.map((c) => (
              <Link key={c.id} to={`/candidate/${c.id}`}
                className="card flex items-center justify-between py-3 px-4 hover:bg-[var(--color-bg-hover)]">
                <div className="flex items-center gap-4">
                  <div className="w-9 h-9 rounded-full bg-[var(--color-accent)]/15 flex items-center justify-center text-sm font-semibold text-[var(--color-accent-light)]">
                    {(c.full_name || '?')[0]}
                  </div>
                  <div>
                    <p className="font-medium">{c.full_name || 'Unknown'}</p>
                    <p className="text-xs text-[var(--color-text-muted)]">{c.email || 'No email'}</p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <span className={`badge badge-${c.overall_confidence >= 0.8 ? 'high' : c.overall_confidence >= 0.5 ? 'medium' : 'low'}`}>
                    {(c.overall_confidence * 100).toFixed(0)}%
                  </span>
                  <span className="text-xs text-[var(--color-text-muted)]">{c.sources_count} sources</span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
