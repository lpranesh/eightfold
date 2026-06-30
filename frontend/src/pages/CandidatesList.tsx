import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Search, ChevronRight } from 'lucide-react';
import { api } from '../lib/api';
import type { CandidateListItem } from '../types';

export default function CandidatesList() {
  const [candidates, setCandidates] = useState<CandidateListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    api.listCandidates(100).then((r) => { setCandidates(r.candidates); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  const filtered = candidates.filter((c) => {
    const q = search.toLowerCase();
    return !q || (c.full_name?.toLowerCase().includes(q)) || (c.email?.toLowerCase().includes(q)) || (c.current_title?.toLowerCase().includes(q));
  });

  const confBadge = (conf: number) => {
    const level = conf >= 0.8 ? 'high' : conf >= 0.5 ? 'medium' : 'low';
    return <span className={`badge badge-${level}`}>{(conf * 100).toFixed(0)}%</span>;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Candidates</h1>
          <p className="text-[var(--color-text-secondary)] mt-1">{candidates.length} profiles</p>
        </div>
        <Link to="/upload" className="btn-primary">+ New Transform</Link>
      </div>

      {/* Search */}
      <div className="relative">
        <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)]" />
        <input
          type="text"
          placeholder="Search by name, email, or title..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="input-field pl-10"
        />
      </div>

      {/* Table */}
      {loading ? (
        <div className="text-center py-12 text-[var(--color-text-muted)]">Loading...</div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-12 text-[var(--color-text-muted)]">
          {candidates.length === 0 ? 'No candidates yet. Upload sources to get started.' : 'No candidates match your search.'}
        </div>
      ) : (
        <div className="card p-0 overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-[var(--color-border)] text-left text-xs text-[var(--color-text-muted)] uppercase tracking-wider">
                <th className="px-5 py-3">Name</th>
                <th className="px-5 py-3">Email</th>
                <th className="px-5 py-3">Title</th>
                <th className="px-5 py-3">Sources</th>
                <th className="px-5 py-3">Confidence</th>
                <th className="px-5 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((c) => (
                <tr key={c.id} className="border-b border-[var(--color-border)] last:border-0 hover:bg-[var(--color-bg-hover)] transition-colors">
                  <td className="px-5 py-3.5">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-[var(--color-accent)]/15 flex items-center justify-center text-xs font-semibold text-[var(--color-accent-light)]">
                        {(c.full_name || '?')[0]}
                      </div>
                      <span className="font-medium">{c.full_name || '—'}</span>
                    </div>
                  </td>
                  <td className="px-5 py-3.5 text-sm text-[var(--color-text-secondary)]">{c.email || '—'}</td>
                  <td className="px-5 py-3.5 text-sm text-[var(--color-text-secondary)]">{c.current_title || '—'}</td>
                  <td className="px-5 py-3.5 text-sm">{c.sources_count}</td>
                  <td className="px-5 py-3.5">{confBadge(c.overall_confidence)}</td>
                  <td className="px-5 py-3.5">
                    <Link to={`/candidate/${c.id}`} className="text-[var(--color-accent-light)] hover:text-[var(--color-accent)]">
                      <ChevronRight size={18} />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
