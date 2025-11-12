import React, { useState } from 'react';

interface WidgetType {
  id: string;
  name: string;
  description: string;
  icon: string;
  category: string;
}

const WIDGET_TYPES: WidgetType[] = [
  // Visualization Widgets
  { id: 'kpi_card', name: 'KPI Card', description: 'Single metric with trend', icon: '📊', category: 'Visualization' },
  { id: 'stat', name: 'Stat', description: 'Large single value display', icon: '🔢', category: 'Visualization' },
  { id: 'gauge', name: 'Gauge', description: 'Radial progress meter', icon: '🎯', category: 'Visualization' },
  { id: 'bar_gauge', name: 'Bar Gauge', description: 'Horizontal bar progress', icon: '▬', category: 'Visualization' },
  
  // Time Series Charts
  { id: 'line_chart', name: 'Time Series', description: 'Line chart over time', icon: '📈', category: 'Time Series' },
  { id: 'area_chart', name: 'Area Chart', description: 'Filled area graph', icon: '⛰️', category: 'Time Series' },
  { id: 'bar_chart', name: 'Bar Chart', description: 'Vertical bars', icon: '📊', category: 'Time Series' },
  { id: 'candlestick', name: 'Candlestick', description: 'OHLC financial chart', icon: '🕯️', category: 'Time Series' },
  
  // Comparison Charts
  { id: 'horizontal_bar', name: 'Horizontal Bar', description: 'Compare categories', icon: '▬▬▬', category: 'Comparison' },
  { id: 'pie_chart', name: 'Pie Chart', description: 'Proportion breakdown', icon: '🥧', category: 'Comparison' },
  { id: 'donut_chart', name: 'Donut Chart', description: 'Ring chart', icon: '�', category: 'Comparison' },
  { id: 'heatmap', name: 'Heatmap', description: 'Color-coded matrix', icon: '�', category: 'Comparison' },
  
  // Data Display
  { id: 'table', name: 'Table', description: 'Sortable data table', icon: '📋', category: 'Data Display' },
  { id: 'logs', name: 'Logs', description: 'Live log viewer', icon: '📜', category: 'Data Display' },
  { id: 'json', name: 'JSON', description: 'Formatted JSON display', icon: '{ }', category: 'Data Display' },
  
  // Industrial/SCADA
  { id: 'process_status', name: 'Process Status', description: 'Live process states', icon: '⚙️', category: 'Industrial' },
  { id: 'equipment_health', name: 'Equipment Health', description: 'Asset condition', icon: '🔧', category: 'Industrial' },
  { id: 'oee', name: 'OEE Dashboard', description: 'Overall Equipment Effectiveness', icon: '📈', category: 'Industrial' },
  { id: 'motor_status', name: 'Motor Status', description: 'Motor monitoring', icon: '🔌', category: 'Industrial' },
  { id: 'tank_level', name: 'Tank Level', description: 'Visual tank display', icon: '⛽', category: 'Industrial' },
  { id: 'valve_status', name: 'Valve Control', description: 'Valve open/close', icon: '🚰', category: 'Industrial' },
  
  // Alerts & Events
  { id: 'active_alarms', name: 'Active Alarms', description: 'Current alarms list', icon: '�', category: 'Alerts' },
  { id: 'alarm_history', name: 'Alarm History', description: 'Recent alarm log', icon: '📋', category: 'Alerts' },
  { id: 'notification_list', name: 'Notifications', description: 'System notifications', icon: '🔔', category: 'Alerts' },
  
  // Analytics
  { id: 'trend_analysis', name: 'Trend Analysis', description: 'Statistical trends', icon: '📊', category: 'Analytics' },
  { id: 'distribution', name: 'Distribution', description: 'Value distribution', icon: '�', category: 'Analytics' },
  { id: 'correlation', name: 'Correlation', description: 'Variable correlation', icon: '🔗', category: 'Analytics' },
  { id: 'anomaly_detection', name: 'Anomaly Detection', description: 'ML-based anomalies', icon: '🔍', category: 'Analytics' },
  
  // Maps & Geo
  { id: 'geomap', name: 'Geo Map', description: 'Geographic visualization', icon: '�️', category: 'Maps' },
  { id: 'facility_map', name: 'Facility Map', description: 'Plant layout', icon: '🏭', category: 'Maps' },
  
  // Custom
  { id: 'iframe', name: 'iFrame', description: 'Embed external content', icon: '🖼️', category: 'Custom' },
  { id: 'html', name: 'HTML', description: 'Custom HTML content', icon: '�', category: 'Custom' },
  { id: 'image', name: 'Image', description: 'Display image', icon: '�️', category: 'Custom' },
];

const CATEGORIES = [
  'All', 
  'Visualization', 
  'Time Series', 
  'Comparison', 
  'Data Display', 
  'Industrial', 
  'Alerts', 
  'Analytics', 
  'Maps', 
  'Custom'
];

interface WidgetLibraryProps {
  onClose: () => void;
  onSelectWidget: (widgetType: string) => void;
}

const WidgetLibrary: React.FC<WidgetLibraryProps> = ({ onClose, onSelectWidget }) => {
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredWidgets = WIDGET_TYPES.filter((widget) => {
    const matchesCategory = selectedCategory === 'All' || widget.category === selectedCategory;
    const matchesSearch = widget.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          widget.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-2xl max-w-4xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Widget Library</h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 text-2xl"
            >
              ×
            </button>
          </div>
          
          {/* Search */}
          <div className="mt-4">
            <input
              type="text"
              placeholder="Search widgets..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
          </div>
        </div>

        {/* Category Tabs */}
        <div className="px-6 py-3 border-b border-gray-200 dark:border-gray-700 overflow-x-auto">
          <div className="flex space-x-2">
            {CATEGORIES.map((category) => (
              <button
                key={category}
                onClick={() => setSelectedCategory(category)}
                className={`px-4 py-2 rounded-lg font-medium transition-colors whitespace-nowrap ${
                  selectedCategory === category
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                {category}
              </button>
            ))}
          </div>
        </div>

        {/* Widget Grid */}
        <div className="flex-1 overflow-y-auto p-6">
          {filteredWidgets.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">🔍</div>
              <p className="text-gray-600 dark:text-gray-400">No widgets found</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredWidgets.map((widget) => (
                <button
                  key={widget.id}
                  onClick={() => onSelectWidget(widget.id)}
                  className="p-4 border-2 border-gray-200 dark:border-gray-600 rounded-lg hover:border-blue-500 dark:hover:border-blue-400 hover:shadow-lg transition-all text-left group"
                >
                  <div className="flex items-start space-x-3">
                    <div className="text-4xl group-hover:scale-110 transition-transform">
                      {widget.icon}
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400">
                        {widget.name}
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                        {widget.description}
                      </p>
                      <span className="inline-block mt-2 text-xs px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded">
                        {widget.category}
                      </span>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            💡 Tip: Click on any widget to add it to your dashboard
          </p>
        </div>
      </div>
    </div>
  );
};

export default WidgetLibrary;
