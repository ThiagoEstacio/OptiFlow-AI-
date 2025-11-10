import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Alert,
  LinearProgress,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  List,
  ListItem,
  ListItemText,
  Paper,
  CircularProgress,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Download as DownloadIcon,
} from '@mui/icons-material';
import axios from 'axios';

interface ExcelImportTabProps {
  siteId: number;
  dataSources: any[];
  onImportComplete: () => void;
}

const ExcelImportTab: React.FC<ExcelImportTabProps> = ({
  siteId,
  dataSources,
  onImportComplete,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedDataSource, setSelectedDataSource] = useState<number | ''>('');
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // Validate file type
      const validTypes = [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-excel',
        'text/csv',
      ];
      if (validTypes.includes(file.type) || file.name.endsWith('.xlsx') || file.name.endsWith('.xls') || file.name.endsWith('.csv')) {
        setSelectedFile(file);
        setError(null);
        setImportResult(null);
      } else {
        setError('Please select a valid Excel (.xlsx, .xls) or CSV (.csv) file');
        setSelectedFile(null);
      }
    }
  };

  const handleImport = async () => {
    if (!selectedFile || !selectedDataSource) {
      setError('Please select a file and data source');
      return;
    }

    setImporting(true);
    setError(null);
    setImportResult(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('site_id', siteId.toString());
      formData.append('data_source_id', selectedDataSource.toString());

      const token = localStorage.getItem('access_token');
      const endpoint = selectedFile.name.endsWith('.csv')
        ? '/api/v1/gbm/import/csv/'
        : '/api/v1/gbm/import/excel/';

      const response = await axios.post(
        `${import.meta.env.VITE_API_URL}${endpoint}`,
        formData,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      setImportResult(response.data);

      if (response.data.status === 'success') {
        // Clear form
        setSelectedFile(null);
        setSelectedDataSource('');
        // Reset file input
        const fileInput = document.getElementById('file-input') as HTMLInputElement;
        if (fileInput) fileInput.value = '';

        // Notify parent
        onImportComplete();
      }
    } catch (err: any) {
      console.error('Import error:', err);
      setError(err.response?.data?.detail || 'Import failed');
    } finally {
      setImporting(false);
    }
  };

  const downloadTemplate = () => {
    // Create sample CSV template
    const csvContent = `operation_type,operation_date,vehicle_id,product_type,net_weight_kg,gross_weight_kg,tare_weight_kg,moisture_percent,impurity_percent,loading_time_minutes,waiting_time_minutes,origin,destination,notes
ship_loading,2025-01-15 14:30:00,MV GRAIN CARRIER,soy,35000,38500,3500,12.5,0.8,120,45,Santos,China,Normal operation
road_discharge,2025-01-15 09:00:00,ABC-1234,corn,28000,32000,4000,14.2,1.2,60,30,Farm ABC,Terminal,Quality approved
rail_discharge,2025-01-15 16:00:00,Train-001,wheat,50000,52500,2500,13.0,0.5,180,15,Interior,Terminal,Large shipment`;

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'gbm_import_template.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  const excelDataSources = dataSources.filter(
    (ds) => ds.source_type === 'excel' || ds.source_type === 'csv'
  );

  return (
    <Box>
      <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
        {/* Upload Card */}
        <Box sx={{ flex: '1 1 calc(50% - 12px)', minWidth: '300px' }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Upload File
              </Typography>

              <Box sx={{ my: 3 }}>
                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>Data Source</InputLabel>
                  <Select
                    value={selectedDataSource}
                    onChange={(e) => setSelectedDataSource(e.target.value as number)}
                    label="Data Source"
                  >
                    {excelDataSources.map((ds) => (
                      <MenuItem key={ds.id} value={ds.id}>
                        {ds.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>

                <input
                  accept=".xlsx,.xls,.csv"
                  style={{ display: 'none' }}
                  id="file-input"
                  type="file"
                  onChange={handleFileSelect}
                />
                <label htmlFor="file-input">
                  <Button
                    variant="outlined"
                    component="span"
                    fullWidth
                    startIcon={<UploadIcon />}
                    sx={{ mb: 2 }}
                  >
                    Select File
                  </Button>
                </label>

                {selectedFile && (
                  <Paper sx={{ p: 2, mb: 2, bgcolor: 'grey.100' }}>
                    <Typography variant="body2" fontWeight="bold">
                      Selected File:
                    </Typography>
                    <Typography variant="body2">{selectedFile.name}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Size: {(selectedFile.size / 1024).toFixed(2)} KB
                    </Typography>
                  </Paper>
                )}

                <Button
                  variant="contained"
                  fullWidth
                  onClick={handleImport}
                  disabled={!selectedFile || !selectedDataSource || importing}
                  startIcon={importing ? <CircularProgress size={20} /> : <UploadIcon />}
                >
                  {importing ? 'Importing...' : 'Import Data'}
                </Button>
              </Box>

              {importing && <LinearProgress sx={{ my: 2 }} />}

              {error && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  {error}
                </Alert>
              )}

              {importResult && (
                <Box sx={{ mt: 2 }}>
                  {importResult.status === 'success' && (
                    <Alert severity="success" icon={<SuccessIcon />}>
                      <Typography variant="body2" fontWeight="bold">
                        Import Successful!
                      </Typography>
                      <Typography variant="body2">
                        Imported: {importResult.records_imported} records
                      </Typography>
                      {importResult.records_failed > 0 && (
                        <Typography variant="body2" color="warning.main">
                          Failed: {importResult.records_failed} records
                        </Typography>
                      )}
                      {importResult.records_duplicate > 0 && (
                        <Typography variant="body2" color="info.main">
                          Duplicates: {importResult.records_duplicate} records
                        </Typography>
                      )}
                    </Alert>
                  )}

                  {importResult.status === 'pending_approval' && (
                    <Alert severity="warning">
                      <Typography variant="body2" fontWeight="bold">
                        Pending Approval
                      </Typography>
                      <Typography variant="body2">
                        Data validation found issues. Manual approval required.
                      </Typography>
                    </Alert>
                  )}

                  {importResult.warnings && importResult.warnings.length > 0 && (
                    <Alert severity="warning" sx={{ mt: 1 }}>
                      <Typography variant="body2" fontWeight="bold">
                        Warnings:
                      </Typography>
                      {importResult.warnings.slice(0, 3).map((warning: any, idx: number) => (
                        <Typography key={idx} variant="body2">
                          • {warning.message}
                        </Typography>
                      ))}
                    </Alert>
                  )}
                </Box>
              )}
            </CardContent>
          </Card>
        </Box>

        {/* Instructions Card */}
        <Box sx={{ flex: '1 1 calc(50% - 12px)', minWidth: '300px' }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Import Instructions
              </Typography>

              <Box sx={{ my: 2 }}>
                <Typography variant="body2" paragraph>
                  <strong>Step 1:</strong> Select a data source configuration
                </Typography>
                <Typography variant="body2" paragraph>
                  <strong>Step 2:</strong> Choose an Excel (.xlsx, .xls) or CSV (.csv) file
                </Typography>
                <Typography variant="body2" paragraph>
                  <strong>Step 3:</strong> Click "Import Data" to process the file
                </Typography>
              </Box>

              <Button
                variant="outlined"
                fullWidth
                startIcon={<DownloadIcon />}
                onClick={downloadTemplate}
                sx={{ mb: 2 }}
              >
                Download Template
              </Button>

              <Paper sx={{ p: 2, bgcolor: 'info.light', color: 'info.contrastText' }}>
                <Typography variant="body2" fontWeight="bold" gutterBottom>
                  Required Columns:
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemText
                      primary="• operation_type"
                      secondary="Type of operation (ship_loading, road_discharge, etc.)"
                      secondaryTypographyProps={{ style: { color: 'inherit', opacity: 0.8 } }}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="• operation_date"
                      secondary="Date and time (YYYY-MM-DD HH:MM:SS)"
                      secondaryTypographyProps={{ style: { color: 'inherit', opacity: 0.8 } }}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="• net_weight_kg"
                      secondary="Net weight in kilograms"
                      secondaryTypographyProps={{ style: { color: 'inherit', opacity: 0.8 } }}
                    />
                  </ListItem>
                </List>
              </Paper>

              <Box sx={{ mt: 2 }}>
                <Typography variant="caption" color="text.secondary">
                  <strong>Note:</strong> Field mapping will be applied based on the selected data
                  source configuration. Duplicates are detected using external_id if present.
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Box>
      </Box>

      {/* Supported Formats */}
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Supported Data Formats
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            <Chip label="GBM Logística" color="primary" />
            <Chip label="Excel (.xlsx)" color="success" />
            <Chip label="Excel 97-2003 (.xls)" color="success" />
            <Chip label="CSV (.csv)" color="success" />
            <Chip label="Custom APIs" color="info" />
            <Chip label="Manual Entry" color="warning" />
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default ExcelImportTab;
