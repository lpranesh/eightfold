import { Link } from 'react-router-dom';
import { Upload, ArrowRight, Activity } from 'lucide-react';

export default function Dashboard() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-[var(--color-text-secondary)] mt-1">
          Multi-source candidate data transformation overview
        </p>
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
        <Link to="/pipeline" className="card group cursor-pointer flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-lg bg-[var(--color-success)]/10 flex items-center justify-center">
              <Activity size={20} className="text-[var(--color-success)]" />
            </div>
            <div>
              <h3 className="font-semibold">View Pipeline</h3>
              <p className="text-sm text-[var(--color-text-muted)]">Explore transformation stages</p>
            </div>
          </div>
          <ArrowRight size={18} className="text-[var(--color-text-muted)] group-hover:text-[var(--color-success)] transition-colors" />
        </Link>
      </div>
    </div>
  );
}
