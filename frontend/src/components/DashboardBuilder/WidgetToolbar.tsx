/**
 * Widget Toolbar - Professional
 * Organized widget categories for easy access
 */

import React, { useState } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';

type WidgetType = 'gauge' | 'timeseries' | 'value' | 'chart' | 'kpi' | 'status' | 'table' | 'progress' | 'sparkline' | 'pie' | 'bar' | 'heatmap';

interface WidgetToolbarProps {
  onAddWidget: (type: WidgetType) => void;
}

export const WidgetToolbar: React.FC<WidgetToolbarProps> = ({ onAddWidget }) => {
  const [expandedCategory, setExpandedCategory] = useState<string>('indicators');

  const widgetCategories = [
    {
      id: 'indicators',
      label: 'Indicators',
      widgets: [
        { type: 'kpi' as const, icon: '📊', label: 'KPI Card', description: 'Key Performance Indicator with trends' },
        { type: 'gauge' as const, icon: '🎯', label: 'Gauge', description: 'Dial/speedometer display' },
        { type: 'value' as const, icon: '🔢', label: 'Value', description: 'Large number display' },
        { type: 'status' as const, icon: '🚦', label: 'Status', description: 'Equipment status indicator' },
      ]
    },
    {
      id: 'progress',
      label: 'Progress',
      widgets: [
        { type: 'progress' as const, icon: '📶', label: 'Progress Bar', description: 'Progress/loading bar' },
        { type: 'sparkline' as const, icon: '📉', label: 'Sparkline', description: 'Compact trend chart' },
      ]
    },
    {
      id: 'charts',
      label: 'Charts',
      widgets: [
        { type: 'timeseries' as const, icon: '📈', label: 'Time Series', description: 'Historical trend chart' },
        { type: 'bar' as const, icon: '📊', label: 'Bar Chart', description: 'Comparison bar chart' },
        { type: 'pie' as const, icon: '🥧', label: 'Pie Chart', description: 'Distribution pie chart' },
        { type: 'heatmap' as const, icon: '🗺️', label: 'Heat Map', description: 'Data density visualization' },
      ]
    },
    {
      id: 'data',
      label: 'Data',
      widgets: [
        { type: 'table' as const, icon: '📋', label: 'Table', description: 'Data table with sorting' },
      ]
    },
  ];

  const toggleCategory = (categoryId: string) => {
    setExpandedCategory(expandedCategory === categoryId ? '' : categoryId);
  };

  return (
    <div className="bg-white border-b border-gray-200">
      {/* Main toolbar */}
      <div className="px-4 py-2 flex items-center space-x-1">
        <span className="text-sm font-semibold text-gray-700 mr-3">Add Widget:</span>

        {widgetCategories.map((category) => (
          <div key={category.id} className="relative group">
            {/* Category button */}
            <button
              onClick={() => toggleCategory(category.id)}
              className={`
                flex items-center space-x-1 px-3 py-2 rounded transition-colors
                ${expandedCategory === category.id
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-gray-100 hover:bg-gray-200 text-gray-700'}
              `}
            >
              <span className="text-sm font-medium">{category.label}</span>
              {expandedCategory === category.id ? (
                <ChevronDown className="w-4 h-4" />
              ) : (
                <ChevronRight className="w-4 h-4" />
              )}
            </button>

            {/* Dropdown with widgets */}
            {expandedCategory === category.id && (
              <div className="absolute top-full left-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-50 min-w-[200px]">
                <div className="p-2 space-y-1">
                  {category.widgets.map((widget) => (
                    <button
                      key={widget.type}
                      onClick={() => {
                        onAddWidget(widget.type);
                        setExpandedCategory('');
                      }}
                      className="w-full flex items-center space-x-3 px-3 py-2 hover:bg-blue-50 rounded transition-colors group text-left"
                      title={widget.description}
                    >
                      <span className="text-2xl">{widget.icon}</span>
                      <div className="flex-1">
                        <div className="text-sm font-medium text-gray-900 group-hover:text-blue-700">
                          {widget.label}
                        </div>
                        <div className="text-xs text-gray-500">
                          {widget.description}
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}

        {/* Quick access popular widgets */}
        <div className="flex-1" />
        <div className="border-l border-gray-300 pl-3 flex items-center space-x-1">
          <span className="text-xs text-gray-500 mr-2">Quick:</span>
          {[
            { type: 'kpi' as const, icon: '📊' },
            { type: 'gauge' as const, icon: '🎯' },
            { type: 'timeseries' as const, icon: '📈' },
            { type: 'table' as const, icon: '📋' },
          ].map((widget) => (
            <button
              key={widget.type}
              onClick={() => onAddWidget(widget.type)}
              className="p-2 hover:bg-gray-100 rounded transition-colors"
              title={`Add ${widget.type}`}
            >
              <span className="text-xl">{widget.icon}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
