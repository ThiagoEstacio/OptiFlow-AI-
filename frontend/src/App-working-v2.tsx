/**
 * 🎯 OptiFlow AI - Working App v2 (Minimal pages, no lazy load)
 * ==============================================================
 *
 * Versão funcional com páginas simples inline
 */
import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, Link } from 'react-router-dom';
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

// Simple inline pages (no MUI)
function DashboardPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">📊 Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm text-gray-500">Tags Ativos</h3>
          <p className="text-3xl font-bold text-blue-600">156</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm text-gray-500">Alarmes Ativos</h3>
          <p className="text-3xl font-bold text-red-600">3</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm text-gray-500">Uptime</h3>
          <p className="text-3xl font-bold text-green-600">99.8%</p>
        </div>
      </div>
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold mb-4">Navegação Rápida</h2>
        <div className="flex gap-4">
          <Link to="/realtime" className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
            Real-time
          </Link>
          <Link to="/alarms" className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600">
            Alarmes
          </Link>
          <Link to="/analytics" className="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600">
            Analytics
          </Link>
          <Link to="/settings" className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600">
            Configurações
          </Link>
        </div>
      </div>
    </div>
  );
}

function RealtimePage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">⚡ Monitoramento Real-time</h1>
      <div className="bg-white p-6 rounded-lg shadow">
        <p className="text-gray-600">Visualização de tags em tempo real.</p>
        <p className="text-sm text-gray-400 mt-2">Funcionalidade será expandida em breve.</p>
      </div>
    </div>
  );
}

function AlarmsPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">🚨 Central de Alarmes</h1>
      <div className="bg-white p-6 rounded-lg shadow">
        <p className="text-gray-600">Gerenciamento de alarmes e eventos.</p>
        <div className="mt-4 space-y-2">
          <div className="p-3 bg-red-50 border-l-4 border-red-500 rounded">
            <span className="font-medium text-red-700">Alta Temperatura - Silo 1</span>
          </div>
          <div className="p-3 bg-yellow-50 border-l-4 border-yellow-500 rounded">
            <span className="font-medium text-yellow-700">Nível Baixo - Tanque 3</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function AnalyticsPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">🤖 Analytics & ML</h1>
      <div className="bg-white p-6 rounded-lg shadow">
        <p className="text-gray-600">Insights de Machine Learning e análises preditivas.</p>
      </div>
    </div>
  );
}

function SettingsPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">⚙️ Configurações</h1>
      <div className="bg-white p-6 rounded-lg shadow">
        <p className="text-gray-600">Configurações do sistema.</p>
      </div>
    </div>
  );
}

function AppContent() {
  useEffect(() => {
    const wsUrl = 'ws://localhost:8000/api/v1/ws/simulator/stream';
    console.log('🔌 Connecting to WebSocket:', wsUrl);
    websocketService.connect(wsUrl);
    return () => websocketService.disconnect();
  }, []);

  return (
    <>
      <Toaster />
      <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />

          <Route
            path="/"
            element={
              <PrivateRoute>
                <SimplifiedLayoutNoMui />
              </PrivateRoute>
            }
          >
            <Route index element={<DashboardPage />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="dashboard/*" element={<DashboardPage />} />
            <Route path="realtime" element={<RealtimePage />} />
            <Route path="realtime/*" element={<RealtimePage />} />
            <Route path="alarms" element={<AlarmsPage />} />
            <Route path="alarms/*" element={<AlarmsPage />} />
            <Route path="analytics" element={<AnalyticsPage />} />
            <Route path="analytics/*" element={<AnalyticsPage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="reports" element={<AnalyticsPage />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Route>

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
