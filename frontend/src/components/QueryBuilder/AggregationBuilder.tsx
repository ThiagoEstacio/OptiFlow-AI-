/**
 * AggregationBuilder Component
 *
 * Select and configure aggregation functions
 */

import React from 'react';
import { Plus, Trash2, TrendingUp } from 'lucide-react';

export interface QueryAggregation {
  function: string;
  field: string;
  window?: string;
  params?: Record<string, any>;
}

export interface AggregationBuilderProps {
  aggregations: QueryAggregation[];
  onChange: (aggregations: QueryAggregation[]) => void;
}

const AGGREGATION_FUNCTIONS = [
  // Basic
  { value: 'mean', label: 'Mean (Average)', category: 'Basic', hasParams: false },
  { value: 'median', label: 'Median', category: 'Basic', hasParams: false },
  { value: 'mode', label: 'Mode', category: 'Basic', hasParams: false },
  { value: 'min', label: 'Minimum', category: 'Basic', hasParams: false },
  { value: 'max', label: 'Maximum', category: 'Basic', hasParams: false },
  { value: 'sum', label: 'Sum', category: 'Basic', hasParams: false },
  { value: 'count', label: 'Count', category: 'Basic', hasParams: false },
  // Statistical
  { value: 'stddev', label: 'Standard Deviation', category: 'Statistical', hasParams: false },
  { value: 'variance', label: 'Variance', category: 'Statistical', hasParams: false },
  { value: 'percentile', label: 'Percentile', category: 'Statistical', hasParams: true },
  // Advanced
  { value: 'correlation', label: 'Correlation', category: 'Advanced', hasParams: true },
  { value: 'moving_average', label: 'Moving Average', category: 'Advanced', hasParams: true },
  { value: 'rate_of_change', label: 'Rate of Change', category: 'Advanced', hasParams: false },
];

const TIME_WINDOWS = ['1m', '5m', '15m', '30m', '1h', '6h', '1d'];

export const AggregationBuilder: React.FC<AggregationBuilderProps> = ({
  aggregations,
  onChange,
}) => {
  const handleAddAggregation = () => {
    onChange([
      ...aggregations,
      { function: 'mean', field: 'value', window: '1h' },
    ]);
  };

  const handleRemoveAggregation = (index: number) => {
    onChange(aggregations.filter((_, i) => i !== index));
  };

  const handleAggregationChange = (
    index: number,
    field: keyof QueryAggregation,
    value: any
  ) => {
    const newAggregations = [...aggregations];
    newAggregations[index] = {
      ...newAggregations[index],
      [field]: value,
    };
    onChange(newAggregations);
  };

  const renderParams = (agg: QueryAggregation, index: number) => {
    if (agg.function === 'percentile') {
      return (
        <div className="flex items-center gap-2">
          <label className="text-xs text-gray-600">Percentile:</label>
          <input
            type="number"
            min="0"
            max="100"
            value={agg.params?.percentile || 95}
            onChange={(e) =>
              handleAggregationChange(index, 'params', {
                ...agg.params,
                percentile: parseInt(e.target.value),
              })
            }
            className="w-20 px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          <span className="text-xs text-gray-500">(0-100)</span>
        </div>
      );
    }

    if (agg.function === 'correlation') {
      return (
        <div className="flex items-center gap-2">
          <label className="text-xs text-gray-600">Target Tag ID:</label>
          <input
            type="text"
            value={agg.params?.target_tag || ''}
            onChange={(e) =>
              handleAggregationChange(index, 'params', {
                ...agg.params,
                target_tag: e.target.value,
              })
            }
            placeholder="e.g., pressure_sensor_01"
            className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      );
    }

    if (agg.function === 'moving_average') {
      return (
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <label className="text-xs text-gray-600">Type:</label>
            <select
              value={agg.params?.type || 'simple'}
              onChange={(e) =>
                handleAggregationChange(index, 'params', {
                  ...agg.params,
                  type: e.target.value,
                })
              }
              className="px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="simple">Simple</option>
              <option value="exponential">Exponential</option>
              <option value="weighted">Weighted</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-xs text-gray-600">Window Size:</label>
            <input
              type="number"
              min="2"
              value={agg.params?.window_size || 10}
              onChange={(e) =>
                handleAggregationChange(index, 'params', {
                  ...agg.params,
                  window_size: parseInt(e.target.value),
                })
              }
              className="w-20 px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
      );
    }

    return null;
  };

  const getFunctionConfig = (funcValue: string) => {
    return AGGREGATION_FUNCTIONS.find(f => f.value === funcValue);
  };

  return (
    <div className="aggregation-builder">
      <div className="flex items-center justify-between mb-3">
        <label className="block text-sm font-medium text-gray-700">
          <TrendingUp size={16} className="inline mr-1" />
          Aggregations ({aggregations.length})
        </label>
        <button
          onClick={handleAddAggregation}
          className="flex items-center gap-1 px-3 py-1 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus size={16} />
          Add Aggregation
        </button>
      </div>

      {aggregations.length === 0 ? (
        <div className="text-center py-8 text-gray-500 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
          <TrendingUp size={32} className="mx-auto mb-2 text-gray-400" />
          <p>No aggregations added. Add at least one to analyze your data.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {aggregations.map((agg, index) => {
            const funcConfig = getFunctionConfig(agg.function);

            return (
              <div
                key={index}
                className="p-3 bg-gray-50 rounded-lg border border-gray-200 space-y-3"
              >
                <div className="flex items-center gap-2">
                  {/* Function selector */}
                  <select
                    value={agg.function}
                    onChange={(e) => handleAggregationChange(index, 'function', e.target.value)}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
                  >
                    {['Basic', 'Statistical', 'Advanced'].map(category => (
                      <optgroup key={category} label={category}>
                        {AGGREGATION_FUNCTIONS.filter(f => f.category === category).map(func => (
                          <option key={func.value} value={func.value}>
                            {func.label}
                          </option>
                        ))}
                      </optgroup>
                    ))}
                  </select>

                  {/* Field selector */}
                  <select
                    value={agg.field}
                    onChange={(e) => handleAggregationChange(index, 'field', e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
                  >
                    <option value="value">Value</option>
                    <option value="quality">Quality</option>
                  </select>

                  {/* Time window (only for non-correlation functions) */}
                  {agg.function !== 'correlation' && (
                    <select
                      value={agg.window}
                      onChange={(e) => handleAggregationChange(index, 'window', e.target.value)}
                      className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
                    >
                      {TIME_WINDOWS.map(window => (
                        <option key={window} value={window}>
                          {window}
                        </option>
                      ))}
                    </select>
                  )}

                  {/* Remove button */}
                  <button
                    onClick={() => handleRemoveAggregation(index)}
                    className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    title="Remove aggregation"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>

                {/* Function-specific parameters */}
                {funcConfig?.hasParams && (
                  <div className="pl-2 border-l-2 border-blue-300">
                    {renderParams(agg, index)}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default AggregationBuilder;
