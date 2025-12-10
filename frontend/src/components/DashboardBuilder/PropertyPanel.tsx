/**
 * Property Panel Component
 * Advanced widget configuration panel with widget-specific options
 */

import React, { useState } from 'react';
import { X, ChevronDown, ChevronRight, Palette, Database, Settings, Target, BarChart2, Bell, Info } from 'lucide-react';
import type { Widget } from '../../pages/DashboardBuilderPage';

interface PropertyPanelProps {
  widget: Widget | null;
  onUpdate: (widgetId: string, updates: Partial<Widget>) => void;
  onClose: () => void;
}

// Widget type configurations
const WIDGET_CONFIGS: Record<string, {
  name: string;
  icon: string;
  sections: string[];
  defaults: Record<string, any>;
}> = {
  kpi_card: {
    name: 'KPI Card',
    icon: '📊',
    sections: ['general', 'data', 'appearance', 'thresholds'],
    defaults: { decimals: 1, showTrend: true, showSparkline: false },
  },
  stat: {
    name: 'Estatística',
    icon: '🔢',
    sections: ['general', 'data', 'appearance'],
    defaults: { decimals: 1, size: 'lg' },
  },
  gauge: {
    name: 'Gauge',
    icon: '🎯',
    sections: ['general', 'data', 'appearance', 'thresholds', 'gauge_options'],
    defaults: { min: 0, max: 100, decimals: 1, gaugeType: 'semicircle' },
  },
  bar_gauge: {
    name: 'Bar Gauge',
    icon: '▬',
    sections: ['general', 'data', 'appearance', 'thresholds'],
    defaults: { min: 0, max: 100, orientation: 'horizontal' },
  },
  line_chart: {
    name: 'Gráfico de Linha',
    icon: '📈',
    sections: ['general', 'data', 'appearance', 'chart_options', 'time_range'],
    defaults: { showGrid: true, showLegend: true, timeRange: '1h' },
  },
  area_chart: {
    name: 'Gráfico de Área',
    icon: '⛰️',
    sections: ['general', 'data', 'appearance', 'chart_options', 'time_range'],
    defaults: { showGrid: true, fillOpacity: 0.3, timeRange: '1h' },
  },
  bar_chart: {
    name: 'Gráfico de Barras',
    icon: '📊',
    sections: ['general', 'data', 'appearance', 'chart_options'],
    defaults: { showGrid: true, stacked: false },
  },
  pie_chart: {
    name: 'Gráfico Pizza',
    icon: '🥧',
    sections: ['general', 'data', 'appearance', 'chart_options'],
    defaults: { showLegend: true, showLabels: true },
  },
  donut_chart: {
    name: 'Gráfico Donut',
    icon: '🍩',
    sections: ['general', 'data', 'appearance', 'chart_options'],
    defaults: { showLegend: true, innerRadius: 60 },
  },
  table: {
    name: 'Tabela',
    icon: '📋',
    sections: ['general', 'data', 'table_options'],
    defaults: { pageSize: 10, sortable: true, striped: true },
  },
  process_status: {
    name: 'Status Processo',
    icon: '⚙️',
    sections: ['general', 'data', 'status_options'],
    defaults: { showAnimation: true },
  },
  motor_status: {
    name: 'Status Motor',
    icon: '🔌',
    sections: ['general', 'data', 'motor_options'],
    defaults: { showRPM: true, showPower: true },
  },
  tank_level: {
    name: 'Nível Tanque',
    icon: '⛽',
    sections: ['general', 'data', 'tank_options', 'thresholds'],
    defaults: { min: 0, max: 100, showPercentage: true, tankShape: 'rectangle' },
  },
  valve_status: {
    name: 'Status Válvula',
    icon: '🚰',
    sections: ['general', 'data', 'valve_options'],
    defaults: { showPercentage: true },
  },
  active_alarms: {
    name: 'Alarmes Ativos',
    icon: '🔔',
    sections: ['general', 'alarm_options'],
    defaults: { maxAlarms: 5, showSeverity: true },
  },
  heatmap: {
    name: 'Mapa de Calor',
    icon: '🗺️',
    sections: ['general', 'data', 'heatmap_options'],
    defaults: { colorScheme: 'warm' },
  },
  oee: {
    name: 'OEE Dashboard',
    icon: '📈',
    sections: ['general', 'data', 'oee_options'],
    defaults: { showComponents: true, targetOEE: 85 },
  },
  equipment_health: {
    name: 'Saúde Equipamento',
    icon: '🔧',
    sections: ['general', 'data', 'health_options'],
    defaults: { showMTBF: true, showMTTR: true },
  },
};

