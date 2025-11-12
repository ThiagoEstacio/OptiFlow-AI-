import React, { useState, useEffect } from 'react';

interface Dashboard {
  id?: string;
  name: string;
  description?: string;
  module: string;
  theme: string;
  auto_refresh: boolean;
  refresh_interval: number;
  is_public: boolean;
}

interface DashboardSettingsProps {
  dashboard: Dashboard | null;
  onClose: () => void;
  onSave: (data: Partial<Dashboard>) => void;
}

const MODULES = [
  { value: 'operations', label: 'Operations', icon: '⚙️' },
  { value: 'maintenance', label: 'Maintenance', icon: '🔧' },
  { value: 'engineering', label: 'Engineering', icon: '📐' },
  { value: 'executive', label: 'Executive', icon: '💼' },
];

const DashboardSettings: React.FC<DashboardSettingsProps> = ({ dashboard, onClose, onSave }) => {
  const [formData, setFormData] = useState({
    name: dashboard?.name || '',
    description: dashboard?.description || '',
    module: dashboard?.module || 'operations',
    theme: dashboard?.theme || 'auto',
    auto_refresh: dashboard?.auto_refresh ?? true,
    refresh_interval: dashboard?.refresh_interval || 30,
    is_public: dashboard?.is_public ?? false,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-auto">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              {dashboard ? 'Dashboard Settings' : 'Create Dashboard'}
            </h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 text-2xl"
            >
              ×
            </button>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Dashboard Name *
            </label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="My Dashboard"
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="Describe your dashboard..."
            />
          </div>

          {/* Module */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Module *
            </label>
            <div className="grid grid-cols-2 gap-3">
              {MODULES.map((module) => (
                <button
                  key={module.value}
                  type="button"
                  onClick={() => setFormData({ ...formData, module: module.value })}
                  className={`p-4 border-2 rounded-lg flex items-center space-x-3 transition-all ${
                    formData.module === module.value
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-gray-200 dark:border-gray-600 hover:border-gray-300'
                  }`}
                >
                  <span className="text-2xl">{module.icon}</span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {module.label}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Theme */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Theme
            </label>
            <select
              value={formData.theme}
              onChange={(e) => setFormData({ ...formData, theme: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="light">Light</option>
              <option value="dark">Dark</option>
              <option value="auto">Auto (System)</option>
            </select>
          </div>

          {/* Auto Refresh */}
          <div className="flex items-center space-x-3">
            <input
              type="checkbox"
              id="auto_refresh"
              checked={formData.auto_refresh}
              onChange={(e) => setFormData({ ...formData, auto_refresh: e.target.checked })}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <label htmlFor="auto_refresh" className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Enable auto-refresh
            </label>
          </div>

          {/* Refresh Interval */}
          {formData.auto_refresh && (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Refresh Interval (seconds)
              </label>
              <input
                type="number"
                min="5"
                max="3600"
                value={formData.refresh_interval}
                onChange={(e) => setFormData({ ...formData, refresh_interval: parseInt(e.target.value) })}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                How often to refresh widget data (5-3600 seconds)
              </p>
            </div>
          )}

          {/* Public */}
          <div className="flex items-center space-x-3">
            <input
              type="checkbox"
              id="is_public"
              checked={formData.is_public}
              onChange={(e) => setFormData({ ...formData, is_public: e.target.checked })}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <label htmlFor="is_public" className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Make dashboard public (visible to all users in organization)
            </label>
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200 dark:border-gray-700">
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              {dashboard ? 'Save Changes' : 'Create Dashboard'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default DashboardSettings;
