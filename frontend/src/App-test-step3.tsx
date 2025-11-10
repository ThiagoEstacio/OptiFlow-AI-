/**
 * App Test Step 3 - Add Toaster and basic Routes (LoginPage only)
 */
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Provider } from 'react-redux';
import { store } from './store';
import { ThemeProvider } from './contexts/ThemeContext';
import { AssetProvider } from './contexts/AssetContext';
import { Toaster } from './components/Toast/Toaster';
import { LoginPage } from './pages/LoginPage';

function AppTestStep3() {
  return (
    <Provider store={store}>
      <ThemeProvider>
        <AssetProvider>
          <Toaster />
          <BrowserRouter>
            <Routes>
              {/* Test just login page */}
              <Route path="/login" element={<LoginPage />} />

              {/* Temporary landing for testing */}
              <Route path="/" element={
                <div style={{
                  padding: '50px',
                  fontFamily: 'Arial',
                  backgroundColor: '#e8f5e9',
                  minHeight: '100vh'
                }}>
                  <h1 style={{ color: '#2e7d32' }}>✅ Teste Step 3: Routes + Toaster</h1>
                  <div style={{
                    marginTop: '30px',
                    padding: '20px',
                    backgroundColor: 'white',
                    borderRadius: '8px'
                  }}>
                    <h2>Status</h2>
                    <ul>
                      <li>✅ React: OK</li>
                      <li>✅ Redux Provider: OK</li>
                      <li>✅ BrowserRouter: OK</li>
                      <li>✅ ThemeProvider: OK</li>
                      <li>✅ AssetProvider: OK</li>
                      <li>✅ Toaster: OK</li>
                      <li>✅ Routes: OK</li>
                    </ul>
                    <p style={{ marginTop: '20px' }}>
                      <a href="/login" style={{ color: '#1976d2', textDecoration: 'none', fontWeight: 'bold' }}>
                        → Testar página de Login
                      </a>
                    </p>
                  </div>
                </div>
              } />

              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </BrowserRouter>
        </AssetProvider>
      </ThemeProvider>
    </Provider>
  );
}

export default AppTestStep3;
