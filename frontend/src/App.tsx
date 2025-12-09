/**
 * 🎯 OptiFlow AI - Professional Tremor App (No MUI)
 * ==================================================
 *
 * Versão profissional usando apenas Tremor para dashboards.
 * Sem MUI para evitar conflitos com Emotion.
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
import { FloatingAIChat } from './components/FloatingAIChat';
import { useChartColors } from './hooks/useChartColors';

// ========================================
// 📊 TREMOR PAGES - Professional Dashboard Components (No MUI)
// ========================================
import { lazy, Suspense } from 'react';

// Loading component
const PageLoading = () => (
  <div className="flex items-center justify-center h-64">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    <span className="ml-3 text-gray-600">Carregando...</span>
  </div>
);

// Tremor Professional Pages (No MUI)
const TremorDashboard = lazy(() => import('./pages/tremor/TremorDashboard'));
const TremorRealtime = lazy(() => import('./pages/tremor/TremorRealtime'));
const TremorAlarms = lazy(() => import('./pages/tremor/TremorAlarms'));
const TremorAnalytics = lazy(() => import('./pages/tremor/TremorAnalytics'));
const TremorSettings = lazy(() => import('./pages/tremor/TremorSettings'));
const TremorExecutive = lazy(() => import('./pages/tremor/TremorExecutive'));
const TremorOEE = lazy(() => import('./pages/tremor/TremorOEE'));
const TremorEnergy = lazy(() => import('./pages/tremor/TremorEnergy'));
const TremorReports = lazy(() => import('./pages/tremor/TremorReports'));
const TremorMonitoring = lazy(() => import('./pages/tremor/TremorMonitoring'));
const TremorHistory = lazy(() => import('./pages/tremor/TremorHistory'));
const TremorQuality = lazy(() => import('./pages/tremor/TremorQuality'));
const TremorMaintenance = lazy(() => import('./pages/tremor/TremorMaintenance'));
const TremorAssetFramework = lazy(() => import('./pages/tremor/TremorAssetFramework'));
const TremorDashboardsList = lazy(() => import('./pages/tremor/TremorDashboardsList'));
const TremorDashboardBuilder = lazy(() => import('./pages/tremor/TremorDashboardBuilder'));
const TremorDashboardView = lazy(() => import('./pages/tremor/TremorDashboardView'));
const TremorTagDetails = lazy(() => import('./pages/tremor/TremorTagDetails'));

// Placeholder for pages that need to be migrated
function ComingSoonPage({ title }: { title: string }) {
  return (
    <div className="p-8 text-center bg-white rounded-lg shadow-sm">
      <h2 className="text-xl font-bold text-gray-700">🚧 {title}</h2>
      <p className="text-gray-500 mt-2">Esta funcionalidade está sendo migrada para a nova versão.</p>
      <p className="text-sm text-gray-400 mt-4">Em breve disponível com novos recursos.</p>
    </div>
  );
}

function AppContent() {
  const { currentAlarm, acknowledgeAlarm, dismissAlarm } = useCriticalAlarms();

  // Aplica cores suaves nos gráficos (força override de estilos inline)
  useChartColors();

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
      {/* Floating AI Chat - disponível em todas as telas */}
      <FloatingAIChat />
      <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <Routes>
          {/* Public */}
          <Route path="/login" element={<LoginPage />} />

          {/* Private - Protected Routes */}
          <Route
            path="/"
            element={
              <PrivateRoute>
                <SimplifiedLayoutNoMui />
              </PrivateRoute>
            }
          >
            {/* Dashboard - Tremor Professional */}
            <Route index element={<Suspense fallback={<PageLoading />}><TremorDashboard /></Suspense>} />
            <Route path="dashboard" element={<Suspense fallback={<PageLoading />}><TremorDashboard /></Suspense>} />
            <Route path="dashboard/executive" element={<Suspense fallback={<PageLoading />}><TremorExecutive /></Suspense>} />
            <Route path="dashboards" element={<Suspense fallback={<PageLoading />}><TremorDashboardsList /></Suspense>} />
            <Route path="dashboards/builder" element={<Suspense fallback={<PageLoading />}><TremorDashboardBuilder /></Suspense>} />
            <Route path="dashboards/new" element={<Suspense fallback={<PageLoading />}><TremorDashboardBuilder /></Suspense>} />
            <Route path="dashboards/:id" element={<Suspense fallback={<PageLoading />}><TremorDashboardView /></Suspense>} />

            {/* Real-time - Tremor Professional */}
            <Route path="realtime" element={<Suspense fallback={<PageLoading />}><TremorRealtime /></Suspense>} />
            <Route path="realtime/tags/:id" element={<Suspense fallback={<PageLoading />}><TremorTagDetails /></Suspense>} />

            {/* Alarms - Tremor Professional */}
            <Route path="alarms" element={<Suspense fallback={<PageLoading />}><TremorAlarms /></Suspense>} />
            <Route path="alarms/*" element={<Suspense fallback={<PageLoading />}><TremorAlarms /></Suspense>} />

            {/* Analytics - Tremor Professional */}
            <Route path="analytics" element={<Suspense fallback={<PageLoading />}><TremorAnalytics /></Suspense>} />
            <Route path="analytics/chat" element={<ComingSoonPage title="AI Chat" />} />

            {/* Settings - Tremor Professional */}
            <Route path="settings" element={<Suspense fallback={<PageLoading />}><TremorSettings /></Suspense>} />

            {/* Reports - Tremor Professional */}
            <Route path="reports" element={<Suspense fallback={<PageLoading />}><TremorReports /></Suspense>} />

            {/* Executive routes - Tremor Professional */}
            <Route path="executive" element={<Suspense fallback={<PageLoading />}><TremorExecutive /></Suspense>} />
            <Route path="executive/overview" element={<Suspense fallback={<PageLoading />}><TremorExecutive /></Suspense>} />
            <Route path="executive/analytics" element={<Suspense fallback={<PageLoading />}><TremorAnalytics /></Suspense>} />
            <Route path="executive/oee" element={<Suspense fallback={<PageLoading />}><TremorOEE /></Suspense>} />
            <Route path="executive/energy" element={<Suspense fallback={<PageLoading />}><TremorEnergy /></Suspense>} />
            <Route path="executive/reports" element={<Suspense fallback={<PageLoading />}><TremorReports /></Suspense>} />
            <Route path="executive/quality" element={<Suspense fallback={<PageLoading />}><TremorQuality /></Suspense>} />
            <Route path="quality" element={<Suspense fallback={<PageLoading />}><TremorQuality /></Suspense>} />

            {/* Monitoring routes - Tremor Professional */}
            <Route path="monitoring" element={<Suspense fallback={<PageLoading />}><TremorMonitoring /></Suspense>} />
            <Route path="monitoring/supervision" element={<Suspense fallback={<PageLoading />}><TremorMonitoring /></Suspense>} />
            <Route path="monitoring/trends" element={<Suspense fallback={<PageLoading />}><TremorMonitoring /></Suspense>} />
            <Route path="monitoring/history" element={<Suspense fallback={<PageLoading />}><TremorHistory /></Suspense>} />
            <Route path="history" element={<Suspense fallback={<PageLoading />}><TremorHistory /></Suspense>} />

            {/* Maintenance - PCM Dashboard with tab routing */}
            <Route path="maintenance" element={<Suspense fallback={<PageLoading />}><TremorMaintenance /></Suspense>} />
            <Route path="maintenance/pcm" element={<Suspense fallback={<PageLoading />}><TremorMaintenance /></Suspense>} />
            <Route path="maintenance/kpis" element={<Suspense fallback={<PageLoading />}><TremorMaintenance /></Suspense>} />
            <Route path="maintenance/backlog" element={<Suspense fallback={<PageLoading />}><TremorMaintenance /></Suspense>} />
            <Route path="maintenance/analysis" element={<Suspense fallback={<PageLoading />}><TremorMaintenance /></Suspense>} />

            {/* Asset Framework - PI Asset Framework style */}
            <Route path="assets" element={<Suspense fallback={<PageLoading />}><TremorAssetFramework /></Suspense>} />
            <Route path="assets/framework" element={<Suspense fallback={<PageLoading />}><TremorAssetFramework /></Suspense>} />

            {/* Legacy redirects */}
            <Route path="operations" element={<Navigate to="/dashboard" replace />} />
            <Route path="operations/*" element={<Navigate to="/dashboard" replace />} />
            <Route path="engineering" element={<Navigate to="/settings" replace />} />
            <Route path="config" element={<Navigate to="/settings" replace />} />
            <Route path="config/*" element={<Navigate to="/settings" replace />} />
            <Route path="tags" element={<Navigate to="/realtime" replace />} />
            <Route path="tags/:id" element={<Suspense fallback={<PageLoading />}><TremorTagDetails /></Suspense>} />
            <Route path="chat" element={<ComingSoonPage title="AI Chat" />} />
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
