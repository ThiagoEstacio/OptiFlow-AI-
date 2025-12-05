/**
 * App Test Step 3.5 - Login + SimplifiedLayout + MuiThemeWrapper
 * Testando componentes intermediários
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
import { MuiThemeWrapper } from './components/professional/MuiThemeWrapper';

// Simple test dashboard
function TestDashboard() {
  return (
    <div style={{ padding: '40px' }}>
      <h1>✅ Step 3.5: Layout + MUI funcionando!</h1>
      <p>Se você vê isso, SimplifiedLayout e MuiThemeWrapper estão OK.</p>
    </div>
  );
}

function App() {
  return (
    <Provider store={store}>
      <ThemeProvider>
        <MuiThemeWrapper>
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
        </MuiThemeWrapper>
      </ThemeProvider>
    </Provider>
  );
}

export default App;
