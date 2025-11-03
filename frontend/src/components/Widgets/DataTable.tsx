/**
 * Data Table Widget - Real-time data table display
 * Features:
 * - Live data updates
 * - Sortable columns
 * - Status indicators
 * - Color-coded values
 * - Compact and detailed views
 * - Export capability
 */

import React, { useState, useMemo } from 'react';
import { ArrowUp, ArrowDown, AlertCircle, CheckCircle } from 'lucide-react';

export interface TableColumn {
  key: string;
  label: string;
  width?: string;
  align?: 'left' | 'center' | 'right';
  format?: 'number' | 'percentage' | 'status' | 'timestamp';
  decimals?: number;
  sortable?: boolean;
}

export interface TableRow {
  id: string | number;
  [key: string]: any;
  _status?: 'good' | 'warning' | 'alarm' | 'neutral';
  _highlight?: boolean;
}

interface DataTableProps {
  columns: TableColumn[];
  data: TableRow[];
  title?: string;
  size?: 'sm' | 'md' | 'lg';
  striped?: boolean;
  hoverable?: boolean;
  bordered?: boolean;
  maxHeight?: string;
  emptyMessage?: string;
}

export const DataTable: React.FC<DataTableProps> = ({
  columns,
  data,
  title,
  size = 'md',
  striped = true,
  hoverable = true,
  bordered = false,
  maxHeight = '400px',
  emptyMessage = 'No data available',
}) => {
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');

  // Sort data
  const sortedData = useMemo(() => {
    if (!sortColumn) return data;

    return [...data].sort((a, b) => {
      const aVal = a[sortColumn];
      const bVal = b[sortColumn];

      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
      }

      const aStr = String(aVal || '');
      const bStr = String(bVal || '');
      return sortDirection === 'asc'
        ? aStr.localeCompare(bStr)
        : bStr.localeCompare(aStr);
    });
  }, [data, sortColumn, sortDirection]);

  const handleSort = (columnKey: string, sortable?: boolean) => {
    if (sortable === false) return;

    if (sortColumn === columnKey) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(columnKey);
      setSortDirection('asc');
    }
  };

  // Format cell value
  const formatValue = (value: any, column: TableColumn): React.ReactNode => {
    if (value === null || value === undefined) return '-';

    switch (column.format) {
      case 'number':
        if (typeof value === 'number') {
          return value.toLocaleString(undefined, {
            minimumFractionDigits: column.decimals ?? 0,
            maximumFractionDigits: column.decimals ?? 2,
          });
        }
        return value;

      case 'percentage':
        if (typeof value === 'number') {
          return `${value.toFixed(column.decimals ?? 1)}%`;
        }
        return value;

      case 'status':
        return (
          <div className="flex items-center justify-center">
            {value === 'good' || value === true ? (
              <CheckCircle className="w-4 h-4 text-green-500" />
            ) : value === 'alarm' || value === false ? (
              <AlertCircle className="w-4 h-4 text-red-500" />
            ) : value === 'warning' ? (
              <AlertCircle className="w-4 h-4 text-yellow-500" />
            ) : (
              <span className="text-gray-400">-</span>
            )}
          </div>
        );

      case 'timestamp':
        if (value instanceof Date) {
          return value.toLocaleString();
        }
        if (typeof value === 'string') {
          return new Date(value).toLocaleString();
        }
        return value;

      default:
        return String(value);
    }
  };

  // Size classes
  const sizeClasses = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
  };

  const paddingClasses = {
    sm: 'px-2 py-1',
    md: 'px-3 py-2',
    lg: 'px-4 py-3',
  };

  // Row status colors
  const getRowClasses = (row: TableRow) => {
    const classes = [];

    if (row._highlight) {
      classes.push('bg-blue-50');
    }

    if (row._status) {
      const statusClasses = {
        good: 'bg-green-50',
        warning: 'bg-yellow-50',
        alarm: 'bg-red-50',
        neutral: '',
      };
      if (!row._highlight) {
        classes.push(statusClasses[row._status]);
      }
    }

    return classes.join(' ');
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Title */}
      {title && (
        <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
          <h3 className="text-sm font-semibold text-gray-700">{title}</h3>
        </div>
      )}

      {/* Table */}
      <div className="flex-1 overflow-auto" style={{ maxHeight }}>
        <table className={`w-full ${sizeClasses[size]}`}>
          {/* Header */}
          <thead className="bg-gray-50 sticky top-0 z-10">
            <tr>
              {columns.map((column) => (
                <th
                  key={column.key}
                  className={`
                    ${paddingClasses[size]}
                    font-semibold text-gray-700 border-b-2 border-gray-200
                    ${bordered ? 'border-r border-gray-200' : ''}
                    ${column.sortable !== false ? 'cursor-pointer hover:bg-gray-100 select-none' : ''}
                    text-${column.align || 'left'}
                  `}
                  style={{ width: column.width }}
                  onClick={() => handleSort(column.key, column.sortable)}
                >
                  <div className="flex items-center justify-between">
                    <span>{column.label}</span>
                    {column.sortable !== false && sortColumn === column.key && (
                      <span className="ml-1">
                        {sortDirection === 'asc' ? (
                          <ArrowUp className="w-3 h-3" />
                        ) : (
                          <ArrowDown className="w-3 h-3" />
                        )}
                      </span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>

          {/* Body */}
          <tbody>
            {sortedData.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-4 py-8 text-center text-gray-500"
                >
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              sortedData.map((row, rowIndex) => (
                <tr
                  key={row.id || rowIndex}
                  className={`
                    ${striped && rowIndex % 2 === 1 ? 'bg-gray-50' : 'bg-white'}
                    ${hoverable ? 'hover:bg-gray-100' : ''}
                    ${getRowClasses(row)}
                    transition-colors
                  `}
                >
                  {columns.map((column) => (
                    <td
                      key={column.key}
                      className={`
                        ${paddingClasses[size]}
                        border-b border-gray-200
                        ${bordered ? 'border-r border-gray-200' : ''}
                        text-${column.align || 'left'}
                      `}
                    >
                      {formatValue(row[column.key], column)}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Footer */}
      {sortedData.length > 0 && (
        <div className="px-4 py-2 border-t border-gray-200 bg-gray-50">
          <span className="text-xs text-gray-600">
            {sortedData.length} {sortedData.length === 1 ? 'row' : 'rows'}
          </span>
        </div>
      )}
    </div>
  );
};
