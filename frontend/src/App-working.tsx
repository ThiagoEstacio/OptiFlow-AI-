/**
 * 🎯 OptiFlow AI - Working App (No MUI in Layout)
 * ================================================
 *
 * Versão funcional sem MUI no layout principal.
 * Usa SimplifiedLayoutNoMui + TopBarSimple
 */
import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Provider } from 'react-redux';
import { store } from './store';
import { PrivateRoute } from './components/PrivateRoute';
import { SimplifiedLayoutNoMui } from './components/Layout/SimplifiedLayoutNoMui';
import { LoginPage } from './pages/LoginPage';
import { Toaster } from './components/Toast/Toaster';
import { ErrorBoundary } from './components/ErrorBoundary';
import { ThemeProvider } from './contexts/ThemeContext';
import { AssetProvider } from './contexts/AssetContext';
import { websocketService } from './services/websocket';
import { CriticalAlarmNotification } from './components/CriticalAlarmNotification';
import { useCriticalAlarms } from './hooks/useCriticalAlarms';

// ========================================
// 📊 CORE PAGES - Lazy loaded to avoid MUI issues
// ========================================
import { lazy, Suspense } from 'react';

// Loading component
const PageLoading = () => (
  <div className="flex items-center justify-center h-64">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
  </div>
);

// Lazy load pages that might use MUI internally
const ProfessionalDashboard = lazy(() => import('./pages/ProfessionalDashboard').then(m => ({ default: m.ProfessionalDashboard })));
const ModernDashboard = lazy(() => import('./pages/ModernDashboard').then(m => ({ default: m.ModernDashboard })));
const ProfessionalRealtime = lazy(() => import('./pages/ProfessionalRealtime').then(m => ({ default: m.ProfessionalRealtime })));
const ModernAlarmsPage = lazy(() => import('./pages/ModernAlarmsPage').then(m => ({ default: m.ModernAlarmsPage })));
const MLAnalyticsDashboard = lazy(() => import('./pages/MLAnalyticsDashboard').then(m => ({ default: m.MLAnalyticsDashboard })));
const SettingsPage = lazy(() => import('./pages/SettingsPage').then(m => ({ default: m.SettingsPage })));
const ReportsDashboard = lazy(() => import('./pages/ReportsDashboard').then(m => ({ default: m.ReportsDashboard })));
const ChatPage = lazy(() => import('./pages/ChatPage').then(m => ({ default: m.ChatPage })));
const TagDetailsPage = lazy(() => import('./pages/TagDetailsPage').then(m => ({ default: m.TagDetailsPage })));
const DashboardsList = lazy(() => import('./pages/DashboardsList'));
const ExecutiveDashboard = lazy(() => import('./pages/ExecutiveDashboard'));

// Placeholder for DashboardBuilder (uses react-draggable which is broken)
function DashboardBuilderPlaceholder() {
  return (
    <div className="p-8 text-center">
      <h2 className="text-xl font-bold text-gray-700">🚧 Dashboard Builder</h2>
      <p className="text-gray-500 mt-2">Esta funcionalidade está sendo atualizada.</p>
    </div>
  );
}

function AppContent() {
  const { currentAlarm, acknowledgeAlarm, dismissAlarm } = useCriticalAlarms();

  useEffect(() => {
    const wsUrl = 'ws://localhost:8000/api/v1/ws/simulator/stream';
    console.log('🔌 Connecting to WebSocket:', wsUrl);
    websocketService.connect(wsUrl);
    return () => websocketService.disconnect();
  }, []);

  return (
    <>
      <Toaster />
      <CriticalAlarmNotification
        alarm={currentAlarm}
        onAcknowledge={acknowledgeAlarm}
        onClose={dismissAlarm}
      />
      <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <Routes>
          {/* Public */}
          <Route path="/login" element={<LoginPage />} />

          {/* Private */}
          <Route
            path="/"
            element={
              <PrivateRoute>
                <SimplifiedLayoutNoMui />
              </PrivateRoute>
            }
          >
            {/* Dashboard */}
            <Route index element={<Suspense fallback={<PageLoading />}><ProfessionalDashboard /></Suspense>} />
            <Route path="dashboard" element={<Suspense fallback={<PageLoading />}><ProfessionalDashboard /></Suspense>} />
            <Route path="dashboard/classic" element={<Suspense fallback={<PageLoading />}><ModernDashboard /></Suspense>} />
            <Route path="dashboard/executive" element={<Suspense fallback={<PageLoading />}><ExecutiveDashboard /></Suspense>} />
            <Route path="dashboards" element={<Suspense fallback={<PageLoading />}><DashboardsList /></Suspense>} />
            <Route path="dashboards/builder" element={<DashboardBuilderPlaceholder />} />
            <Route path="dashboards/new" element={<DashboardBuilderPlaceholder />} />
            <Route path="dashboards/:id" element={<DashboardBuilderPlaceholder />} />

            {/* Real-time */}
            <Route path="realtime" element={<Suspense fallback={<PageLoading />}><ProfessionalRealtime /></Suspense>} />
            <Route path="realtime/tags/:id" element={<Suspense fallback={<PageLoading />}><TagDetailsPage /></Suspense>} />

            {/* Alarms */}
            <Route path="alarms" element={<Suspense fallback={<PageLoading />}><ModernAlarmsPage /></Suspense>} />
            <Route path="alarms/*" element={<Suspense fallback={<PageLoading />}><ModernAlarmsPage /></Suspense>} />

            {/* Analytics */}
            <Route path="analytics" element={<Suspense fallback={<PageLoading />}><MLAnalyticsDashboard /></Suspense>} />
            <Route path="analytics/chat" element={<Suspense fallback={<PageLoading />}><ChatPage /></Suspense>} />

            {/* Settings */}
            <Route path="settings" element={<Suspense fallback={<PageLoading />}><SettingsPage /></Suspense>} />

            {/* Reports */}
            <Route path="reports" element={<Suspense fallback={<PageLoading />}><ReportsDashboard /></Suspense>} />

            {/* Legacy redirects */}
            <Route path="operations" element={<Navigate to="/dashboard" replace />} />
            <Route path="operations/*" element={<Navigate to="/dashboard" replace />} />
            <Route path="maintenance" element={<Navigate to="/analytics" replace />} />
            <Route path="engineering" element={<Navigate to="/settings" replace />} />
            <Route path="config" element={<Navigate to="/settings" replace />} />
            <Route path="config/*" element={<Navigate to="/settings" replace />} />
            <Route path="tags" element={<Navigate to="/realtime" replace />} />
            <Route path="tags/:id" element={<Suspense fallback={<PageLoading />}><TagDetailsPage /></Suspense>} />
            <Route path="chat" element={<Suspense fallback={<PageLoading />}><ChatPage /></Suspense>} />
          </Route>

          {/* 404 */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <Provider store={store}>
        <ThemeProvider>
          <AssetProvider>
            <AppContent />
          </AssetProvider>
        </ThemeProvider>
      </Provider>
    </ErrorBoundary>
  );
}

export default App;
