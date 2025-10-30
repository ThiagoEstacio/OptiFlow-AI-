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
import { PieChart } from '../Visualizations/PieChart';
import { BarChart } from '../Visualizations/BarChart';
import { HeatmapChart } from '../Visualizations/HeatmapChart';
import { KPICard } from '../Widgets/KPICard';
import { StatusIndicator } from '../Widgets/StatusIndicator';
import { DataTable } from '../Widgets/DataTable';
import { ProgressWidget } from '../Widgets/ProgressWidget';
import { SparklineWidget } from '../Widgets/SparklineWidget';
import { useLiveTagData } from '../../hooks/useLiveTagData';
import { Activity } from 'lucide-react';

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

  // Debug log
  console.log('WidgetComponent rendering:', widget.id, widget.type, widget.position);

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
        // Check if we have multiple tags
        const hasMultipleTags = widget.config.tagIds && widget.config.tagIds.length > 1;
        
        console.log('Timeseries widget config:', {
          tagId: widget.config.tagId,
          tagIds: widget.config.tagIds,
          hasMultipleTags
        });
        
        if (hasMultipleTags) {
          // Generate data for multiple series
          const generateMultiSeriesData = () => {
            const data: Array<{ timestamp: string; [key: string]: any }> = [];
            const now = Date.now();
            const points = 50;
            
            for (let i = points; i >= 0; i--) {
              const timestamp = new Date(now - i * 60000).toISOString();
              const dataPoint: any = { timestamp };
              
              // Generate data for each tag
              widget.config.tagIds!.forEach((tagId, index) => {
                const range = 100; // Default range
                const baseValue = 50 + (index * 10); // Offset each series
                const variation = (Math.random() - 0.5) * (range * 0.3);
                const wave = Math.sin((points - i) / 5 + index) * (range * 0.2);
                dataPoint[tagId] = Math.max(0, Math.min(100, baseValue + variation + wave));
              });
              
              data.push(dataPoint);
            }
            return data;
          };

          // Create series config for each tag
          const seriesConfig = widget.config.tagIds!.map((tagId, index) => ({
            dataKey: tagId,
            label: tagId, // TODO: Get tag name from tags list
            color: ['#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6'][index % 5],
            yAxisId: index < 2 ? 'left' : 'right', // First 2 on left, rest on right
          }));

          return (
            <TimeSeriesChart
              data={generateMultiSeriesData()}
              series={seriesConfig}
              title={widget.config.title || 'Multi-Variable Chart'}
              height={widget.size.height - 60}
              showLegend={true}
            />
          );
        } else {
          // Single tag - original behavior
          const generateTimeSeriesData = () => {
            const data: Array<{ timestamp: string; value: number }> = [];
            const now = Date.now();
            const points = 50;
            const range = (widget.config.max ?? 100) - (widget.config.min ?? 0);
            const baseValue = typeof value === 'number' ? value : (widget.config.min ?? 0) + range * 0.5;

            for (let i = points; i >= 0; i--) {
              const timestamp = new Date(now - i * 60000).toISOString();
              const variation = (Math.random() - 0.5) * (range * 0.3);
              const wave = Math.sin((points - i) / 5) * (range * 0.2);
              const dataValue = Math.max(
                widget.config.min ?? 0,
                Math.min(widget.config.max ?? 100, baseValue + variation + wave)
              );
              data.push({ timestamp, value: dataValue });
            }
            return data;
          };

          return (
            <TimeSeriesChart
              data={generateTimeSeriesData()}
              title={widget.config.title || widget.config.tagName || 'Time Series'}
              height={widget.size.height - 60}
              showLegend={false}
              color={widget.config.color || '#3B82F6'}
              unit={widget.config.unit}
            />
          );
        }

      case 'chart':
        return (
          <div className="p-4 text-center text-gray-500">
            Chart widget - Coming soon
          </div>
        );

      case 'kpi':
        return (
          <KPICard
            title={widget.config.title || 'KPI'}
            value={typeof value === 'number' ? value : 0}
            unit={widget.config.unit}
            previousValue={widget.config.previousValue}
            target={widget.config.target}
            trend={widget.config.trend}
            format={widget.config.format}
            decimals={widget.config.decimals || 1}
            status={typeof value === 'number' && widget.config.max
              ? value >= widget.config.max * 0.9 ? 'critical' : value >= widget.config.max * 0.75 ? 'warning' : 'good'
              : 'neutral'}
            theme={widget.config.theme}
            size={widget.config.size}
            icon={<Activity className="w-5 h-5" />}
          />
        );

      case 'status':
        const determineStatus = () => {
          if (widget.config.status) return widget.config.status;
          if (typeof value === 'number' && widget.config.max) {
            if (value >= widget.config.max * 0.9) return 'alarm';
            if (value >= widget.config.max * 0.75) return 'warning';
            if (value > widget.config.min!) return 'running';
          }
          return 'idle';
        };

        return (
          <StatusIndicator
            label={widget.config.title || 'Status'}
            status={determineStatus()}
            value={typeof value === 'number' ? value : undefined}
            unit={widget.config.unit}
            size={widget.config.size}
          />
        );

      case 'progress':
        return (
          <ProgressWidget
            title={widget.config.title || 'Progress'}
            value={typeof value === 'number' ? value : 0}
            max={widget.config.max}
            min={widget.config.min}
            unit={widget.config.unit}
            target={widget.config.target}
            thresholds={widget.config.thresholds}
            type={widget.config.progressType || 'bar'}
            size={widget.config.size}
            showPercentage={true}
            showValue={true}
          />
        );

      case 'sparkline':
        // Generate mock historical data for sparkline
        const generateSparklineData = () => {
          const dataPoints = 20;
          const data: number[] = [];
          const current = typeof value === 'number' ? value : 50;
          const range = (widget.config.max ?? 100) - (widget.config.min ?? 0);

          for (let i = 0; i < dataPoints; i++) {
            const variation = (Math.random() - 0.5) * (range * 0.2);
            data.push(Math.max(widget.config.min ?? 0, Math.min(widget.config.max ?? 100, current + variation)));
          }
          return data;
        };

        return (
          <SparklineWidget
            title={widget.config.title || 'Trend'}
            data={generateSparklineData()}
            currentValue={typeof value === 'number' ? value : undefined}
            unit={widget.config.unit}
            style={widget.config.sparklineStyle}
            showMinMax={widget.config.showMinMax}
            showTrend={widget.config.showTrend}
            decimals={widget.config.decimals || 1}
          />
        );

      case 'pie':
        // Mock data for pie chart
        const pieData = [
          { name: 'Running', value: typeof value === 'number' ? value : 60 },
          { name: 'Idle', value: 25 },
          { name: 'Stopped', value: 15 },
        ];
        return (
          <PieChart
            data={pieData}
            title={widget.config.title || 'Distribution'}
            height={widget.size.height - 60}
          />
        );

      case 'bar':
        // Mock data for bar chart
        const barData = [
          { category: 'Conv 1', value: typeof value === 'number' ? value : 120 },
          { category: 'Conv 2', value: 150 },
          { category: 'Elevator', value: 180 },
          { category: 'Shiploader', value: 200 },
        ];
        return (
          <BarChart
            data={barData}
            title={widget.config.title || 'Comparison'}
            height={widget.size.height - 60}
          />
        );

      case 'table':
        // Mock table data
        const tableData = [
          { id: 1, name: 'Conveyor 1', value: typeof value === 'number' ? value.toFixed(1) : '0', status: 'good', unit: widget.config.unit },
          { id: 2, name: 'Conveyor 2', value: '145.3', status: 'good', unit: widget.config.unit },
          { id: 3, name: 'Elevator', value: '180.2', status: 'warning', unit: widget.config.unit },
          { id: 4, name: 'Shiploader', value: '220.5', status: 'good', unit: widget.config.unit },
        ];

        const tableColumns = [
          { key: 'name', label: 'Equipment', sortable: true },
          { key: 'value', label: 'Value', format: 'number', decimals: 1, sortable: true },
          { key: 'unit', label: 'Unit', sortable: false },
          { key: 'status', label: 'Status', format: 'status', align: 'center' },
        ];

        return (
          <DataTable
            columns={tableColumns}
            data={tableData}
            title={widget.config.title}
            size={widget.config.size}
          />
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
          zIndex: isSelected ? 100 : 10,
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
              ${isSelected ? 'border-blue-500 shadow-lg' : 'border-gray-300'}
              ${isOver && canDrop ? 'border-green-400 bg-green-50' : ''}
            `}
            style={{
              backgroundColor: 'white',
              minHeight: '150px',
              minWidth: '200px',
            }}
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
