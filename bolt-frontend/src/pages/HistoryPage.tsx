import { useEffect, useState } from 'react';
import { History, FileText, ChevronRight, Calendar } from 'lucide-react';
import { api } from '@/lib/api';
import { useToast } from '@/context/ToastContext';
import { PageSpinner } from '@/components/Spinner';
import type { ReportListItem } from '@/types';

interface HistoryProps {
  onOpenReport: (id: number) => void;
}

export function HistoryPage({ onOpenReport }: HistoryProps) {
  const { showError } = useToast();
  const [reports, setReports] = useState<ReportListItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    api
      .reports()
      .then((list) => {
        if (!cancelled) setReports(list);
      })
      .catch((e) => {
        if (!cancelled) showError(e instanceof Error ? e.message : 'Failed to load reports');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [showError]);

  if (loading) return <PageSpinner label="Loading history…" />;

  if (reports.length === 0) {
    return (
      <div className="max-w-2xl mx-auto px-6 py-20 text-center">
        <div
          className="w-16 h-16 rounded-2xl mx-auto mb-5 flex items-center justify-center"
          style={{ background: 'var(--teal-soft)' }}
        >
          <History size={30} style={{ color: 'var(--teal)' }} />
        </div>
        <h2 className="text-2xl font-semibold mb-2" style={{ color: 'var(--ink)' }}>
          No reports yet
        </h2>
        <p style={{ color: 'var(--muted)' }}>Your uploaded reports will appear here.</p>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-6 py-8">
      <h2 className="text-2xl font-semibold mb-1.5" style={{ color: 'var(--ink)' }}>
        Report history
      </h2>
      <p className="text-sm mb-6" style={{ color: 'var(--muted)' }}>
        {reports.length} {reports.length === 1 ? 'report' : 'reports'} — click any to view its dashboard.
      </p>

      <div className="space-y-2.5">
        {reports.map((r, i) => (
          <button
            key={r.id}
            onClick={() => onOpenReport(r.id)}
            className="card w-full flex items-center gap-4 p-4 text-left transition-all hover:shadow-md fade-up"
            style={{ animationDelay: `${i * 40}ms` }}
          >
            <div
              className="w-11 h-11 rounded-xl flex items-center justify-center shrink-0"
              style={{ background: 'var(--teal-soft)' }}
            >
              <FileText size={20} style={{ color: 'var(--teal)' }} />
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-semibold truncate" style={{ color: 'var(--ink)' }}>
                {r.report_name}
              </p>
              <div className="flex items-center gap-2 mt-1">
                <Calendar size={13} style={{ color: 'var(--muted)' }} />
                <p className="text-sm" style={{ color: 'var(--muted)' }}>
                  Uploaded {new Date(r.upload_date).toLocaleDateString(undefined, {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                  })}
                </p>
              </div>
            </div>
            <ChevronRight size={18} style={{ color: 'var(--muted)' }} className="shrink-0" />
          </button>
        ))}
      </div>
    </div>
  );
}
