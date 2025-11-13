/**
 * TimeRangePicker Component
 *
 * Time range selector with presets and custom date/time selection
 */

import React, { useState } from 'react';
import { Calendar, Clock } from 'lucide-react';

export interface TimeRange {
  start: Date;
  end: Date;
  preset?: string;
}

export interface TimeRangePickerProps {
  value: TimeRange;
  onChange: (range: TimeRange) => void;
}

const PRESETS = [
  { label: 'Last Hour', value: '1h', hours: 1 },
  { label: 'Last 6 Hours', value: '6h', hours: 6 },
  { label: 'Last 24 Hours', value: '24h', hours: 24 },
  { label: 'Last 7 Days', value: '7d', days: 7 },
  { label: 'Last 30 Days', value: '30d', days: 30 },
  { label: 'Custom', value: 'custom' },
];

export const TimeRangePicker: React.FC<TimeRangePickerProps> = ({
  value,
  onChange,
}) => {
  const [selectedPreset, setSelectedPreset] = useState('24h');
  const [showCustom, setShowCustom] = useState(false);

  const handlePresetChange = (preset: typeof PRESETS[0]) => {
    setSelectedPreset(preset.value);

    if (preset.value === 'custom') {
      setShowCustom(true);
      return;
    }

    setShowCustom(false);

    const end = new Date();
    const start = new Date();

    if (preset.hours) {
      start.setHours(start.getHours() - preset.hours);
    } else if (preset.days) {
      start.setDate(start.getDate() - preset.days);
    }

    onChange({
      start,
      end,
      preset: preset.value,
    });
  };

  const handleCustomChange = (field: 'start' | 'end', dateValue: string) => {
    const newDate = new Date(dateValue);

    onChange({
      ...value,
      [field]: newDate,
      preset: 'custom',
    } as TimeRange);
  };

  const formatDateTimeLocal = (date: Date): string => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');

    return `${year}-${month}-${day}T${hours}:${minutes}`;
  };

  return (
    <div className="time-range-picker">
      <label className="block text-sm font-medium text-gray-700 mb-2">
        Time Range
      </label>

      {/* Preset buttons */}
      <div className="flex flex-wrap gap-2 mb-4">
        {PRESETS.map(preset => (
          <button
            key={preset.value}
            onClick={() => handlePresetChange(preset)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              selectedPreset === preset.value
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {preset.label}
          </button>
        ))}
      </div>

      {/* Custom date/time inputs */}
      {showCustom && (
        <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              <Calendar size={14} className="inline mr-1" />
              Start Date & Time
            </label>
            <input
              type="datetime-local"
              value={formatDateTimeLocal(value.start)}
              onChange={(e) => handleCustomChange('start', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              <Calendar size={14} className="inline mr-1" />
              End Date & Time
            </label>
            <input
              type="datetime-local"
              value={formatDateTimeLocal(value.end)}
              onChange={(e) => handleCustomChange('end', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
            />
          </div>
        </div>
      )}

      {/* Current selection summary */}
      <div className="mt-3 text-sm text-gray-600 bg-blue-50 p-3 rounded-lg">
        <Clock size={14} className="inline mr-1" />
        <strong>Selected:</strong> {value.start.toLocaleString()} → {value.end.toLocaleString()}
        <span className="ml-2 text-gray-500">
          ({Math.round((value.end.getTime() - value.start.getTime()) / (1000 * 60 * 60))} hours)
        </span>
      </div>
    </div>
  );
};

export default TimeRangePicker;
