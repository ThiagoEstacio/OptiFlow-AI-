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
import { Save, FolderOpen, FileDown, Settings, Grid3X3, Layout, Zap, Sparkles } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '../store';
import { fetchTags } from '../store/slices/tagsSlice';
import { TagsPanel } from '../components/DashboardBuilder/TagsPanel';
import { TagEditModal } from '../components/DashboardBuilder/TagEditModal';
import { WidgetCanvas } from '../components/DashboardBuilder/WidgetCanvas';
import { WidgetToolbar } from '../components/DashboardBuilder/WidgetToolbar';
import { PropertyPanel } from '../components/DashboardBuilder/PropertyPanel';
import { GridBackground } from '../components/DashboardBuilder/GridBackground';
import { TemplateSelector } from '../components/DashboardBuilder/TemplateSelector';
import { DashboardManager } from '../components/DashboardBuilder/DashboardManager';
import { AIAssistantPanel } from '../components/DashboardBuilder/AIAssistantPanel';
import { SimulationControlPanel } from '../components/SimulationControlPanel';
import { ThemeToggle } from '../components/ThemeToggle';
import { useGridSnapping } from '../hooks/useGridSnapping';
import { useDashboardManager } from '../hooks/useDashboardManager';
import { getTemplate, type DashboardTemplate } from '../data/dashboardTemplates';
import { showToast } from '../utils/toast';
import { PORT_GRAIN_TERMINAL_TAGS, type Tag as PortTag } from '../data/portGrainTerminalTags';

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

