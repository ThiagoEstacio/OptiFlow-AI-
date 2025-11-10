/**
 * App Test Step 1 - Provider and BrowserRouter only
 */
import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { Provider } from 'react-redux';
import { store } from './store';

function AppTestStep1() {
  return (
    <Provider store={store}>
      <BrowserRouter>
        <div style={{
          padding: '50px',
          fontFamily: 'Arial',
          backgroundColor: '#e3f2fd',
          minHeight: '100vh'
        }}>
          <h1 style={{ color: '#1976d2' }}>✅ Teste Step 1: Redux + Router</h1>
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
            </ul>
            <p style={{ marginTop: '20px', color: '#666' }}>
              Se você vê esta mensagem, Redux e Router estão funcionando.
            </p>
          </div>
        </div>
      </BrowserRouter>
    </Provider>
  );
}

export default AppTestStep1;
