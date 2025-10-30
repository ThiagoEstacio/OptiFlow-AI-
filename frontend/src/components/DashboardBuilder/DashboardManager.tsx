/**
 * Dashboard Manager Component
 * Manage multiple dashboards - create, edit, delete, import, export
 */

import React, { useState } from 'react';
import { Plus, Download, Upload, Copy, Trash2, Edit2, Share2, FolderOpen, X } from 'lucide-react';
import type { Dashboard } from '../../hooks/useDashboardManager';

interface DashboardManagerProps {
  isOpen: boolean;
  onClose: () => void;
  dashboards: Dashboard[];
  currentDashboardId?: string;
  onSelectDashboard: (dashboard: Dashboard) => void;
  onCreateDashboard: (name: string, description?: string) => void;
  onDeleteDashboard: (id: string) => void;
  onDuplicateDashboard: (id: string) => void;
  onExportDashboard: (dashboard: Dashboard) => void;
  onImportDashboard: (file: File) => void;
  onShareDashboard: (id: string) => void;
}

export const DashboardManager: React.FC<DashboardManagerProps> = ({
  isOpen,
  onClose,
  dashboards,
  currentDashboardId,
  onSelectDashboard,
  onCreateDashboard,
  onDeleteDashboard,
  onDuplicateDashboard,
  onExportDashboard,
  onImportDashboard,
  onShareDashboard,
}) => {
  const [isCreating, setIsCreating] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDescription, setNewDescription] = useState('');

  if (!isOpen) return null;

  const handleCreate = () => {
    if (newName.trim()) {
      onCreateDashboard(newName, newDescription || undefined);
      setNewName('');
      setNewDescription('');
      setIsCreating(false);
    }
  };

  const handleImport = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (file) {
        onImportDashboard(file);
      }
    };
    input.click();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-2xl max-w-4xl w-full max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <FolderOpen className="w-6 h-6 text-blue-600" />
            <div>
              <h2 className="text-xl font-bold text-gray-900">Dashboard Manager</h2>
              <p className="text-sm text-gray-600">Manage your dashboards</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Toolbar */}
        <div className="px-6 py-3 border-b border-gray-200 bg-gray-50 flex items-center space-x-2">
          <button
            onClick={() => setIsCreating(true)}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span className="text-sm font-medium">New Dashboard</span>
          </button>

          <button
            onClick={handleImport}
            className="flex items-center space-x-2 px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded hover:bg-gray-50 transition-colors"
          >
            <Upload className="w-4 h-4" />
            <span className="text-sm font-medium">Import</span>
          </button>

          <div className="flex-1" />

          <span className="text-sm text-gray-600">
            {dashboards.length} dashboard(s)
          </span>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Create Form */}
          {isCreating && (
            <div className="mb-6 p-4 border border-blue-200 bg-blue-50 rounded-lg">
              <h3 className="font-semibold text-gray-900 mb-3">Create New Dashboard</h3>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Name *
                  </label>
                  <input
                    type="text"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    placeholder="My Dashboard"
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                    autoFocus
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    value={newDescription}
                    onChange={(e) => setNewDescription(e.target.value)}
                    placeholder="Optional description..."
                    rows={2}
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={handleCreate}
                    disabled={!newName.trim()}
                    className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Create
                  </button>
                  <button
                    onClick={() => {
                      setIsCreating(false);
                      setNewName('');
                      setNewDescription('');
                    }}
                    className="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Dashboards List */}
          <div className="space-y-3">
            {dashboards.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <FolderOpen className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                <p className="font-medium">No dashboards yet</p>
                <p className="text-sm mt-1">Create your first dashboard to get started</p>
              </div>
            ) : (
              dashboards.map((dashboard) => (
                <div
                  key={dashboard.id}
                  className={`
                    border rounded-lg p-4 hover:shadow-md transition-all
                    ${
                      currentDashboardId === dashboard.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 bg-white'
                    }
                  `}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <button
                        onClick={() => {
                          onSelectDashboard(dashboard);
                          onClose();
                        }}
                        className="text-left w-full group"
                      >
                        <h3 className="font-semibold text-gray-900 group-hover:text-blue-700 transition-colors truncate">
                          {dashboard.name}
                        </h3>
                        {dashboard.description && (
                          <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                            {dashboard.description}
                          </p>
                        )}
                        <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                          <span>{dashboard.widgets.length} widgets</span>
                          <span>•</span>
                          <span>
                            Updated {new Date(dashboard.updatedAt).toLocaleDateString()}
                          </span>
                          {dashboard.isPublic && (
                            <>
                              <span>•</span>
                              <span className="text-green-600 font-medium">Public</span>
                            </>
                          )}
                        </div>
                      </button>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center space-x-1 ml-4">
                      <button
                        onClick={() => onShareDashboard(dashboard.id)}
                        className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                        title="Share"
                      >
                        <Share2 className="w-4 h-4" />
                      </button>

                      <button
                        onClick={() => onExportDashboard(dashboard)}
                        className="p-2 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded transition-colors"
                        title="Export"
                      >
                        <Download className="w-4 h-4" />
                      </button>

                      <button
                        onClick={() => onDuplicateDashboard(dashboard.id)}
                        className="p-2 text-gray-400 hover:text-purple-600 hover:bg-purple-50 rounded transition-colors"
                        title="Duplicate"
                      >
                        <Copy className="w-4 h-4" />
                      </button>

                      <button
                        onClick={() => {
                          if (
                            confirm(
                              `Are you sure you want to delete "${dashboard.name}"?`
                            )
                          ) {
                            onDeleteDashboard(dashboard.id);
                          }
                        }}
                        className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                        title="Delete"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  {/* Tags */}
                  {dashboard.tags && dashboard.tags.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {dashboard.tags.map((tag, index) => (
                        <span
                          key={index}
                          className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-700"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 flex items-center justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
