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
import OEEWidget from './widgets/OEEWidget';
import ValveStatusWidget from './widgets/ValveStatusWidget';
import EquipmentHealthWidget from './widgets/EquipmentHealthWidget';

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

// Widget type to component mapping
const WIDGET_COMPONENTS: Record<string, React.FC<{ widget: Widget }>> = {
  kpi_card: KPICard,
  stat: StatWidget,
  line_chart: LineChartWidget,
  area_chart: AreaChartWidget,
  bar_chart: BarChartWidget,
  gauge: GaugeWidget,
  bar_gauge: BarGaugeWidget,
  pie_chart: PieChartWidget,
  donut_chart: DonutChartWidget,
  heatmap: HeatmapWidget,
  table: DataTableWidget,
  process_status: ProcessStatusWidget,
  tank_level: TankLevelWidget,
  motor_status: MotorStatusWidget,
  valve_status: ValveStatusWidget,
  active_alarms: ActiveAlarmsWidget,
  oee: OEEWidget,
  equipment_health: EquipmentHealthWidget,
};

// Widget placeholder info for widgets in development
const WIDGET_PLACEHOLDERS: Record<string, { icon: string; name: string }> = {
  candlestick: { icon: '🕯️', name: 'Candlestick' },
  horizontal_bar: { icon: '▬▬▬', name: 'Barras Horizontais' },
  logs: { icon: '📜', name: 'Visualizador de Logs' },
  json: { icon: '{ }', name: 'JSON Viewer' },
  alarm_history: { icon: '📋', name: 'Histórico de Alarmes' },
  notification_list: { icon: '🔔', name: 'Notificações' },
  trend_analysis: { icon: '📊', name: 'Análise de Tendências' },
  distribution: { icon: '📊', name: 'Distribuição' },
  correlation: { icon: '🔗', name: 'Correlação' },
  anomaly_detection: { icon: '🔍', name: 'Detecção de Anomalias' },
  geomap: { icon: '🗺️', name: 'Mapa Geográfico' },
  facility_map: { icon: '🏭', name: 'Mapa da Planta' },
  iframe: { icon: '🖼️', name: 'iFrame' },
  html: { icon: '<>', name: 'HTML Customizado' },
  image: { icon: '🖼️', name: 'Imagem' },
};

const WidgetRenderer: React.FC<WidgetRendererProps> = ({ widget, isEditMode = false }) => {
  const renderWidget = () => {
    // Check if we have a component for this widget type
    const WidgetComponent = WIDGET_COMPONENTS[widget.type];

    if (WidgetComponent) {
      return <WidgetComponent widget={widget} />;
    }

    // Check if it's a known placeholder
    const placeholder = WIDGET_PLACEHOLDERS[widget.type];
    if (placeholder) {
      return (
        <div className="flex items-center justify-center h-full">
          <div className="text-center p-4">
            <div className="text-5xl mb-3">{placeholder.icon}</div>
            <p className="text-gray-600 dark:text-gray-400 font-medium">
              {placeholder.name}
            </p>
            <p className="text-gray-500 dark:text-gray-500 text-xs mt-2">
              Em desenvolvimento
            </p>
          </div>
        </div>
      );
    }

    // Unknown widget type
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center p-4">
          <div className="text-4xl mb-2">🔧</div>
          <p className="text-gray-600 dark:text-gray-400 text-sm font-medium">
            {widget.type}
          </p>
          <p className="text-gray-500 dark:text-gray-500 text-xs mt-1">
            Widget não implementado
          </p>
        </div>
      </div>
    );
  };

  return (
    <div className="h-full w-full overflow-hidden">
      {!isEditMode && widget.title && (
        <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-2 px-1 truncate">
          {widget.config?.title || widget.title}
        </h3>
      )}
      <div className={`${!isEditMode && widget.title ? 'h-[calc(100%-28px)]' : 'h-full'}`}>
        {renderWidget()}
      </div>
    </div>
  );
};

export default WidgetRenderer;
