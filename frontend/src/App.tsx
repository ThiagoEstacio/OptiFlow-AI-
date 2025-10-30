import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Link, NavLink } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layers, Tag, LayoutDashboard, Home, MessageCircle, X } from 'lucide-react';
import DevicesPage from './pages/DevicesPage';
import TagsPage from './pages/TagsPage';
import ChatBot from './components/ChatBot';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function HomePage() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          OptiFlow AI - SmartPort
        </h1>
        <p className="text-xl text-gray-600">
          Industrial IoT Platform with OPC UA Integration + AI Assistant
        </p>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        <Link
          to="/devices"
          className="bg-white p-6 rounded-lg shadow-md border-2 border-transparent hover:border-blue-500 transition-all"
        >
          <div className="flex items-center justify-center w-12 h-12 bg-blue-100 rounded-lg mb-4">
            <Layers className="h-6 w-6 text-blue-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Devices</h3>
          <p className="text-sm text-gray-600">
            Manage OPC UA devices and PLC connections
          </p>
        </Link>

        <Link
          to="/tags"
          className="bg-white p-6 rounded-lg shadow-md border-2 border-transparent hover:border-green-500 transition-all"
        >
          <div className="flex items-center justify-center w-12 h-12 bg-green-100 rounded-lg mb-4">
            <Tag className="h-6 w-6 text-green-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Tags</h3>
          <p className="text-sm text-gray-600">
            View all available tags from connected devices
          </p>
        </Link>

        <Link
          to="/dashboard"
          className="bg-white p-6 rounded-lg shadow-md border-2 border-transparent hover:border-purple-500 transition-all"
        >
          <div className="flex items-center justify-center w-12 h-12 bg-purple-100 rounded-lg mb-4">
            <LayoutDashboard className="h-6 w-6 text-purple-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Dashboard</h3>
          <p className="text-sm text-gray-600">
            Build dashboards with real-time tag data
          </p>
        </Link>
      </div>

      <div className="mt-12 bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-blue-900 mb-3">Quick Start Guide</h2>
        <ol className="space-y-2 text-sm text-blue-800">
          <li className="flex items-start">
            <span className="font-semibold mr-2">1.</span>
            <span>Go to <strong>Devices</strong> and add your OPC UA server</span>
          </li>
          <li className="flex items-start">
            <span className="font-semibold mr-2">2.</span>
            <span>Test the connection and browse available tags</span>
          </li>
          <li className="flex items-start">
            <span className="font-semibold mr-2">3.</span>
            <span>Select and import tags to the system</span>
          </li>
          <li className="flex items-start">
            <span className="font-semibold mr-2">4.</span>
            <span>View all tags in the <strong>Tags</strong> page</span>
          </li>
          <li className="flex items-start">
            <span className="font-semibold mr-2">5.</span>
            <span>Use tags in your dashboards for real-time monitoring</span>
          </li>
          <li className="flex items-start">
            <span className="font-semibold mr-2">6.</span>
            <span>💬 Click the <strong>AI Assistant</strong> button to get help anytime!</span>
          </li>
        </ol>
      </div>

      {/* AI Assistant Feature Highlight */}
      <div className="mt-8 bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 rounded-lg p-6">
        <div className="flex items-center mb-3">
          <MessageCircle className="h-6 w-6 text-purple-600 mr-2" />
          <h2 className="text-lg font-semibold text-purple-900">AI Assistant Available</h2>
        </div>
        <p className="text-sm text-purple-800 mb-4">
          Get intelligent insights about your devices, tags, and system status. The AI assistant
          can help you troubleshoot issues, analyze data, and optimize your operations.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
          <div className="bg-white/60 p-3 rounded">
            <div className="font-semibold text-purple-900 mb-1">🤖 Smart Analysis</div>
            <div className="text-purple-700">Get insights about your industrial data</div>
          </div>
          <div className="bg-white/60 p-3 rounded">
            <div className="font-semibold text-purple-900 mb-1">📊 Real-time Monitoring</div>
            <div className="text-purple-700">Check alarms and device status</div>
          </div>
          <div className="bg-white/60 p-3 rounded">
            <div className="font-semibold text-purple-900 mb-1">💡 Recommendations</div>
            <div className="text-purple-700">Optimization suggestions</div>
          </div>
        </div>
      </div>
    </div>
  );
}

