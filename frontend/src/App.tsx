/**
 * Main App Component with Routing
 */
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Provider } from 'react-redux';
import { store } from './store';
import { PrivateRoute } from './components/PrivateRoute';
import { AppLayout } from './components/Layout/AppLayout';
import { LoginPage } from './pages/LoginPage';
import { Dashboard } from './pages/Dashboard';
import { ModernDashboard } from './pages/ModernDashboard';
import { SitesPage } from './pages/SitesPage';
import { DevicesPage } from './pages/DevicesPage';
import { TagsPage } from './pages/TagsPage';
import { AlarmsPage } from './pages/AlarmsPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { TagDetailsPage } from './pages/TagDetailsPage';
import { SettingsPage } from './pages/SettingsPage';
import { DashboardBuilderPage } from './pages/DashboardBuilderPage';
import { AIInsightsPage } from './pages/AIInsightsPage';
import { ChatPage } from './pages/ChatPage';
import SimulatorPage from './pages/SimulatorPage';
import AdminPage from './pages/AdminPage';
import ExecutiveDashboard from './pages/ExecutiveDashboard';
import GBMDataImport from './pages/GBMDataImport';
import GBMInsights from './pages/GBMInsights';
import HistoricalTrends from './pages/HistoricalTrends';
import { AssetHealthDashboard } from './pages/AssetHealthDashboard';
import { HealthTrendsPage } from './pages/HealthTrendsPage';
import { AnalyticsHub } from './pages/AnalyticsHub';
import { AssetHealthHub } from './pages/AssetHealthHub';
import { GatewayManagementPage } from './pages/GatewayManagementPage';
import { GatewayDetailsPage } from './pages/GatewayDetailsPage';
import { ExtendedTagsPage } from './pages/ExtendedTagsPage';
import RealtimeTagPage from './pages/RealtimeTagPage';
import SCADAPage from './pages/SCADAPage';
import OperationsHub from './pages/OperationsHub';
import MaintenanceHub from './pages/MaintenanceHub';
import EngineeringHub from './pages/EngineeringHub';
import ConfigurationHub from './pages/ConfigurationHub';
import SimulatorConfigPage from './pages/SimulatorConfigPage';
import InsightsPage from './pages/InsightsPage';
import MLInsightsDashboard from './pages/MLInsightsDashboard';
import RealTimeDataView from './pages/RealTimeDataView';
import AlarmsEventsView from './pages/AlarmsEventsView';
import HistoricalDataAnalysis from './pages/HistoricalDataAnalysis';
import MLModelExecutionView from './pages/MLModelExecutionView';
import QualityDashboard from './pages/QualityDashboard';
import { Toaster } from './components/Toast/Toaster';
import { ErrorBoundary } from './components/ErrorBoundary';
import { ThemeProvider } from './contexts/ThemeContext';
import { AssetProvider } from './contexts/AssetContext';

function App() {
  return (
    <ErrorBoundary>
      <Provider store={store}>
        <ThemeProvider>
          <AssetProvider>
            <Toaster />
            <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
            <Routes>
            {/* Public Routes */}
            <Route path="/login" element={<LoginPage />} />

            {/* Private Routes */}
            <Route
              path="/"
              element={
                <PrivateRoute>
                  <AppLayout />
                </PrivateRoute>
              }
            >
              {/* Home Dashboard */}
              <Route index element={<ModernDashboard />} />

              {/* OPERATIONS MODULE */}
              <Route path="operations" element={<OperationsHub />} />
              <Route path="operations/scada" element={<SCADAPage />} />
              <Route path="operations/overview" element={<ModernDashboard />} />

              {/* MAINTENANCE MODULE */}
              <Route path="maintenance" element={<MaintenanceHub />} />
              <Route path="maintenance/predictive" element={<AssetHealthHub />} />

              {/* ENGINEERING MODULE */}
              <Route path="engineering" element={<EngineeringHub />} />

              {/* AI INSIGHTS & ML DEMO */}
              <Route path="insights" element={<InsightsPage />} />
              <Route path="ml-insights" element={<MLInsightsDashboard />} />
              <Route path="data/realtime" element={<RealTimeDataView />} />
              <Route path="data/alarms-events" element={<AlarmsEventsView />} />
              <Route path="data/historical" element={<HistoricalDataAnalysis />} />
              <Route path="ml-demo" element={<MLModelExecutionView />} />

              {/* QUALITY MANAGEMENT */}
              <Route path="quality" element={<QualityDashboard />} />

              {/* EXECUTIVE MODULE */}
              <Route path="executive/:siteId" element={<ExecutiveDashboard />} />
              <Route path="gbm-import/:siteId" element={<GBMDataImport />} />
              <Route path="gbm-insights/:siteId" element={<GBMInsights />} />
              <Route path="historical-trends/:siteId" element={<HistoricalTrends />} />

              {/* CONFIGURATION MODULE */}
              <Route path="config" element={<ConfigurationHub />} />
              <Route path="config/simulator" element={<SimulatorConfigPage />} />
              <Route path="config/data-sources" element={<GatewayManagementPage />} />
              <Route path="config/tags" element={<TagsPage />} />
              <Route path="config/alarms" element={<AlarmsPage />} />
              <Route path="config/users" element={<SettingsPage />} />
              <Route path="admin" element={<AdminPage />} />

              {/* LEGACY ROUTES - Redirect to new structure */}
              <Route path="simulator" element={<Navigate to="/config/simulator" replace />} />
              <Route path="simulador" element={<Navigate to="/config/simulator" replace />} />
              <Route path="simulator/realtime" element={<Navigate to="/operations/scada" replace />} />
              <Route path="simulator/scada" element={<Navigate to="/operations/scada" replace />} />
              <Route path="asset-health-hub" element={<Navigate to="/maintenance/predictive" replace />} />
              <Route path="asset-health" element={<Navigate to="/maintenance/predictive" replace />} />
              <Route path="health-trends" element={<Navigate to="/maintenance/predictive" replace />} />
              <Route path="analytics-hub" element={<AnalyticsHub />} />
              <Route path="analytics" element={<Navigate to="/analytics-hub" replace />} />
              <Route path="ai-insights" element={<Navigate to="/analytics-hub" replace />} />
              <Route path="gateways" element={<Navigate to="/config/data-sources" replace />} />
              <Route path="gateways/:id" element={<GatewayDetailsPage />} />
              <Route path="tags" element={<Navigate to="/config/tags" replace />} />
              <Route path="tags/:id" element={<TagDetailsPage />} />
              <Route path="alarms" element={<Navigate to="/config/alarms" replace />} />
              <Route path="executivo/:siteId" element={<ExecutiveDashboard />} />

              {/* OTHER PAGES */}
              <Route path="sites" element={<SitesPage />} />
              <Route path="devices" element={<DevicesPage />} />
              <Route path="extended-tags" element={<ExtendedTagsPage />} />
              <Route path="dashboard-builder" element={<DashboardBuilderPage />} />
              <Route path="chat" element={<ChatPage />} />
              <Route path="settings" element={<SettingsPage />} />
              <Route path="classic-dashboard" element={<Dashboard />} />
            </Route>

            {/* Redirect unknown routes */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
          </AssetProvider>
        </ThemeProvider>
      </Provider>
    </ErrorBoundary>
  );
}

export default App;
