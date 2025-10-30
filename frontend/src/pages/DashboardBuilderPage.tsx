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
  type: 'gauge' | 'timeseries' | 'value' | 'chart' | 'kpi' | 'status' | 'table' | 'progress' | 'sparkline' | 'pie' | 'bar' | 'heatmap';
  position: { x: number; y: number };
  size: { width: number; height: number };
  config: {
    tagId?: string;
    tagIds?: string[]; // For multi-tag widgets like tables
    tagName?: string;
    title?: string;
    unit?: string;
    min?: number;
    max?: number;
    timeRange?: string;
    color?: string;
    // KPI specific
    previousValue?: number;
    target?: number;
    trend?: 'up' | 'down' | 'neutral';
    format?: 'number' | 'percentage' | 'currency';
    decimals?: number;
    // Status specific
    status?: 'running' | 'stopped' | 'warning' | 'alarm' | 'offline' | 'idle' | 'maintenance';
    // Progress specific
    progressType?: 'bar' | 'circular';
    thresholds?: {
      warning?: number;
      critical?: number;
    };
    // Sparkline specific
    sparklineStyle?: 'line' | 'area' | 'bar';
    showMinMax?: boolean;
    showTrend?: boolean;
    // Table specific
    columns?: any[];
    // General
    theme?: 'default' | 'minimal' | 'modern' | 'industrial';
    size?: 'sm' | 'md' | 'lg';
  };
}

// Mock tags for when backend is not available
const MOCK_TAGS = [
  { id: '1', name: 'CONV1_MOTOR_CURRENT', description: 'Conveyor 1 Motor Current', unit: 'A', category: 'Motors', min_value: 0, max_value: 300, data_type: 'float' },
  { id: '2', name: 'CONV1_MOTOR_TEMP', description: 'Conveyor 1 Motor Temperature', unit: '°C', category: 'Motors', min_value: 20, max_value: 120, data_type: 'float' },
  { id: '3', name: 'CONV1_VIBRATION', description: 'Conveyor 1 Vibration', unit: 'mm/s', category: 'Motors', min_value: 0, max_value: 15, data_type: 'float' },
  { id: '4', name: 'ELEV1_MOTOR_CURRENT', description: 'Elevator Motor Current', unit: 'A', category: 'Motors', min_value: 0, max_value: 400, data_type: 'float' },
  { id: '5', name: 'SHIP_MOTOR_CURRENT', description: 'Shiploader Motor Current', unit: 'A', category: 'Motors', min_value: 0, max_value: 500, data_type: 'float' },
  { id: '6', name: 'SHIP_FLOW_RATE', description: 'Shiploader Flow Rate', unit: 't/h', category: 'Production', min_value: 0, max_value: 3000, data_type: 'float' },
  { id: '7', name: 'VESSEL_PROGRESS', description: 'Vessel Loading Progress', unit: '%', category: 'Production', min_value: 0, max_value: 100, data_type: 'float' },
  { id: '8', name: 'LOADING_RATE_TOTAL', description: 'Total Loading Rate', unit: 't', category: 'Production', min_value: 0, max_value: 100000, data_type: 'float' },
  { id: '9', name: 'PRODUCT_MOISTURE', description: 'Product Moisture', unit: '%', category: 'Quality', min_value: 0, max_value: 100, data_type: 'float' },
  { id: '10', name: 'PRODUCT_TEMP', description: 'Product Temperature', unit: '°C', category: 'Quality', min_value: -10, max_value: 60, data_type: 'float' },
];

export const DashboardBuilderPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const tagsFromStore = useAppSelector((state) => state.tags.items);
  const loading = useAppSelector((state) => state.tags.loading);

  // Use mock tags if no tags loaded from backend
  const tags = tagsFromStore.length > 0 ? tagsFromStore : MOCK_TAGS;

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
    // Determine widget size based on type
    const getWidgetSize = (widgetType: Widget['type']) => {
      switch (widgetType) {
        case 'kpi':
          return { width: 280, height: 180 };
        case 'status':
          return { width: 250, height: 150 };
        case 'progress':
          return { width: 300, height: 180 };
        case 'sparkline':
          return { width: 280, height: 160 };
        case 'table':
          return { width: 500, height: 350 };
        case 'timeseries':
        case 'bar':
        case 'pie':
        case 'heatmap':
          return { width: 400, height: 300 };
        case 'gauge':
          return { width: 280, height: 280 };
        case 'value':
          return { width: 220, height: 180 };
        default:
          return { width: 250, height: 250 };
      }
    };

    const newWidget: Widget = {
      id: `widget-${Date.now()}`,
      type,
      position: { x: 50 + widgets.length * 20, y: 50 + widgets.length * 20 },
      size: getWidgetSize(type),
      config: {
        title: `${type.charAt(0).toUpperCase() + type.slice(1)} Widget`,
        timeRange: '1h',
        color: '#3B82F6',
        size: 'md',
        decimals: 1,
        showTrend: true,
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
