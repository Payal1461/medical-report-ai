import { useCallback, useRef, useState } from 'react';
import { UploadCloud, FileText, X, CheckCircle } from 'lucide-react';
import { api } from '@/lib/api';
import { useToast } from '@/context/ToastContext';
import type { UploadResponse } from '@/types';

interface UploadProps {
  onUploaded: (reportId: number) => void;
}

export function UploadPage({ onUploaded }: UploadProps) {
  const { showError, showSuccess } = useToast();
  const [dragging, setDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<UploadResponse | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const accept = useCallback((f: File | undefined) => {
    if (!f) return;
    if (f.type !== 'application/pdf' && !f.name.toLowerCase().endsWith('.pdf')) {
      showError('Please select a PDF file.');
      return;
    }
    setFile(f);
    setResult(null);
  }, [showError]);

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      accept(e.dataTransfer.files?.[0]);
    },
    [accept],
  );

  const onUpload = useCallback(async () => {
    if (!file) return;
    setBusy(true);
    try {
      const res = await api.upload(file);
      setResult(res);
      showSuccess(res.message || 'Report uploaded successfully.');
    } catch (e) {
      showError(e instanceof Error ? e.message : 'Upload failed');
    } finally {
      setBusy(false);
    }
  }, [file, showError, showSuccess]);

  return (
    <div className="max-w-2xl mx-auto px-6 py-10">
      <h2 className="text-2xl font-semibold mb-1.5" style={{ color: 'var(--ink)' }}>
        Upload a report
      </h2>
      <p className="text-sm mb-7" style={{ color: 'var(--muted)' }}>
        Upload a PDF of your medical report. We'll extract and analyze the biomarkers for you.
      </p>

      {/* Drop zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        className="card p-10 flex flex-col items-center justify-center text-center cursor-pointer transition-all"
        style={{
          borderStyle: dragging ? 'dashed' : 'solid',
          borderColor: dragging ? 'var(--teal)' : 'var(--line)',
          background: dragging ? 'var(--teal-soft)' : 'var(--surface)',
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf,.pdf"
          className="hidden"
          onChange={(e) => accept(e.target.files?.[0])}
        />
        <div
          className="w-14 h-14 rounded-2xl flex items-center justify-center mb-4"
          style={{ background: 'var(--teal-soft)' }}
        >
          <UploadCloud size={28} style={{ color: 'var(--teal)' }} />
        </div>
        <p className="font-medium mb-1" style={{ color: 'var(--ink)' }}>
          {dragging ? 'Drop your file here' : 'Drag & drop your PDF here'}
        </p>
        <p className="text-sm" style={{ color: 'var(--muted)' }}>
          or click to browse — PDF files only
        </p>
      </div>

      {/* Selected file */}
      {file && !result && (
        <div className="card p-4 mt-4 flex items-center gap-3 fade-up">
          <FileText size={20} style={{ color: 'var(--teal)' }} />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate" style={{ color: 'var(--ink)' }}>
              {file.name}
            </p>
            <p className="text-xs" style={{ color: 'var(--muted)' }}>
              {(file.size / 1024).toFixed(0)} KB
            </p>
          </div>
          <button
            onClick={() => setFile(null)}
            className="opacity-50 hover:opacity-100 transition-opacity"
            aria-label="Remove file"
          >
            <X size={18} />
          </button>
        </div>
      )}

      {/* Upload button */}
      {file && !result && (
        <button onClick={onUpload} disabled={busy} className="btn-primary w-full mt-4">
          {busy ? 'Uploading & analyzing…' : 'Upload report'}
        </button>
      )}

      {/* Success */}
      {result && (
        <div className="card p-5 mt-4 flex items-start gap-3 fade-up" style={{ background: 'var(--teal-soft)', borderColor: 'transparent' }}>
          <CheckCircle size={22} style={{ color: 'var(--teal)' }} className="mt-0.5 shrink-0" />
          <div className="flex-1">
            <p className="font-semibold" style={{ color: 'var(--teal)' }}>
              {result.message}
            </p>
            <p className="text-sm mt-0.5" style={{ color: 'var(--ink)' }}>
              {result.report.report_name}
            </p>
          </div>
          <button onClick={() => onUploaded(result.report.id)} className="btn-primary text-sm">
            View dashboard
          </button>
        </div>
      )}
    </div>
  );
}
