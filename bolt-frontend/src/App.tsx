import { useState } from 'react';
import { AuthProvider, useAuth } from '@/context/AuthContext';
import { ToastProvider } from '@/context/ToastContext';
import { FullPageSpinner } from '@/components/Spinner';
import { AppShell, type Route } from '@/components/AppShell';
import { AuthPage } from '@/pages/AuthPage';
import { DashboardPage } from '@/pages/DashboardPage';
import { UploadPage } from '@/pages/UploadPage';
import { HistoryPage } from '@/pages/HistoryPage';
import { TrendsPage } from '@/pages/TrendsPage';

function AppInner() {
  const { user, loading } = useAuth();
  const [route, setRoute] = useState<Route>('dashboard');
  const [dashboardReportId, setDashboardReportId] = useState<number | null>(null);

  if (loading) return <FullPageSpinner label="Loading MedInsight AI…" />;

  if (!user) return <AuthPage />;

  function navigate(r: Route) {
    if (r === 'dashboard') setDashboardReportId(null);
    setRoute(r);
  }

  function openReportInDashboard(id: number) {
    setDashboardReportId(id);
    setRoute('dashboard');
  }

  return (
    <AppShell route={route} onNavigate={navigate}>
      {route === 'dashboard' && (
        <DashboardPage
          preselectedId={dashboardReportId}
          onConsumePreselect={() => setDashboardReportId(null)}
          onGoUpload={() => setRoute('upload')}
        />
      )}
      {route === 'upload' && (
        <UploadPage onUploaded={(id) => openReportInDashboard(id)} />
      )}
      {route === 'history' && <HistoryPage onOpenReport={openReportInDashboard} />}
      {route === 'trends' && <TrendsPage />}
    </AppShell>
  );
}

export default function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <AppInner />
      </AuthProvider>
    </ToastProvider>
  );
}
