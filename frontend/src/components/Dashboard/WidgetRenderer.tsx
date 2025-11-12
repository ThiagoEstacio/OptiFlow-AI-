import React from 'react';
import KPICard from './widgets/KPICard';
import LineChartWidget from './widgets/LineChartWidget';
import BarChartWidget from './widgets/BarChartWidget';
import GaugeWidget from './widgets/GaugeWidget';
import DataTableWidget from './widgets/DataTableWidget';
import ProcessStatusWidget from './widgets/ProcessStatusWidget';
import ActiveAlarmsWidget from './widgets/ActiveAlarmsWidget';
import StatWidget from './widgets/StatWidget';
import BarGaugeWidget from './widgets/BarGaugeWidget';
import TankLevelWidget from './widgets/TankLevelWidget';
import MotorStatusWidget from './widgets/MotorStatusWidget';
import PieChartWidget from './widgets/PieChartWidget';
import DonutChartWidget from './widgets/DonutChartWidget';
import AreaChartWidget from './widgets/AreaChartWidget';
import HeatmapWidget from './widgets/HeatmapWidget';

interface Widget {
  id: string;
  title: string;
  type: string;
  config: any;
  data_config: any;
  display_config: any;
}

interface WidgetRendererProps {
  widget: Widget;
  isEditMode?: boolean;
}

const WidgetRenderer: React.FC<WidgetRendererProps> = ({ widget, isEditMode = false }) => {
  const renderWidget = () => {
    switch (widget.type) {
      case 'kpi_card':
        return <KPICard widget={widget} />;
      
      case 'stat':
        return <StatWidget widget={widget} />;
      
      case 'line_chart':
        return <LineChartWidget widget={widget} />;
      
      case 'area_chart':
        return <AreaChartWidget widget={widget} />;
      
      case 'bar_chart':
        return <BarChartWidget widget={widget} />;
      
      case 'gauge':
        return <GaugeWidget widget={widget} />;
      
      case 'bar_gauge':
        return <BarGaugeWidget widget={widget} />;
      
      case 'pie_chart':
        return <PieChartWidget widget={widget} />;
      
      case 'donut_chart':
        return <DonutChartWidget widget={widget} />;
      
      case 'heatmap':
        return <HeatmapWidget widget={widget} />;
      
      case 'table':
        return <DataTableWidget widget={widget} />;
      
      case 'process_status':
        return <ProcessStatusWidget widget={widget} />;
      
      case 'tank_level':
        return <TankLevelWidget widget={widget} />;
      
      case 'motor_status':
        return <MotorStatusWidget widget={widget} />;
      
      case 'active_alarms':
        return <ActiveAlarmsWidget widget={widget} />;
      
      default:
        return (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="text-4xl mb-2">🔧</div>
              <p className="text-gray-600 dark:text-gray-400 text-sm">
                {widget.type}
              </p>
              <p className="text-gray-500 dark:text-gray-500 text-xs mt-1">
                Widget not yet implemented
              </p>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="h-full w-full">
      {!isEditMode && widget.title && (
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
          {widget.title}
        </h3>
      )}
      {renderWidget()}
    </div>
  );
};

export default WidgetRenderer;
