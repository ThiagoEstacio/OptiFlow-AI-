/**
 * Widget Toolbar - Professional Modern Design
 * Organized widget categories for easy access with modern UI
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  ChevronDown,
  Gauge,
  LineChart,
  Hash,
  Activity,
  BarChart3,
  TrendingUp,
  PieChart,
  Table2,
  Thermometer,
  CircleDot,
  Plus,
  Bell,
  Map,
  Type,
  Image,
  Video
} from 'lucide-react';

type WidgetType = 'gauge' | 'timeseries' | 'value' | 'chart' | 'kpi' | 'status' | 'table' | 'progress' | 'sparkline' | 'pie' | 'bar' | 'heatmap' | 'alarm' | 'map' | 'text' | 'image' | 'video';

interface WidgetToolbarProps {
  onAddWidget: (type: WidgetType) => void;
}

export const WidgetToolbar: React.FC<WidgetToolbarProps> = ({ onAddWidget }) => {
  const [expandedCategory, setExpandedCategory] = useState<string>('');
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setExpandedCategory('');
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const widgetCategories = [
    {
      id: 'indicators',
      label: 'Indicators',
      icon: <Activity className="w-4 h-4" />,
      color: 'from-blue-500 to-blue-600',
      widgets: [
        { type: 'kpi' as const, icon: <TrendingUp className="w-5 h-5" />, label: 'KPI Card', description: 'Key Performance Indicator with trends', color: 'text-blue-600 bg-blue-50' },
        { type: 'gauge' as const, icon: <Gauge className="w-5 h-5" />, label: 'Gauge', description: 'Dial/speedometer display', color: 'text-green-600 bg-green-50' },
        { type: 'value' as const, icon: <Hash className="w-5 h-5" />, label: 'Value', description: 'Large number display', color: 'text-purple-600 bg-purple-50' },
        { type: 'status' as const, icon: <CircleDot className="w-5 h-5" />, label: 'Status', description: 'Equipment status indicator', color: 'text-orange-600 bg-orange-50' },
      ]
    },
    {
      id: 'progress',
      label: 'Progress',
      icon: <Thermometer className="w-4 h-4" />,
      color: 'from-green-500 to-green-600',
      widgets: [
        { type: 'progress' as const, icon: <Thermometer className="w-5 h-5" />, label: 'Progress Bar', description: 'Progress/loading bar', color: 'text-green-600 bg-green-50' },
        { type: 'sparkline' as const, icon: <TrendingUp className="w-5 h-5" />, label: 'Sparkline', description: 'Compact trend chart', color: 'text-cyan-600 bg-cyan-50' },
      ]
    },
    {
      id: 'charts',
      label: 'Charts',
      icon: <LineChart className="w-4 h-4" />,
      color: 'from-purple-500 to-purple-600',
      widgets: [
        { type: 'timeseries' as const, icon: <LineChart className="w-5 h-5" />, label: 'Time Series', description: 'Historical trend chart', color: 'text-indigo-600 bg-indigo-50' },
        { type: 'bar' as const, icon: <BarChart3 className="w-5 h-5" />, label: 'Bar Chart', description: 'Comparison bar chart', color: 'text-pink-600 bg-pink-50' },
        { type: 'pie' as const, icon: <PieChart className="w-5 h-5" />, label: 'Pie Chart', description: 'Distribution pie chart', color: 'text-amber-600 bg-amber-50' },
        { type: 'heatmap' as const, icon: <Activity className="w-5 h-5" />, label: 'Heat Map', description: 'Data density visualization', color: 'text-red-600 bg-red-50' },
      ]
    },
    {
      id: 'data',
      label: 'Data',
      icon: <Table2 className="w-4 h-4" />,
      color: 'from-gray-500 to-gray-600',
      widgets: [
        { type: 'table' as const, icon: <Table2 className="w-5 h-5" />, label: 'Table', description: 'Data table with sorting', color: 'text-gray-600 bg-gray-50' },
        { type: 'alarm' as const, icon: <Bell className="w-5 h-5" />, label: 'Alarm List', description: 'Active alarms panel', color: 'text-red-600 bg-red-50' },
      ]
    },
    {
      id: 'media',
      label: 'Media',
      icon: <Image className="w-4 h-4" />,
      color: 'from-cyan-500 to-cyan-600',
      widgets: [
        { type: 'text' as const, icon: <Type className="w-5 h-5" />, label: 'Text', description: 'Rich text block', color: 'text-slate-600 bg-slate-50' },
        { type: 'image' as const, icon: <Image className="w-5 h-5" />, label: 'Image', description: 'Image or logo', color: 'text-cyan-600 bg-cyan-50' },
        { type: 'video' as const, icon: <Video className="w-5 h-5" />, label: 'Video', description: 'Video stream or file', color: 'text-violet-600 bg-violet-50' },
        { type: 'map' as const, icon: <Map className="w-5 h-5" />, label: 'Map', description: 'Geographic map view', color: 'text-emerald-600 bg-emerald-50' },
      ]
    },
  ];

  const toggleCategory = (categoryId: string) => {
    setExpandedCategory(expandedCategory === categoryId ? '' : categoryId);
  };

  return (
    <div className="bg-gradient-to-r from-gray-50 to-white dark:from-gray-800 dark:to-gray-900 border-b border-gray-200/80 dark:border-gray-700 shadow-sm">
      {/* Main toolbar */}
      <div className="px-6 py-3 flex items-center" ref={dropdownRef}>
        {/* Add Widget Label */}
        <div className="flex items-center gap-2 mr-4">
          <div className="p-1.5 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
            <Plus className="w-4 h-4 text-blue-600 dark:text-blue-400" />
          </div>
          <span className="text-sm font-semibold text-gray-700 dark:text-gray-200">Add Widget</span>
        </div>

        {/* Category Buttons */}
        <div className="flex items-center gap-2">
          {widgetCategories.map((category) => (
            <div key={category.id} className="relative">
              {/* Category button */}
              <button
                onClick={() => toggleCategory(category.id)}
                className={`
                  flex items-center gap-2 px-4 py-2 rounded-lg transition-all duration-200
                  ${expandedCategory === category.id
                    ? `bg-gradient-to-r ${category.color} text-white shadow-md`
                    : 'bg-white dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-200 border border-gray-200 dark:border-gray-600 hover:shadow-sm'}
                `}
              >
                {category.icon}
                <span className="text-sm font-medium">{category.label}</span>
                <ChevronDown
                  className={`w-4 h-4 transition-transform duration-200 ${
                    expandedCategory === category.id ? 'rotate-180' : ''
                  }`}
                />
              </button>

              {/* Dropdown with widgets */}
              {expandedCategory === category.id && (
                <div className="absolute top-full left-0 mt-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-xl z-50 min-w-[280px] overflow-hidden animate-in fade-in slide-in-from-top-2 duration-200">
                  <div className="p-2 space-y-1">
                    {category.widgets.map((widget) => (
                      <button
                        key={widget.type}
                        onClick={() => {
                          onAddWidget(widget.type);
                          setExpandedCategory('');
                        }}
                        className="w-full flex items-center gap-3 px-3 py-3 hover:bg-gray-50 dark:hover:bg-gray-700/50 rounded-lg transition-all group text-left"
                        title={widget.description}
                      >
                        <div className={`p-2 rounded-lg ${widget.color} transition-transform group-hover:scale-110`}>
                          {widget.icon}
                        </div>
                        <div className="flex-1">
                          <div className="text-sm font-semibold text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400">
                            {widget.label}
                          </div>
                          <div className="text-xs text-gray-500 dark:text-gray-400">
                            {widget.description}
                          </div>
                        </div>
                        <Plus className="w-4 h-4 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Quick Access Section */}
        <div className="flex items-center gap-1 pl-4 border-l border-gray-300 dark:border-gray-600">
          <span className="text-xs font-medium text-gray-500 dark:text-gray-400 mr-3 uppercase tracking-wide">Quick Add</span>
          {[
            { type: 'kpi' as const, icon: <TrendingUp className="w-4 h-4" />, label: 'KPI', color: 'hover:bg-blue-50 hover:text-blue-600 dark:hover:bg-blue-900/30 dark:hover:text-blue-400' },
            { type: 'gauge' as const, icon: <Gauge className="w-4 h-4" />, label: 'Gauge', color: 'hover:bg-green-50 hover:text-green-600 dark:hover:bg-green-900/30 dark:hover:text-green-400' },
            { type: 'timeseries' as const, icon: <LineChart className="w-4 h-4" />, label: 'Chart', color: 'hover:bg-purple-50 hover:text-purple-600 dark:hover:bg-purple-900/30 dark:hover:text-purple-400' },
            { type: 'table' as const, icon: <Table2 className="w-4 h-4" />, label: 'Table', color: 'hover:bg-gray-100 hover:text-gray-700 dark:hover:bg-gray-700 dark:hover:text-gray-200' },
          ].map((widget) => (
            <button
              key={widget.type}
              onClick={() => onAddWidget(widget.type)}
              className={`p-2.5 rounded-lg text-gray-500 dark:text-gray-400 transition-all ${widget.color} hover:shadow-sm`}
              title={`Add ${widget.label}`}
            >
              {widget.icon}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
