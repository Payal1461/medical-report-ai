import { useEffect, useState } from 'react';
import {
  CheckCircle,
  ArrowDownCircle,
  ArrowUpCircle,
  ChevronDown,
  Sparkles,
  FileText,
  AlertCircle,
} from 'lucide-react';
import { api } from '@/lib/api';
import { useToast } from '@/context/ToastContext';
import { PageSpinner } from '@/components/Spinner';
import type { Biomarker, ReportListItem, ReportSummary } from '@/types';

interface DashboardProps {
  preselectedId: number | null;
  onConsumePreselect: () => void;
  onGoUpload: () => void;
}

export function DashboardPage({
  preselectedId,
  onConsumePreselect,
  onGoUpload,
}: DashboardProps) {
  const { showError } = useToast();
  const [reports, setReports] = useState<ReportListItem[]>([]);
  const [loadingReports, setLoadingReports] = useState(true);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [pickerOpen, setPickerOpen] = useState(false);
  const [dashboard, setDashboard] = useState<ReportSummary | null>(null);
  const [loadingDashboard, setLoadingDashboard] = useState(false);

  // Load report list once
  useEffect(() => {
    let cancelled = false;
    setLoadingReports(true);
    api
      .reports()
      .then((list) => {
        if (cancelled) return;
        setReports(list);
        if (preselectedId) {
          setSelectedId(preselectedId);
          onConsumePreselect();
        } else if (list.length > 0) {
          setSelectedId(list[0].id); // most recent first
        }
      })
      .catch((e) => {
        if (!cancelled) showError(e instanceof Error ? e.message : 'Failed to load reports');
      })
      .finally(() => {
        if (!cancelled) setLoadingReports(false);
      });
    return () => {
      cancelled = true;
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Load dashboard data when a report is selected
  useEffect(() => {
    if (selectedId == null) return;
    let cancelled = false;
    setLoadingDashboard(true);
    setDashboard(null);
    api
      .dashboard(selectedId)
      .then((d) => {
        if (!cancelled) setDashboard(d);
      })
      .catch((e) => {
        if (!cancelled) showError(e instanceof Error ? e.message : 'Failed to load dashboard');
      })
      .finally(() => {
        if (!cancelled) setLoadingDashboard(false);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedId, showError]);

  if (loadingReports) return <PageSpinner label="Loading your reports…" />;

  if (reports.length === 0) {
    return (
      <div className="max-w-2xl mx-auto px-6 py-20 text-center fade-up">
        <div
          className="w-16 h-16 rounded-2xl mx-auto mb-5 flex items-center justify-center"
          style={{ background: 'var(--teal-soft)' }}
        >
          <FileText size={30} style={{ color: 'var(--teal)' }} />
        </div>
        <h2 className="text-2xl font-semibold mb-2" style={{ color: 'var(--ink)' }}>
          No reports yet
        </h2>
        <p className="mb-6" style={{ color: 'var(--muted)' }}>
          Upload your first medical report (PDF) to see AI-powered insights here.
        </p>
        <button onClick={onGoUpload} className="btn-primary">
          Upload a report
        </button>
      </div>
    );
  }

  const selectedReport = reports.find((r) => r.id === selectedId);

  return (
    <div className="max-w-5xl mx-auto px-6 py-8 space-y-6">
      {/* Report picker */}
      <div className="relative">
        <button
          onClick={() => setPickerOpen((o) => !o)}
          className="w-full card flex items-center justify-between px-4 py-3.5 text-left transition-shadow hover:shadow-md"
        >
          <div className="flex items-center gap-3 min-w-0">
            <FileText size={20} style={{ color: 'var(--teal)' }} className="shrink-0" />
            <div className="min-w-0">
              <p className="text-xs uppercase tracking-wide font-medium" style={{ color: 'var(--muted)' }}>
                Viewing report
              </p>
              <p className="font-semibold truncate" style={{ color: 'var(--ink)' }}>
                {selectedReport?.report_name ?? 'Select a report'}
              </p>
            </div>
          </div>
          <ChevronDown
            size={18}
            style={{ color: 'var(--muted)' }}
            className={`transition-transform ${pickerOpen ? 'rotate-180' : ''}`}
          />
        </button>
        {pickerOpen && (
          <>
            <div className="fixed inset-0 z-10" onClick={() => setPickerOpen(false)} />
            <div className="absolute left-0 right-0 top-full mt-1.5 card shadow-lg z-20 overflow-hidden">
              <ul className="max-h-72 overflow-y-auto">
                {reports.map((r) => (
                  <li key={r.id}>
                    <button
                      onClick={() => {
                        setSelectedId(r.id);
                        setPickerOpen(false);
                      }}
                      className="w-full flex items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-black/[0.03]"
                      style={
                        r.id === selectedId
                          ? { background: 'var(--teal-soft)' }
                          : undefined
                      }
                    >
                      <FileText size={16} style={{ color: 'var(--muted)' }} />
                      <div className="min-w-0">
                        <p className="text-sm font-medium truncate" style={{ color: 'var(--ink)' }}>
                          {r.report_name}
                        </p>
                        <p className="text-xs" style={{ color: 'var(--muted)' }}>
                          {new Date(r.upload_date).toLocaleDateString(undefined, {
                            year: 'numeric',
                            month: 'short',
                            day: 'numeric',
                          })}
                        </p>
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          </>
        )}
      </div>

      {loadingDashboard || !dashboard ? (
        <PageSpinner label="Analyzing report…" />
      ) : (
        <DashboardContent data={dashboard} />
      )}
    </div>
  );
}

function DashboardContent({ data }: { data: ReportSummary }) {
  const { summary } = data;
  const abnormal = data.biomarkers.filter((b) => b.status !== 'NORMAL');

  return (
    <div className="space-y-6 fade-up">
      {/* Health snapshot */}
      <div className="grid grid-cols-3 gap-3 sm:gap-4">
        <SnapshotCard
          label="Normal"
          count={summary.normal_count}
          icon={<CheckCircle size={20} />}
          color="var(--teal)"
          bg="var(--teal-soft)"
        />
        <SnapshotCard
          label="Low"
          count={summary.low_count}
          icon={<ArrowDownCircle size={20} />}
          color="var(--slate-blue)"
          bg="var(--slate-blue-soft)"
        />
        <SnapshotCard
          label="High"
          count={summary.high_count}
          icon={<ArrowUpCircle size={20} />}
          color="var(--amber)"
          bg="var(--amber-soft)"
        />
      </div>

      {/* AI summary */}
      {data.overall_summary && (
        <div className="card p-5" style={{ background: 'var(--teal-soft)', borderColor: 'transparent' }}>
          <div className="flex items-start gap-3">
            <div
              className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0"
              style={{ background: 'var(--teal)' }}
            >
              <Sparkles size={18} className="text-white" />
            </div>
            <div>
              <h3 className="text-sm font-semibold mb-1" style={{ color: 'var(--teal)' }}>
                AI Health Summary
              </h3>
              <p className="text-sm leading-relaxed" style={{ color: 'var(--ink)' }}>
                {data.overall_summary}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Biomarker cards */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold" style={{ color: 'var(--ink)' }}>
            Biomarkers
          </h3>
          <span className="text-sm" style={{ color: 'var(--muted)' }}>
            {data.biomarkers.length} total · {abnormal.length} need attention
          </span>
        </div>
        <div className="grid sm:grid-cols-2 gap-3">
          {data.biomarkers.map((b) => (
            <BiomarkerCard key={b.id} biomarker={b} />
          ))}
        </div>
      </div>
    </div>
  );
}

function SnapshotCard({
  label,
  count,
  icon,
  color,
  bg,
}: {
  label: string;
  count: number;
  icon: React.ReactNode;
  color: string;
  bg: string;
}) {
  return (
    <div className="card p-4 flex flex-col gap-2" style={{ background: bg, borderColor: 'transparent' }}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wide" style={{ color }}>
          {label}
        </span>
        <span style={{ color }}>{icon}</span>
      </div>
      <p className="text-3xl font-semibold" style={{ color: 'var(--ink)' }}>
        {count}
      </p>
    </div>
  );
}

function BiomarkerCard({ biomarker: b }: { biomarker: Biomarker }) {
  const isAbnormal = b.status !== 'NORMAL';
  const statusColor =
    b.status === 'NORMAL' ? 'var(--teal)' : b.status === 'LOW' ? 'var(--slate-blue)' : 'var(--amber)';
  const statusBg =
    b.status === 'NORMAL'
      ? 'var(--teal-soft)'
      : b.status === 'LOW'
        ? 'var(--slate-blue-soft)'
        : 'var(--amber-soft)';

  return (
    <div className="card p-4 flex flex-col gap-3">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="font-semibold" style={{ color: 'var(--ink)' }}>
            {b.name}
          </p>
          <p className="text-sm mt-0.5" style={{ color: 'var(--muted)' }}>
            {b.value} {b.unit}
            <span className="mx-1.5">·</span>
            Ref: {b.ref_low}–{b.ref_high} {b.unit}
          </p>
        </div>
        <span
          className="text-xs font-semibold px-2.5 py-1 rounded-full shrink-0"
          style={{ color: statusColor, background: statusBg }}
        >
          {b.status}
        </span>
      </div>

      {/* range bar */}
      <RangeBar value={b.value} low={b.ref_low} high={b.ref_high} status={b.status} />

      {isAbnormal && b.explanation && (
        <div
          className="flex items-start gap-2 rounded-lg px-3 py-2.5 text-sm leading-relaxed"
          style={{ background: statusBg, color: 'var(--ink)' }}
        >
          <AlertCircle size={15} style={{ color: statusColor }} className="mt-0.5 shrink-0" />
          <p>{b.explanation}</p>
        </div>
      )}
    </div>
  );
}

function RangeBar({
  value,
  low,
  high,
  status,
}: {
  value: number;
  low: number;
  high: number;
  status: string;
}) {
  const span = high - low || 1;
  // Map value onto 0–100, clamped
  const pct = Math.max(2, Math.min(98, ((value - low) / span) * 100));
  const color =
    status === 'NORMAL' ? 'var(--teal)' : status === 'LOW' ? 'var(--slate-blue)' : 'var(--amber)';

  return (
    <div className="relative h-2 rounded-full" style={{ background: 'var(--line)' }}>
      {/* normal range zone */}
      <div
        className="absolute top-0 bottom-0 rounded-full"
        style={{ left: '0%', right: '0%', background: 'var(--teal-soft)' }}
      />
      {/* marker */}
      <div
        className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-3 h-3 rounded-full border-2 border-white shadow"
        style={{ left: `${pct}%`, background: color }}
      />
    </div>
  );
}
