/**
 * Property Panel Component
 * Advanced widget configuration panel
 */

import React, { useState } from 'react';
import { X, ChevronDown, ChevronRight } from 'lucide-react';
import type { Widget } from '../../pages/DashboardBuilderPage';

interface PropertyPanelProps {
  widget: Widget | null;
  onUpdate: (widgetId: string, updates: Partial<Widget>) => void;
  onClose: () => void;
}

export const PropertyPanel: React.FC<PropertyPanelProps> = ({
  widget,
  onUpdate,
  onClose,
}) => {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['general', 'appearance', 'data'])
  );

  if (!widget) {
    return (
      <div className="w-80 bg-gray-50 border-l border-gray-200 flex items-center justify-center text-gray-500">
        <div className="text-center p-4">
          <p className="text-sm">Select a widget to configure</p>
        </div>
      </div>
    );
  }

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

  const Section: React.FC<{ title: string; id: string; children: React.ReactNode }> = ({
    title,
    id,
    children,
  }) => {
    const isExpanded = expandedSections.has(id);

    return (
      <div className="border-b border-gray-200">
        <button
          onClick={() => toggleSection(id)}
          className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-100 transition-colors"
        >
          <span className="font-medium text-gray-700">{title}</span>
          {isExpanded ? (
            <ChevronDown className="w-4 h-4 text-gray-500" />
          ) : (
            <ChevronRight className="w-4 h-4 text-gray-500" />
          )}
        </button>
        {isExpanded && <div className="px-4 py-3 space-y-3 bg-white">{children}</div>}
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
  }> = ({ label, value, onChange, type = 'text', options, min, max, step }) => {
    return (
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">
          {label}
        </label>
        {type === 'select' ? (
          <select
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {options?.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        ) : (
          <input
            type={type}
            value={value || ''}
            onChange={(e) =>
              onChange(type === 'number' ? parseFloat(e.target.value) : e.target.value)
            }
            min={min}
            max={max}
            step={step}
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        )}
      </div>
    );
  };

  const Checkbox: React.FC<{
    label: string;
    checked: boolean;
    onChange: (checked: boolean) => void;
  }> = ({ label, checked, onChange }) => {
    return (
      <label className="flex items-center space-x-2 cursor-pointer">
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
          className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
        />
        <span className="text-sm text-gray-700">{label}</span>
      </label>
    );
  };

  return (
    <div className="w-80 bg-gray-50 border-l border-gray-200 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 bg-white border-b border-gray-200 flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-gray-900">Properties</h2>
          <p className="text-xs text-gray-500 mt-0.5">
            {widget.type.charAt(0).toUpperCase() + widget.type.slice(1)} Widget
          </p>
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto">
        {/* General Section */}
        <Section title="General" id="general">
          <Input
            label="Title"
            value={widget.config.title}
            onChange={(v) => updateConfig('title', v)}
          />

          <Input
            label="Tag"
            value={widget.config.tagName || 'No tag bound'}
            onChange={() => {}}
            type="text"
          />
        </Section>

        {/* Appearance Section */}
        <Section title="Appearance" id="appearance">
          <Input
            label="Size"
            value={widget.config.size || 'md'}
            onChange={(v) => updateConfig('size', v)}
            type="select"
            options={[
              { value: 'sm', label: 'Small' },
              { value: 'md', label: 'Medium' },
              { value: 'lg', label: 'Large' },
            ]}
          />

          <Input
            label="Theme"
            value={widget.config.theme || 'default'}
            onChange={(v) => updateConfig('theme', v)}
            type="select"
            options={[
              { value: 'default', label: 'Default' },
              { value: 'minimal', label: 'Minimal' },
              { value: 'modern', label: 'Modern' },
              { value: 'industrial', label: 'Industrial' },
            ]}
          />

          <Input
            label="Color"
            value={widget.config.color || '#3B82F6'}
            onChange={(v) => updateConfig('color', v)}
            type="color"
          />
        </Section>

        {/* Data Section */}
        <Section title="Data" id="data">
          <Input
            label="Unit"
            value={widget.config.unit}
            onChange={(v) => updateConfig('unit', v)}
          />

          <Input
            label="Decimals"
            value={widget.config.decimals || 1}
            onChange={(v) => updateConfig('decimals', v)}
            type="number"
            min={0}
            max={5}
            step={1}
          />

          {widget.type !== 'status' && (
            <>
              <Input
                label="Min Value"
                value={widget.config.min || 0}
                onChange={(v) => updateConfig('min', v)}
                type="number"
              />

              <Input
                label="Max Value"
                value={widget.config.max || 100}
                onChange={(v) => updateConfig('max', v)}
                type="number"
              />
            </>
          )}
        </Section>

        {/* Widget-specific sections */}
        {(widget.type === 'kpi' || widget.type === 'progress') && (
          <Section title="Targets & Thresholds" id="targets">
            <Input
              label="Target Value"
              value={widget.config.target}
              onChange={(v) => updateConfig('target', v)}
              type="number"
            />

            <Input
              label="Warning Threshold"
              value={widget.config.thresholds?.warning}
              onChange={(v) =>
                updateConfig('thresholds', {
                  ...widget.config.thresholds,
                  warning: v,
                })
              }
              type="number"
            />

            <Input
              label="Critical Threshold"
              value={widget.config.thresholds?.critical}
              onChange={(v) =>
                updateConfig('thresholds', {
                  ...widget.config.thresholds,
                  critical: v,
                })
              }
              type="number"
            />
          </Section>
        )}

        {widget.type === 'sparkline' && (
          <Section title="Sparkline Options" id="sparkline">
            <Input
              label="Style"
              value={widget.config.sparklineStyle || 'area'}
              onChange={(v) => updateConfig('sparklineStyle', v)}
              type="select"
              options={[
                { value: 'line', label: 'Line' },
                { value: 'area', label: 'Area' },
                { value: 'bar', label: 'Bar' },
              ]}
            />

            <Checkbox
              label="Show Min/Max"
              checked={widget.config.showMinMax ?? false}
              onChange={(v) => updateConfig('showMinMax', v)}
            />

            <Checkbox
              label="Show Trend"
              checked={widget.config.showTrend ?? true}
              onChange={(v) => updateConfig('showTrend', v)}
            />
          </Section>
        )}

        {widget.type === 'progress' && (
          <Section title="Progress Options" id="progress">
            <Input
              label="Type"
              value={widget.config.progressType || 'bar'}
              onChange={(v) => updateConfig('progressType', v)}
              type="select"
              options={[
                { value: 'bar', label: 'Bar' },
                { value: 'circular', label: 'Circular' },
              ]}
            />
          </Section>
        )}

        {widget.type === 'status' && (
          <Section title="Status Options" id="status">
            <Input
              label="Status"
              value={widget.config.status || 'idle'}
              onChange={(v) => updateConfig('status', v)}
              type="select"
              options={[
                { value: 'running', label: 'Running' },
                { value: 'stopped', label: 'Stopped' },
                { value: 'warning', label: 'Warning' },
                { value: 'alarm', label: 'Alarm' },
                { value: 'offline', label: 'Offline' },
                { value: 'idle', label: 'Idle' },
                { value: 'maintenance', label: 'Maintenance' },
              ]}
            />
          </Section>
        )}

        {widget.type === 'kpi' && (
          <Section title="KPI Options" id="kpi">
            <Input
              label="Format"
              value={widget.config.format || 'number'}
              onChange={(v) => updateConfig('format', v)}
              type="select"
              options={[
                { value: 'number', label: 'Number' },
                { value: 'percentage', label: 'Percentage' },
                { value: 'currency', label: 'Currency' },
              ]}
            />

            <Input
              label="Previous Value"
              value={widget.config.previousValue}
              onChange={(v) => updateConfig('previousValue', v)}
              type="number"
            />
          </Section>
        )}
      </div>

      {/* Footer with widget info */}
      <div className="px-4 py-2 bg-white border-t border-gray-200 text-xs text-gray-500">
        <div className="flex justify-between">
          <span>Position:</span>
          <span>
            x:{widget.position.x}, y:{widget.position.y}
          </span>
        </div>
        <div className="flex justify-between mt-1">
          <span>Size:</span>
          <span>
            {widget.size.width}x{widget.size.height}
          </span>
        </div>
      </div>
    </div>
  );
};
