/**
 * App Minimal - Tela de teste
 */
import React from 'react';

function App() {
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      height: '100vh',
      backgroundColor: '#1a1a2e',
      color: 'white',
      fontFamily: 'system-ui'
    }}>
      <div style={{ textAlign: 'center' }}>
        <h1 style={{ fontSize: '3rem', marginBottom: '1rem' }}>OptiFlow AI</h1>
        <p style={{ fontSize: '1.2rem', color: '#888' }}>Frontend funcionando!</p>
        <p style={{ fontSize: '0.9rem', color: '#666', marginTop: '2rem' }}>
          Versao minimal de teste
        </p>
      </div>
    </div>
  );
}

export default App;
