import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload as UploadIcon, X, FileText, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';
import { api } from '../lib/api';
import { SOURCE_TYPE_LABELS, type SourceType } from '../types';

interface FileEntry {
  file: File;
  sourceType: SourceType;
}

const SOURCE_TYPES = Object.entries(SOURCE_TYPE_LABELS) as [SourceType, string][];

export default function UploadPage() {
  const navigate = useNavigate();
  const [entries, setEntries] = useState<FileEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);

  const addFiles = useCallback((files: FileList | null) => {
    if (!files) return;
    const newEntries: FileEntry[] = [];
    for (const file of Array.from(files)) {
      const ext = file.name.split('.').pop()?.toLowerCase() || '';
      let type: SourceType = 'ats_json';
      if (ext === 'pdf') type = 'resume';
      else if (ext === 'csv') type = 'recruiter_csv';
      else if (ext === 'txt') type = 'recruiter_notes';
      else if (ext === 'json') {
        const lower = file.name.toLowerCase();
        if (lower.includes('github')) type = 'github';
        else if (lower.includes('linkedin')) type = 'linkedin';
      }
      newEntries.push({ file, sourceType: type });
    }
    setEntries((prev) => [...prev, ...newEntries]);
    setError(null);
  }, []);

  const removeEntry = (index: number) => {
    setEntries((prev) => prev.filter((_, i) => i !== index));
  };

  const updateType = (index: number, type: SourceType) => {
    setEntries((prev) => prev.map((e, i) => (i === index ? { ...e, sourceType: type } : e)));
  };

  const handleSubmit = async () => {
    if (entries.length === 0) { setError('Add at least one file'); return; }
    setLoading(true);
    setError(null);
    try {
      const result = await api.transform(
        entries.map((e) => e.file),
        entries.map((e) => e.sourceType),
      );
      navigate(`/candidate/${result.candidate_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Transform failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold">Upload Sources</h1>
        <p className="text-[var(--color-text-secondary)] mt-1">
          Upload candidate data from multiple sources to create a unified profile
        </p>
      </div>

      {/* Dropzone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => { e.preventDefault(); setDragOver(false); addFiles(e.dataTransfer.files); }}
        className={`card border-2 border-dashed text-center py-12 cursor-pointer transition-colors ${
          dragOver ? 'border-[var(--color-accent)] bg-[var(--color-accent)]/5' : 'border-[var(--color-border)]'
        }`}
        onClick={() => document.getElementById('file-input')?.click()}
      >
        <UploadIcon size={40} className="mx-auto text-[var(--color-text-muted)] mb-3" />
        <p className="font-medium">Drop files here or click to browse</p>
        <p className="text-sm text-[var(--color-text-muted)] mt-1">
          Supports PDF, CSV, JSON, and TXT files
        </p>
        <input
          id="file-input"
          type="file"
          multiple
          accept=".pdf,.csv,.json,.txt"
          className="hidden"
          onChange={(e) => addFiles(e.target.files)}
        />
      </div>

      {/* File List */}
      {entries.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider">
            Sources ({entries.length})
          </h2>
          {entries.map((entry, i) => (
            <div key={i} className="card flex items-center gap-4 py-3">
              <FileText size={20} className="text-[var(--color-accent-light)] shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{entry.file.name}</p>
                <p className="text-xs text-[var(--color-text-muted)]">
                  {(entry.file.size / 1024).toFixed(1)} KB
                </p>
              </div>
              <select
                value={entry.sourceType}
                onChange={(e) => updateType(i, e.target.value as SourceType)}
                className="input-field w-48 text-sm"
              >
                {SOURCE_TYPES.map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
              <button onClick={() => removeEntry(i)} className="text-[var(--color-text-muted)] hover:text-[var(--color-error)] transition-colors">
                <X size={18} />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-[var(--color-error)]/10 text-[var(--color-error)] text-sm">
          <AlertCircle size={16} /> {error}
        </div>
      )}

      {/* Submit */}
      <button
        onClick={handleSubmit}
        disabled={loading || entries.length === 0}
        className="btn-primary flex items-center gap-2"
      >
        {loading ? <Loader2 size={16} className="animate-spin" /> : <CheckCircle2 size={16} />}
        {loading ? 'Transforming...' : 'Transform Sources'}
      </button>
    </div>
  );
}
