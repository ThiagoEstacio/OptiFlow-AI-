/**
 * App Test Step 3.4b - Login + SimplifiedLayoutNoMui (sem MUI/Emotion)
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
import { SimplifiedLayoutNoMui } from './components/Layout/SimplifiedLayoutNoMui';

// Simple test dashboard
function TestDashboard() {
  return (
    <div className="p-8 bg-green-50 rounded-lg">
      <h1 className="text-2xl font-bold text-green-700">✅ Step 3.4b: Layout sem MUI funcionando!</h1>
      <p className="mt-2 text-gray-600">SimplifiedLayoutNoMui + TopBar + Breadcrumbs estão OK.</p>
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
                    <SimplifiedLayoutNoMui />
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
