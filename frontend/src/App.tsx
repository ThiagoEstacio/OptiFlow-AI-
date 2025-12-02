/**
 * 🎯 OptiFlow AI - App Simplificado e Focado
 * ==========================================
 * 
 * Estrutura limpa com 5 módulos principais:
 * 1. Dashboard - Overview e KPIs
 * 2. Real-time - Tags e Trends ao vivo
 * 3. Alarms - Sistema de alarmes e eventos
 * 4. Analytics - Insights de ML e análises
 * 5. Settings - Configurações e admin
 */
import React, { useEffect, Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Provider } from 'react-redux';
import { store } from './store';
import { PrivateRoute } from './components/PrivateRoute';
import { SimplifiedLayout } from './components/Layout/SimplifiedLayout';
import { LoginPage } from './pages/LoginPage';
import { Toaster } from './components/Toast/Toaster';
import { ErrorBoundary } from './components/ErrorBoundary';
import { ThemeProvider } from './contexts/ThemeContext';
import { MuiThemeWrapper } from './components/professional/MuiThemeWrapper';
import { AssetProvider } from './contexts/AssetContext';
import { websocketService } from './services/websocket';
import { CriticalAlarmNotification } from './components/CriticalAlarmNotification';
import { useCriticalAlarms } from './hooks/useCriticalAlarms';
import FloatingChat from './components/FloatingChat';

// ========================================
// 📊 CORE PAGES (5 principais)
// ========================================
import { ModernDashboard } from './pages/ModernDashboard';
import { ProfessionalDashboard } from './pages/ProfessionalDashboard';
import { ProfessionalAnalytics } from './pages/ProfessionalAnalytics';
import { MLAnalyticsDashboard } from './pages/MLAnalyticsDashboard';
import { ProfessionalRealtime } from './pages/ProfessionalRealtime';
import { ProfessionalAlarms } from './pages/ProfessionalAlarms';
import RealtimeTagPage from './pages/RealtimeTagPage';
import RealtimeTagsMonitor from './pages/RealtimeTagsMonitor';
import EquipmentStatistics from './pages/EquipmentStatistics';
import { ModernAlarmsPage } from './pages/ModernAlarmsPage';
import { AnalyticsHub } from './pages/AnalyticsHub';
import { SettingsPage } from './pages/SettingsPage';

// ========================================
// 🔧 SUPPORT PAGES (detalhes e configs)
// ========================================
import { TagDetailsPage } from './pages/TagDetailsPage';
import { ExtendedTagsPage } from './pages/ExtendedTagsPage';
import { ChatPage } from './pages/ChatPage';
// DevicesPage, TagsPage, GatewayManagementPage removed - managed via Gateway UI at localhost:8080/ui/
import DashboardsList from './pages/DashboardsList';
// Lazy load DashboardBuilder to avoid react-grid-layout initialization issues
const DashboardBuilder = lazy(() => import('./pages/DashboardBuilder'));
import SimulatorPage from './pages/SimulatorPage';
import DashboardBuilderPage from './pages/DashboardBuilderPage';
import ExecutiveDashboard from './pages/ExecutiveDashboard';
import { AIMonitoringDashboard } from './pages/AIMonitoringDashboard';
// TagConfiguration removed - managed via Gateway UI at localhost:8080/ui/
import { ReportsDashboard } from './pages/ReportsDashboard';
import { TagHistoricalTrends } from './pages/TagHistoricalTrends';
// GatewayEdgePage removed - using external Gateway UI at localhost:8080/ui/

