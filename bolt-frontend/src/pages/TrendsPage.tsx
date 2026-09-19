import { useEffect, useMemo, useState } from 'react';
import { TrendingUp, Search, Sparkles } from 'lucide-react';
import { api } from '@/lib/api';
import { useToast } from '@/context/ToastContext';
import { PageSpinner } from '@/components/Spinner';
import type { TrendResponse } from '@/types';

export function TrendsPage() {
  const { showError } = useToast();
  const [query, setQuery] = useState('');
  const [submitted, setSubmitted] = useState<string | null>(null);
  const [data, setData] = useState<TrendResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!submitted) return;
    let cancelled = false;
    setLoading(true);
    setData(null);
    api
      .trends(submitted)
      .then((d) => {
        if (!cancelled) setData(d);
      })
      .catch((e) => {
        if (!cancelled) showError(e instanceof Error ? e.message : 'Failed to load trends');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [submitted, showError]);

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) return;
    setSubmitted(trimmed);
  };

  return (
    <div className="max-w-3xl mx-auto px-6 py-8">
      <h2 className="text-2xl font-semibold mb-1.5" style={{ color: 'var(--ink)' }}>
        Biomarker trends
      </h2>
      <p className="text-sm mb-6" style={{ color: 'var(--muted)' }}>
        Track how a specific biomarker has changed across all your reports over time.
      </p>

      <form onSubmit={onSubmit} className="flex gap-2 mb-6">
        <div className="relative flex-1">
          <Search
            size={18}
            style={{ color: 'var(--muted)' }}
            className="absolute left-3 top-1/2 -translate-y-1/2"
          />
          <input
            className="input-field pl-10"
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g. Glucose, Hemoglobin, Cholesterol"
            autoFocus
          />
        </div>
        <button type="submit" className="btn-primary whitespace-nowrap">
          Show trend
        </button>
      </form>

      {!submitted && !loading && (
        <div className="card p-10 text-center">
          <div
            className="w-14 h-14 rounded-2xl mx-auto mb-4 flex items-center justify-center"
            style={{ background: 'var(--teal-soft)' }}
          >
            <TrendingUp size={28} style={{ color: 'var(--teal)' }} />
          </div>
          <p className="font-medium mb-1" style={{ color: 'var(--ink)' }}>
            Search for a biomarker
          </p>
          <p className="text-sm" style={{ color: 'var(--muted)' }}>
            Enter a biomarker name above to see how your values have changed over time.
          </p>
        </div>
      )}

      {loading && <PageSpinner label="Loading trend data…" />}

      {!loading && data && <TrendResult data={data} />}
    </div>
  );
}

