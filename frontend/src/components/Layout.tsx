import { NavLink, Outlet } from 'react-router-dom';
import {
  LayoutDashboard,
  Upload,
  Users,
  Activity,
  Layers,
  Settings,
} from 'lucide-react';

const NAV_ITEMS = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/upload', icon: Upload, label: 'Upload Sources' },
  { to: '/candidates', icon: Users, label: 'Candidates' },
  { to: '/pipeline', icon: Layers, label: 'Pipeline' },
  { to: '/projection', icon: Settings, label: 'Projection' },
  { to: '/health', icon: Activity, label: 'Health' },
];

export default function Layout() {
  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="w-64 border-r border-[var(--color-border)] bg-[var(--color-bg-secondary)] flex flex-col">
        <div className="p-5 border-b border-[var(--color-border)]">
          <h1 className="text-lg font-bold tracking-tight">
            <span className="bg-gradient-to-r from-[var(--color-accent-light)] to-[var(--color-accent)] bg-clip-text text-transparent">
              Eightfold
            </span>
            <span className="text-[var(--color-text-muted)] font-normal ml-1.5 text-sm">
              CDT
            </span>
          </h1>
          <p className="text-xs text-[var(--color-text-muted)] mt-1">
            Candidate Data Transformer
          </p>
        </div>
        <nav className="flex-1 py-4 px-3 space-y-1">
          {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                  isActive
                    ? 'bg-[var(--color-accent)]/10 text-[var(--color-accent-light)] font-medium'
                    : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-bg-hover)]'
                }`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="p-4 border-t border-[var(--color-border)] text-xs text-[var(--color-text-muted)]">
          v1.0.0 · Multi-Source Transformer
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <div className="max-w-7xl mx-auto p-6 lg:p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
