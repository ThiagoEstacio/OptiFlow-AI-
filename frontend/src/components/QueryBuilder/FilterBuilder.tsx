/**
 * FilterBuilder Component
 *
 * Visual filter construction with field, operator, and value selection
 */

import React from 'react';
import { Plus, Trash2, Filter } from 'lucide-react';

export interface QueryFilter {
  field: string;
  operator: 'eq' | 'ne' | 'gt' | 'lt' | 'gte' | 'lte' | 'in' | 'between';
  value: any;
}

export interface FilterBuilderProps {
  filters: QueryFilter[];
  onChange: (filters: QueryFilter[]) => void;
}

const OPERATORS = [
  { value: 'eq', label: 'Equals (=)' },
  { value: 'ne', label: 'Not Equals (≠)' },
  { value: 'gt', label: 'Greater Than (>)' },
  { value: 'lt', label: 'Less Than (<)' },
  { value: 'gte', label: 'Greater or Equal (≥)' },
  { value: 'lte', label: 'Less or Equal (≤)' },
  { value: 'in', label: 'In List' },
  { value: 'between', label: 'Between' },
];

const FIELDS = [
  { value: 'value', label: 'Value' },
  { value: 'quality', label: 'Quality' },
  { value: 'device_id', label: 'Device ID' },
  { value: 'tag_name', label: 'Tag Name' },
];

export const FilterBuilder: React.FC<FilterBuilderProps> = ({
  filters,
  onChange,
}) => {
  const handleAddFilter = () => {
    onChange([
      ...filters,
      { field: 'value', operator: 'eq', value: '' },
    ]);
  };

  const handleRemoveFilter = (index: number) => {
    onChange(filters.filter((_, i) => i !== index));
  };

  const handleFilterChange = (
    index: number,
    field: keyof QueryFilter,
    value: any
  ) => {
    const newFilters = [...filters];
    newFilters[index] = {
      ...newFilters[index],
      [field]: value,
    };
    onChange(newFilters);
  };

  const renderValueInput = (filter: QueryFilter, index: number) => {
    if (filter.operator === 'in') {
      return (
        <input
          type="text"
          value={Array.isArray(filter.value) ? filter.value.join(', ') : filter.value}
          onChange={(e) =>
            handleFilterChange(
              index,
              'value',
              e.target.value.split(',').map(v => v.trim())
            )
          }
          placeholder="value1, value2, value3"
          className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      );
    }

    if (filter.operator === 'between') {
      const values = Array.isArray(filter.value) ? filter.value : ['', ''];
      return (
        <div className="flex-1 flex gap-2">
          <input
            type="number"
            value={values[0] || ''}
            onChange={(e) =>
              handleFilterChange(index, 'value', [e.target.value, values[1] || ''])
            }
            placeholder="Min"
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          <span className="text-gray-500 self-center">and</span>
          <input
            type="number"
            value={values[1] || ''}
            onChange={(e) =>
              handleFilterChange(index, 'value', [values[0] || '', e.target.value])
            }
            placeholder="Max"
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      );
    }

    // Check if field is quality (dropdown)
    if (filter.field === 'quality') {
      return (
        <select
          value={filter.value}
          onChange={(e) => handleFilterChange(index, 'value', e.target.value)}
          className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="">Select quality...</option>
          <option value="good">Good</option>
          <option value="bad">Bad</option>
          <option value="uncertain">Uncertain</option>
        </select>
      );
    }

    // Default: text/number input
    return (
      <input
        type={filter.field === 'value' ? 'number' : 'text'}
        value={filter.value}
        onChange={(e) => handleFilterChange(index, 'value', e.target.value)}
        placeholder="Enter value..."
        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
      />
    );
  };

  return (
    <div className="filter-builder">
      <div className="flex items-center justify-between mb-3">
        <label className="block text-sm font-medium text-gray-700">
          <Filter size={16} className="inline mr-1" />
          Filters ({filters.length})
        </label>
        <button
          onClick={handleAddFilter}
          className="flex items-center gap-1 px-3 py-1 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus size={16} />
          Add Filter
        </button>
      </div>

      {filters.length === 0 ? (
        <div className="text-center py-8 text-gray-500 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
          <Filter size={32} className="mx-auto mb-2 text-gray-400" />
          <p>No filters added. Click "Add Filter" to get started.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filters.map((filter, index) => (
            <div
              key={index}
              className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg border border-gray-200"
            >
              {/* Field selector */}
              <select
                value={filter.field}
                onChange={(e) => handleFilterChange(index, 'field', e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
              >
                {FIELDS.map(field => (
                  <option key={field.value} value={field.value}>
                    {field.label}
                  </option>
                ))}
              </select>

              {/* Operator selector */}
              <select
                value={filter.operator}
                onChange={(e) => handleFilterChange(index, 'operator', e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
              >
                {OPERATORS.map(op => (
                  <option key={op.value} value={op.value}>
                    {op.label}
                  </option>
                ))}
              </select>

              {/* Value input(s) */}
              {renderValueInput(filter, index)}

              {/* Remove button */}
              <button
                onClick={() => handleRemoveFilter(index)}
                className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                title="Remove filter"
              >
                <Trash2 size={18} />
              </button>
            </div>
          ))}
        </div>
      )}

      {filters.length > 0 && (
        <div className="mt-2 text-xs text-gray-500">
          Filters are applied with AND logic (all must match)
        </div>
      )}
    </div>
  );
};

export default FilterBuilder;
