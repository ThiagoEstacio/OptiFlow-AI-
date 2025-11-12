import React, { useState, useEffect } from 'react';
import { useLiveTagData } from '../../../hooks/useLiveTagData';

interface Widget {
  id: string;
  title: string;
  config: any;
  data_config: any;
  display_config: any;
}

interface HeatmapWidgetProps {
  widget: Widget;
}

const HeatmapWidget: React.FC<HeatmapWidgetProps> = ({ widget }) => {
  const tagIds = widget.config?.tagIds || widget.data_config?.tagIds || [];
  
  // Get live data for all tags
  const tagData = tagIds.map((tagId: string, index: number) => {
    const data = useLiveTagData({ tagId });
    return {
      name: widget.config?.tagNames?.[index] || `Tag ${index + 1}`,
      value: typeof data.value === 'number' ? data.value : 0,
      loading: data.loading,
    };
  });

  const loading = tagData.some(t => t.loading);

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (tagIds.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center text-gray-400">
          <div className="text-5xl mb-2">🔥</div>
          <p className="text-sm">Drag tags for heatmap</p>
        </div>
      </div>
    );
  }

  // Get min and max values for color scaling
  const values = tagData.map(t => t.value);
  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);

  // Get color based on value (normalized 0-1)
  const getColor = (value: number) => {
    if (maxValue === minValue) return '#3B82F6';
    
    const normalized = (value - minValue) / (maxValue - minValue);
    
    // Color gradient: blue (cold) -> green -> yellow -> red (hot)
    if (normalized < 0.25) {
      // Blue to Cyan
      const t = normalized / 0.25;
      return `rgb(${Math.round(59 * (1 - t) + 6 * t)}, ${Math.round(130 * (1 - t) + 182 * t)}, ${Math.round(246 * (1 - t) + 212 * t)})`;
    } else if (normalized < 0.5) {
      // Cyan to Green
      const t = (normalized - 0.25) / 0.25;
      return `rgb(${Math.round(6 * (1 - t) + 16 * t)}, ${Math.round(182 * (1 - t) + 185 * t)}, ${Math.round(212 * (1 - t) + 129 * t)})`;
    } else if (normalized < 0.75) {
      // Green to Yellow
      const t = (normalized - 0.5) / 0.25;
      return `rgb(${Math.round(16 * (1 - t) + 245 * t)}, ${Math.round(185 * (1 - t) + 158 * t)}, ${Math.round(129 * (1 - t) + 11 * t)})`;
    } else {
      // Yellow to Red
      const t = (normalized - 0.75) / 0.25;
      return `rgb(${Math.round(245 * (1 - t) + 239 * t)}, ${Math.round(158 * (1 - t) + 68 * t)}, ${Math.round(11 * (1 - t) + 68 * t)})`;
    }
  };

  // Calculate grid dimensions (try to make it somewhat square)
  const totalTags = tagData.length;
  const cols = Math.ceil(Math.sqrt(totalTags));
  const rows = Math.ceil(totalTags / cols);

  return (
    <div className="h-full flex flex-col p-4">
      {/* Title */}
      <div className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">
        {widget.title || 'Heatmap'}
      </div>

      {/* Heatmap Grid */}
      <div className="flex-1 min-h-0 overflow-auto">
        <div
          className="grid gap-2 h-full"
          style={{
            gridTemplateColumns: `repeat(${cols}, 1fr)`,
            gridTemplateRows: `repeat(${rows}, 1fr)`,
          }}
        >
          {tagData.map((tag, index) => (
            <div
              key={index}
              className="relative rounded-lg shadow-sm overflow-hidden transition-all duration-300 hover:scale-105 hover:shadow-lg"
              style={{
                backgroundColor: getColor(tag.value),
              }}
            >
              <div className="absolute inset-0 flex flex-col items-center justify-center p-2 text-white">
                <div className="text-xs font-medium text-center mb-1 drop-shadow-lg">
                  {tag.name}
                </div>
                <div className="text-lg font-bold drop-shadow-lg">
                  {tag.value.toFixed(1)}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Color Legend */}
      <div className="mt-4">
        <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
          <span>{minValue.toFixed(1)}</span>
          <span className="font-medium text-gray-700 dark:text-gray-300">Value Range</span>
          <span>{maxValue.toFixed(1)}</span>
        </div>
        <div
          className="h-3 rounded-full"
          style={{
            background: 'linear-gradient(to right, rgb(59, 130, 246), rgb(6, 182, 212), rgb(16, 185, 129), rgb(245, 158, 11), rgb(239, 68, 68))',
          }}
        />
      </div>
    </div>
  );
};

export default HeatmapWidget;
