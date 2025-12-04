/**
 * Export Service - Professional Data Export
 * ==========================================
 *
 * Serviço para exportação de dados em múltiplos formatos:
 * - CSV
 * - Excel (XLSX)
 * - PDF
 * - JSON
 *
 * Suporta exportação de tabelas, gráficos e dashboards completos.
 */

export type ExportFormat = 'csv' | 'xlsx' | 'pdf' | 'json';

export interface ExportOptions {
  filename?: string;
  format: ExportFormat;
  title?: string;
  subtitle?: string;
  includeTimestamp?: boolean;
  includeHeaders?: boolean;
  dateFormat?: string;
  numberFormat?: string;
  sheetName?: string;
}

export interface TableData {
  headers: string[];
  rows: Array<Record<string, any>>;
}

export interface ChartExportData {
  title: string;
  type: string;
  data: any[];
  imageDataUrl?: string;
}

// Helper: Format date for filenames
const formatDateForFilename = (): string => {
  const now = new Date();
  return now.toISOString().slice(0, 19).replace(/[:-]/g, '').replace('T', '_');
};

// Helper: Format value for export
const formatValue = (value: any, type?: string): string => {
  if (value === null || value === undefined) return '';
  if (value instanceof Date) {
    return value.toLocaleDateString('pt-BR');
  }
  if (typeof value === 'number') {
    return value.toLocaleString('pt-BR');
  }
  return String(value);
};

// Helper: Escape CSV value
const escapeCSV = (value: string): string => {
  if (value.includes(',') || value.includes('"') || value.includes('\n')) {
    return `"${value.replace(/"/g, '""')}"`;
  }
  return value;
};

// CSV Export
export const exportToCSV = (
  data: TableData,
  options: Partial<ExportOptions> = {}
): void => {
  const {
    filename = `export_${formatDateForFilename()}`,
    includeHeaders = true,
    includeTimestamp = true,
  } = options;

  const lines: string[] = [];

  // Add metadata
  if (options.title) {
    lines.push(escapeCSV(options.title));
  }
  if (options.subtitle) {
    lines.push(escapeCSV(options.subtitle));
  }
  if (includeTimestamp) {
    lines.push(`Exportado em: ${new Date().toLocaleString('pt-BR')}`);
  }
  if (lines.length > 0) {
    lines.push(''); // Empty line after metadata
  }

  // Add headers
  if (includeHeaders) {
    lines.push(data.headers.map(escapeCSV).join(','));
  }

  // Add rows
  data.rows.forEach((row) => {
    const values = data.headers.map((header) => escapeCSV(formatValue(row[header])));
    lines.push(values.join(','));
  });

  // Download
  const blob = new Blob(['\ufeff' + lines.join('\n')], {
    type: 'text/csv;charset=utf-8;',
  });
  downloadBlob(blob, `${filename}.csv`);
};

// JSON Export
export const exportToJSON = (
  data: any,
  options: Partial<ExportOptions> = {}
): void => {
  const {
    filename = `export_${formatDateForFilename()}`,
    includeTimestamp = true,
  } = options;

  const exportData = {
    ...(options.title && { title: options.title }),
    ...(options.subtitle && { subtitle: options.subtitle }),
    ...(includeTimestamp && { exportedAt: new Date().toISOString() }),
    data,
  };

  const blob = new Blob([JSON.stringify(exportData, null, 2)], {
    type: 'application/json',
  });
  downloadBlob(blob, `${filename}.json`);
};

// Excel Export (simplified - creates CSV with Excel-compatible encoding)
// For full XLSX support, consider adding xlsx library
export const exportToExcel = async (
  data: TableData,
  options: Partial<ExportOptions> = {}
): Promise<void> => {
  const {
    filename = `export_${formatDateForFilename()}`,
    sheetName = 'Dados',
    includeTimestamp = true,
  } = options;

  try {
    // Try to use xlsx library if available
    const XLSX = await import('xlsx').catch(() => null);

    if (XLSX) {
      const workbook = XLSX.utils.book_new();

      // Create worksheet data
      const wsData: any[][] = [];

      // Add title if provided
      if (options.title) {
        wsData.push([options.title]);
        wsData.push([]);
      }

      // Add headers
      wsData.push(data.headers);

      // Add rows
      data.rows.forEach((row) => {
        wsData.push(data.headers.map((header) => row[header]));
      });

      // Add timestamp
      if (includeTimestamp) {
        wsData.push([]);
        wsData.push([`Exportado em: ${new Date().toLocaleString('pt-BR')}`]);
      }

      const worksheet = XLSX.utils.aoa_to_sheet(wsData);
      XLSX.utils.book_append_sheet(workbook, worksheet, sheetName);

      XLSX.writeFile(workbook, `${filename}.xlsx`);
    } else {
      // Fallback to CSV with .xlsx extension hint
      console.warn('xlsx library not available, falling back to CSV format');
      exportToCSV(data, { ...options, filename: `${filename}_excel` });
    }
  } catch (error) {
    console.error('Excel export error:', error);
    // Fallback to CSV
    exportToCSV(data, { ...options, filename: `${filename}_excel` });
  }
};

