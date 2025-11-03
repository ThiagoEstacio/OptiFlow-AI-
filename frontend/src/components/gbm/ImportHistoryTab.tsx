import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  CircularProgress,
  Alert,
} from '@mui/material';
import axios from 'axios';

interface ImportHistoryTabProps {
  siteId: number;
}

const ImportHistoryTab: React.FC<ImportHistoryTabProps> = ({ siteId }) => {
  const [imports, setImports] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchImportHistory();
  }, [siteId]);

  const fetchImportHistory = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      const response = await axios.get(
        `${import.meta.env.VITE_API_URL}/api/v1/gbm/imports/${siteId}`,
        {
          headers: { Authorization: `Bearer ${token}` },
          params: { limit: 50 },
        }
      );
      setImports(response.data);
      setError(null);
    } catch (err: any) {
      console.error('Error fetching import history:', err);
      setError(err.response?.data?.detail || 'Failed to load import history');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'pending':
      case 'pending_approval':
        return 'warning';
      case 'processing':
        return 'info';
      default:
        return 'default';
    }
  };

  const getImportTypeLabel = (type: string) => {
    switch (type) {
      case 'excel_upload':
        return 'Excel Upload';
      case 'csv_upload':
        return 'CSV Upload';
      case 'api_sync':
        return 'API Sync';
      case 'manual_entry':
        return 'Manual Entry';
      default:
        return type;
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={4}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" onClose={() => setError(null)}>
        {error}
      </Alert>
    );
  }

  if (imports.length === 0) {
    return (
      <Card>
        <CardContent>
          <Alert severity="info">No import history found. Start by importing data.</Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Box>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Import History
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Recent data import operations
          </Typography>

          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Date</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>File Name</TableCell>
                  <TableCell align="right">Total</TableCell>
                  <TableCell align="right">Imported</TableCell>
                  <TableCell align="right">Failed</TableCell>
                  <TableCell align="right">Duplicates</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell align="right">Duration</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {imports.map((imp) => (
                  <TableRow key={imp.id} hover>
                    <TableCell>
                      {new Date(imp.created_at).toLocaleString()}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={getImportTypeLabel(imp.import_type)}
                        size="small"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                        {imp.file_name || '-'}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">{imp.records_total}</TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" color="success.main" fontWeight="bold">
                        {imp.records_imported}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      {imp.records_failed > 0 ? (
                        <Typography variant="body2" color="error.main" fontWeight="bold">
                          {imp.records_failed}
                        </Typography>
                      ) : (
                        imp.records_failed
                      )}
                    </TableCell>
                    <TableCell align="right">{imp.records_duplicate}</TableCell>
                    <TableCell>
                      <Chip
                        label={imp.status}
                        size="small"
                        color={getStatusColor(imp.status)}
                      />
                    </TableCell>
                    <TableCell align="right">
                      {imp.processing_duration_seconds
                        ? `${imp.processing_duration_seconds.toFixed(1)}s`
                        : '-'}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  );
};

export default ImportHistoryTab;