const COLOR_PRESETS = [
  { name: 'Azul', value: '#3B82F6' },
  { name: 'Verde', value: '#10B981' },
  { name: 'Amarelo', value: '#F59E0B' },
  { name: 'Vermelho', value: '#EF4444' },
  { name: 'Roxo', value: '#8B5CF6' },
  { name: 'Ciano', value: '#06B6D4' },
  { name: 'Rosa', value: '#EC4899' },
  { name: 'Laranja', value: '#F97316' },
];

export const PropertyPanel: React.FC<PropertyPanelProps> = ({
  widget,
  onUpdate,
  onClose,
}) => {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['general', 'data'])
  );

  if (!widget) {
    return (
      <div className="w-80 bg-gray-50 border-l border-gray-200 flex items-center justify-center">
        <div className="text-center p-6">
          <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center mx-auto mb-4">
            <Settings className="w-8 h-8 text-gray-400" />
          </div>
          <p className="text-sm text-gray-600 font-medium">Nenhum widget selecionado</p>
          <p className="text-xs text-gray-500 mt-1">Clique em um widget para configurar</p>
        </div>
      </div>
    );
  }

  const widgetConfig = WIDGET_CONFIGS[widget.type] || {
    name: widget.type,
    icon: '📦',
    sections: ['general', 'data', 'appearance'],
    defaults: {},
  };

  const toggleSection = (section: string) => {
    setExpandedSections(prev => {
      const next = new Set(prev);
      if (next.has(section)) {
        next.delete(section);
      } else {
        next.add(section);
      }
      return next;
    });
  };

  const updateConfig = (key: string, value: any) => {
    onUpdate(widget.id, {
      config: {
        ...widget.config,
        [key]: value,
      },
    });
  };

  const updateNestedConfig = (parent: string, key: string, value: any) => {
    onUpdate(widget.id, {
      config: {
        ...widget.config,
        [parent]: {
          ...(widget.config[parent] || {}),
          [key]: value,
        },
      },
    });
  };

  // UI Components
  const Section: React.FC<{ title: string; id: string; icon?: React.ReactNode; children: React.ReactNode }> = ({
    title,
    id,
    icon,
    children,
  }) => {
    const isExpanded = expandedSections.has(id);

    return (
      <div className="border-b border-gray-200">
        <button
          onClick={() => toggleSection(id)}
          className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-100 transition-colors"
        >
          <div className="flex items-center gap-2">
            {icon}
            <span className="font-medium text-gray-700">{title}</span>
          </div>
          {isExpanded ? (
            <ChevronDown className="w-4 h-4 text-gray-500" />
          ) : (
            <ChevronRight className="w-4 h-4 text-gray-500" />
          )}
        </button>
        {isExpanded && <div className="px-4 py-3 space-y-4 bg-white">{children}</div>}
      </div>
    );
  };

  const Input: React.FC<{
    label: string;
    value: any;
    onChange: (value: any) => void;
    type?: 'text' | 'number' | 'color' | 'select';
    options?: { value: string; label: string }[];
    min?: number;
    max?: number;
    step?: number;
    placeholder?: string;
    helpText?: string;
  }> = ({ label, value, onChange, type = 'text', options, min, max, step, placeholder, helpText }) => {
    return (
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1.5">
          {label}
        </label>
        {type === 'select' ? (
          <select
            value={value ?? ''}
            onChange={(e) => onChange(e.target.value)}
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
          >
            {options?.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        ) : type === 'color' ? (
          <div className="flex gap-2">
            <input
              type="color"
              value={value || '#3B82F6'}
              onChange={(e) => onChange(e.target.value)}
              className="w-10 h-10 rounded cursor-pointer border border-gray-300"
            />
            <div className="flex-1 grid grid-cols-4 gap-1">
              {COLOR_PRESETS.map((color) => (
                <button
                  key={color.value}
                  onClick={() => onChange(color.value)}
                  className={`w-6 h-6 rounded-full border-2 ${value === color.value ? 'border-gray-800' : 'border-gray-200'}`}
                  style={{ backgroundColor: color.value }}
                  title={color.name}
                />
              ))}
            </div>
          </div>
        ) : (
          <input
            type={type}
            value={value ?? ''}
            onChange={(e) =>
              onChange(type === 'number' ? parseFloat(e.target.value) || 0 : e.target.value)
            }
            min={min}
            max={max}
            step={step}
            placeholder={placeholder}
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        )}
        {helpText && <p className="text-xs text-gray-500 mt-1">{helpText}</p>}
      </div>
    );
  };

  const Checkbox: React.FC<{
    label: string;
    checked: boolean;
    onChange: (checked: boolean) => void;
    helpText?: string;
  }> = ({ label, checked, onChange, helpText }) => {
    return (
      <div>
        <label className="flex items-center space-x-2 cursor-pointer">
          <input
            type="checkbox"
            checked={checked}
            onChange={(e) => onChange(e.target.checked)}
            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
          />
          <span className="text-sm text-gray-700">{label}</span>
        </label>
        {helpText && <p className="text-xs text-gray-500 mt-1 ml-6">{helpText}</p>}
      </div>
    );
  };

  const RangeSlider: React.FC<{
    label: string;
    value: number;
    onChange: (value: number) => void;
    min: number;
    max: number;
    step?: number;
    unit?: string;
  }> = ({ label, value, onChange, min, max, step = 1, unit }) => {
    return (
      <div>
        <div className="flex justify-between mb-1.5">
          <label className="text-xs font-medium text-gray-600">{label}</label>
          <span className="text-xs text-gray-500">{value}{unit}</span>
        </div>
        <input
          type="range"
          value={value}
          onChange={(e) => onChange(parseFloat(e.target.value))}
          min={min}
          max={max}
          step={step}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
        />
      </div>
    );
  };

  // Render sections based on widget type
  const renderGeneralSection = () => (
    <Section title="Geral" id="general" icon={<Settings className="w-4 h-4 text-gray-500" />}>
      <Input
        label="Título"
        value={widget.config.title || widget.title}
        onChange={(v) => updateConfig('title', v)}
        placeholder="Título do widget"
      />
      <Input
        label="Subtítulo"
        value={widget.config.subtitle}
        onChange={(v) => updateConfig('subtitle', v)}
        placeholder="Descrição opcional"
      />
    </Section>
  );

  const renderDataSection = () => (
    <Section title="Dados" id="data" icon={<Database className="w-4 h-4 text-gray-500" />}>
      <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
        <p className="text-xs font-medium text-gray-600 mb-1">Tag Vinculada</p>
        <p className="text-sm text-gray-900">{widget.config.tagName || widget.config.tagId || 'Nenhuma'}</p>
        {widget.config.tagId && (
          <p className="text-xs text-gray-500 mt-1 font-mono">{widget.config.tagId}</p>
        )}
      </div>
      <Input
        label="Unidade"
        value={widget.config.unit}
        onChange={(v) => updateConfig('unit', v)}
        placeholder="Ex: °C, bar, m³/h"
      />
      <Input
        label="Casas Decimais"
        value={widget.config.decimals ?? 1}
        onChange={(v) => updateConfig('decimals', v)}
        type="number"
        min={0}
        max={5}
      />
      {!['pie_chart', 'donut_chart', 'table', 'active_alarms', 'process_status'].includes(widget.type) && (
        <>
          <Input
            label="Valor Mínimo"
            value={widget.config.min ?? 0}
            onChange={(v) => updateConfig('min', v)}
            type="number"
          />
          <Input
            label="Valor Máximo"
            value={widget.config.max ?? 100}
            onChange={(v) => updateConfig('max', v)}
            type="number"
          />
        </>
      )}
    </Section>
  );

  const renderAppearanceSection = () => (
    <Section title="Aparência" id="appearance" icon={<Palette className="w-4 h-4 text-gray-500" />}>
      <Input
        label="Cor Principal"
        value={widget.config.color || '#3B82F6'}
        onChange={(v) => updateConfig('color', v)}
        type="color"
      />
      <Input
        label="Tamanho"
        value={widget.config.size || 'md'}
        onChange={(v) => updateConfig('size', v)}
        type="select"
        options={[
          { value: 'sm', label: 'Pequeno' },
          { value: 'md', label: 'Médio' },
          { value: 'lg', label: 'Grande' },
        ]}
      />
      <Input
        label="Tema"
        value={widget.config.theme || 'default'}
        onChange={(v) => updateConfig('theme', v)}
        type="select"
        options={[
          { value: 'default', label: 'Padrão' },
          { value: 'minimal', label: 'Minimalista' },
          { value: 'modern', label: 'Moderno' },
          { value: 'industrial', label: 'Industrial' },
        ]}
      />
    </Section>
  );

  const renderThresholdsSection = () => (
    <Section title="Limites e Alarmes" id="thresholds" icon={<Target className="w-4 h-4 text-gray-500" />}>
      <Input
        label="Limite de Aviso"
        value={widget.config.thresholds?.warning}
        onChange={(v) => updateNestedConfig('thresholds', 'warning', v)}
        type="number"
        helpText="Valor acima do qual mostra aviso"
      />
      <Input
        label="Limite Crítico"
        value={widget.config.thresholds?.critical}
        onChange={(v) => updateNestedConfig('thresholds', 'critical', v)}
        type="number"
        helpText="Valor acima do qual mostra alarme"
      />
      <Input
        label="Meta/Target"
        value={widget.config.target}
        onChange={(v) => updateConfig('target', v)}
        type="number"
        helpText="Valor ideal a ser atingido"
      />
      <Checkbox
        label="Inverter lógica (menor = pior)"
        checked={widget.config.invertThresholds ?? false}
        onChange={(v) => updateConfig('invertThresholds', v)}
      />
    </Section>
  );

  const renderChartOptionsSection = () => (
    <Section title="Opções do Gráfico" id="chart_options" icon={<BarChart2 className="w-4 h-4 text-gray-500" />}>
      <Checkbox
        label="Mostrar Grade"
        checked={widget.config.showGrid ?? true}
        onChange={(v) => updateConfig('showGrid', v)}
      />
      <Checkbox
        label="Mostrar Legenda"
        checked={widget.config.showLegend ?? true}
        onChange={(v) => updateConfig('showLegend', v)}
      />
      <Checkbox
        label="Animações"
        checked={widget.config.animated ?? true}
        onChange={(v) => updateConfig('animated', v)}
      />
      {['line_chart', 'area_chart'].includes(widget.type) && (
        <>
          <Checkbox
            label="Mostrar Pontos"
            checked={widget.config.showDots ?? false}
            onChange={(v) => updateConfig('showDots', v)}
          />
          <Checkbox
            label="Linha Suave"
            checked={widget.config.smoothLine ?? true}
            onChange={(v) => updateConfig('smoothLine', v)}
          />
        </>
      )}
      {widget.type === 'area_chart' && (
        <RangeSlider
          label="Opacidade do Preenchimento"
          value={widget.config.fillOpacity ?? 0.3}
          onChange={(v) => updateConfig('fillOpacity', v)}
          min={0}
          max={1}
          step={0.1}
        />
      )}
      {widget.type === 'bar_chart' && (
        <Checkbox
          label="Barras Empilhadas"
          checked={widget.config.stacked ?? false}
          onChange={(v) => updateConfig('stacked', v)}
        />
      )}
      {widget.type === 'donut_chart' && (
        <RangeSlider
          label="Raio Interno"
          value={widget.config.innerRadius ?? 60}
          onChange={(v) => updateConfig('innerRadius', v)}
          min={0}
          max={90}
          unit="%"
        />
      )}
    </Section>
  );

  const renderTimeRangeSection = () => (
    <Section title="Período de Tempo" id="time_range" icon={<BarChart2 className="w-4 h-4 text-gray-500" />}>
      <Input
        label="Intervalo"
        value={widget.config.timeRange || '1h'}
        onChange={(v) => updateConfig('timeRange', v)}
        type="select"
        options={[
          { value: '5m', label: '5 minutos' },
          { value: '15m', label: '15 minutos' },
          { value: '30m', label: '30 minutos' },
          { value: '1h', label: '1 hora' },
          { value: '6h', label: '6 horas' },
          { value: '24h', label: '24 horas' },
          { value: '7d', label: '7 dias' },
        ]}
      />
      <Input
        label="Atualização (segundos)"
        value={widget.config.refreshInterval ?? 30}
        onChange={(v) => updateConfig('refreshInterval', v)}
        type="number"
        min={5}
        max={3600}
      />
    </Section>
  );

  const renderGaugeOptionsSection = () => (
    <Section title="Opções do Gauge" id="gauge_options" icon={<Target className="w-4 h-4 text-gray-500" />}>
      <Input
        label="Tipo"
        value={widget.config.gaugeType || 'semicircle'}
        onChange={(v) => updateConfig('gaugeType', v)}
        type="select"
        options={[
          { value: 'semicircle', label: 'Semicírculo' },
          { value: 'full', label: 'Círculo Completo' },
          { value: 'arc', label: 'Arco' },
        ]}
      />
      <Checkbox
        label="Mostrar Agulha"
        checked={widget.config.showNeedle ?? true}
        onChange={(v) => updateConfig('showNeedle', v)}
      />
      <RangeSlider
        label="Espessura do Arco"
        value={widget.config.arcWidth ?? 20}
        onChange={(v) => updateConfig('arcWidth', v)}
        min={5}
        max={40}
        unit="px"
      />
    </Section>
  );

  const renderTankOptionsSection = () => (
    <Section title="Opções do Tanque" id="tank_options" icon={<Info className="w-4 h-4 text-gray-500" />}>
      <Input
        label="Formato"
        value={widget.config.tankShape || 'rectangle'}
        onChange={(v) => updateConfig('tankShape', v)}
        type="select"
        options={[
          { value: 'rectangle', label: 'Retangular' },
          { value: 'cylinder', label: 'Cilíndrico' },
          { value: 'sphere', label: 'Esférico' },
        ]}
      />
      <Checkbox
        label="Mostrar Percentual"
        checked={widget.config.showPercentage ?? true}
        onChange={(v) => updateConfig('showPercentage', v)}
      />
      <Checkbox
        label="Animação de Líquido"
        checked={widget.config.showWaves ?? true}
        onChange={(v) => updateConfig('showWaves', v)}
      />
      <Input
        label="Cor do Líquido"
        value={widget.config.liquidColor || '#3B82F6'}
        onChange={(v) => updateConfig('liquidColor', v)}
        type="color"
      />
    </Section>
  );

  const renderAlarmOptionsSection = () => (
    <Section title="Opções de Alarme" id="alarm_options" icon={<Bell className="w-4 h-4 text-gray-500" />}>
      <Input
        label="Máximo de Alarmes"
        value={widget.config.maxAlarms ?? 5}
        onChange={(v) => updateConfig('maxAlarms', v)}
        type="number"
        min={1}
        max={20}
      />
      <Checkbox
        label="Mostrar Severidade"
        checked={widget.config.showSeverity ?? true}
        onChange={(v) => updateConfig('showSeverity', v)}
      />
      <Checkbox
        label="Mostrar Timestamp"
        checked={widget.config.showTimestamp ?? true}
        onChange={(v) => updateConfig('showTimestamp', v)}
      />
      <Input
        label="Filtrar Severidade"
        value={widget.config.severityFilter || 'all'}
        onChange={(v) => updateConfig('severityFilter', v)}
        type="select"
        options={[
          { value: 'all', label: 'Todos' },
          { value: 'critical', label: 'Crítico' },
          { value: 'high', label: 'Alto' },
          { value: 'medium', label: 'Médio' },
          { value: 'low', label: 'Baixo' },
        ]}
      />
    </Section>
  );

  const renderTableOptionsSection = () => (
    <Section title="Opções da Tabela" id="table_options" icon={<Database className="w-4 h-4 text-gray-500" />}>
      <Input
        label="Linhas por Página"
        value={widget.config.pageSize ?? 10}
        onChange={(v) => updateConfig('pageSize', v)}
        type="number"
        min={5}
        max={50}
      />
      <Checkbox
        label="Permitir Ordenação"
        checked={widget.config.sortable ?? true}
        onChange={(v) => updateConfig('sortable', v)}
      />
      <Checkbox
        label="Linhas Alternadas"
        checked={widget.config.striped ?? true}
        onChange={(v) => updateConfig('striped', v)}
      />
      <Checkbox
        label="Mostrar Borda"
        checked={widget.config.bordered ?? false}
        onChange={(v) => updateConfig('bordered', v)}
      />
    </Section>
  );

  const renderMotorOptionsSection = () => (
    <Section title="Opções do Motor" id="motor_options" icon={<Settings className="w-4 h-4 text-gray-500" />}>
      <Checkbox
        label="Mostrar RPM"
        checked={widget.config.showRPM ?? true}
        onChange={(v) => updateConfig('showRPM', v)}
      />
      <Checkbox
        label="Mostrar Potência"
        checked={widget.config.showPower ?? true}
        onChange={(v) => updateConfig('showPower', v)}
      />
      <Checkbox
        label="Mostrar Corrente"
        checked={widget.config.showCurrent ?? false}
        onChange={(v) => updateConfig('showCurrent', v)}
      />
      <Checkbox
        label="Animação de Rotação"
        checked={widget.config.showAnimation ?? true}
        onChange={(v) => updateConfig('showAnimation', v)}
      />
    </Section>
  );

  const renderOEEOptionsSection = () => (
    <Section title="Opções OEE" id="oee_options" icon={<BarChart2 className="w-4 h-4 text-gray-500" />}>
      <Input
        label="Meta OEE (%)"
        value={widget.config.targetOEE ?? 85}
        onChange={(v) => updateConfig('targetOEE', v)}
        type="number"
        min={0}
        max={100}
      />
      <Checkbox
        label="Mostrar Componentes"
        checked={widget.config.showComponents ?? true}
        onChange={(v) => updateConfig('showComponents', v)}
        helpText="Disponibilidade, Performance, Qualidade"
      />
      <Checkbox
        label="Mostrar Tendência"
        checked={widget.config.showTrend ?? true}
        onChange={(v) => updateConfig('showTrend', v)}
      />
    </Section>
  );

  // Build sections based on widget type
  const sections = widgetConfig.sections || ['general', 'data', 'appearance'];

  return (
    <div className="w-80 bg-gray-50 border-l border-gray-200 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 bg-white border-b border-gray-200 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{widgetConfig.icon}</span>
          <div>
            <h2 className="text-sm font-semibold text-gray-900">{widgetConfig.name}</h2>
            <p className="text-xs text-gray-500">Configurações do Widget</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1 text-gray-400 hover:text-gray-600 transition-colors rounded-full hover:bg-gray-100"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto">
        {sections.includes('general') && renderGeneralSection()}
        {sections.includes('data') && renderDataSection()}
        {sections.includes('appearance') && renderAppearanceSection()}
        {sections.includes('thresholds') && renderThresholdsSection()}
        {sections.includes('chart_options') && renderChartOptionsSection()}
        {sections.includes('time_range') && renderTimeRangeSection()}
        {sections.includes('gauge_options') && renderGaugeOptionsSection()}
        {sections.includes('tank_options') && renderTankOptionsSection()}
        {sections.includes('alarm_options') && renderAlarmOptionsSection()}
        {sections.includes('table_options') && renderTableOptionsSection()}
        {sections.includes('motor_options') && renderMotorOptionsSection()}
        {sections.includes('oee_options') && renderOEEOptionsSection()}
      </div>

      {/* Footer with widget info */}
      <div className="px-4 py-3 bg-white border-t border-gray-200">
        <div className="grid grid-cols-2 gap-2 text-xs text-gray-500">
          <div>
            <span className="font-medium">Posição:</span> x:{widget.position.x}, y:{widget.position.y}
          </div>
          <div>
            <span className="font-medium">Tamanho:</span> {widget.size.width}x{widget.size.height}
          </div>
        </div>
      </div>
    </div>
  );
};