function TrendResult({ data }: { data: TrendResponse }) {
  const points = data.history;

  if (points.length === 0) {
    return (
      <div className="card p-8 text-center">
        <p className="font-medium mb-1" style={{ color: 'var(--ink)' }}>
          No data found
        </p>
        <p className="text-sm" style={{ color: 'var(--muted)' }}>
          No history found for "{data.name}". Check the spelling or try another biomarker.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4 fade-up">
      <div className="card p-5">
        <div className="flex items-center justify-between mb-1">
          <h3 className="text-lg font-semibold" style={{ color: 'var(--ink)' }}>
            {data.name}
          </h3>
          <span className="text-sm" style={{ color: 'var(--muted)' }}>
            {data.unit}
          </span>
        </div>
        <p className="text-sm mb-5" style={{ color: 'var(--muted)' }}>
          {points.length} {points.length === 1 ? 'measurement' : 'measurements'} over time
        </p>
        <LineChart points={points} unit={data.unit} />
      </div>

      {data.trend_summary && (
        <div className="card p-5" style={{ background: 'var(--teal-soft)', borderColor: 'transparent' }}>
          <div className="flex items-start gap-3">
            <div
              className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0"
              style={{ background: 'var(--teal)' }}
            >
              <Sparkles size={18} className="text-white" />
            </div>
            <div>
              <h4 className="text-sm font-semibold mb-1" style={{ color: 'var(--teal)' }}>
                AI Trend Summary
              </h4>
              <p className="text-sm leading-relaxed" style={{ color: 'var(--ink)' }}>
                {data.trend_summary}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

interface ChartPoint {
  report_id: number;
  report_date: string;
  value: number;
  status: 'LOW' | 'NORMAL' | 'HIGH';
}

function LineChart({ points, unit }: { points: ChartPoint[]; unit: string }) {
  const W = 640;
  const H = 260;
  const padL = 56;
  const padR = 24;
  const padT = 20;
  const padB = 44;

  const values = points.map((p) => p.value);
  const minV = Math.min(...values);
  const maxV = Math.max(...values);
  const range = maxV - minV || 1;
  // add 10% padding to the y range
  const yMin = minV - range * 0.1;
  const yMax = maxV + range * 0.1;
  const yRange = yMax - yMin || 1;

  const chartW = W - padL - padR;
  const chartH = H - padT - padB;

  const xFor = (i: number) =>
    points.length === 1 ? padL + chartW / 2 : padL + (i / (points.length - 1)) * chartW;
  const yFor = (v: number) => padT + chartH - ((v - yMin) / yRange) * chartH;

  const linePath = points
    .map((p, i) => `${i === 0 ? 'M' : 'L'} ${xFor(i).toFixed(1)} ${yFor(p.value).toFixed(1)}`)
    .join(' ');

  const areaPath =
    `${linePath} L ${xFor(points.length - 1).toFixed(1)} ${(padT + chartH).toFixed(1)} ` +
    `L ${xFor(0).toFixed(1)} ${(padT + chartH).toFixed(1)} Z`;

  // y-axis ticks
  const ticks = useMemo(() => {
    const n = 4;
    const arr: number[] = [];
    for (let i = 0; i <= n; i++) arr.push(yMin + (yRange * i) / n);
    return arr;
  }, [yMin, yRange]);

  const colorFor = (status: string) =>
    status === 'NORMAL' ? 'var(--teal)' : status === 'LOW' ? 'var(--slate-blue)' : 'var(--amber)';

  return (
    <div className="w-full overflow-x-auto">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ minWidth: 480 }}>
        {/* grid + y labels */}
        {ticks.map((t, i) => {
          const y = yFor(t);
          return (
            <g key={i}>
              <line
                x1={padL}
                x2={W - padR}
                y1={y}
                y2={y}
                stroke="var(--line)"
                strokeWidth={1}
              />
              <text
                x={padL - 10}
                y={y + 4}
                textAnchor="end"
                fontSize={11}
                fill="var(--muted)"
              >
                {t.toFixed(1)}
              </text>
            </g>
          );
        })}

        {/* area */}
        <defs>
          <linearGradient id="trendArea" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--teal)" stopOpacity={0.16} />
            <stop offset="100%" stopColor="var(--teal)" stopOpacity={0} />
          </linearGradient>
        </defs>
        <path d={areaPath} fill="url(#trendArea)" />

        {/* line */}
        <path
          d={linePath}
          fill="none"
          stroke="var(--teal)"
          strokeWidth={2.5}
          strokeLinejoin="round"
          strokeLinecap="round"
        />

        {/* points */}
        {points.map((p, i) => (
          <g key={p.report_id}>
            <circle
              cx={xFor(i)}
              cy={yFor(p.value)}
              r={5}
              fill="white"
              stroke={colorFor(p.status)}
              strokeWidth={2.5}
            />
            <text
              x={xFor(i)}
              y={yFor(p.value) - 12}
              textAnchor="middle"
              fontSize={11}
              fontWeight={600}
              fill="var(--ink)"
            >
              {p.value}
            </text>
          </g>
        ))}

        {/* x labels */}
        {points.map((p, i) => (
          <text
            key={`x-${p.report_id}`}
            x={xFor(i)}
            y={H - padB + 20}
            textAnchor={i === 0 ? 'start' : i === points.length - 1 ? 'end' : 'middle'}
            fontSize={11}
            fill="var(--muted)"
          >
            {new Date(p.report_date).toLocaleDateString(undefined, {
              month: 'short',
              day: 'numeric',
            })}
          </text>
        ))}

        {/* unit label */}
        <text x={padL} y={H - 2} fontSize={10} fill="var(--muted)">
          Values in {unit}
        </text>
      </svg>
    </div>
  );
}
