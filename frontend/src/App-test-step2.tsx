/**
 * App Test Step 2 - Add ThemeProvider and AssetProvider
 */
import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { Provider } from 'react-redux';
import { store } from './store';
import { ThemeProvider } from './contexts/ThemeContext';
import { AssetProvider } from './contexts/AssetContext';

function AppTestStep2() {
  return (
    <Provider store={store}>
      <ThemeProvider>
        <AssetProvider>
          <BrowserRouter>
            <div style={{
              padding: '50px',
              fontFamily: 'Arial',
              backgroundColor: '#fff3e0',
              minHeight: '100vh'
            }}>
              <h1 style={{ color: '#e65100' }}>✅ Teste Step 2: Contexts</h1>
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
                </ul>
                <p style={{ marginTop: '20px', color: '#666' }}>
                  Se você vê esta mensagem, todos os Providers estão funcionando.
                </p>
              </div>
            </div>
          </BrowserRouter>
        </AssetProvider>
      </ThemeProvider>
    </Provider>
  );
}

export default AppTestStep2;