export const DashboardBuilderPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const tagsFromStore = useAppSelector((state) => state.tags.items);
  const loading = useAppSelector((state) => state.tags.loading);

  // State
  const [widgets, setWidgets] = useState<Widget[]>([]);
  const [selectedWidget, setSelectedWidget] = useState<string | null>(null);
  const [showTagsPanel, setShowTagsPanel] = useState(true);
  const [showPropertyPanel, setShowPropertyPanel] = useState(false);
  const [showGrid, setShowGrid] = useState(true);
  const [dashboardName, setDashboardName] = useState('My Dashboard');

  // Modal states
  const [showTemplateSelector, setShowTemplateSelector] = useState(false);
  const [showDashboardManager, setShowDashboardManager] = useState(false);
  const [showSimulationPanel, setShowSimulationPanel] = useState(false);
  const [showAIAssistant, setShowAIAssistant] = useState(false);
  const [tagEditModal, setTagEditModal] = useState<{ isOpen: boolean; tag: PortTag | null }>({
    isOpen: false,
    tag: null,
  });
  const [editableTags, setEditableTags] = useState<PortTag[]>(PORT_GRAIN_TERMINAL_TAGS);

  // Advanced hooks
  const gridSnapping = useGridSnapping({ gridSize: 10, enabled: true });
  const dashboardManager = useDashboardManager();

  // Current dashboard ID (for multi-dashboard support)
  const [currentDashboardId, setCurrentDashboardId] = useState<string | null>(null);

  // Handle tag edit
  const handleEditTag = useCallback((tag: PortTag) => {
    setTagEditModal({ isOpen: true, tag });
  }, []);

  const handleSaveTag = useCallback((updatedTag: PortTag) => {
    setEditableTags(prev =>
      prev.map(t => (t.id === updatedTag.id ? updatedTag : t))
    );
    showToast.success(`Tag "${updatedTag.name}" atualizada com sucesso`);
  }, []);

  // Use editable tags
  const displayTags = tagsFromStore.length > 0 ? tagsFromStore : editableTags;

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
      prev.map(w => {
        if (w.id !== widgetId) return w;
        
        // Deep merge config if provided
        const newWidget = { ...w, ...updates };
        if (updates.config) {
          newWidget.config = { ...w.config, ...updates.config };
        }
        
        return newWidget;
      })
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
    console.log('🔥 handleBindTag CALLED:', { widgetId, tagId });
    
    const tag = displayTags.find((t: any) => t.id === tagId);
    if (!tag) {
      showToast.error('Tag not found');
      return;
    }

    // Use setWidgets with functional update to access latest state
    setWidgets(prev => {
      const widget = prev.find(w => w.id === widgetId);
      console.log('🔥 Found widget:', widget);
      if (!widget) return prev;

      // For timeseries and table widgets, support multiple tags
      const supportsMultipleTags = ['timeseries', 'table'].includes(widget.type);
      console.log('🔥 Widget type:', widget.type, 'supportsMultipleTags:', supportsMultipleTags);

      if (supportsMultipleTags) {
        // Add to tagIds array (don't duplicate)
        const currentTagIds = widget.config.tagIds || [];
        console.log('handleBindTag - Before adding:', { widgetId, currentTagIds, newTagId: tag.id });
        
        if (currentTagIds.includes(tag.id)) {
          showToast.error(`Tag "${tag.name}" already added`);
          return prev;
        }

        const newTagIds = [...currentTagIds, tag.id];
        console.log('handleBindTag - After adding:', { widgetId, newTagIds });
        
        showToast.success(`Tag "${tag.name}" added (${newTagIds.length} total)`);
        
        // Update the widget with new tagIds
        return prev.map(w => w.id === widgetId ? {
          ...w,
          config: {
            ...w.config,
            tagIds: newTagIds,
            tagId: currentTagIds.length === 0 ? tag.id : w.config.tagId,
            tagName: currentTagIds.length === 0 ? tag.name : w.config.tagName,
            title: w.config.title || tag.description || tag.name,
          }
        } : w);
      } else {
        // Single tag widgets - replace the tag
        showToast.success(`Tag "${tag.name}" bound to widget`);
        
        return prev.map(w => w.id === widgetId ? {
          ...w,
          config: {
            ...w.config,
            tagId: tag.id,
            tagName: tag.name,
            title: tag.description || tag.name,
            unit: tag.unit,
            min: tag.min_value,
            max: tag.max_value,
          }
        } : w);
      }
    });
  }, [displayTags]);

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

  // Template functions
  const handleSelectTemplate = useCallback((template: DashboardTemplate) => {
    const templateWidgets: Widget[] = template.widgets.map((w, index) => ({
      ...w,
      id: `widget-${Date.now()}-${index}`,
    } as Widget));

    setWidgets(templateWidgets);
    setDashboardName(template.name);
    showToast.success(`Template "${template.name}" loaded`);
  }, []);

  // Dashboard Manager functions
  const handleSelectDashboard = useCallback((dashboard: any) => {
    setWidgets(dashboard.widgets);
    setDashboardName(dashboard.name);
    setCurrentDashboardId(dashboard.id);
    showToast.success(`Dashboard "${dashboard.name}" loaded`);
  }, []);

  const handleCreateDashboard = useCallback((name: string, description?: string) => {
    dashboardManager.createDashboard(name, widgets, description);
    showToast.success(`Dashboard "${name}" created`);
  }, [dashboardManager, widgets]);

  const handleExportDashboard = useCallback((dashboard: any) => {
    dashboardManager.downloadDashboard(dashboard);
    showToast.success('Dashboard exported');
  }, [dashboardManager]);

  const handleImportDashboard = useCallback(async (file: File) => {
    const imported = await dashboardManager.importDashboardFromFile(file);
    if (imported) {
      showToast.success('Dashboard imported successfully');
    } else {
      showToast.error('Failed to import dashboard');
    }
  }, [dashboardManager]);

  const handleShareDashboard = useCallback((id: string) => {
    const url = dashboardManager.shareDashboard(id);
    navigator.clipboard.writeText(url);
    showToast.success('Share link copied to clipboard!');
  }, [dashboardManager]);

  // Auto-open property panel when widget is selected
  useEffect(() => {
    if (selectedWidget) {
      setShowPropertyPanel(true);
    }
  }, [selectedWidget]);

  // Get selected widget object
  const selectedWidgetObj = selectedWidget
    ? widgets.find(w => w.id === selectedWidget) || null
    : null;

  return (
    <DndProvider backend={HTML5Backend}>
      <div className="h-screen flex flex-col bg-gray-50 dark:bg-gray-900">
        {/* Header */}
        <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 py-3">
          <div className="flex items-center justify-between">
            {/* Left side - Title and name */}
            <div className="flex items-center space-x-4">
              <h1 className="text-xl font-bold text-gray-900 dark:text-white">Dashboard Builder</h1>
              <input
                type="text"
                value={dashboardName}
                onChange={(e) => setDashboardName(e.target.value)}
                className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                placeholder="Dashboard name"
              />
            </div>

            {/* Right side - Actions */}
            <div className="flex items-center space-x-2">
              {/* Templates */}
              <button
                onClick={() => setShowTemplateSelector(true)}
                className="flex items-center space-x-1 px-3 py-2 text-sm bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-200 hover:bg-purple-200 dark:hover:bg-purple-800 rounded transition-colors"
                title="Load Template"
              >
                <Layout className="w-4 h-4" />
                <span>Templates</span>
              </button>

              {/* Dashboard Manager */}
              <button
                onClick={() => setShowDashboardManager(true)}
                className="flex items-center space-x-1 px-3 py-2 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600 rounded transition-colors"
                title="Manage Dashboards"
              >
                <FolderOpen className="w-4 h-4" />
                <span>Dashboards</span>
              </button>

              {/* Grid Toggle */}
              <button
                onClick={() => setShowGrid(!showGrid)}
                className={`flex items-center space-x-1 px-3 py-2 text-sm rounded transition-colors ${
                  showGrid
                    ? 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-200'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200'
                }`}
                title="Toggle Grid"
              >
                <Grid3X3 className="w-4 h-4" />
              </button>

              {/* AI Assistant Toggle */}
              <button
                onClick={() => setShowAIAssistant(!showAIAssistant)}
                className="flex items-center space-x-1 px-3 py-2 text-sm bg-gradient-to-r from-blue-500 to-purple-600 text-white hover:from-blue-600 hover:to-purple-700 rounded transition-colors shadow-lg"
                title="AI Assistant"
              >
                <Sparkles className="w-4 h-4" />
                <span>AI Assistant</span>
              </button>

              {/* Snap Toggle */}
              <button
                onClick={gridSnapping.toggleSnapping}
                className={`px-3 py-2 text-xs rounded transition-colors ${
                  gridSnapping.isSnapping
                    ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-200'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400'
                }`}
                title="Toggle Grid Snapping"
              >
                {gridSnapping.isSnapping ? '🧲 Snap ON' : '🧲 Snap OFF'}
              </button>

              {/* Tags Panel Toggle */}
              <button
                onClick={() => setShowTagsPanel(!showTagsPanel)}
                className="px-3 py-2 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600 rounded transition-colors"
              >
                {showTagsPanel ? '◀ Hide Tags' : '▶ Show Tags'}
              </button>

              {/* Properties Panel Toggle */}
              <button
                onClick={() => setShowPropertyPanel(!showPropertyPanel)}
                className={`flex items-center space-x-1 px-3 py-2 text-sm rounded transition-colors ${
                  showPropertyPanel
                    ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-200'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
                title="Toggle Properties Panel"
              >
                <Settings className="w-4 h-4" />
                <span>Properties</span>
              </button>

              {/* Simulation Control */}
              <button
                onClick={() => setShowSimulationPanel(!showSimulationPanel)}
                className="flex items-center space-x-1 px-3 py-2 text-sm bg-orange-100 dark:bg-orange-900 text-orange-700 dark:text-orange-200 hover:bg-orange-200 dark:hover:bg-orange-800 rounded transition-colors"
                title="Simulation Control"
              >
                <Zap className="w-4 h-4" />
                <span>Simulation</span>
              </button>

              {/* Theme Toggle */}
              <ThemeToggle variant="icon" size="md" />

              {/* Save */}
              <button
                onClick={handleSave}
                className="flex items-center space-x-1 px-4 py-2 text-sm bg-blue-600 text-white hover:bg-blue-700 rounded transition-colors"
                title="Save Dashboard"
              >
                <Save className="w-4 h-4" />
                <span>Save</span>
              </button>
            </div>
          </div>
        </div>

        {/* Toolbar */}
        <WidgetToolbar onAddWidget={handleAddWidget} />

        {/* Main Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Tags Panel */}
          {showTagsPanel && (
            <TagsPanel
              tags={displayTags as any}
              loading={loading}
              onClose={() => setShowTagsPanel(false)}
              onEditTag={handleEditTag}
            />
          )}

          {/* Canvas */}
          <div className="flex-1 relative bg-white dark:bg-gray-800">
            {/* Grid Background */}
            <GridBackground
              gridSize={gridSnapping.gridSize}
              show={showGrid}
            />

            <WidgetCanvas
              widgets={widgets}
              selectedWidget={selectedWidget}
              onSelectWidget={setSelectedWidget}
              onUpdateWidget={handleUpdateWidget}
              onDeleteWidget={handleDeleteWidget}
              onBindTag={handleBindTag}
            />
          </div>

          {/* Property Panel */}
          {showPropertyPanel && (
            <PropertyPanel
              widget={selectedWidgetObj}
              onUpdate={handleUpdateWidget}
              onClose={() => setShowPropertyPanel(false)}
            />
          )}
        </div>

        {/* Status Bar */}
        <div className="bg-gray-800 dark:bg-gray-900 text-white px-4 py-2 text-sm flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <span>Widgets: {widgets.length}</span>
            <span>Tags: {displayTags.length}</span>
            {selectedWidget && <span>• Selected: {selectedWidgetObj?.type}</span>}
            <span>• Grid: {showGrid ? 'ON' : 'OFF'}</span>
            <span>• Snap: {gridSnapping.isSnapping ? 'ON' : 'OFF'}</span>
            <span className="flex items-center">
              <span className="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse"></span>
              Live
            </span>
          </div>
          <div className="text-gray-400">
            💡 Tip: Use Templates for quick start • Right-click widgets for options
          </div>
        </div>

        {/* Modals */}
        <TemplateSelector
          isOpen={showTemplateSelector}
          onClose={() => setShowTemplateSelector(false)}
          onSelectTemplate={handleSelectTemplate}
        />

        <DashboardManager
          isOpen={showDashboardManager}
          onClose={() => setShowDashboardManager(false)}
          dashboards={dashboardManager.dashboards}
          currentDashboardId={currentDashboardId}
          onSelectDashboard={handleSelectDashboard}
          onCreateDashboard={handleCreateDashboard}
          onDeleteDashboard={dashboardManager.deleteDashboard}
          onDuplicateDashboard={dashboardManager.duplicateDashboard}
          onExportDashboard={handleExportDashboard}
          onImportDashboard={handleImportDashboard}
          onShareDashboard={handleShareDashboard}
        />

        {/* Tag Edit Modal */}
        {tagEditModal.tag && (
          <TagEditModal
            tag={tagEditModal.tag}
            isOpen={tagEditModal.isOpen}
            onClose={() => setTagEditModal({ isOpen: false, tag: null })}
            onSave={handleSaveTag}
          />
        )}

        {/* Simulation Control Panel Modal */}
        {showSimulationPanel && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="max-w-2xl w-full">
              <SimulationControlPanel onClose={() => setShowSimulationPanel(false)} />
            </div>
          </div>
        )}

        {/* AI Assistant Panel */}
        {showAIAssistant && (
          <AIAssistantPanel
            availableTags={displayTags}
            currentWidgets={widgets}
            onAddWidgets={(newWidgets) => {
              setWidgets(prev => [...prev, ...newWidgets]);
            }}
            onClose={() => setShowAIAssistant(false)}
          />
        )}
      </div>
    </DndProvider>
  );
};

export default DashboardBuilderPage;
