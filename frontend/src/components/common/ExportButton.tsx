/**
 * Export Button Component
 * =======================
 *
 * Dropdown button for exporting data in multiple formats.
 */
import React, { useState, useRef, useEffect } from 'react';
import { Download, FileSpreadsheet, FileText, FileJson, Printer, ChevronDown } from 'lucide-react';
import { exportData, ExportFormat, TableData } from '../../services/exportService';

interface ExportButtonProps {
  data: TableData | any[];
  filename?: string;
  title?: string;
  subtitle?: string;
  formats?: ExportFormat[];
  variant?: 'primary' | 'secondary' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  disabled?: boolean;
}

const formatConfig: Record<ExportFormat, { label: string; icon: React.ReactNode; description: string }> = {
  csv: {
    label: 'CSV',
    icon: <FileText className="w-4 h-4" />,
    description: 'Planilha simples',
  },
  xlsx: {
    label: 'Excel',
    icon: <FileSpreadsheet className="w-4 h-4" />,
    description: 'Microsoft Excel',
  },
  pdf: {
    label: 'PDF',
    icon: <Printer className="w-4 h-4" />,
    description: 'Documento imprimível',
  },
  json: {
    label: 'JSON',
    icon: <FileJson className="w-4 h-4" />,
    description: 'Dados estruturados',
  },
};

export const ExportButton: React.FC<ExportButtonProps> = ({
  data,
  filename = 'export',
  title,
  subtitle,
  formats = ['csv', 'xlsx', 'pdf', 'json'],
  variant = 'secondary',
  size = 'md',
  className = '',
  disabled = false,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [exporting, setExporting] = useState<ExportFormat | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleExport = async (format: ExportFormat) => {
    setExporting(format);
    try {
      await exportData(data, {
        format,
        filename,
        title,
        subtitle,
        includeTimestamp: true,
        includeHeaders: true,
      });
    } catch (error) {
      console.error(`Export to ${format} failed:`, error);
    } finally {
      setExporting(null);
      setIsOpen(false);
    }
  };

  const variantStyles = {
    primary: 'bg-blue-600 hover:bg-blue-700 text-white',
    secondary: 'bg-white hover:bg-slate-50 text-slate-700 border border-slate-200',
    ghost: 'bg-transparent hover:bg-slate-100 text-slate-600',
  };

  const sizeStyles = {
    sm: 'px-2.5 py-1.5 text-xs',
    md: 'px-3 py-2 text-sm',
    lg: 'px-4 py-2.5 text-base',
  };

  // If only one format, show simple button
  if (formats.length === 1) {
    const format = formats[0];
    const config = formatConfig[format];

    return (
      <button
        onClick={() => handleExport(format)}
        disabled={disabled || exporting !== null}
        className={`
          inline-flex items-center gap-2 rounded-lg font-medium transition-colors
          focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2
          disabled:opacity-50 disabled:cursor-not-allowed
          ${variantStyles[variant]}
          ${sizeStyles[size]}
          ${className}
        `}
      >
        {exporting === format ? (
          <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        ) : (
          config.icon
        )}
        <span>Exportar {config.label}</span>
      </button>
    );
  }

  // Multiple formats - show dropdown
  return (
    <div ref={dropdownRef} className="relative inline-block">
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled || exporting !== null}
        className={`
          inline-flex items-center gap-2 rounded-lg font-medium transition-colors
          focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2
          disabled:opacity-50 disabled:cursor-not-allowed
          ${variantStyles[variant]}
          ${sizeStyles[size]}
          ${className}
        `}
      >
        {exporting ? (
          <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        ) : (
          <Download className="w-4 h-4" />
        )}
        <span>Exportar</span>
        <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-xl border border-slate-200 py-1 z-50">
          <div className="px-3 py-2 border-b border-slate-100">
            <p className="text-xs font-medium text-slate-500 uppercase">Formato de exportação</p>
          </div>

          {formats.map((format) => {
            const config = formatConfig[format];
            return (
              <button
                key={format}
                onClick={() => handleExport(format)}
                disabled={exporting !== null}
                className="w-full flex items-start gap-3 px-3 py-2.5 hover:bg-slate-50 transition-colors disabled:opacity-50"
              >
                <div className="p-1.5 rounded-lg bg-slate-100 text-slate-600">
                  {exporting === format ? (
                    <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                  ) : (
                    config.icon
                  )}
                </div>
                <div className="text-left">
                  <p className="text-sm font-medium text-slate-700">{config.label}</p>
                  <p className="text-xs text-slate-500">{config.description}</p>
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default ExportButton;
