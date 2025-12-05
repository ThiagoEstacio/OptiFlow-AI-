/**
 * DataTable Component - Professional v1.0
 * ========================================
 *
 * Reusable table component with:
 * - Pagination (client-side)
 * - Sorting
 * - Search/filter
 * - Responsive design
 * - Accessibility support
 * - Loading and empty states
 */
import React, { useState, useMemo, useCallback } from 'react';
import {
  ChevronUp,
  ChevronDown,
  ChevronsUpDown,
  ChevronLeft,
  ChevronRight,
  Search,
  Loader2,
  AlertCircle,
  Database,
} from 'lucide-react';

// ============================================
// TYPES
// ============================================
export interface Column<T> {
  key: keyof T | string;
  header: string;
  sortable?: boolean;
  width?: string;
  align?: 'left' | 'center' | 'right';
  render?: (value: any, row: T, index: number) => React.ReactNode;
}

export interface DataTableProps<T> {
  data: T[];
  columns: Column<T>[];
  pageSize?: number;
  pageSizeOptions?: number[];
  searchable?: boolean;
  searchPlaceholder?: string;
  searchKeys?: (keyof T)[];
  loading?: boolean;
  emptyMessage?: string;
  emptyIcon?: React.ReactNode;
  className?: string;
  rowClassName?: string | ((row: T, index: number) => string);
  onRowClick?: (row: T, index: number) => void;
  stickyHeader?: boolean;
  maxHeight?: string;
  showRowNumbers?: boolean;
  isDemo?: boolean;
}

type SortDirection = 'asc' | 'desc' | null;

