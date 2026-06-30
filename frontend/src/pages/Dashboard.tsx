import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Upload, Shield, ArrowRight } from 'lucide-react';
import { api } from '../lib/api';
import type { HealthResponse } from '../types';

export default function Dashboard() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.health()
      .then(setHealth)
      .finally(() => setLoading(false));
  }, []);

  const stats = [
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
      </div>
    </div>
  );
}
