import { Loader2 } from 'lucide-react';

export function Spinner({ size = 20 }: { size?: number }) {
  return (
    <Loader2
      size={size}
      className="animate-spin"
      style={{ color: 'var(--teal)' }}
    />
  );
}

export function FullPageSpinner({ label = 'Loading…' }: { label?: string }) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center gap-3">
      <Spinner size={32} />
      <p className="text-sm" style={{ color: 'var(--muted)' }}>{label}</p>
    </div>
  );
}

export function PageSpinner({ label }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-3">
      <Spinner size={28} />
      {label && <p className="text-sm" style={{ color: 'var(--muted)' }}>{label}</p>}
    </div>
  );
}