// PDF Export (simplified - creates print-friendly HTML)
// For full PDF support, consider adding jspdf or pdfmake
export const exportToPDF = async (
  data: TableData,
  options: Partial<ExportOptions> = {}
): Promise<void> => {
  const {
    filename = `export_${formatDateForFilename()}`,
    title,
    subtitle,
    includeTimestamp = true,
  } = options;

  // Create print-friendly HTML
  const html = `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <title>${title || 'Relatório OptiFlow'}</title>
      <style>
        body { font-family: Arial, sans-serif; margin: 40px; color: #333; }
        h1 { color: #1e40af; margin-bottom: 5px; }
        h2 { color: #64748b; font-weight: normal; margin-top: 0; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th { background-color: #1e40af; color: white; padding: 12px 8px; text-align: left; font-weight: 600; }
        td { padding: 10px 8px; border-bottom: 1px solid #e2e8f0; }
        tr:nth-child(even) { background-color: #f8fafc; }
        tr:hover { background-color: #f1f5f9; }
        .footer { margin-top: 30px; padding-top: 15px; border-top: 1px solid #e2e8f0; color: #64748b; font-size: 12px; }
        .logo { font-size: 24px; font-weight: bold; color: #1e40af; }
        @media print {
          body { margin: 20px; }
          .no-print { display: none; }
        }
      </style>
    </head>
    <body>
      <div class="logo">OptiFlow</div>
      ${title ? `<h1>${title}</h1>` : ''}
      ${subtitle ? `<h2>${subtitle}</h2>` : ''}

      <table>
        <thead>
          <tr>
            ${data.headers.map((h) => `<th>${h}</th>`).join('')}
          </tr>
        </thead>
        <tbody>
          ${data.rows
            .map(
              (row) => `
            <tr>
              ${data.headers.map((header) => `<td>${formatValue(row[header])}</td>`).join('')}
            </tr>
          `
            )
            .join('')}
        </tbody>
      </table>

      <div class="footer">
        ${includeTimestamp ? `Exportado em: ${new Date().toLocaleString('pt-BR')} | ` : ''}
        Gerado por OptiFlow AI Platform
      </div>

      <script class="no-print">
        window.onload = function() { window.print(); }
      </script>
    </body>
    </html>
  `;

  // Open in new window for printing
  const printWindow = window.open('', '_blank');
  if (printWindow) {
    printWindow.document.write(html);
    printWindow.document.close();
  }
};

// Helper: Download blob
const downloadBlob = (blob: Blob, filename: string): void => {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

// Main export function
export const exportData = async (
  data: TableData | any[],
  options: ExportOptions
): Promise<void> => {
  // Convert array to TableData if needed
  let tableData: TableData;
  if (Array.isArray(data)) {
    if (data.length === 0) {
      tableData = { headers: [], rows: [] };
    } else {
      tableData = {
        headers: Object.keys(data[0]),
        rows: data,
      };
    }
  } else {
    tableData = data;
  }

  switch (options.format) {
    case 'csv':
      exportToCSV(tableData, options);
      break;
    case 'xlsx':
      await exportToExcel(tableData, options);
      break;
    case 'pdf':
      await exportToPDF(tableData, options);
      break;
    case 'json':
      exportToJSON(tableData.rows, options);
      break;
    default:
      console.error(`Unsupported export format: ${options.format}`);
  }
};

// Export Dashboard (captures current view)
export const exportDashboard = async (
  elementId: string,
  options: Partial<ExportOptions> = {}
): Promise<void> => {
  const element = document.getElementById(elementId);
  if (!element) {
    console.error(`Element with id "${elementId}" not found`);
    return;
  }

  try {
    // Try to use html2canvas if available
    const html2canvas = await import('html2canvas').catch(() => null);

    if (html2canvas) {
      const canvas = await html2canvas.default(element, {
        scale: 2,
        useCORS: true,
        logging: false,
      });

      const link = document.createElement('a');
      link.download = `${options.filename || 'dashboard'}_${formatDateForFilename()}.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();
    } else {
      console.warn('html2canvas not available, using browser print');
      window.print();
    }
  } catch (error) {
    console.error('Dashboard export error:', error);
    window.print();
  }
};

// Export component for UI
export interface ExportButtonProps {
  data: TableData | any[];
  filename?: string;
  title?: string;
  formats?: ExportFormat[];
  className?: string;
}

export default {
  exportToCSV,
  exportToJSON,
  exportToExcel,
  exportToPDF,
  exportData,
  exportDashboard,
};
