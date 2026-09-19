import {
  createContext,
  useCallback,
  useContext,
  useState,
  type ReactNode,
} from 'react';
import { CheckCircle, AlertTriangle, Info, X } from 'lucide-react';

type ToastKind = 'error' | 'success' | 'info';

interface Toast {
  id: number;
  kind: ToastKind;
  message: string;
}

interface ToastContextValue {
  showError: (msg: string) => void;
  showSuccess: (msg: string) => void;
  showInfo: (msg: string) => void;
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

let nextId = 0;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const remove = useCallback((id: number) => {
    setToasts((t) => t.filter((x) => x.id !== id));
  }, []);

  const push = useCallback(
    (kind: ToastKind, message: string) => {
      const id = ++nextId;
      setToasts((t) => [...t, { id, kind, message }]);
      window.setTimeout(() => remove(id), 5000);
    },
    [remove],
  );

  const showError = useCallback((m: string) => push('error', m), [push]);
  const showSuccess = useCallback((m: string) => push('success', m), [push]);
  const showInfo = useCallback((m: string) => push('info', m), [push]);

  return (
    <ToastContext.Provider value={{ showError, showSuccess, showInfo }}>
      {children}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2.5 w-[360px] max-w-[calc(100vw-2rem)]">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`toast-enter card flex items-start gap-3 px-4 py-3.5 shadow-lg shadow-black/5 ${
              t.kind === 'error'
                ? 'border-l-4'
                : t.kind === 'success'
                  ? 'border-l-4'
                  : ''
            }`}
            style={{
              borderLeftColor:
                t.kind === 'error'
                  ? 'var(--amber)'
                  : t.kind === 'success'
                    ? 'var(--teal)'
                    : 'var(--slate-blue)',
            }}
          >
            {t.kind === 'error' && (
              <AlertTriangle size={18} style={{ color: 'var(--amber)' }} className="mt-0.5 shrink-0" />
            )}
            {t.kind === 'success' && (
              <CheckCircle size={18} style={{ color: 'var(--teal)' }} className="mt-0.5 shrink-0" />
            )}
            {t.kind === 'info' && (
              <Info size={18} style={{ color: 'var(--slate-blue)' }} className="mt-0.5 shrink-0" />
            )}
            <p className="text-sm leading-snug flex-1" style={{ color: 'var(--ink)' }}>
              {t.message}
            </p>
            <button
              onClick={() => remove(t.id)}
              className="shrink-0 opacity-40 hover:opacity-100 transition-opacity"
              aria-label="Dismiss"
            >
              <X size={16} />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within ToastProvider');
  return ctx;
}
