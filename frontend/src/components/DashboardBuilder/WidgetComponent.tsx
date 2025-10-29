/**
 * Widget Component
 * Individual widget that accepts tag drops and displays live data
 */

import React, { useState, useEffect, useRef } from 'react';
import { useDrop } from 'react-dnd';
import Draggable from 'react-draggable';
import { ResizableBox } from 'react-resizable';
import 'react-resizable/css/styles.css';
import type { Widget } from '../../pages/DashboardBuilderPage';
import { GaugeChart } from '../Visualizations/GaugeChart';
import { TimeSeriesChart } from '../Charts/TimeSeriesChart';
import { useLiveTagData } from '../../hooks/useLiveTagData';

interface WidgetComponentProps {
  widget: Widget;
  isSelected: boolean;
  onSelect: () => void;
  onUpdate: (updates: Partial<Widget>) => void;
  onDelete: () => void;
  onBindTag: (tagId: string) => void;
}

export const WidgetComponent: React.FC<WidgetComponentProps> = ({
  widget,
  isSelected,
  onSelect,
  onUpdate,
  onDelete,
  onBindTag,
}) => {
  const nodeRef = useRef(null);
  const [isEditing, setIsEditing] = useState(false);

  // Drop target for tags
  const [{ isOver, canDrop }, drop] = useDrop(() => ({
    accept: 'TAG',
    drop: (item: { tagId: string; tagName: string }) => {
      onBindTag(item.tagId);
      return { widgetId: widget.id };
    },
    collect: (monitor) => ({
      isOver: monitor.isOver(),
      canDrop: monitor.canDrop(),
    }),
  }));

  // Live data hook with min/max for realistic simulation
  const { value, timestamp, loading } = useLiveTagData({
    tagId: widget.config.tagId,
    min: widget.config.min ?? 0,
    max: widget.config.max ?? 100,
  });

  // Render widget content based on type
  const renderContent = () => {
    if (!widget.config.tagId) {
      return (
        <div className="flex items-center justify-center h-full text-gray-400 text-center p-4">
          <div>
            <p className="text-sm font-medium">No tag bound</p>
            <p className="text-xs mt-1">Drag a tag here to display data</p>
          </div>
        </div>
      );
    }

    if (loading) {
      return (
        <div className="flex items-center justify-center h-full">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      );
    }

    switch (widget.type) {
      case 'gauge':
        return (
          <GaugeChart
            value={typeof value === 'number' ? value : 0}
            min={widget.config.min ?? 0}
            max={widget.config.max ?? 100}
            unit={widget.config.unit}
            title={widget.config.title}
            height={widget.size.height - 60}
          />
        );

      case 'value':
        return (
          <div className="flex flex-col items-center justify-center h-full">
            <div className="text-4xl font-bold text-gray-900">
              {typeof value === 'number' ? value.toFixed(2) : value?.toString() || '--'}
            </div>
            {widget.config.unit && (
              <div className="text-lg text-gray-600 mt-2">{widget.config.unit}</div>
            )}
            {timestamp && (
              <div className="text-xs text-gray-400 mt-2">
                {new Date(timestamp).toLocaleTimeString()}
              </div>
            )}
          </div>
        );

      case 'timeseries':
        // For time series, we would fetch historical data
        // For now, show a placeholder
        return (
          <div className="p-4">
            <p className="text-sm text-gray-600 mb-2">Time Series Chart</p>
            <p className="text-xs text-gray-500">Tag: {widget.config.tagName}</p>
            <p className="text-xs text-gray-500">Current: {typeof value === 'number' ? value.toFixed(2) : value?.toString()}</p>
            <div className="mt-4 h-full bg-gray-100 rounded flex items-center justify-center text-gray-400">
              Historical chart would appear here
            </div>
          </div>
        );

      case 'chart':
        return (
          <div className="p-4 text-center text-gray-500">
            Chart widget - Coming soon
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <Draggable
      nodeRef={nodeRef}
      handle=".widget-handle"
      position={widget.position}
      onStop={(e, data) => {
        onUpdate({ position: { x: data.x, y: data.y } });
      }}
      disabled={!isSelected}
    >
      <div
        ref={nodeRef}
        style={{
          position: 'absolute',
          width: widget.size.width,
          height: widget.size.height,
        }}
        onClick={(e) => {
          e.stopPropagation();
          onSelect();
        }}
      >
        <ResizableBox
          width={widget.size.width}
          height={widget.size.height}
          onResizeStop={(e, data) => {
            onUpdate({ size: { width: data.size.width, height: data.size.height } });
          }}
          minConstraints={[200, 150]}
          maxConstraints={[800, 600]}
        >
          <div
            ref={drop}
            className={`
              w-full h-full bg-white rounded-lg shadow-md
              border-2 transition-all
              ${isSelected ? 'border-blue-500 shadow-lg' : 'border-transparent'}
              ${isOver && canDrop ? 'border-green-400 bg-green-50' : ''}
            `}
          >
            {/* Header */}
            <div className="widget-handle flex items-center justify-between px-3 py-2 bg-gray-50 border-b border-gray-200 rounded-t-lg cursor-move">
              <div className="flex-1 min-w-0">
                {isEditing ? (
                  <input
                    type="text"
                    value={widget.config.title || ''}
                    onChange={(e) => onUpdate({ config: { ...widget.config, title: e.target.value } })}
                    onBlur={() => setIsEditing(false)}
                    autoFocus
                    className="w-full px-2 py-1 text-sm border border-blue-300 rounded"
                  />
                ) : (
                  <h3
                    className="text-sm font-medium text-gray-900 truncate cursor-text"
                    onDoubleClick={() => setIsEditing(true)}
                  >
                    {widget.config.title || 'Untitled Widget'}
                  </h3>
                )}
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete();
                }}
                className="ml-2 text-gray-400 hover:text-red-600 text-sm"
                title="Delete widget"
              >
                ✕
              </button>
            </div>

            {/* Content */}
            <div className="p-2 h-[calc(100%-48px)]">
              {renderContent()}
            </div>
          </div>
        </ResizableBox>
      </div>
    </Draggable>
  );
};
