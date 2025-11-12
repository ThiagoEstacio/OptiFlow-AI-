import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import DashboardSettings from '../components/Dashboard/DashboardSettings';
import * as dashboardsApi from '../services/dashboards.api';
import type { Dashboard } from '../services/dashboards.api';

const DashboardsList: React.FC = () => {
  const navigate = useNavigate();
  const [dashboards, setDashboards] = useState<Dashboard[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [filterModule, setFilterModule] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [showSettings, setShowSettings] = useState(false);

  // Load dashboards from API
  useEffect(() => {
    const loadDashboards = async () => {
      try {
        setLoading(true);
        const data = await dashboardsApi.getDashboards();
        setDashboards(data);
      } catch (error) {
        console.error('Error loading dashboards:', error);
        // Show empty state on error
        setDashboards([]);
      } finally {
        setLoading(false);
      }
    };
    
    loadDashboards();
  }, []);

  const filteredDashboards = dashboards.filter((dashboard) => {
    const matchesModule = filterModule === 'all' || dashboard.module === filterModule;
    const matchesSearch = dashboard.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         dashboard.description?.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesModule && matchesSearch;
  });

  const getModuleIcon = (module: string) => {
    const icons: Record<string, string> = {
      operations: '⚙️',
      maintenance: '🔧',
      engineering: '📐',
      executive: '💼',
    };
    return icons[module] || '📊';
  };

  const getModuleColor = (module: string) => {
    const colors: Record<string, string> = {
      operations: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      maintenance: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
      engineering: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
      executive: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
    };
    return colors[module] || 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
  };

  const handleCreateDashboard = async (data: any) => {
    try {
      console.log('Creating dashboard:', data);
      
      // Create dashboard via API
      const newDashboard = await dashboardsApi.createDashboard({
        name: data.name,
        description: data.description,
        module: data.module || 'operations',
        theme: data.theme || 'light',
        layout: [],
        is_public: data.is_public || false,
      });
      
      console.log('Dashboard created:', newDashboard);
      
      setShowSettings(false);
      
      // Navigate to builder to add widgets
      navigate(`/dashboards/${newDashboard.id}/edit`);
    } catch (error) {
      console.error('Error creating dashboard:', error);
      alert('Failed to create dashboard. Please try again.');
    }
  };

  const handleCloneDashboard = async (dashboard: Dashboard) => {
    try {
      if (!dashboard.id) return;
      
      const newName = prompt('Enter a name for the cloned dashboard:', `${dashboard.name} (Copy)`);
      if (!newName) return;
      
      console.log('Cloning dashboard:', dashboard.id);
      
      const cloned = await dashboardsApi.cloneDashboard(dashboard.id, newName);
      
      // Refresh the list
      const data = await dashboardsApi.getDashboards();
      setDashboards(data);
      
      console.log('Dashboard cloned:', cloned);
    } catch (error) {
      console.error('Error cloning dashboard:', error);
      alert('Failed to clone dashboard. Please try again.');
    }
  };

  const handleDeleteDashboard = async (id: string) => {
    if (!confirm('Are you sure you want to delete this dashboard?')) {
      return;
    }
    
    try {
      await dashboardsApi.deleteDashboard(id);
      
      // Remove from local state
      setDashboards(dashboards.filter((d) => d.id !== id));
      
      console.log('Dashboard deleted:', id);
    } catch (error) {
      console.error('Error deleting dashboard:', error);
      alert('Failed to delete dashboard. Please try again.');
    }
  };

  const toggleFavorite = async (id: string) => {
    const dashboard = dashboards.find(d => d.id === id);
    if (!dashboard || !dashboard.id) return;
    
    try {
      // Optimistic update
      setDashboards(
        dashboards.map((d) =>
          d.id === id ? { ...d, is_favorite: !d.is_favorite } : d
        )
      );
      
      // Update on server
      await dashboardsApi.updateDashboard(dashboard.id, {
        is_favorite: !dashboard.is_favorite
      });
    } catch (error) {
      console.error('Error toggling favorite:', error);
      // Revert on error
      setDashboards(
        dashboards.map((d) =>
          d.id === id ? { ...d, is_favorite: dashboard.is_favorite } : d
        )
      );
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Dashboards
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Create and manage custom dashboards for your organization
          </p>
        </div>
        <button
          onClick={() => setShowSettings(true)}
          className="mt-4 md:mt-0 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium flex items-center space-x-2"
        >
          <span>+</span>
          <span>Create Dashboard</span>
        </button>
      </div>

      {/* Filters and Search */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 mb-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0 md:space-x-4">
          {/* Search */}
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search dashboards..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
          </div>

          {/* Module Filter */}
          <select
            value={filterModule}
            onChange={(e) => setFilterModule(e.target.value)}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          >
            <option value="all">All Modules</option>
            <option value="operations">Operations</option>
            <option value="maintenance">Maintenance</option>
            <option value="engineering">Engineering</option>
            <option value="executive">Executive</option>
          </select>

          {/* View Mode */}
          <div className="flex space-x-2">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded ${
                viewMode === 'grid'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
              }`}
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM11 13a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
              </svg>
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded ${
                viewMode === 'list'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
              }`}
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Dashboards Grid/List */}
      {filteredDashboards.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-12 text-center">
          <div className="text-6xl mb-4">📊</div>
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
            No dashboards found
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            {searchTerm || filterModule !== 'all'
              ? 'Try adjusting your filters'
              : 'Create your first dashboard to get started'}
          </p>
          {!searchTerm && filterModule === 'all' && (
            <button
              onClick={() => setShowSettings(true)}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              Create Dashboard
            </button>
          )}
        </div>
      ) : viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredDashboards.map((dashboard) => (
            <div
              key={dashboard.id}
              className="bg-white dark:bg-gray-800 rounded-lg shadow-md hover:shadow-lg transition-shadow"
            >
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="text-2xl">{getModuleIcon(dashboard.module)}</span>
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                        {dashboard.name}
                      </h3>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                      {dashboard.description || 'No description'}
                    </p>
                  </div>
                  <button
                    onClick={() => toggleFavorite(dashboard.id)}
                    className="text-xl"
                  >
                    {dashboard.is_favorite ? '⭐' : '☆'}
                  </button>
                </div>

                <div className="flex items-center space-x-2 mb-4">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getModuleColor(dashboard.module)}`}>
                    {dashboard.module}
                  </span>
                  {dashboard.is_public && (
                    <span className="px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200">
                      Public
                    </span>
                  )}
                </div>

                <div className="flex space-x-2">
                  <button
                    onClick={() => navigate(`/dashboards/${dashboard.id}`)}
                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors text-sm"
                  >
                    View
                  </button>
                  <button
                    onClick={() => navigate(`/dashboards/${dashboard.id}/edit`)}
                    className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-sm"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleCloneDashboard(dashboard)}
                    className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-sm"
                    title="Clone"
                  >
                    📋
                  </button>
                  <button
                    onClick={() => handleDeleteDashboard(dashboard.id)}
                    className="px-4 py-2 border border-red-300 dark:border-red-600 text-red-600 dark:text-red-400 rounded hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors text-sm"
                    title="Delete"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden">
          {filteredDashboards.map((dashboard, index) => (
            <div
              key={dashboard.id}
              className={`p-6 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${
                index !== filteredDashboards.length - 1 ? 'border-b border-gray-200 dark:border-gray-700' : ''
              }`}
            >
              <div className="flex items-center space-x-4 flex-1">
                <span className="text-3xl">{getModuleIcon(dashboard.module)}</span>
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-1">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                      {dashboard.name}
                    </h3>
                    <button onClick={() => toggleFavorite(dashboard.id)} className="text-lg">
                      {dashboard.is_favorite ? '⭐' : '☆'}
                    </button>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {dashboard.description || 'No description'}
                  </p>
                  <div className="flex items-center space-x-2 mt-2">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getModuleColor(dashboard.module)}`}>
                      {dashboard.module}
                    </span>
                    {dashboard.is_public && (
                      <span className="px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200">
                        Public
                      </span>
                    )}
                  </div>
                </div>
              </div>
              <div className="flex space-x-2 ml-4">
                <button
                  onClick={() => navigate(`/dashboards/${dashboard.id}`)}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors text-sm"
                >
                  View
                </button>
                <button
                  onClick={() => navigate(`/dashboards/${dashboard.id}/edit`)}
                  className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-sm"
                >
                  Edit
                </button>
                <button
                  onClick={() => handleCloneDashboard(dashboard)}
                  className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-sm"
                  title="Clone"
                >
                  📋
                </button>
                <button
                  onClick={() => handleDeleteDashboard(dashboard.id)}
                  className="px-4 py-2 border border-red-300 dark:border-red-600 text-red-600 dark:text-red-400 rounded hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors text-sm"
                  title="Delete"
                >
                  🗑️
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Dashboard Settings Modal */}
      {showSettings && (
        <DashboardSettings
          dashboard={null}
          onClose={() => setShowSettings(false)}
          onSave={handleCreateDashboard}
        />
      )}
    </div>
  );
};

export default DashboardsList;