function DashboardPlaceholder() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 text-center">
      <LayoutDashboard className="h-16 w-16 text-gray-400 mx-auto mb-4" />
      <h2 className="text-2xl font-semibold text-gray-900 mb-2">Dashboard Builder</h2>
      <p className="text-gray-600 mb-6">Coming soon - will consume tags from /tags endpoint</p>
      <Link
        to="/tags"
        className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
      >
        <Tag className="h-4 w-4 mr-2" />
        View Available Tags
      </Link>
    </div>
  );
}

function Navigation() {
  return (
    <nav className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <Link to="/" className="flex items-center">
              <div className="flex-shrink-0 flex items-center">
                <Home className="h-6 w-6 text-blue-600 mr-2" />
                <span className="text-xl font-bold text-gray-900">SmartPort</span>
              </div>
            </Link>
            <div className="hidden sm:ml-8 sm:flex sm:space-x-4">
              <NavLink
                to="/devices"
                className={({ isActive }) =>
                  `inline-flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                    isActive
                      ? 'text-blue-700 bg-blue-50'
                      : 'text-gray-700 hover:text-blue-600 hover:bg-gray-50'
                  }`
                }
              >
                <Layers className="h-4 w-4 mr-2" />
                Devices
              </NavLink>
              <NavLink
                to="/tags"
                className={({ isActive }) =>
                  `inline-flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                    isActive
                      ? 'text-blue-700 bg-blue-50'
                      : 'text-gray-700 hover:text-blue-600 hover:bg-gray-50'
                  }`
                }
              >
                <Tag className="h-4 w-4 mr-2" />
                Tags
              </NavLink>
              <NavLink
                to="/dashboard"
                className={({ isActive }) =>
                  `inline-flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                    isActive
                      ? 'text-blue-700 bg-blue-50'
                      : 'text-gray-700 hover:text-blue-600 hover:bg-gray-50'
                  }`
                }
              >
                <LayoutDashboard className="h-4 w-4 mr-2" />
                Dashboard
              </NavLink>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}

function App() {
  const [showChat, setShowChat] = useState(false);

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-gray-50">
          <Navigation />
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/devices" element={<DevicesPage />} />
            <Route path="/tags" element={<TagsPage />} />
            <Route path="/dashboard" element={<DashboardPlaceholder />} />
          </Routes>

          {/* Floating AI Assistant Button */}
          {!showChat && (
            <button
              onClick={() => setShowChat(true)}
              className="fixed bottom-6 right-6 bg-gradient-to-r from-purple-500 to-pink-500 text-white p-4 rounded-full shadow-lg hover:shadow-xl transform hover:scale-110 transition-all z-50"
              title="Open AI Assistant"
            >
              <MessageCircle className="h-6 w-6" />
            </button>
          )}

          {/* AI Assistant Chat Window */}
          {showChat && (
            <div className="fixed bottom-6 right-6 w-96 h-[600px] bg-white rounded-lg shadow-2xl z-50 flex flex-col border border-gray-200">
              <div className="bg-gradient-to-r from-purple-500 to-pink-500 text-white p-4 rounded-t-lg flex justify-between items-center">
                <div className="flex items-center">
                  <MessageCircle className="h-5 w-5 mr-2" />
                  <h3 className="font-semibold">AI Assistant</h3>
                </div>
                <button
                  onClick={() => setShowChat(false)}
                  className="text-white hover:bg-white/20 rounded p-1 transition-colors"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
              <div className="flex-1 overflow-hidden">
                <ChatBot />
              </div>
            </div>
          )}
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
