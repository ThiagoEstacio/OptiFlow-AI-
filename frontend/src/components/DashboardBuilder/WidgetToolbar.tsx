/**
 * Widget Toolbar
 * Buttons to add new widgets to dashboard
 */

import React from 'react';

interface WidgetToolbarProps {
  onAddWidget: (type: 'gauge' | 'timeseries' | 'value' | 'chart') => void;
}

export const WidgetToolbar: React.FC<WidgetToolbarProps> = ({ onAddWidget }) => {
  const widgets = [
    { type: 'gauge' as const, icon: '🎯', label: 'Gauge', description: 'Dial/speedometer' },
    { type: 'value' as const, icon: '🔢', label: 'Value', description: 'Current value display' },
    { type: 'timeseries' as const, icon: '📈', label: 'Time Series', description: 'Historical chart' },
    { type: 'chart' as const, icon: '📊', label: 'Chart', description: 'Bar/pie chart' },
  ];

  return (
    <div className="bg-white border-b border-gray-200 px-4 py-2">
      <div className="flex items-center space-x-2">
        <span className="text-sm font-medium text-gray-700 mr-2">Add Widget:</span>
        {widgets.map((widget) => (
          <button
            key={widget.type}
            onClick={() => onAddWidget(widget.type)}
            className="flex items-center space-x-2 px-3 py-2 bg-gray-100 hover:bg-blue-100 rounded transition-colors group"
            title={widget.description}
          >
            <span className="text-xl">{widget.icon}</span>
            <span className="text-sm font-medium text-gray-700 group-hover:text-blue-700">
              {widget.label}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
};
