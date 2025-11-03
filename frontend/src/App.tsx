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
import { ExecutiveDashboard } from './components/ExecutiveDashboard';
import { AssetHealthDashboard } from './pages/AssetHealthDashboard';
import { HealthTrendsPage } from './pages/HealthTrendsPage';
import { AnalyticsHub } from './pages/AnalyticsHub';
import { AssetHealthHub } from './pages/AssetHealthHub';
import { Toaster } from './components/Toast/Toaster';
import { ThemeProvider } from './contexts/ThemeContext';
import { AssetProvider } from './contexts/AssetContext';

function App() {
  return (
    <Provider store={store}>
      <ThemeProvider>
        <AssetProvider>
          <Toaster />
          <BrowserRouter>
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
              <Route index element={<Dashboard />} />
              <Route path="sites" element={<SitesPage />} />
              <Route path="devices" element={<DevicesPage />} />
              <Route path="tags" element={<TagsPage />} />
              <Route path="tags/:id" element={<TagDetailsPage />} />
              <Route path="alarms" element={<AlarmsPage />} />

              {/* Consolidated Analytics Hub */}
              <Route path="analytics-hub" element={<AnalyticsHub />} />
              {/* Legacy redirects */}
              <Route path="analytics" element={<Navigate to="/analytics-hub" replace />} />
              <Route path="ai-insights" element={<Navigate to="/analytics-hub" replace />} />

              {/* Consolidated Asset Health Hub */}
              <Route path="asset-health-hub" element={<AssetHealthHub />} />
              {/* Legacy redirects */}
              <Route path="asset-health" element={<Navigate to="/asset-health-hub" replace />} />
              <Route path="health-trends" element={<Navigate to="/asset-health-hub" replace />} />

              <Route path="dashboard-builder" element={<DashboardBuilderPage />} />
              <Route path="chat" element={<ChatPage />} />
              <Route path="simulator" element={<SimulatorPage />} />
              <Route path="simulador" element={<SimulatorPage />} />
              <Route path="admin" element={<AdminPage />} />
              <Route path="executive" element={<ExecutiveDashboard />} />
              <Route path="executivo" element={<ExecutiveDashboard />} />
              <Route path="settings" element={<SettingsPage />} />
            </Route>

            {/* Redirect unknown routes */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
        </AssetProvider>
      </ThemeProvider>
    </Provider>
  );
}

export default App;
