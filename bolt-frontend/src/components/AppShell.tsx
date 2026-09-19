import { useState, type ReactNode } from 'react';
import {
  LayoutDashboard,
  UploadCloud,
  History,
  TrendingUp,
  LogOut,
  Activity,
  Menu,
  X,
} from 'lucide-react';
import { useAuth } from '@/context/AuthContext';

export type Route = 'dashboard' | 'upload' | 'history' | 'trends';

interface ShellProps {
  route: Route;
  onNavigate: (r: Route) => void;
  children: ReactNode;
}

const NAV: { id: Route; label: string; icon: typeof Activity }[] = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'upload', label: 'Upload Report', icon: UploadCloud },
  { id: 'history', label: 'Report History', icon: History },
  { id: 'trends', label: 'Biomarker Trends', icon: TrendingUp },
];

export function AppShell({ route, onNavigate, children }: ShellProps) {
  const { user, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);

  const go = (r: Route) => {
    onNavigate(r);
    setMobileOpen(false);
  };

  return (
    <div className="min-h-screen flex" style={{ background: 'var(--bg)' }}>
      {/* Sidebar — desktop */}
      <aside
        className="hidden md:flex flex-col w-64 shrink-0 border-r"
        style={{ borderColor: 'var(--line)', background: 'var(--surface)' }}
      >
        <SidebarContent route={route} onNavigate={go} user={user} onLogout={logout} />
      </aside>

      {/* Sidebar — mobile drawer */}
      {mobileOpen && (
        <div className="md:hidden fixed inset-0 z-40">
          <div className="absolute inset-0 bg-black/30" onClick={() => setMobileOpen(false)} />
          <aside
            className="absolute left-0 top-0 bottom-0 w-72 flex flex-col shadow-xl"
            style={{ background: 'var(--surface)' }}
          >
            <SidebarContent route={route} onNavigate={go} user={user} onLogout={logout} />
          </aside>
        </div>
      )}

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Mobile top bar */}
        <header
          className="md:hidden flex items-center justify-between px-4 h-14 border-b"
          style={{ borderColor: 'var(--line)', background: 'var(--surface)' }}
        >
          <button onClick={() => setMobileOpen(true)} aria-label="Open menu">
            <Menu size={22} style={{ color: 'var(--ink)' }} />
          </button>
          <div className="flex items-center gap-2">
            <Activity size={18} style={{ color: 'var(--teal)' }} />
            <span className="font-semibold text-sm" style={{ color: 'var(--ink)' }}>MedInsight AI</span>
          </div>
          <div className="w-6" />
        </header>

        <main className="flex-1 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}

function SidebarContent({
  route,
  onNavigate,
  user,
  onLogout,
}: {
  route: Route;
  onNavigate: (r: Route) => void;
  user: { name: string; email: string } | null;
  onLogout: () => void;
}) {
  return (
    <>
      <div className="flex items-center justify-between px-5 h-16 border-b" style={{ borderColor: 'var(--line)' }}>
        <div className="flex items-center gap-2.5">
          <div
            className="w-9 h-9 rounded-xl flex items-center justify-center"
            style={{ background: 'var(--teal-soft)' }}
          >
            <Activity size={20} style={{ color: 'var(--teal)' }} />
          </div>
          <span className="font-semibold tracking-tight" style={{ color: 'var(--ink)' }}>
            MedInsight AI
          </span>
        </div>
        <button className="md:hidden" onClick={() => onNavigate('dashboard')}>
          <X size={20} style={{ color: 'var(--muted)' }} />
        </button>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {NAV.map((item) => {
          const active = route === item.id;
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                active ? '' : 'hover:bg-black/[0.03]'
              }`}
              style={
                active
                  ? { background: 'var(--teal-soft)', color: 'var(--teal)' }
                  : { color: 'var(--muted)' }
              }
            >
              <Icon size={19} />
              {item.label}
            </button>
          );
        })}
      </nav>

      <div className="px-3 py-4 border-t" style={{ borderColor: 'var(--line)' }}>
        <div className="px-3 py-2 mb-1">
          <p className="text-sm font-medium truncate" style={{ color: 'var(--ink)' }}>
            {user?.name ?? 'User'}
          </p>
          <p className="text-xs truncate" style={{ color: 'var(--muted)' }}>
            {user?.email ?? ''}
          </p>
        </div>
        <button
          onClick={onLogout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors hover:bg-black/[0.03]"
          style={{ color: 'var(--muted)' }}
        >
          <LogOut size={19} />
          Sign out
        </button>
      </div>
    </>
  );
}
