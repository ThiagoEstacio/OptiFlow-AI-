/**
 * Minimal App for Testing
 */
import React from 'react';

function AppMinimal() {
  return (
    <div style={{
      padding: '50px',
      fontFamily: 'Arial',
      backgroundColor: '#f0f0f0',
      minHeight: '100vh'
    }}>
      <h1 style={{ color: '#333' }}>✅ OptiFlow AI - React Funcionando!</h1>
      <p style={{ fontSize: '18px', color: '#666' }}>
        Se você vê esta mensagem, o React está carregando corretamente.
      </p>
      <div style={{
        marginTop: '30px',
        padding: '20px',
        backgroundColor: 'white',
        borderRadius: '8px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
      }}>
        <h2>Status do Sistema</h2>
        <ul>
          <li>✅ React: Funcionando</li>
          <li>✅ TypeScript: Compilando</li>
          <li>✅ Vite: Servindo arquivos</li>
        </ul>
      </div>
      <p style={{ marginTop: '30px', color: '#888', fontSize: '14px' }}>
        Este é um App mínimo para testar se o problema está no React ou nos componentes/dependencies.
      </p>
    </div>
  );
}

export default AppMinimal;
