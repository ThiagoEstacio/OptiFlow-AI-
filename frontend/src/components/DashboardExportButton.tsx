import React, { useState } from 'react';
import {
  Button,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  CircularProgress,
  Snackbar,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Typography,
  Box
} from '@mui/material';
import {
  FileDownload,
  PictureAsPdf,
  TableChart,
  CheckCircle
} from '@mui/icons-material';

interface DashboardExportButtonProps {
  dashboardId: string;
  dashboardName: string;
  /**
   * Function to extract widget data from the dashboard
   * Should return an array of widget objects with:
   * - title: Widget title
   * - type: 'metric' | 'chart' | 'table' | 'status'
   * - value, trend, unit (for metrics)
   * - data, headers (for tables/charts)
   * - status, message (for status widgets)
   */
  getWidgetsData: () => any[];
  variant?: 'text' | 'outlined' | 'contained';
  size?: 'small' | 'medium' | 'large';
}

export const DashboardExportButton: React.FC<DashboardExportButtonProps> = ({
  dashboardId,
  dashboardName,
  getWidgetsData,
  variant = 'outlined',
  size = 'medium'
}) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [confirmDialog, setConfirmDialog] = useState<{
    open: boolean;
    format: string;
  }>({ open: false, format: '' });

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleExportClick = (format: 'pdf' | 'excel') => {
    handleClose();
    setConfirmDialog({ open: true, format });
  };

  const handleConfirmExport = async () => {
    const format = confirmDialog.format;
    setConfirmDialog({ open: false, format: '' });

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      // Get widget data from dashboard
      const widgetsData = getWidgetsData();

      if (!widgetsData || widgetsData.length === 0) {
        throw new Error('Nenhum widget encontrado no dashboard');
      }

      // Get auth token
      const token = localStorage.getItem('access_token');
      if (!token) {
        throw new Error('Usuário não autenticado');
      }

      // Call export API
      const response = await fetch('http://localhost:8000/api/v1/reports/export-dashboard', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          dashboard_id: dashboardId,
          dashboard_name: dashboardName,
          format: format,
          widgets: widgetsData
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Erro ao exportar dashboard');
      }

      const data = await response.json();

      // Auto download
      if (data.filename) {
        const downloadUrl = `http://localhost:8000/api/v1/reports/download/${data.filename}`;
        window.open(downloadUrl, '_blank');
      }

      setSuccess(`Dashboard exportado com sucesso! (${(data.file_size_bytes / 1024).toFixed(0)} KB)`);

    } catch (err: any) {
      setError(err.message || 'Erro ao exportar dashboard');
      console.error('Export error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Button
        variant={variant}
        size={size}
        startIcon={loading ? <CircularProgress size={20} /> : <FileDownload />}
        onClick={handleClick}
        disabled={loading}
      >
        {loading ? 'Exportando...' : 'Exportar'}
      </Button>

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
      >
        <MenuItem onClick={() => handleExportClick('pdf')}>
          <ListItemIcon>
            <PictureAsPdf fontSize="small" />
          </ListItemIcon>
          <ListItemText>Exportar como PDF</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => handleExportClick('excel')}>
          <ListItemIcon>
            <TableChart fontSize="small" />
          </ListItemIcon>
          <ListItemText>Exportar como Excel</ListItemText>
        </MenuItem>
      </Menu>

      {/* Confirmation Dialog */}
      <Dialog
        open={confirmDialog.open}
        onClose={() => setConfirmDialog({ open: false, format: '' })}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Confirmar Exportação</DialogTitle>
        <DialogContent>
          <Box sx={{ py: 2 }}>
            <Typography variant="body1" gutterBottom>
              Você está prestes a exportar o dashboard:
            </Typography>
            <Typography variant="h6" color="primary" gutterBottom sx={{ mt: 2 }}>
              {dashboardName}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
              Formato: <strong>{confirmDialog.format.toUpperCase()}</strong>
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Widgets incluídos: <strong>{getWidgetsData().length}</strong>
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDialog({ open: false, format: '' })}>
            Cancelar
          </Button>
          <Button
            variant="contained"
            onClick={handleConfirmExport}
            startIcon={<FileDownload />}
          >
            Exportar
          </Button>
        </DialogActions>
      </Dialog>

      {/* Success Snackbar */}
      <Snackbar
        open={!!success}
        autoHideDuration={6000}
        onClose={() => setSuccess(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={() => setSuccess(null)}
          severity="success"
          sx={{ width: '100%' }}
          icon={<CheckCircle />}
        >
          {success}
        </Alert>
      </Snackbar>

      {/* Error Snackbar */}
      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={() => setError(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={() => setError(null)}
          severity="error"
          sx={{ width: '100%' }}
        >
          {error}
        </Alert>
      </Snackbar>
    </>
  );
};
