import React, { useState } from 'react'
import { Dashboard } from './components/Dashboard'

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  // Check if user is authenticated
  React.useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (token) {
      setIsAuthenticated(true)
    }
  }, [])

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full">
          <h1 className="text-3xl font-bold text-blue-600 mb-6 text-center">
            OptiFlow AI Platform
          </h1>
          <p className="text-center text-gray-600 mb-6">
            Industrial IoT Platform with AI-powered optimization
          </p>
          <div className="space-y-4">
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <h3 className="font-semibold text-green-800 mb-2">Now Available:</h3>
              <ul className="space-y-1 text-sm text-green-700">
                <li>✓ Backend API with FastAPI</li>
                <li>✓ Database Models & Migrations (Alembic)</li>
                <li>✓ WebSocket Real-time Communication</li>
                <li>✓ Industrial Protocol Handlers (OPC UA, Modbus, MQTT)</li>
                <li>✓ Time Series Data with InfluxDB</li>
                <li>✓ Dashboard Components</li>
                <li>✓ Test Suite with pytest</li>
              </ul>
            </div>
            <button
              onClick={() => setIsAuthenticated(true)}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors"
            >
              View Dashboard (Demo)
            </button>
          </div>
        </div>
      </div>
    )
  }

  return <Dashboard />
}

export default App
