/**
 * Dashboard Builder Page
 *
 * Drag-and-drop dashboard creation (PI Vision / Power BI style)
 *
 * Features:
 * - Drag tags to widgets
 * - Auto-binding to live data
 * - Real-time updates via WebSocket
 * - Historical data queries
 * - Save/load dashboard configurations
 */

import React, { useState, useCallback, useEffect } from 'react';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { useAppDispatch, useAppSelector } from '../store';
import { fetchTags } from '../store/slices/tagsSlice';
import { TagsPanel } from '../components/DashboardBuilder/TagsPanel';
import { WidgetCanvas } from '../components/DashboardBuilder/WidgetCanvas';
import { WidgetToolbar } from '../components/DashboardBuilder/WidgetToolbar';
import { showToast } from '../utils/toast';

export interface Widget {
  id: string;
  type: 'gauge' | 'timeseries' | 'value' | 'chart';
  position: { x: number; y: number };
  size: { width: number; height: number };
  config: {
    tagId?: string;
    tagName?: string;
    title?: string;
    unit?: string;
    min?: number;
    max?: number;
    timeRange?: string;
    color?: string;
  };
}

export const DashboardBuilderPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const tags = useAppSelector((state) => state.tags.items);
  const loading = useAppSelector((state) => state.tags.loading);

  const [widgets, setWidgets] = useState<Widget[]>([]);
  const [selectedWidget, setSelectedWidget] = useState<string | null>(null);
  const [showTagsPanel, setShowTagsPanel] = useState(true);
  const [dashboardName, setDashboardName] = useState('My Dashboard');

  // Load tags on mount
  useEffect(() => {
    dispatch(fetchTags({}));
  }, [dispatch]);

  // Add new widget
  const handleAddWidget = useCallback((type: Widget['type']) => {
    const newWidget: Widget = {
      id: `widget-${Date.now()}`,
      type,
      position: { x: 50 + widgets.length * 20, y: 50 + widgets.length * 20 },
      size: {
        width: type === 'timeseries' || type === 'chart' ? 400 : 250,
        height: type === 'timeseries' || type === 'chart' ? 300 : 250
      },
      config: {
        title: `${type.charAt(0).toUpperCase() + type.slice(1)} Widget`,
        timeRange: '1h',
        color: '#3B82F6',
      },
    };

    setWidgets([...widgets, newWidget]);
    setSelectedWidget(newWidget.id);
    showToast.success(`${type} widget added`);
  }, [widgets]);

  // Update widget (position, size, config)
  const handleUpdateWidget = useCallback((widgetId: string, updates: Partial<Widget>) => {
    setWidgets(prev =>
      prev.map(w => w.id === widgetId ? { ...w, ...updates } : w)
    );
  }, []);

  // Delete widget
  const handleDeleteWidget = useCallback((widgetId: string) => {
    setWidgets(prev => prev.filter(w => w.id !== widgetId));
    if (selectedWidget === widgetId) {
      setSelectedWidget(null);
    }
    showToast.success('Widget deleted');
  }, [selectedWidget]);

  // Bind tag to widget (drag-and-drop)
  const handleBindTag = useCallback((widgetId: string, tagId: string) => {
    const tag = tags.find(t => t.id === tagId);
    if (!tag) {
      showToast.error('Tag not found');
      return;
    }

    handleUpdateWidget(widgetId, {
      config: {
        ...widgets.find(w => w.id === widgetId)?.config,
        tagId: tag.id,
        tagName: tag.name,
        title: tag.description || tag.name,
        unit: tag.unit,
        min: tag.min_value,
        max: tag.max_value,
      }
    });

    showToast.success(`Tag "${tag.name}" bound to widget`);
  }, [tags, widgets, handleUpdateWidget]);

  // Save dashboard
  const handleSave = useCallback(() => {
    const dashboard = {
      name: dashboardName,
      widgets,
      createdAt: new Date().toISOString(),
    };

    // Save to localStorage for now (could be API call)
    localStorage.setItem('dashboard', JSON.stringify(dashboard));
    showToast.success('Dashboard saved!');
  }, [dashboardName, widgets]);

  // Load dashboard
  const handleLoad = useCallback(() => {
    const saved = localStorage.getItem('dashboard');
    if (saved) {
      const dashboard = JSON.parse(saved);
      setDashboardName(dashboard.name);
      setWidgets(dashboard.widgets);
      showToast.success('Dashboard loaded!');
    } else {
      showToast.error('No saved dashboard found');
    }
  }, []);

  // Clear dashboard
  const handleClear = useCallback(() => {
    if (confirm('Clear all widgets?')) {
      setWidgets([]);
      setSelectedWidget(null);
      showToast.success('Dashboard cleared');
    }
  }, []);

  return (
    <DndProvider backend={HTML5Backend}>
      <div className="h-screen flex flex-col bg-gray-50">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h1 className="text-xl font-bold text-gray-900">Dashboard Builder</h1>
            <input
              type="text"
              value={dashboardName}
              onChange={(e) => setDashboardName(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded text-sm"
              placeholder="Dashboard name"
            />
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowTagsPanel(!showTagsPanel)}
              className="px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded"
            >
              {showTagsPanel ? '◀ Hide' : '▶ Show'} Tags
            </button>
            <button
              onClick={handleLoad}
              className="px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded"
            >
              📂 Load
            </button>
            <button
              onClick={handleSave}
              className="px-3 py-2 text-sm bg-blue-600 text-white hover:bg-blue-700 rounded"
            >
              💾 Save
            </button>
            <button
              onClick={handleClear}
              className="px-3 py-2 text-sm bg-red-100 text-red-700 hover:bg-red-200 rounded"
            >
              🗑️ Clear
            </button>
          </div>
        </div>

        {/* Toolbar */}
        <WidgetToolbar onAddWidget={handleAddWidget} />

        {/* Main Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Tags Panel */}
          {showTagsPanel && (
            <TagsPanel
              tags={tags}
              loading={loading}
              onClose={() => setShowTagsPanel(false)}
            />
          )}

          {/* Canvas */}
          <WidgetCanvas
            widgets={widgets}
            selectedWidget={selectedWidget}
            onSelectWidget={setSelectedWidget}
            onUpdateWidget={handleUpdateWidget}
            onDeleteWidget={handleDeleteWidget}
            onBindTag={handleBindTag}
          />
        </div>

        {/* Status Bar */}
        <div className="bg-gray-800 text-white px-4 py-2 text-sm flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <span>Widgets: {widgets.length}</span>
            <span>Tags: {tags.length}</span>
            <span className="flex items-center">
              <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
              Connected
            </span>
          </div>
          <div className="text-gray-400">
            💡 Tip: Drag tags from the left panel onto widgets to bind data
          </div>
        </div>
      </div>
    </DndProvider>
  );
};

export default DashboardBuilderPage;
