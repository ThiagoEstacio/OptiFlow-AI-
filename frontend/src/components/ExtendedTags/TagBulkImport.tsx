/**
 * Tag Bulk Import Component
 *
 * Import tags from CSV/Excel files with:
 * - File upload and parsing
 * - Preview before import
 * - Validation and error handling
 * - Progress tracking
 * - Template download
 */

import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  Alert,
  LinearProgress,
  Chip,
  IconButton,
  FormControlLabel,
  Switch,
  Link
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Download as DownloadIcon,
  Close as CloseIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon
} from '@mui/icons-material';
import { TagImportRequest, TagImportItem, TagType } from '../../types/extendedTags';

interface TagBulkImportProps {
  open: boolean;
  onClose: () => void;
  onImport: (request: TagImportRequest) => Promise<void>;
  gatewayId?: number;
}

interface ParsedTag {
  row: number;
  data: Partial<TagImportItem>;
  errors: string[];
  warnings: string[];
}

export const TagBulkImport: React.FC<TagBulkImportProps> = ({
  open,
  onClose,
  onImport,
  gatewayId
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [parsedTags, setParsedTags] = useState<ParsedTag[]>([]);
  const [importing, setImporting] = useState(false);
  const [progress, setProgress] = useState(0);
  const [overwriteExisting, setOverwriteExisting] = useState(false);
  const [result, setResult] = useState<{
    success: boolean;
    message: string;
    created?: number;
    skipped?: number;
    errors?: string[];
  } | null>(null);

  // Download CSV template
  const downloadTemplate = () => {
    const template = `tag_name,asset_path,tag_type,node_id,data_type,unit,description,archive_enabled
TEMP_01,/Plant/Area1/Equipment1,physical,ns=2;s=Temperature,float,°C,Sensor de temperatura,true
PRESS_01,/Plant/Area1/Equipment1,physical,ns=2;s=Pressure,float,bar,Sensor de pressão,true
CALC_EFFICIENCY,/Plant/Area1/Equipment1,calculated,,float,%,Eficiência calculada,true`;

    const blob = new Blob([template], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'template_tags_import.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  // Parse CSV file
  const parseCSV = (text: string): string[][] => {
    const lines = text.split('\n');
    return lines.map(line => {
      const values: string[] = [];
      let current = '';
      let inQuotes = false;

      for (let i = 0; i < line.length; i++) {
        const char = line[i];
        if (char === '"') {
          inQuotes = !inQuotes;
        } else if (char === ',' && !inQuotes) {
          values.push(current.trim());
          current = '';
        } else {
          current += char;
        }
      }
      values.push(current.trim());
      return values;
    });
  };

  // Handle file upload
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const uploadedFile = event.target.files?.[0];
    if (!uploadedFile) return;

    setFile(uploadedFile);
    setResult(null);

    try {
      const text = await uploadedFile.text();
      const rows = parseCSV(text);

      if (rows.length < 2) {
        throw new Error('Arquivo vazio ou sem dados');
      }

      // Parse header
      const header = rows[0].map(h => h.toLowerCase().trim());
      const requiredColumns = ['tag_name', 'asset_path', 'node_id'];
      const missing = requiredColumns.filter(col => !header.includes(col));

      if (missing.length > 0) {
        throw new Error(`Colunas obrigatórias faltando: ${missing.join(', ')}`);
      }

      // Parse data rows
      const parsed: ParsedTag[] = [];
      for (let i = 1; i < rows.length; i++) {
        const row = rows[i];
        if (row.length === 0 || !row[0]) continue; // Skip empty rows

        const errors: string[] = [];
        const warnings: string[] = [];

        const tagData: Partial<TagImportItem> = {
          tag_name: row[header.indexOf('tag_name')],
          asset_path: row[header.indexOf('asset_path')],
          tag_type: (row[header.indexOf('tag_type')] as TagType) || TagType.PHYSICAL,
          address_config: {},
          data_type: row[header.indexOf('data_type')] || 'float',
          unit: row[header.indexOf('unit')],
          description: row[header.indexOf('description')],
          archive_enabled: row[header.indexOf('archive_enabled')] !== 'false'
        };

        // Parse address config
        const nodeId = row[header.indexOf('node_id')];
        if (nodeId) {
          tagData.address_config = { node_id: nodeId };
        }

        // Validate
        if (!tagData.tag_name) {
          errors.push('Nome do tag obrigatório');
        }
        if (!tagData.asset_path) {
          errors.push('Caminho do asset obrigatório');
        }
        if (tagData.tag_type === TagType.PHYSICAL && !nodeId) {
          errors.push('node_id obrigatório para tags físicos');
        }

        // Warnings
        if (!tagData.description) {
          warnings.push('Sem descrição');
        }
        if (!tagData.unit) {
          warnings.push('Sem unidade');
        }

        parsed.push({
          row: i + 1,
          data: tagData,
          errors,
          warnings
        });
      }

      setParsedTags(parsed);
    } catch (error: any) {
      setResult({
        success: false,
        message: error.message || 'Erro ao processar arquivo'
      });
    }
  };

  // Execute import
  const executeImport = async () => {
    if (!gatewayId) {
      setResult({
        success: false,
        message: 'Gateway ID não especificado'
      });
      return;
    }

    const validTags = parsedTags.filter(t => t.errors.length === 0);
    if (validTags.length === 0) {
      setResult({
        success: false,
        message: 'Nenhum tag válido para importar'
      });
      return;
    }

    setImporting(true);
    setProgress(0);

    try {
      const importRequest: TagImportRequest = {
        gateway_id: gatewayId,
        tags: validTags.map(t => t.data as TagImportItem),
        overwrite_existing: overwriteExisting
      };

      await onImport(importRequest);

      setResult({
        success: true,
        message: `Importação concluída com sucesso!`,
        created: validTags.length,
        skipped: parsedTags.length - validTags.length
      });

      setProgress(100);
    } catch (error: any) {
      setResult({
        success: false,
        message: error.response?.data?.detail || 'Erro na importação',
        errors: error.response?.data?.errors
      });
    } finally {
      setImporting(false);
    }
  };

  const handleClose = () => {
    setFile(null);
    setParsedTags([]);
    setResult(null);
    setProgress(0);
    onClose();
  };

  const totalErrors = parsedTags.reduce((sum, t) => sum + t.errors.length, 0);
  const totalWarnings = parsedTags.reduce((sum, t) => sum + t.warnings.length, 0);
  const validCount = parsedTags.filter(t => t.errors.length === 0).length;

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="lg" fullWidth>
      <DialogTitle>
        Importação em Lote de Tags
        <IconButton
          onClick={handleClose}
          sx={{ position: 'absolute', right: 8, top: 8 }}
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent dividers>
        {/* Template Download */}
        <Alert severity="info" sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="body2">
              Baixe o template CSV com as colunas necessárias
            </Typography>
            <Button
              startIcon={<DownloadIcon />}
              onClick={downloadTemplate}
              size="small"
              variant="outlined"
            >
              Download Template
            </Button>
          </Box>
        </Alert>

        {/* File Upload */}
        {!file && !result && (
          <Box
            sx={{
              border: '2px dashed',
              borderColor: 'divider',
              borderRadius: 2,
              p: 4,
              textAlign: 'center',
              cursor: 'pointer',
              '&:hover': {
                borderColor: 'primary.main',
                backgroundColor: 'action.hover'
              }
            }}
          >
            <input
              type="file"
              accept=".csv,.txt"
              onChange={handleFileUpload}
              style={{ display: 'none' }}
              id="csv-upload"
            />
            <label htmlFor="csv-upload" style={{ cursor: 'pointer' }}>
              <UploadIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                Clique para selecionar arquivo CSV
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Formatos aceitos: .csv, .txt
              </Typography>
            </label>
          </Box>
        )}

        {/* Preview Table */}
        {parsedTags.length > 0 && !result && (
          <Box>
            <Box sx={{ mb: 2, display: 'flex', gap: 2, alignItems: 'center' }}>
              <Chip
                label={`${validCount} válidos`}
                color="success"
                size="small"
                icon={<SuccessIcon />}
              />
              {totalErrors > 0 && (
                <Chip
                  label={`${totalErrors} erros`}
                  color="error"
                  size="small"
                  icon={<ErrorIcon />}
                />
              )}
              {totalWarnings > 0 && (
                <Chip
                  label={`${totalWarnings} avisos`}
                  color="warning"
                  size="small"
                />
              )}
            </Box>

            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Linha</TableCell>
                  <TableCell>Nome Tag</TableCell>
                  <TableCell>Asset</TableCell>
                  <TableCell>Tipo</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {parsedTags.slice(0, 10).map((tag, idx) => (
                  <TableRow key={idx}>
                    <TableCell>{tag.row}</TableCell>
                    <TableCell>{tag.data.tag_name}</TableCell>
                    <TableCell>{tag.data.asset_path}</TableCell>
                    <TableCell>{tag.data.tag_type}</TableCell>
                    <TableCell>
                      {tag.errors.length > 0 ? (
                        <Chip label="Erro" color="error" size="small" />
                      ) : tag.warnings.length > 0 ? (
                        <Chip label="Aviso" color="warning" size="small" />
                      ) : (
                        <Chip label="OK" color="success" size="small" />
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>

            {parsedTags.length > 10 && (
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                Mostrando 10 de {parsedTags.length} tags
              </Typography>
            )}

            <FormControlLabel
              control={
                <Switch
                  checked={overwriteExisting}
                  onChange={(e) => setOverwriteExisting(e.target.checked)}
                />
              }
              label="Sobrescrever tags existentes"
              sx={{ mt: 2 }}
            />
          </Box>
        )}

        {/* Import Progress */}
        {importing && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" gutterBottom>
              Importando tags...
            </Typography>
            <LinearProgress variant="determinate" value={progress} />
          </Box>
        )}

        {/* Result */}
        {result && (
          <Alert severity={result.success ? 'success' : 'error'} sx={{ mt: 2 }}>
            <Typography variant="body2">{result.message}</Typography>
            {result.created !== undefined && (
              <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                Criados: {result.created} | Ignorados: {result.skipped}
              </Typography>
            )}
            {result.errors && result.errors.length > 0 && (
              <Box sx={{ mt: 1 }}>
                {result.errors.slice(0, 5).map((err, idx) => (
                  <Typography key={idx} variant="caption" display="block" color="error">
                    • {err}
                  </Typography>
                ))}
              </Box>
            )}
          </Alert>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose}>
          {result ? 'Fechar' : 'Cancelar'}
        </Button>
        {parsedTags.length > 0 && !result && (
          <Button
            onClick={executeImport}
            variant="contained"
            disabled={importing || validCount === 0}
          >
            Importar {validCount} Tag(s)
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default TagBulkImport;
