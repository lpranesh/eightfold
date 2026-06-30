import { ArrowRight, FileInput, Search, Layers, Zap, Shield, Database, Eye } from 'lucide-react';

const STAGES = [
  { name: 'Input', desc: 'Upload source files (PDF, CSV, JSON, TXT)', icon: FileInput, color: '#6366f1' },
  { name: 'Parser', desc: 'Parse each file format into structured content', icon: Search, color: '#8b5cf6' },
  { name: 'Extractor', desc: 'Extract field values using regex & rules', icon: Layers, color: '#a78bfa' },
  { name: 'Normalizer', desc: 'Standardize formats (phone, email, names)', icon: Zap, color: '#f59e0b' },
  { name: 'Fusion', desc: 'Resolve conflicts between competing sources', icon: Shield, color: '#10b981' },
  { name: 'Confidence', desc: 'Score each field deterministically', icon: Shield, color: '#06b6d4' },
  { name: 'Provenance', desc: 'Record why each value was selected', icon: Database, color: '#3b82f6' },
  { name: 'Validator', desc: 'Validate the final canonical profile', icon: Shield, color: '#22c55e' },
  { name: 'Projection', desc: 'Create customized output views', icon: Eye, color: '#ec4899' },
];

export default function PipelinePage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Transformation Pipeline</h1>
        <p className="text-[var(--color-text-secondary)] mt-1">
          Visual representation of the candidate data transformation flow
        </p>
      </div>

      <div className="space-y-4">
        {STAGES.map((stage, i) => {
          const Icon = stage.icon;
          return (
            <div key={stage.name}>
              <div className="card flex items-center gap-5">
                <div className="w-12 h-12 rounded-xl flex items-center justify-center shrink-0"
                  style={{ background: `${stage.color}18` }}>
                  <Icon size={22} style={{ color: stage.color }} />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono text-[var(--color-text-muted)]">Stage {i + 1}</span>
                    <h3 className="font-semibold">{stage.name}</h3>
                  </div>
                  <p className="text-sm text-[var(--color-text-secondary)]">{stage.desc}</p>
                </div>
                <div className="w-2 h-2 rounded-full" style={{ background: stage.color }} />
              </div>
              {i < STAGES.length - 1 && (
                <div className="flex justify-center py-1">
                  <ArrowRight size={16} className="text-[var(--color-text-muted)] rotate-90" />
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="card">
        <h3 className="font-semibold mb-3">Design Patterns Used</h3>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="flex gap-2"><span className="text-[var(--color-accent-light)]">●</span> Strategy — Parsers, Extractors, Fusion policies</div>
          <div className="flex gap-2"><span className="text-[var(--color-success)]">●</span> Factory — Parser selection based on file type</div>
          <div className="flex gap-2"><span className="text-[var(--color-warning)]">●</span> Adapter — Heterogeneous inputs → common model</div>
          <div className="flex gap-2"><span className="text-[var(--color-info)]">●</span> Pipeline — Linear transformation flow</div>
        </div>
      </div>
    </div>
  );
}
