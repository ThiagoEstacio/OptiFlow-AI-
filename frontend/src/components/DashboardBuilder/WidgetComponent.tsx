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
import { Activity, GripVertical, Trash2, Settings, Maximize2, Link2 } from 'lucide-react';
import { WidgetErrorBoundary } from '../ErrorBoundary';

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
        // Check if we have multiple tags
        const hasMultipleTags = widget.config.tagIds && widget.config.tagIds.length > 1;
        
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
          { label: 'Running', value: typeof value === 'number' ? value : 60 },
          { label: 'Idle', value: 25 },
          { label: 'Stopped', value: 15 },
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
        const barCategories = ['Conv 1', 'Conv 2', 'Elevator', 'Shiploader'];
        const barValues = [
          typeof value === 'number' ? value : 120,
          150,
          180,
          200,
        ];
        return (
          <BarChart
            categories={barCategories}
            data={barValues}
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

        const tableColumns: import('../Widgets/DataTable').TableColumn[] = [
          { key: 'name', label: 'Equipment', sortable: true },
          { key: 'value', label: 'Value', format: 'number' as const, decimals: 1, sortable: true },
          { key: 'unit', label: 'Unit', sortable: false },
          { key: 'status', label: 'Status', format: 'status' as const, align: 'center' as const },
        ];

        return (
          <DataTable
            columns={tableColumns}
            data={tableData}
            title={widget.config.title}
            size={widget.config.size}
          />
        );

      case 'alarm':
        // Mock alarm data
        const alarmData = [
          { id: 1, time: new Date().toISOString(), tag: 'TEMP_01', message: 'High Temperature', severity: 'critical', acked: false },
          { id: 2, time: new Date(Date.now() - 300000).toISOString(), tag: 'PRESS_02', message: 'Low Pressure', severity: 'warning', acked: true },
          { id: 3, time: new Date(Date.now() - 600000).toISOString(), tag: 'FLOW_03', message: 'Flow Rate Low', severity: 'warning', acked: false },
        ];

        return (
          <div className="h-full overflow-auto">
            <div className="space-y-2">
              {alarmData.map((alarm) => (
                <div
                  key={alarm.id}
                  className={`p-3 rounded-lg border-l-4 ${
                    alarm.severity === 'critical'
                      ? 'bg-red-50 border-red-500'
                      : 'bg-yellow-50 border-yellow-500'
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-semibold text-sm">{alarm.message}</p>
                      <p className="text-xs text-gray-600">{alarm.tag}</p>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded ${
                      alarm.acked ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                    }`}>
                      {alarm.acked ? 'ACK' : 'NEW'}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {new Date(alarm.time).toLocaleTimeString()}
                  </p>
                </div>
              ))}
            </div>
          </div>
        );

      case 'text':
        return (
          <div className="h-full p-4">
            <div
              className="text-gray-700 prose prose-sm max-w-none"
              contentEditable
              suppressContentEditableWarning
            >
              {widget.config.content || 'Double-click to edit text...'}
            </div>
          </div>
        );

      case 'image':
        return (
          <div className="h-full flex items-center justify-center bg-gray-50 rounded">
            {widget.config.imageUrl ? (
              <img
                src={widget.config.imageUrl}
                alt={widget.config.title || 'Image'}
                className="max-w-full max-h-full object-contain"
              />
            ) : (
              <div className="text-center text-gray-400">
                <Activity className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p className="text-sm">Add image URL in properties</p>
              </div>
            )}
          </div>
        );

      case 'video':
        return (
          <div className="h-full flex items-center justify-center bg-black rounded">
            {widget.config.videoUrl ? (
              <video
                src={widget.config.videoUrl}
                controls
                className="max-w-full max-h-full"
              />
            ) : (
              <div className="text-center text-gray-400">
                <Activity className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p className="text-sm">Add video URL in properties</p>
              </div>
            )}
          </div>
        );

      case 'map':
        return (
          <div className="h-full flex items-center justify-center bg-blue-50 rounded">
            <div className="text-center">
              <div className="w-full h-full bg-gradient-to-br from-blue-100 to-green-100 rounded-lg p-4">
                <p className="text-blue-600 font-medium">Map Widget</p>
                <p className="text-xs text-gray-500 mt-2">
                  Geographic visualization coming soon
                </p>
                <div className="mt-4 grid grid-cols-3 gap-2">
                  <div className="h-8 bg-blue-200 rounded opacity-50"></div>
                  <div className="h-8 bg-green-200 rounded opacity-50"></div>
                  <div className="h-8 bg-blue-200 rounded opacity-50"></div>
                </div>
              </div>
            </div>
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
              w-full h-full rounded-xl shadow-lg backdrop-blur-sm
              border transition-all duration-300 ease-in-out
              ${isSelected
                ? 'border-blue-500/60 shadow-blue-500/20 shadow-xl ring-2 ring-blue-400/30'
                : 'border-gray-200/60 hover:border-gray-300/80 hover:shadow-xl'}
              ${isOver && canDrop
                ? 'border-green-400 bg-green-50/80 shadow-green-500/20'
                : 'bg-white/95'}
            `}
            style={{
              minHeight: '150px',
              minWidth: '200px',
            }}
          >
            {/* Modern Header with Glassmorphism */}
            <div className="widget-handle flex items-center justify-between px-4 py-3 bg-gradient-to-r from-gray-50/90 to-white/90 border-b border-gray-200/50 rounded-t-xl cursor-move backdrop-blur-sm">
              <div className="flex items-center gap-2 flex-1 min-w-0">
                <GripVertical className="w-4 h-4 text-gray-400 opacity-60" />
                {isEditing ? (
                  <input
                    type="text"
                    value={widget.config.title || ''}
                    onChange={(e) => onUpdate({ config: { ...widget.config, title: e.target.value } })}
                    onBlur={() => setIsEditing(false)}
                    onKeyDown={(e) => e.key === 'Enter' && setIsEditing(false)}
                    autoFocus
                    className="w-full px-2 py-1 text-sm font-medium border border-blue-400 rounded-md focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 transition-all"
                  />
                ) : (
                  <h3
                    className="text-sm font-semibold text-gray-800 truncate cursor-text hover:text-blue-600 transition-colors"
                    onDoubleClick={() => setIsEditing(true)}
                    title="Double-click to edit"
                  >
                    {widget.config.title || 'Untitled Widget'}
                  </h3>
                )}
              </div>

              {/* Modern Action Buttons */}
              <div className="flex items-center gap-1 ml-2">
                {widget.config.tagId && (
                  <div className="flex items-center gap-1 px-2 py-1 bg-blue-50 rounded-md mr-2">
                    <Link2 className="w-3 h-3 text-blue-500" />
                    <span className="text-xs font-medium text-blue-600 truncate max-w-[80px]">
                      {widget.config.tagName || widget.config.tagId}
                    </span>
                  </div>
                )}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    // Future: Open settings modal
                  }}
                  className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-md transition-all"
                  title="Widget settings"
                >
                  <Settings className="w-4 h-4" />
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    // Future: Maximize widget
                  }}
                  className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-md transition-all"
                  title="Maximize"
                >
                  <Maximize2 className="w-4 h-4" />
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete();
                  }}
                  className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-md transition-all"
                  title="Delete widget"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Content Area with Better Padding */}
            <div className="p-3 h-[calc(100%-56px)] overflow-hidden">
              <WidgetErrorBoundary>
                {renderContent()}
              </WidgetErrorBoundary>
            </div>

            {/* Live Status Indicator */}
            {widget.config.tagId && !loading && (
              <div className="absolute bottom-2 right-2 flex items-center gap-1">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                </span>
                <span className="text-xs text-gray-400 font-medium">LIVE</span>
              </div>
            )}
          </div>
        </ResizableBox>
      </div>
    </Draggable>
  );
};
