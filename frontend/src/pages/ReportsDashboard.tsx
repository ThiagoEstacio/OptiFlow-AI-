import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  Button,
  Stack,
  Card,
  CardContent,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  CircularProgress,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Divider,
  useTheme,
  alpha
} from '@mui/material';
import { Grid } from '../components/GridWrapper';
import {
  Description,
  PictureAsPdf,
  TableChart,
  DataObject,
  Download,
  Delete,
  Refresh,
  Add,
  CalendarToday,
  FilterList,
  Assessment,
  Timeline,
  Psychology,
  Warning,
  Bolt,
  Factory
} from '@mui/icons-material';

interface ReportTemplate {
  id: string;
  name: string;
  description: string;
  formats: string[];
  parameters: string[];
  estimated_time: string;
}

interface ReportHistoryItem {
  report_id: string;
  report_type: string;
  created_at: string;
  filename: string;
  format: string;
  file_size_bytes: number;
}

export const ReportsDashboard: React.FC = () => {
  const theme = useTheme();

  // State
  const [templates, setTemplates] = useState<ReportTemplate[]>([]);
  const [history, setHistory] = useState<ReportHistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Dialog state
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<ReportTemplate | null>(null);
  const [reportConfig, setReportConfig] = useState({
    format: 'pdf',
    start_date: new Date().toISOString().split('T')[0],
    end_date: new Date().toISOString().split('T')[0],
    filters: {}
  });

  // Load data on mount
  useEffect(() => {
    loadTemplates();
    loadHistory();
  }, []);

  const loadTemplates = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/reports/templates');
      if (response.ok) {
        const data = await response.json();
        setTemplates(data);
      }
    } catch (err) {
      console.error('Error loading templates:', err);
    }
  };

  const loadHistory = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/reports/history?limit=20');
      if (response.ok) {
        const data = await response.json();
        setHistory(data);
      }
    } catch (err) {
      console.error('Error loading history:', err);
    }
  };

  const handleGenerateReport = async () => {
    if (!selectedTemplate) return;

    setGenerating(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch('http://localhost:8000/api/v1/reports/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          report_type: selectedTemplate.id,
          start_date: reportConfig.start_date,
          end_date: reportConfig.end_date,
          format: reportConfig.format,
          filters: reportConfig.filters
        })
      });

      if (response.ok) {
        const data = await response.json();
        setSuccess(`Relatório gerado com sucesso! Tamanho: ${(data.file_size_bytes / 1024).toFixed(0)} KB`);
        setDialogOpen(false);
        loadHistory();

        // Auto download
        if (data.filename) {
          handleDownload(data.filename);
        }
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Erro ao gerar relatório');
      }
    } catch (err) {
      setError('Erro de conexão ao gerar relatório');
      console.error(err);
    } finally {
      setGenerating(false);
    }
  };

  const handleDownload = async (filename: string) => {
    try {
      window.open(`http://localhost:8000/api/v1/reports/download/${filename}`, '_blank');
    } catch (err) {
      console.error('Error downloading report:', err);
    }
  };

  const handleDelete = async (filename: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/reports/${filename}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        setSuccess('Relatório deletado com sucesso');
        loadHistory();
      }
    } catch (err) {
      console.error('Error deleting report:', err);
      setError('Erro ao deletar relatório');
    }
  };

  const openGenerateDialog = (template: ReportTemplate) => {
    setSelectedTemplate(template);
    setReportConfig({
      format: template.formats[0],
      start_date: new Date().toISOString().split('T')[0],
      end_date: new Date().toISOString().split('T')[0],
      filters: {}
    });
    setDialogOpen(true);
  };

  const getFormatIcon = (format: string) => {
    switch (format) {
      case 'pdf': return <PictureAsPdf />;
      case 'excel': return <TableChart />;
      case 'csv': return <DataObject />;
      default: return <Description />;
    }
  };

  const getTemplateIcon = (templateId: string) => {
    if (templateId.includes('operational')) return <Factory sx={{ fontSize: 40 }} />;
    if (templateId.includes('quality')) return <Assessment sx={{ fontSize: 40 }} />;
    if (templateId.includes('ml')) return <Psychology sx={{ fontSize: 40 }} />;
    if (templateId.includes('alarm')) return <Warning sx={{ fontSize: 40 }} />;
    if (templateId.includes('energy')) return <Bolt sx={{ fontSize: 40 }} />;
    return <Description sx={{ fontSize: 40 }} />;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <Box sx={{ bgcolor: 'background.default', minHeight: '100vh', pb: 4 }}>
      {/* Header */}
      <Paper
        elevation={0}
        sx={{
          background: `linear-gradient(135deg, ${theme.palette.info.main} 0%, ${theme.palette.info.dark} 100%)`,
          color: 'white',
          pt: 4,
          pb: 6,
          mb: 4
        }}
      >
        <Container maxWidth="xl">
          <Stack direction="row" alignItems="center" spacing={2} mb={2}>
            <Description sx={{ fontSize: 40 }} />
            <Box>
              <Typography variant="h4" fontWeight={700}>
                Relatórios e Exportação
              </Typography>
              <Typography variant="body1" sx={{ opacity: 0.9 }}>
                Gere relatórios profissionais em PDF, Excel ou CSV
              </Typography>
            </Box>
          </Stack>

          <Stack direction="row" spacing={2} mt={3}>
            <Chip
              label={`${templates.length} Templates Disponíveis`}
              sx={{
                bgcolor: 'rgba(255, 255, 255, 0.2)',
                color: 'white',
                fontWeight: 600,
                backdropFilter: 'blur(10px)'
              }}
            />
            <Chip
              label={`${history.length} Relatórios Gerados`}
              sx={{
                bgcolor: 'rgba(255, 255, 255, 0.2)',
                color: 'white',
                fontWeight: 600,
                backdropFilter: 'blur(10px)'
              }}
            />
          </Stack>
        </Container>
      </Paper>

      <Container maxWidth="xl">
        {/* Alerts */}
        {error && (
          <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}
        {success && (
          <Alert severity="success" onClose={() => setSuccess(null)} sx={{ mb: 3 }}>
            {success}
          </Alert>
        )}

        {/* Report Templates */}
        <Box mb={4}>
          <Stack direction="row" justifyContent="space-between" alignItems="center" mb={3}>
            <Typography variant="h5" fontWeight={600}>
              Templates de Relatórios
            </Typography>
            <Button
              startIcon={<Refresh />}
              onClick={loadTemplates}
              disabled={loading}
            >
              Atualizar
            </Button>
          </Stack>

          <Grid container spacing={3}>
            {templates.map((template) => (
              <Grid item xs={12} md={6} lg={4} key={template.id}>
                <Card
                  sx={{
                    height: '100%',
                    transition: 'transform 0.2s, box-shadow 0.2s',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: 4
                    }
                  }}
                >
                  <CardContent>
                    <Stack spacing={2}>
                      {/* Icon & Title */}
                      <Stack direction="row" spacing={2} alignItems="center">
                        <Box
                          sx={{
                            bgcolor: alpha(theme.palette.primary.main, 0.1),
                            borderRadius: 2,
                            p: 1.5,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center'
                          }}
                        >
                          {getTemplateIcon(template.id)}
                        </Box>
                        <Box flex={1}>
                          <Typography variant="h6" fontWeight={600} gutterBottom>
                            {template.name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            ⏱️ {template.estimated_time}
                          </Typography>
                        </Box>
                      </Stack>

                      {/* Description */}
                      <Typography variant="body2" color="text.secondary">
                        {template.description}
                      </Typography>

                      {/* Formats */}
                      <Box>
                        <Typography variant="caption" color="text.secondary" fontWeight={600}>
                          FORMATOS DISPONÍVEIS
                        </Typography>
                        <Stack direction="row" spacing={1} mt={1}>
                          {template.formats.map((format) => (
                            <Chip
                              key={format}
                              icon={getFormatIcon(format)}
                              label={format.toUpperCase()}
                              size="small"
                              variant="outlined"
                            />
                          ))}
                        </Stack>
                      </Box>

                      {/* Generate Button */}
                      <Button
                        variant="contained"
                        fullWidth
                        startIcon={<Add />}
                        onClick={() => openGenerateDialog(template)}
                        sx={{ mt: 2 }}
                      >
                        Gerar Relatório
                      </Button>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>

        <Divider sx={{ my: 4 }} />

        {/* Report History */}
        <Box>
          <Stack direction="row" justifyContent="space-between" alignItems="center" mb={3}>
            <Typography variant="h5" fontWeight={600}>
              Histórico de Relatórios
            </Typography>
            <Button
              startIcon={<Refresh />}
              onClick={loadHistory}
            >
              Atualizar
            </Button>
          </Stack>

          <Paper>
            {history.length === 0 ? (
              <Box sx={{ p: 8, textAlign: 'center' }}>
                <Description sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  Nenhum relatório gerado ainda
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Selecione um template acima para gerar seu primeiro relatório
                </Typography>
              </Box>
            ) : (
              <List>
                {history.map((item, index) => (
                  <React.Fragment key={item.report_id}>
                    {index > 0 && <Divider />}
                    <ListItem>
                      <Stack direction="row" spacing={2} alignItems="center" sx={{ width: '100%' }}>
                        {/* Icon */}
                        <Box
                          sx={{
                            bgcolor: alpha(theme.palette.primary.main, 0.1),
                            borderRadius: 1,
                            p: 1,
                            display: 'flex'
                          }}
                        >
                          {getFormatIcon(item.format)}
                        </Box>

                        {/* Info */}
                        <Box flex={1}>
                          <Typography variant="body1" fontWeight={600}>
                            {item.filename}
                          </Typography>
                          <Stack direction="row" spacing={2} mt={0.5}>
                            <Typography variant="caption" color="text.secondary">
                              {new Date(item.created_at).toLocaleString('pt-BR')}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {formatFileSize(item.file_size_bytes)}
                            </Typography>
                            <Chip
                              label={item.report_type.toUpperCase()}
                              size="small"
                              sx={{ height: 20 }}
                            />
                          </Stack>
                        </Box>

                        {/* Actions */}
                        <Stack direction="row" spacing={1}>
                          <IconButton
                            color="primary"
                            onClick={() => handleDownload(item.filename)}
                            title="Download"
                          >
                            <Download />
                          </IconButton>
                          <IconButton
                            color="error"
                            onClick={() => handleDelete(item.filename)}
                            title="Deletar"
                          >
                            <Delete />
                          </IconButton>
                        </Stack>
                      </Stack>
                    </ListItem>
                  </React.Fragment>
                ))}
              </List>
            )}
          </Paper>
        </Box>
      </Container>

      {/* Generate Report Dialog */}
      <Dialog
        open={dialogOpen}
        onClose={() => !generating && setDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Stack direction="row" spacing={2} alignItems="center">
            {selectedTemplate && getTemplateIcon(selectedTemplate.id)}
            <Box>
              <Typography variant="h6">{selectedTemplate?.name}</Typography>
              <Typography variant="caption" color="text.secondary">
                Configure os parâmetros do relatório
              </Typography>
            </Box>
          </Stack>
        </DialogTitle>

        <DialogContent>
          <Stack spacing={3} sx={{ mt: 2 }}>
            {/* Format Selection */}
            <FormControl fullWidth>
              <InputLabel>Formato</InputLabel>
              <Select
                value={reportConfig.format}
                label="Formato"
                onChange={(e) => setReportConfig({ ...reportConfig, format: e.target.value })}
                disabled={generating}
              >
                {selectedTemplate?.formats.map((format) => (
                  <MenuItem key={format} value={format}>
                    <Stack direction="row" spacing={1} alignItems="center">
                      {getFormatIcon(format)}
                      <span>{format.toUpperCase()}</span>
                    </Stack>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {/* Date Range */}
            {selectedTemplate?.parameters.includes('start_date') && (
              <TextField
                label="Data Inicial"
                type="date"
                value={reportConfig.start_date}
                onChange={(e) => setReportConfig({ ...reportConfig, start_date: e.target.value })}
                InputLabelProps={{ shrink: true }}
                fullWidth
                disabled={generating}
              />
            )}

            {selectedTemplate?.parameters.includes('end_date') && (
              <TextField
                label="Data Final"
                type="date"
                value={reportConfig.end_date}
                onChange={(e) => setReportConfig({ ...reportConfig, end_date: e.target.value })}
                InputLabelProps={{ shrink: true }}
                fullWidth
                disabled={generating}
              />
            )}

            {/* Info */}
            <Alert severity="info">
              <Typography variant="caption">
                <strong>Tempo estimado:</strong> {selectedTemplate?.estimated_time}
              </Typography>
            </Alert>
          </Stack>
        </DialogContent>

        <DialogActions>
          <Button onClick={() => setDialogOpen(false)} disabled={generating}>
            Cancelar
          </Button>
          <Button
            variant="contained"
            onClick={handleGenerateReport}
            disabled={generating}
            startIcon={generating ? <CircularProgress size={20} /> : <Download />}
          >
            {generating ? 'Gerando...' : 'Gerar e Baixar'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
