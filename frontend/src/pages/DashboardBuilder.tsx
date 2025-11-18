import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Layout, Responsive, WidthProvider } from 'react-grid-layout';
import 'react-grid-layout/css/styles.css';
// // import 'react-grid-layout/css/resizable.css'; // CSS file not found // CSS file not found - resizable styles included in main styles.css

import * as dashboardAPI from '../services/dashboards.api';
import WidgetLibrary from '../components/Dashboard/WidgetLibrary';
import WidgetRenderer from '../components/Dashboard/WidgetRenderer';
import DashboardSettings from '../components/Dashboard/DashboardSettings';

const ResponsiveGridLayout = WidthProvider(Responsive);

interface Widget {
  id: string;
  type: string;
  title: string;
  config: Record<string, any>;
  x: number;
  y: number;
  w: number;
  h: number;
}

interface Dashboard {
  id?: string;
  name: string;
  description?: string;
  module: string;
  theme: string;
  layout: Widget[];
  auto_refresh: boolean;
  refresh_interval: number;
  is_public: boolean;
}

const DashboardBuilder: React.FC = () => {
  const { id } = useParams<{ id?: string }>();
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [widgets, setWidgets] = useState<Widget[]>([]);
  const [layout, setLayout] = useState<Layout[]>([]);
  const [isEditing, setIsEditing] = useState(true); // Default to edit mode
  const [showWidgetLibrary, setShowWidgetLibrary] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      loadDashboard(id);
    } else {
      // New dashboard
      setLoading(false);
      setShowSettings(true);
    }
  }, [id]);

  const loadDashboard = async (dashboardId: string) => {
    try {
      const data = await dashboardAPI.getDashboard(dashboardId);
      setDashboard(data as any);
      setWidgets((data.layout || []) as any);
      setLayout(
        (data.layout || []).map((w: any) => ({
          i: w.id!,
          x: w.x,
          y: w.y,
          w: w.w,
          h: w.h,
        }))
      );
    } catch (error: any) {
      console.error('Failed to load dashboard:', error);
      alert('Failed to load dashboard');
      navigate('/dashboards');
    } finally {
      setLoading(false);
    }
  };

  const handleLayoutChange = async (newLayout: Layout[]) => {
    if (!isEditing || !id) return;

    setLayout(newLayout);

    // Update widget positions
    const updates = newLayout.map((item) => ({
      widget_id: item.i,
      x: item.x,
      y: item.y,
      w: item.w,
      h: item.h,
    }));

    try {
      await dashboardAPI.bulkUpdateWidgets(id, updates);
    } catch (error: any) {
      console.error('Failed to update layout:', error);
    }
  };

  const handleAddWidget = async (widgetType: string) => {
    setShowWidgetLibrary(false);

    if (!id) {
      alert('Please save the dashboard first');
      return;
    }

    // Find next available position
    const maxY = layout.length > 0 ? Math.max(...layout.map((l) => l.y + l.h)) : 0;

    const newWidget: Partial<Widget> = {
      type: widgetType,
      title: widgetType.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase()),
      config: {},
      x: 0,
      y: maxY,
      w: 4,
      h: 4,
    };

    try {
      const created = await dashboardAPI.addWidget(id, newWidget);
      
      const fullWidget: Widget = {
        ...created,
        id: created.id!,
        type: created.type,
        title: created.title,
        config: created.config,
        x: created.x,
        y: created.y,
        w: created.w,
        h: created.h,
      };

      setWidgets([...widgets, fullWidget]);
      setLayout([
        ...layout,
        { i: fullWidget.id, x: fullWidget.x, y: fullWidget.y, w: fullWidget.w, h: fullWidget.h },
      ]);

      console.log('Widget added successfully');
    } catch (error: any) {
      console.error('Failed to add widget:', error);
      alert('Failed to add widget');
    }
  };

  const handleRemoveWidget = async (widgetId: string) => {
    if (!id) return;

    try {
      await dashboardAPI.deleteWidget(id, widgetId);
      setWidgets(widgets.filter((w) => w.id !== widgetId));
      setLayout(layout.filter((l) => l.i !== widgetId));
      console.log('Widget removed successfully');
    } catch (error: any) {
      console.error('Failed to remove widget:', error);
      alert('Failed to remove widget');
    }
  };

  const handleSaveDashboard = async (data: Partial<Dashboard>) => {
    try {
      if (id) {
        await dashboardAPI.updateDashboard(id, data);
        console.log('Dashboard updated successfully');
      } else {
        const created = await dashboardAPI.createDashboard(data);
        console.log('Dashboard created successfully');
        navigate(`/dashboards/${created.id}/edit`);
      }
      setShowSettings(false);
      if (id) {
        loadDashboard(id);
      }
    } catch (error: any) {
      console.error('Failed to save dashboard:', error);
      alert('Failed to save dashboard');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => navigate('/dashboards')}
              className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
            >
              ← Back
            </button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                {dashboard?.name || 'New Dashboard'}
              </h1>
              {dashboard?.description && (
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  {dashboard.description}
                </p>
              )}
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={() => setIsEditing(!isEditing)}
              className={`px-4 py-2 rounded-lg transition-colors ${
                isEditing
                  ? 'bg-green-600 text-white hover:bg-green-700'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {isEditing ? '✓ Done Editing' : '✏️ Edit'}
            </button>

            {isEditing && (
              <>
                <button
                  onClick={() => setShowWidgetLibrary(true)}
                  className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                >
                  + Add Widget
                </button>
                <button
                  onClick={() => setShowSettings(true)}
                  className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                >
                  ⚙️ Settings
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Dashboard Grid */}
      <div className="flex-1 overflow-auto p-6">
        {widgets.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="text-6xl mb-4">📊</div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                No Widgets Yet
              </h2>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                Start building your dashboard by adding widgets
              </p>
              <button
                onClick={() => setShowWidgetLibrary(true)}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
              >
                + Add Your First Widget
              </button>
            </div>
          </div>
        ) : (
          <ResponsiveGridLayout
            className="layout"
            layouts={{ lg: layout }}
            breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 }}
            cols={{ lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 }}
            rowHeight={80}
            isDraggable={isEditing}
            isResizable={isEditing}
            onLayoutChange={handleLayoutChange}
            draggableCancel=".no-drag"
          >
            {widgets.map((widget) => (
              <div
                key={widget.id}
                className="bg-white dark:bg-gray-800 rounded-lg shadow-md border border-gray-200 dark:border-gray-700 overflow-hidden"
              >
                {isEditing && (
                  <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-600">
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300 truncate">
                      {widget.title}
                    </span>
                    <button
                      onClick={() => handleRemoveWidget(widget.id)}
                      className="no-drag text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 text-sm px-2"
                    >
                      🗑️
                    </button>
                  </div>
                )}
                <div className="p-4 h-full overflow-auto">
                  <WidgetRenderer widget={widget as any} isEditMode={isEditing} />
                </div>
              </div>
            ))}
          </ResponsiveGridLayout>
        )}
      </div>

      {/* Widget Library Modal */}
      {showWidgetLibrary && (
        <WidgetLibrary
          onClose={() => setShowWidgetLibrary(false)}
          onSelectWidget={handleAddWidget}
        />
      )}

      {/* Dashboard Settings Modal */}
      {showSettings && (
        <DashboardSettings
          dashboard={dashboard}
          onClose={() => setShowSettings(false)}
          onSave={handleSaveDashboard}
        />
      )}
    </div>
  );
};

export default DashboardBuilder;
