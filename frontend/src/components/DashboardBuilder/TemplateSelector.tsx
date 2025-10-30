/**
 * Template Selector Modal
 * Choose from pre-configured dashboard templates
 */

import React, { useState } from 'react';
import { X, FileText, Activity, BarChart3, Settings } from 'lucide-react';
import { dashboardTemplates, type DashboardTemplate } from '../../data/dashboardTemplates';

interface TemplateSelectorProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectTemplate: (template: DashboardTemplate) => void;
}

export const TemplateSelector: React.FC<TemplateSelectorProps> = ({
  isOpen,
  onClose,
  onSelectTemplate,
}) => {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  if (!isOpen) return null;

  const categories = [
    { id: 'all', label: 'All Templates', icon: FileText },
    { id: 'industrial', label: 'Industrial', icon: Activity },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'monitoring', label: 'Monitoring', icon: Settings },
    { id: 'custom', label: 'Custom', icon: FileText },
  ];

  const filteredTemplates =
    selectedCategory === 'all'
      ? dashboardTemplates
      : dashboardTemplates.filter((t) => t.category === selectedCategory);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-2xl max-w-5xl w-full max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Dashboard Templates</h2>
            <p className="text-sm text-gray-600 mt-1">
              Choose a template to get started quickly
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Sidebar - Categories */}
          <div className="w-48 border-r border-gray-200 bg-gray-50 p-3">
            <div className="space-y-1">
              {categories.map((category) => {
                const Icon = category.icon;
                return (
                  <button
                    key={category.id}
                    onClick={() => setSelectedCategory(category.id)}
                    className={`
                      w-full flex items-center space-x-2 px-3 py-2 rounded transition-colors text-left
                      ${
                        selectedCategory === category.id
                          ? 'bg-blue-100 text-blue-700'
                          : 'text-gray-700 hover:bg-gray-200'
                      }
                    `}
                  >
                    <Icon className="w-4 h-4" />
                    <span className="text-sm font-medium">{category.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Templates Grid */}
          <div className="flex-1 overflow-y-auto p-6">
            <div className="grid grid-cols-2 gap-4">
              {filteredTemplates.map((template) => (
                <button
                  key={template.id}
                  onClick={() => {
                    onSelectTemplate(template);
                    onClose();
                  }}
                  className="group border border-gray-200 rounded-lg p-4 hover:border-blue-500 hover:shadow-lg transition-all text-left"
                >
                  {/* Thumbnail / Preview */}
                  <div className="aspect-video bg-gradient-to-br from-blue-50 to-blue-100 rounded mb-3 flex items-center justify-center">
                    <div className="text-center">
                      <div className="text-4xl mb-2">
                        {template.category === 'industrial' && '🏭'}
                        {template.category === 'analytics' && '📊'}
                        {template.category === 'monitoring' && '📡'}
                        {template.category === 'custom' && '⚙️'}
                      </div>
                      <div className="text-xs text-gray-500">
                        {template.widgets.length} widgets
                      </div>
                    </div>
                  </div>

                  {/* Info */}
                  <h3 className="font-semibold text-gray-900 group-hover:text-blue-700 transition-colors">
                    {template.name}
                  </h3>
                  <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                    {template.description}
                  </p>

                  {/* Badge */}
                  <div className="mt-3">
                    <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-700">
                      {template.category}
                    </span>
                  </div>
                </button>
              ))}
            </div>

            {filteredTemplates.length === 0 && (
              <div className="text-center py-12 text-gray-500">
                <p>No templates found in this category</p>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-600">
              {filteredTemplates.length} template(s) available
            </p>
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
