import React from 'react';
import { BrowserRouter, Routes, Route, Link, NavLink } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layers, Tag, LayoutDashboard, Home } from 'lucide-react';
import DevicesPage from './pages/DevicesPage';
import TagsPage from './pages/TagsPage';

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
          Industrial IoT Platform with OPC UA Integration
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
        </ol>
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
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