function App() {
  // PDCA #5: Critical alarm notification system
  const { currentAlarm, acknowledgeAlarm, dismissAlarm } = useCriticalAlarms();

  // 🚀 Connect to WebSocket on app initialization
  useEffect(() => {
    // Connect to real-time WebSocket server
    const wsUrl = 'ws://localhost:8000/api/v1/ws/simulator/stream';
    console.log('🔌 Connecting to WebSocket:', wsUrl);
    websocketService.connect(wsUrl);

    return () => {
      websocketService.disconnect();
    };
  }, []);

  return (
    <ErrorBoundary>
      <Provider store={store}>
        <ThemeProvider>
          <MuiThemeWrapper>
            <AssetProvider>
              <Toaster />
              {/* PDCA #5: Critical alarm notification overlay */}
              <CriticalAlarmNotification
                alarm={currentAlarm}
                onAcknowledge={acknowledgeAlarm}
                onClose={dismissAlarm}
              />
              <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
                <Routes>
                {/* ========================================
                    🔓 PUBLIC ROUTES
                    ======================================== */}
                <Route path="/login" element={<LoginPage />} />

                {/* ========================================
                    🔐 PRIVATE ROUTES
                    ======================================== */}
                <Route
                  path="/"
                  element={
                    <PrivateRoute>
                      <SimplifiedLayout />
                    </PrivateRoute>
                  }
                >
                  {/* ========================================
                      📊 MODULE 1: DASHBOARD (Overview & KPIs)
                      ======================================== */}
                  <Route index element={<ProfessionalDashboard />} />
                  <Route path="dashboard" element={<ProfessionalDashboard />} />
                  <Route path="dashboard/classic" element={<ModernDashboard />} />
                  <Route path="dashboard/executive" element={<ExecutiveDashboard />} />
                  <Route path="dashboards" element={<DashboardsList />} />
                  <Route path="dashboards/builder" element={<DashboardBuilderPage />} />
                  <Route path="dashboards/new" element={<Suspense fallback={<div>Loading...</div>}><DashboardBuilder /></Suspense>} />
                  <Route path="dashboards/:id" element={<Suspense fallback={<div>Loading...</div>}><DashboardBuilder /></Suspense>} />
                  <Route path="dashboards/:id/edit" element={<Suspense fallback={<div>Loading...</div>}><DashboardBuilder /></Suspense>} />

                  {/* ========================================
                      ⚡ MODULE 2: REAL-TIME (Tags & Trends)
                      ======================================== */}
                  <Route path="realtime" element={<ProfessionalRealtime />} />
                  <Route path="realtime/classic" element={<RealtimeTagPage />} />
                  <Route path="realtime/tags" element={<RealtimeTagsMonitor />} />
                  <Route path="realtime/tags/:id" element={<TagDetailsPage />} />
                  <Route path="realtime/extended" element={<ExtendedTagsPage />} />
                  <Route path="realtime/trends" element={<TagHistoricalTrends />} />

                  {/* ========================================
                      🚨 MODULE 3: ALARMS (Events & History)
                      ======================================== */}
                  <Route path="alarms" element={<ModernAlarmsPage />} />
                  <Route path="alarms/active" element={<ModernAlarmsPage />} />
                  <Route path="alarms/history" element={<ModernAlarmsPage />} />
                  <Route path="alarms/statistics" element={<ModernAlarmsPage />} />
                  <Route path="alarms/professional" element={<ProfessionalAlarms />} />

                  {/* ========================================
                      🤖 MODULE 4: ANALYTICS (ML Insights)
                      ======================================== */}
                  <Route path="analytics" element={<MLAnalyticsDashboard />} />
                  <Route path="analytics/statistics" element={<EquipmentStatistics />} />
                  <Route path="analytics/hub" element={<AnalyticsHub />} />
                  <Route path="analytics/ml-insights" element={<MLAnalyticsDashboard />} />
                  <Route path="analytics/professional" element={<ProfessionalAnalytics />} />
                  <Route path="analytics/ai-monitoring" element={<AIMonitoringDashboard />} />
                  <Route path="analytics/chat" element={<ChatPage />} />

                  {/* ========================================
                      ⚙️ MODULE 5: SETTINGS (User Preferences Only)
                      Device/Tag config moved to Gateway UI
                      ======================================== */}
                  <Route path="settings" element={<SettingsPage />} />

                  {/* ========================================
                      📊 MODULE 6: REPORTS (Export & Download)
                      ======================================== */}
                  <Route path="reports" element={<ReportsDashboard />} />

                  {/* ========================================
                      🔀 LEGACY REDIRECTS (backward compatibility)
                      ======================================== */}
                  <Route path="operations" element={<Navigate to="/dashboard" replace />} />
                  <Route path="operations/scada" element={<Navigate to="/realtime" replace />} />
                  <Route path="operations/overview" element={<Navigate to="/dashboard" replace />} />
                  <Route path="maintenance" element={<Navigate to="/analytics" replace />} />
                  <Route path="engineering" element={<Navigate to="/settings" replace />} />
                  <Route path="config" element={<Navigate to="/settings" replace />} />
                  <Route path="config/*" element={<Navigate to="/settings" replace />} />
                  <Route path="insights" element={<Navigate to="/analytics" replace />} />
                  <Route path="ml-insights" element={<Navigate to="/analytics" replace />} />
                  <Route path="data/realtime" element={<Navigate to="/realtime" replace />} />
                  <Route path="data/alarms-events" element={<Navigate to="/alarms" replace />} />
                  <Route path="tags" element={<Navigate to="/realtime/tags" replace />} />
                  <Route path="tags/:id" element={<TagDetailsPage />} />
                  <Route path="ai-insights" element={<Navigate to="/analytics" replace />} />
                  <Route path="chat" element={<ChatPage />} />
                  
                  {/* Obsolete/unused pages redirects */}
                  <Route path="simulator" element={<Navigate to="/settings" replace />} />
                  <Route path="simulador" element={<Navigate to="/settings" replace />} />
                  <Route path="sites" element={<Navigate to="/settings" replace />} />
                  <Route path="devices" element={<Navigate to="/settings" replace />} />
                  <Route path="settings/devices" element={<Navigate to="/settings" replace />} />
                  <Route path="settings/tags" element={<Navigate to="/settings" replace />} />
                  <Route path="settings/tag-configuration" element={<Navigate to="/settings" replace />} />
                  <Route path="settings/users" element={<Navigate to="/settings" replace />} />
                  <Route path="gateways" element={<Navigate to="/settings" replace />} />
                  <Route path="settings/gateways" element={<Navigate to="/settings" replace />} />
                  <Route path="gateway-edge" element={<Navigate to="/settings" replace />} />
                  <Route path="gateway-edge/*" element={<Navigate to="/settings" replace />} />
                  <Route path="admin" element={<Navigate to="/settings" replace />} />
                  <Route path="quality" element={<Navigate to="/analytics" replace />} />
                  <Route path="executive/:siteId" element={<Navigate to="/dashboard" replace />} />
                  <Route path="gbm-import/:siteId" element={<Navigate to="/analytics" replace />} />
                  <Route path="gbm-insights/:siteId" element={<Navigate to="/analytics" replace />} />
                  <Route path="historical-trends/:siteId" element={<Navigate to="/analytics" replace />} />
                  <Route path="analytics-hub" element={<Navigate to="/analytics" replace />} />
                  <Route path="asset-health-hub" element={<Navigate to="/analytics" replace />} />
                  <Route path="asset-health" element={<Navigate to="/analytics" replace />} />
                  <Route path="health-trends" element={<Navigate to="/analytics" replace />} />
                  <Route path="dashboard-builder" element={<Navigate to="/dashboards/builder" replace />} />
                  <Route path="classic-dashboard" element={<Navigate to="/dashboard" replace />} />
                </Route>

                {/* ========================================
                    🚫 404 HANDLER
                    ======================================== */}
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </BrowserRouter>
              {/* 🤖 Floating AI Chat - disponível em toda aplicação */}
              <FloatingChat />
          </AssetProvider>
          </MuiThemeWrapper>
        </ThemeProvider>
      </Provider>
    </ErrorBoundary>
  );
}

export default App;
