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
import React, { useEffect } from 'react';
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
import { tagDataSimulator } from './services/tagDataSimulator';
import { simulatorDataSync } from './services/simulatorDataSync';
import { websocketService } from './services/websocket';

// ========================================
// 📊 CORE PAGES (5 principais)
// ========================================
import { ModernDashboard } from './pages/ModernDashboard';
import { ProfessionalDashboard } from './pages/ProfessionalDashboard';
import { ProfessionalAnalytics } from './pages/ProfessionalAnalytics';
import { ProfessionalRealtime } from './pages/ProfessionalRealtime';
import { ProfessionalAlarms } from './pages/ProfessionalAlarms';
import RealtimeTagPage from './pages/RealtimeTagPage';
import { ModernAlarmsPage } from './pages/ModernAlarmsPage';
import { AnalyticsHub } from './pages/AnalyticsHub';
import { SettingsPage } from './pages/SettingsPage';

// ========================================
// 🔧 SUPPORT PAGES (detalhes e configs)
// ========================================
import { TagDetailsPage } from './pages/TagDetailsPage';
import { ExtendedTagsPage } from './pages/ExtendedTagsPage';
import { ChatPage } from './pages/ChatPage';
import { DevicesPage } from './pages/DevicesPage';
import { TagsPage } from './pages/TagsPage';
import { GatewayManagementPage } from './pages/GatewayManagementPage';
import DashboardsList from './pages/DashboardsList';
import DashboardBuilder from './pages/DashboardBuilder';
import SimulatorPage from './pages/SimulatorPage';
import DashboardBuilderPage from './pages/DashboardBuilderPage';
import ExecutiveDashboard from './pages/ExecutiveDashboard';
import { AIMonitoringDashboard } from './pages/AIMonitoringDashboard';
import { TagConfiguration } from './pages/TagConfiguration';
import { ReportsDashboard } from './pages/ReportsDashboard';

function App() {
  // 🚀 Start simulator and WebSocket on app initialization
  useEffect(() => {
    console.log('🚀 Starting Grain Terminal Simulator...');
    tagDataSimulator.start();

    // Connect to real-time WebSocket server
    const wsUrl = 'ws://localhost:8000/api/v1/ws/simulator/stream';
    console.log('🔌 Connecting to WebSocket:', wsUrl);
    websocketService.connect(wsUrl);

    // Start syncing data to backend after 2 seconds (let simulator stabilize)
    const syncTimeout = setTimeout(() => {
      console.log('🔄 Starting data sync to backend...');
      simulatorDataSync.start();
    }, 2000);

    return () => {
      clearTimeout(syncTimeout);
      console.log('⏹️ Stopping Grain Terminal Simulator...');
      websocketService.disconnect();
      simulatorDataSync.stop();
      tagDataSimulator.stop();
    };
  }, []);

  return (
    <ErrorBoundary>
      <Provider store={store}>
        <ThemeProvider>
          <MuiThemeWrapper>
            <AssetProvider>
              <Toaster />
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
                  <Route path="dashboards" element={<DashboardsList />} />
                  <Route path="dashboards/:id" element={<DashboardBuilder />} />
                  <Route path="dashboards/:id/edit" element={<DashboardBuilder />} />

                  {/* ========================================
                      ⚡ MODULE 2: REAL-TIME (Tags & Trends)
                      ======================================== */}
                  <Route path="realtime" element={<ProfessionalRealtime />} />
                  <Route path="realtime/classic" element={<RealtimeTagPage />} />
                  <Route path="realtime/tags" element={<ExtendedTagsPage />} />
                  <Route path="realtime/tags/:id" element={<TagDetailsPage />} />

                  {/* ========================================
                      🚨 MODULE 3: ALARMS (Events & History)
                      ======================================== */}
                  <Route path="alarms" element={<ProfessionalAlarms />} />
                  <Route path="alarms/classic" element={<ModernAlarmsPage />} />
                  <Route path="alarms/active" element={<ProfessionalAlarms />} />
                  <Route path="alarms/history" element={<ProfessionalAlarms />} />

                  {/* ========================================
                      🤖 MODULE 4: ANALYTICS (ML Insights)
                      ======================================== */}
                  <Route path="analytics" element={<ProfessionalAnalytics />} />
                  <Route path="analytics/classic" element={<AnalyticsHub />} />
                  <Route path="analytics/ml-insights" element={<ProfessionalAnalytics />} />
                  <Route path="analytics/ai-monitoring" element={<AIMonitoringDashboard />} />
                  <Route path="analytics/chat" element={<ChatPage />} />

                  {/* ========================================
                      ⚙️ MODULE 5: SETTINGS (Configuration)
                      ======================================== */}
                  <Route path="settings" element={<SettingsPage />} />
                  <Route path="settings/devices" element={<DevicesPage />} />
                  <Route path="settings/tags" element={<TagsPage />} />
                  <Route path="settings/tag-configuration" element={<TagConfiguration />} />
                  <Route path="settings/gateways" element={<GatewayManagementPage />} />
                  <Route path="settings/users" element={<SettingsPage />} />

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
                  <Route path="devices" element={<Navigate to="/settings/devices" replace />} />
                  <Route path="gateways" element={<Navigate to="/settings/gateways" replace />} />
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
                  <Route path="dashboard-builder" element={<Navigate to="/dashboard" replace />} />
                  <Route path="classic-dashboard" element={<Navigate to="/dashboard" replace />} />
                </Route>

                {/* ========================================
                    🚫 404 HANDLER
                    ======================================== */}
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </BrowserRouter>
          </AssetProvider>
          </MuiThemeWrapper>
        </ThemeProvider>
      </Provider>
    </ErrorBoundary>
  );
}

export default App;
