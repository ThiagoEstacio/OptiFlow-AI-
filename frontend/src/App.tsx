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
import { Toaster } from './components/Toast/Toaster';
import { ThemeProvider } from './contexts/ThemeContext';

function App() {
  return (
    <Provider store={store}>
      <ThemeProvider>
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
              <Route path="analytics" element={<AnalyticsPage />} />
              <Route path="dashboard-builder" element={<DashboardBuilderPage />} />
              <Route path="settings" element={<SettingsPage />} />
            </Route>

            {/* Redirect unknown routes */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </ThemeProvider>
    </Provider>
  );
}

export default App;
