import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload as UploadIcon, X, FileText, Loader2, AlertCircle, CheckCircle2, Globe } from 'lucide-react';
import { api } from '../lib/api';

export default function UploadPage() {
  const navigate = useNavigate();
  const [files, setFiles] = useState<File[]>([]);
  const [githubUrl, setGithubUrl] = useState('');
  const [linkedinUrl, setLinkedinUrl] = useState('');
  
  // Basic Projection Settings
  const [projection, setProjection] = useState({
    hide_metadata: false,
    include_provenance: true
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);

  const addFiles = useCallback((addedFiles: FileList | null) => {
    if (!addedFiles) return;
    setFiles((prev) => [...prev, ...Array.from(addedFiles)]);
    setError(null);
  }, []);

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async () => {
    if (files.length === 0 && !githubUrl && !linkedinUrl) { 
      setError('Add at least one file or URL'); 
      return; 
    }
    setLoading(true);
    setError(null);
    try {
      const result = await api.transform(files, githubUrl, linkedinUrl, projection);
      navigate(`/result`, { state: { result } });
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

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">GitHub URL</label>
          <div className="relative">
            <Globe className="absolute left-3 top-2.5 text-[var(--color-text-muted)]" size={16} />
            <input 
              type="url" 
              placeholder="https://github.com/username"
              className="input-field pl-9 w-full"
              value={githubUrl}
              onChange={(e) => setGithubUrl(e.target.value)}
            />
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">LinkedIn URL</label>
          <div className="relative">
            <Globe className="absolute left-3 top-2.5 text-[var(--color-text-muted)]" size={16} />
            <input 
              type="url" 
              placeholder="https://linkedin.com/in/username"
              className="input-field pl-9 w-full"
              value={linkedinUrl}
              onChange={(e) => setLinkedinUrl(e.target.value)}
            />
          </div>
        </div>
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
          Supports PDF and CSV files
        </p>
        <input
          id="file-input"
          type="file"
          multiple
          accept=".pdf,.csv,.txt"
          className="hidden"
          onChange={(e) => addFiles(e.target.files)}
        />
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider">
            Files ({files.length})
          </h2>
          {files.map((file, i) => (
            <div key={i} className="card flex items-center gap-4 py-3">
              <FileText size={20} className="text-[var(--color-accent-light)] shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{file.name}</p>
                <p className="text-xs text-[var(--color-text-muted)]">
                  {(file.size / 1024).toFixed(1)} KB
                </p>
              </div>
              <button onClick={() => removeFile(i)} className="text-[var(--color-text-muted)] hover:text-[var(--color-error)] transition-colors">
                <X size={18} />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Projection Config */}
      <div className="card space-y-4 bg-[var(--color-bg-secondary)] border-0">
        <h3 className="font-medium">Projection Configuration</h3>
        <div className="flex gap-6">
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input 
              type="checkbox" 
              className="rounded border-[var(--color-border)]"
              checked={!projection.hide_metadata}
              onChange={(e) => setProjection({...projection, hide_metadata: !e.target.checked})}
            />
            Include Metadata
          </label>
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input 
              type="checkbox" 
              className="rounded border-[var(--color-border)]"
              checked={projection.include_provenance}
              onChange={(e) => setProjection({...projection, include_provenance: e.target.checked})}
            />
            Include Provenance
          </label>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-[var(--color-error)]/10 text-[var(--color-error)] text-sm">
          <AlertCircle size={16} /> {error}
        </div>
      )}

      {/* Submit */}
      <button
        onClick={handleSubmit}
        disabled={loading || (files.length === 0 && !githubUrl && !linkedinUrl)}
        className="btn-primary flex items-center gap-2 w-full justify-center"
      >
        {loading ? <Loader2 size={16} className="animate-spin" /> : <CheckCircle2 size={16} />}
        {loading ? 'Transforming...' : 'Transform Sources'}
      </button>
    </div>
  );
}
