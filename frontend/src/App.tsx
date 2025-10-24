/**
 * OptiFlow AI Platform - Main Application
 */
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { MainLayout } from './components/layout/MainLayout';
import { DashboardPage } from './pages/DashboardPage';
import { LoginPage } from './pages/LoginPage';
import { useAuth } from './hooks/useAuth';
import { LoadingSpinner } from './components/common/LoadingSpinner';

// Protected Route Component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" text="Loading..." />
      </div>
    );
  }

  return isAuthenticated ? <>{children}</> : <Navigate to="/login" />;
};

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route
          path="/"
          element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<DashboardPage />} />

          {/* Placeholder routes - to be implemented */}
          <Route path="realtime" element={<DashboardPage />} />
          <Route path="analytics" element={<DashboardPage />} />
          <Route path="export" element={<div className="text-center p-8"><h2 className="text-2xl font-semibold">Data Export</h2><p className="text-gray-600 mt-2">Export functionality coming soon</p></div>} />
          <Route path="annotations" element={<div className="text-center p-8"><h2 className="text-2xl font-semibold">Annotations</h2><p className="text-gray-600 mt-2">Collaboration features coming soon</p></div>} />
          <Route path="devices" element={<div className="text-center p-8"><h2 className="text-2xl font-semibold">Devices</h2><p className="text-gray-600 mt-2">Device management coming soon</p></div>} />
          <Route path="settings" element={<div className="text-center p-8"><h2 className="text-2xl font-semibold">Settings</h2><p className="text-gray-600 mt-2">Settings coming soon</p></div>} />
        </Route>

        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Router>
  );
}

export default App;