// ============================================
// COMPONENT
// ============================================
export function DataTable<T extends Record<string, any>>({
  data,
  columns,
  pageSize: initialPageSize = 10,
  pageSizeOptions = [5, 10, 20, 50],
  searchable = true,
  searchPlaceholder = 'Buscar...',
  searchKeys,
  loading = false,
  emptyMessage = 'Nenhum dado encontrado',
  emptyIcon,
  className = '',
  rowClassName,
  onRowClick,
  stickyHeader = false,
  maxHeight,
  showRowNumbers = false,
  isDemo = false,
}: DataTableProps<T>) {
  // State
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(initialPageSize);
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>(null);
  const [searchTerm, setSearchTerm] = useState('');

  // Get nested value from object
  const getNestedValue = useCallback((obj: T, key: string): any => {
    return key.split('.').reduce((acc, part) => acc?.[part], obj as any);
  }, []);

  // Filter data
  const filteredData = useMemo(() => {
    if (!searchTerm.trim()) return data;

    const term = searchTerm.toLowerCase();
    const keysToSearch = searchKeys || columns.map(c => c.key as keyof T);

    return data.filter(row =>
      keysToSearch.some(key => {
        const value = getNestedValue(row, key as string);
        if (value == null) return false;
        return String(value).toLowerCase().includes(term);
      })
    );
  }, [data, searchTerm, searchKeys, columns, getNestedValue]);

  // Sort data
  const sortedData = useMemo(() => {
    if (!sortKey || !sortDirection) return filteredData;

    return [...filteredData].sort((a, b) => {
      const aValue = getNestedValue(a, sortKey);
      const bValue = getNestedValue(b, sortKey);

      if (aValue == null && bValue == null) return 0;
      if (aValue == null) return sortDirection === 'asc' ? 1 : -1;
      if (bValue == null) return sortDirection === 'asc' ? -1 : 1;

      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sortDirection === 'asc' ? aValue - bValue : bValue - aValue;
      }

      const aStr = String(aValue).toLowerCase();
      const bStr = String(bValue).toLowerCase();
      const comparison = aStr.localeCompare(bStr, 'pt-BR');
      return sortDirection === 'asc' ? comparison : -comparison;
    });
  }, [filteredData, sortKey, sortDirection, getNestedValue]);

  // Paginate data
  const paginatedData = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return sortedData.slice(start, start + pageSize);
  }, [sortedData, currentPage, pageSize]);

  // Pagination info
  const totalPages = Math.ceil(sortedData.length / pageSize);
  const startItem = (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, sortedData.length);

  // Handlers
  const handleSort = useCallback((key: string) => {
    if (sortKey === key) {
      if (sortDirection === 'asc') {
        setSortDirection('desc');
      } else if (sortDirection === 'desc') {
        setSortKey(null);
        setSortDirection(null);
      }
    } else {
      setSortKey(key);
      setSortDirection('asc');
    }
    setCurrentPage(1);
  }, [sortKey, sortDirection]);

  const handlePageChange = useCallback((page: number) => {
    setCurrentPage(Math.max(1, Math.min(page, totalPages)));
  }, [totalPages]);

  const handlePageSizeChange = useCallback((newSize: number) => {
    setPageSize(newSize);
    setCurrentPage(1);
  }, []);

  const handleSearch = useCallback((value: string) => {
    setSearchTerm(value);
    setCurrentPage(1);
  }, []);

  // Sort icon
  const SortIcon = ({ column }: { column: Column<T> }) => {
    if (!column.sortable) return null;

    const isActive = sortKey === column.key;
    const direction = isActive ? sortDirection : null;

    return (
      <span className="ml-1 inline-flex" aria-hidden="true">
        {direction === 'asc' ? (
          <ChevronUp className="w-4 h-4 text-blue-600" />
        ) : direction === 'desc' ? (
          <ChevronDown className="w-4 h-4 text-blue-600" />
        ) : (
          <ChevronsUpDown className="w-4 h-4 text-slate-300" />
        )}
      </span>
    );
  };

  // Row class resolver
  const getRowClass = (row: T, index: number): string => {
    if (typeof rowClassName === 'function') {
      return rowClassName(row, index);
    }
    return rowClassName || '';
  };

  return (
    <div className={`bg-white rounded-lg border border-slate-200 ${className}`}>
      {/* Header: Search and Demo indicator */}
      {(searchable || isDemo) && (
        <div className="p-4 border-b border-slate-200 flex flex-wrap items-center gap-4 justify-between">
          {searchable && (
            <div className="relative flex-1 min-w-[200px] max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" aria-hidden="true" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => handleSearch(e.target.value)}
                placeholder={searchPlaceholder}
                className="w-full pl-10 pr-4 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400"
                aria-label={searchPlaceholder}
              />
            </div>
          )}
          {isDemo && (
            <span className="text-xs font-medium px-2 py-1 rounded-full bg-amber-100 text-amber-700 flex items-center gap-1">
              <AlertCircle className="w-3 h-3" />
              Dados de demonstração
            </span>
          )}
        </div>
      )}

      {/* Table Container */}
      <div
        className={`overflow-x-auto ${maxHeight ? 'overflow-y-auto' : ''}`}
        style={{ maxHeight }}
      >
        <table className="w-full" role="grid">
          <thead className={stickyHeader ? 'sticky top-0 bg-white z-10' : ''}>
            <tr className="bg-slate-50 border-b border-slate-200">
              {showRowNumbers && (
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider w-12">
                  #
                </th>
              )}
              {columns.map((column) => (
                <th
                  key={String(column.key)}
                  className={`px-4 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wider ${
                    column.align === 'center' ? 'text-center' :
                    column.align === 'right' ? 'text-right' : 'text-left'
                  } ${column.sortable ? 'cursor-pointer hover:bg-slate-100 select-none' : ''}`}
                  style={{ width: column.width }}
                  onClick={column.sortable ? () => handleSort(String(column.key)) : undefined}
                  aria-sort={
                    sortKey === column.key
                      ? sortDirection === 'asc' ? 'ascending' : 'descending'
                      : undefined
                  }
                  role="columnheader"
                  tabIndex={column.sortable ? 0 : undefined}
                  onKeyDown={column.sortable ? (e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      handleSort(String(column.key));
                    }
                  } : undefined}
                >
                  <span className="flex items-center">
                    {column.header}
                    <SortIcon column={column} />
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading ? (
              <tr>
                <td
                  colSpan={columns.length + (showRowNumbers ? 1 : 0)}
                  className="px-4 py-12 text-center"
                >
                  <div className="flex flex-col items-center gap-2 text-slate-500">
                    <Loader2 className="w-8 h-8 animate-spin" />
                    <span>Carregando...</span>
                  </div>
                </td>
              </tr>
            ) : paginatedData.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length + (showRowNumbers ? 1 : 0)}
                  className="px-4 py-12 text-center"
                >
                  <div className="flex flex-col items-center gap-2 text-slate-400">
                    {emptyIcon || <Database className="w-10 h-10" />}
                    <span className="text-sm">{emptyMessage}</span>
                  </div>
                </td>
              </tr>
            ) : (
              paginatedData.map((row, rowIndex) => {
                const actualIndex = (currentPage - 1) * pageSize + rowIndex;
                return (
                  <tr
                    key={actualIndex}
                    className={`hover:bg-slate-50 transition-colors ${
                      onRowClick ? 'cursor-pointer' : ''
                    } ${getRowClass(row, actualIndex)}`}
                    onClick={onRowClick ? () => onRowClick(row, actualIndex) : undefined}
                    role="row"
                    tabIndex={onRowClick ? 0 : undefined}
                    onKeyDown={onRowClick ? (e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        onRowClick(row, actualIndex);
                      }
                    } : undefined}
                  >
                    {showRowNumbers && (
                      <td className="px-4 py-3 text-sm text-slate-400 font-mono">
                        {actualIndex + 1}
                      </td>
                    )}
                    {columns.map((column) => {
                      const value = getNestedValue(row, String(column.key));
                      return (
                        <td
                          key={String(column.key)}
                          className={`px-4 py-3 text-sm text-slate-700 ${
                            column.align === 'center' ? 'text-center' :
                            column.align === 'right' ? 'text-right' : 'text-left'
                          }`}
                          role="gridcell"
                        >
                          {column.render
                            ? column.render(value, row, actualIndex)
                            : value ?? '-'
                          }
                        </td>
                      );
                    })}
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Footer: Pagination */}
      {!loading && sortedData.length > 0 && (
        <div className="px-4 py-3 border-t border-slate-200 flex flex-wrap items-center justify-between gap-4 text-sm">
          {/* Items info */}
          <div className="text-slate-500">
            Mostrando <span className="font-medium text-slate-700">{startItem}</span> a{' '}
            <span className="font-medium text-slate-700">{endItem}</span> de{' '}
            <span className="font-medium text-slate-700">{sortedData.length}</span> itens
            {filteredData.length !== data.length && (
              <span className="text-slate-400"> (filtrado de {data.length})</span>
            )}
          </div>

          {/* Page size selector and pagination */}
          <div className="flex items-center gap-4">
            {/* Page size */}
            <div className="flex items-center gap-2">
              <label htmlFor="pageSize" className="text-slate-500">
                Por página:
              </label>
              <select
                id="pageSize"
                value={pageSize}
                onChange={(e) => handlePageSizeChange(Number(e.target.value))}
                className="px-2 py-1 border border-slate-200 rounded text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/30"
              >
                {pageSizeOptions.map((size) => (
                  <option key={size} value={size}>
                    {size}
                  </option>
                ))}
              </select>
            </div>

            {/* Pagination buttons */}
            <div className="flex items-center gap-1">
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className="p-1.5 rounded hover:bg-slate-100 disabled:opacity-50 disabled:cursor-not-allowed focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
                aria-label="Página anterior"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>

              {/* Page numbers */}
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                let page: number;
                if (totalPages <= 5) {
                  page = i + 1;
                } else if (currentPage <= 3) {
                  page = i + 1;
                } else if (currentPage >= totalPages - 2) {
                  page = totalPages - 4 + i;
                } else {
                  page = currentPage - 2 + i;
                }
                return (
                  <button
                    key={page}
                    onClick={() => handlePageChange(page)}
                    className={`w-8 h-8 rounded text-sm font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 ${
                      currentPage === page
                        ? 'bg-blue-600 text-white'
                        : 'hover:bg-slate-100 text-slate-600'
                    }`}
                    aria-label={`Página ${page}`}
                    aria-current={currentPage === page ? 'page' : undefined}
                  >
                    {page}
                  </button>
                );
              })}

              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="p-1.5 rounded hover:bg-slate-100 disabled:opacity-50 disabled:cursor-not-allowed focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
                aria-label="Próxima página"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default DataTable;
