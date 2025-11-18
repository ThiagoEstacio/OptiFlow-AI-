import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
// import App from './App-test-step3'
import './styles/index.css'
import { initGlobalErrorHandlers } from './utils/globalErrorHandler'

// Initialize global error handlers to catch unhandled errors
initGlobalErrorHandlers();

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
