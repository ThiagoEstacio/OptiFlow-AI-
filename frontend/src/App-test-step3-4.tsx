/**
 * App Test Step 3.4 - Login + SimplifiedLayout (SEM MuiThemeWrapper)
 * Testando se o problema é o MUI/Emotion
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
import { SimplifiedLayout } from './components/Layout/SimplifiedLayout';
// REMOVED: MuiThemeWrapper - testing if this is the issue

// Simple test dashboard
function TestDashboard() {
  return (
    <div style={{ padding: '40px', backgroundColor: '#f5f5f5', minHeight: '100vh' }}>
      <h1 style={{ color: '#1976d2' }}>✅ Step 3.4: Layout funcionando!</h1>
      <p>Se você vê isso, SimplifiedLayout está OK (sem MUI).</p>
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
                    <SimplifiedLayout />
                  </PrivateRoute>
                }
              >
                <Route index element={<TestDashboard />} />
                <Route path="*" element={<TestDashboard />} />
              </Route>
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </BrowserRouter>
        </AssetProvider>
      </ThemeProvider>
    </Provider>
  );
}

export default App;
