/**
 * App Test Step 3.3 - Apenas PrivateRoute (sem SimplifiedLayout)
 */
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Provider } from 'react-redux';
import { store } from './store';
import { ThemeProvider } from './contexts/ThemeContext';
import { AssetProvider } from './contexts/AssetContext';
import { Toaster } from './components/Toast/Toaster';
import { LoginPage } from './pages/LoginPage';
import { PrivateRoute } from './components/PrivateRoute';
// REMOVED: SimplifiedLayout

// Simple test dashboard
function TestDashboard() {
  return (
    <div style={{ padding: '40px', backgroundColor: '#e8f5e9', minHeight: '100vh' }}>
      <h1 style={{ color: '#2e7d32' }}>✅ Step 3.3: PrivateRoute funcionando!</h1>
      <p>Se você vê isso após login, PrivateRoute está OK.</p>
      <p>Você está autenticado!</p>
    </div>
  );
}

function App() {
  return (
    <Provider store={store}>
      <ThemeProvider>
        <AssetProvider>
          <Toaster />
          <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route
                path="/"
                element={
                  <PrivateRoute>
                    <TestDashboard />
                  </PrivateRoute>
                }
              />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </BrowserRouter>
        </AssetProvider>
      </ThemeProvider>
    </Provider>
  );
}

export default App;
