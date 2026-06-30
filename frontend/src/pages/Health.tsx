import { useEffect, useState } from 'react';
import { CheckCircle2, XCircle, RefreshCw } from 'lucide-react';
import { api } from '../lib/api';
import type { HealthResponse } from '../types';

export default function HealthPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const check = () => {
    setLoading(true);
    setError(null);
    api.health()
      .then(setHealth)
      .catch((err) => setError(err instanceof Error ? err.message : 'Health check failed'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { check(); }, []);

  const isHealthy = health?.status === 'ok';
  const dbHealthy = health?.database === 'healthy';

  return (
    <div className="space-y-6 max-w-2xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">System Health</h1>
          <p className="text-[var(--color-text-secondary)] mt-1">Monitor system status and connectivity</p>
        </div>
        <button onClick={check} className="btn-ghost flex items-center gap-2">
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh
        </button>
      </div>

      {error ? (
        <div className="card border-[var(--color-error)]/30">
          <div className="flex items-center gap-3 text-[var(--color-error)]">
            <XCircle size={24} />
            <div>
              <h3 className="font-semibold">System Unreachable</h3>
              <p className="text-sm mt-1">{error}</p>
            </div>
          </div>
        </div>
      ) : health && (
        <div className="space-y-4">
          <div className={`card border-${isHealthy ? '[var(--color-success)]' : '[var(--color-error)]'}/30`}>
            <div className="flex items-center gap-3">
              {isHealthy ? <CheckCircle2 size={24} className="text-[var(--color-success)]" /> : <XCircle size={24} className="text-[var(--color-error)]" />}
              <div>
                <h3 className="font-semibold">{isHealthy ? 'All Systems Operational' : 'Issues Detected'}</h3>
                <p className="text-sm text-[var(--color-text-muted)] mt-0.5">
                  Last checked: {new Date(health.timestamp).toLocaleString()}
                </p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              { label: 'API Server', status: isHealthy, detail: `v${health.version}` },
              { label: 'Database', status: dbHealthy, detail: health.database },
              { label: 'Status', status: isHealthy, detail: health.status },
            ].map(({ label, status, detail }) => (
              <div key={label} className="card">
                <div className="flex items-center gap-2 mb-2">
                  <div className={`w-2 h-2 rounded-full ${status ? 'bg-[var(--color-success)]' : 'bg-[var(--color-error)]'}`} />
                  <span className="text-sm font-medium">{label}</span>
                </div>
                <p className="text-xs text-[var(--color-text-muted)] font-mono">{detail}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
