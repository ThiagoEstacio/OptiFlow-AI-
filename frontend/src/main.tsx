import React from 'react'
import ReactDOM from 'react-dom/client'
// import App from './App-minimal'
// import App from './App-test-step1'
// import App from './App-test-step2'
// import App from './App-test-step3'
// import App from './App-test-step4'
// import App from './App-test-step3-5'
// import App from './App-test-step3-4'
// import App from './App-test-step3-3'
// Test versions (keep for reference)
// import App from './App-minimal'
// import App from './App-test-step3-4b'
// import App from './App-working-v2'

// Main App
import App from './App'
import './styles/index.css'
import './styles/charts.css'
import { initGlobalErrorHandlers } from './utils/globalErrorHandler'

// Initialize global error handlers to catch unhandled errors
initGlobalErrorHandlers();

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
