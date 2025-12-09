/**
 * 📊 TremorReports - Professional Reports Page
 * =============================================
 *
 * Industrial reports management with:
 * - Report templates library (from API)
 * - Report generation and download
 * - Historical report archive
 * - Export functionality (PDF, Excel, CSV)
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Title,
  Text,
  Badge,
  Button,
  Table,
  TableHead,
  TableRow,
  TableHeaderCell,
  TableBody,
  TableCell,
  TextInput,
  TabGroup,
  TabList,
  Tab,
  TabPanels,
  TabPanel,
  Grid,
  Metric,
  Flex,
} from '@tremor/react';
import apiClient from '../../api/client';
import {
  FileText,
  Download,
  Plus,
  Search,
  FileSpreadsheet,
  FileType,
  Eye,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  FolderOpen,
  BarChart3,
  PieChart,
  TrendingUp,
  Zap,
  Settings,
  Loader2,
  X,
} from 'lucide-react';

// Types
interface ReportTemplate {
  id: string;
  name: string;
  description: string;
  formats: string[];
  parameters: string[];
  estimated_time: string;
}

interface GeneratedReport {
  report_id: string;
  report_type: string;
  created_at: string;
  filename: string;
  format: string;
  file_size_bytes: number;
}

// Icon mapping for templates
const templateIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  operational_daily: BarChart3,
  operational_weekly: BarChart3,
  quality_analysis: PieChart,
  ml_performance: TrendingUp,
  executive_summary: FileText,
  alarm_history: AlertCircle,
  equipment_performance: Settings,
  energy_consumption: Zap,
};

export default function TremorReports() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTab, setSelectedTab] = useState(0);
  const [templates, setTemplates] = useState<ReportTemplate[]>([]);
  const [generatedReports, setGeneratedReports] = useState<GeneratedReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [generationMessage, setGenerationMessage] = useState<string | null>(null);

  // Fetch templates and reports from API
  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [templatesRes, historyRes] = await Promise.all([
        apiClient.get('/api/v1/reports/templates'),
        apiClient.get('/api/v1/reports/history'),
      ]);

      setTemplates(templatesRes.data || []);
      setGeneratedReports(historyRes.data || []);
    } catch (err: any) {
      console.error('Error fetching reports data:', err);
      setError('Erro ao carregar dados de relatórios');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Generate report
  const generateReport = async (template: ReportTemplate, format: string) => {
    setGenerating(template.id + '-' + format);
    setGenerationMessage(null);

    try {
      const today = new Date().toISOString().split('T')[0];
      const response = await apiClient.post('/api/v1/reports/generate', {
        report_type: template.id.includes('operational') ? 'operational' :
                     template.id.includes('quality') ? 'quality' :
                     template.id.includes('executive') ? 'executive' :
                     template.id.includes('ml') ? 'ml' : 'custom',
        format: format,
        start_date: today,
        end_date: today,
      });

      if (response.data.success) {
        setGenerationMessage(`Relatório gerado: ${response.data.filename}`);
        // Refresh history
        const historyRes = await apiClient.get('/api/v1/reports/history');
        setGeneratedReports(historyRes.data || []);

        // Auto-download if URL available
        if (response.data.download_url) {
          window.open(response.data.download_url, '_blank');
        }
      } else {
        setGenerationMessage('Erro ao gerar relatório');
      }
    } catch (err: any) {
      console.error('Error generating report:', err);
      setGenerationMessage('Erro ao gerar relatório: ' + (err.response?.data?.detail || err.message));
    } finally {
      setGenerating(null);
    }
  };

  // Download report
  const downloadReport = async (report: GeneratedReport) => {
    try {
      const response = await apiClient.get(`/api/v1/reports/download/${report.report_id}`, {
        responseType: 'blob',
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', report.filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      console.error('Error downloading report:', err);
      alert('Erro ao baixar relatório');
    }
  };

  // View report (open in new tab)
  const viewReport = async (report: GeneratedReport) => {
    try {
      const response = await apiClient.get(`/api/v1/reports/download/${report.report_id}`, {
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data], {
        type: report.format === 'pdf' ? 'application/pdf' : 'application/octet-stream'
      }));
      window.open(url, '_blank');
    } catch (err: any) {
      console.error('Error viewing report:', err);
      alert('Erro ao visualizar relatório');
    }
  };

  // Filter templates by search
  const filteredTemplates = templates.filter((template) =>
    template.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    template.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getFormatIcon = (format: string) => {
    switch (format.toLowerCase()) {
      case 'pdf':
        return <FileType className="h-4 w-4 text-red-500" />;
      case 'excel':
      case 'xlsx':
        return <FileSpreadsheet className="h-4 w-4 text-green-500" />;
      default:
        return <FileText className="h-4 w-4 text-gray-500" />;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="h-8 w-8 text-blue-600 animate-spin" />
          <Text>Carregando relatórios...</Text>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <Title className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <FileText className="h-8 w-8 text-blue-600" />
            Central de Relatórios
          </Title>
          <Text className="text-gray-500 mt-1">
            Geração e gerenciamento de relatórios industriais
          </Text>
        </div>
        <div className="flex gap-2">
          <Button icon={RefreshCw} variant="secondary" onClick={fetchData}>
            Atualizar
          </Button>
        </div>
      </div>

      {/* Error display */}
      {error && (
        <Card className="bg-red-50 border-red-200">
          <Flex alignItems="center" className="gap-2">
            <AlertCircle className="h-5 w-5 text-red-600" />
            <Text className="text-red-700">{error}</Text>
          </Flex>
        </Card>
      )}

      {/* Generation message */}
      {generationMessage && (
        <Card className={generationMessage.includes('Erro') ? "bg-red-50 border-red-200" : "bg-green-50 border-green-200"}>
          <Flex justifyContent="between" alignItems="center">
            <Flex alignItems="center" className="gap-2">
              {generationMessage.includes('Erro') ? (
                <AlertCircle className="h-5 w-5 text-red-600" />
              ) : (
                <CheckCircle className="h-5 w-5 text-green-600" />
              )}
              <Text className={generationMessage.includes('Erro') ? "text-red-700" : "text-green-700"}>
                {generationMessage}
              </Text>
            </Flex>
            <button onClick={() => setGenerationMessage(null)}>
              <X className="h-4 w-4 text-gray-600" />
            </button>
          </Flex>
        </Card>
      )}

      {/* Quick Stats */}
      <Grid numItems={1} numItemsSm={2} numItemsMd={4} className="gap-4">
        <Card decoration="top" decorationColor="blue">
          <Flex alignItems="start">
            <div>
              <Text>Templates Disponíveis</Text>
              <Metric>{templates.length}</Metric>
            </div>
            <FileText className="h-10 w-10 text-blue-600" />
          </Flex>
        </Card>

        <Card decoration="top" decorationColor="green">
          <Flex alignItems="start">
            <div>
              <Text>Relatórios Gerados</Text>
              <Metric>{generatedReports.length}</Metric>
            </div>
            <FolderOpen className="h-10 w-10 text-green-600" />
          </Flex>
        </Card>

        <Card decoration="top" decorationColor="amber">
          <Flex alignItems="start">
            <div>
              <Text>Formatos PDF</Text>
              <Metric>{generatedReports.filter(r => r.format === 'pdf').length}</Metric>
            </div>
            <FileType className="h-10 w-10 text-amber-600" />
          </Flex>
        </Card>

        <Card decoration="top" decorationColor="purple">
          <Flex alignItems="start">
            <div>
              <Text>Formatos Excel</Text>
              <Metric>{generatedReports.filter(r => r.format === 'xlsx' || r.format === 'excel').length}</Metric>
            </div>
            <FileSpreadsheet className="h-10 w-10 text-purple-600" />
          </Flex>
        </Card>
      </Grid>

      {/* Main Content */}
      <TabGroup index={selectedTab} onIndexChange={setSelectedTab}>
        <TabList className="mt-4">
          <Tab icon={FileText}>Templates ({templates.length})</Tab>
          <Tab icon={FolderOpen}>Relatórios Gerados ({generatedReports.length})</Tab>
        </TabList>

        <TabPanels>
          {/* Templates Tab */}
          <TabPanel>
            <Card className="mt-4">
              <div className="flex flex-col md:flex-row gap-4 mb-6">
                <div className="flex-1">
                  <TextInput
                    icon={Search}
                    placeholder="Buscar templates..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </div>
              </div>

              {filteredTemplates.length === 0 ? (
                <div className="text-center py-8">
                  <FileText className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                  <Text className="text-gray-500">Nenhum template encontrado</Text>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {filteredTemplates.map((template) => {
                    const IconComponent = templateIcons[template.id] || FileText;
                    return (
                      <Card
                        key={template.id}
                        className="hover:shadow-lg transition-shadow border border-gray-200"
                      >
                        <Flex alignItems="start" className="gap-3">
                          <div className="p-3 bg-blue-50 rounded-lg">
                            <IconComponent className="h-6 w-6 text-blue-600" />
                          </div>
                          <div className="flex-1">
                            <Title className="text-base">{template.name}</Title>
                            <Text className="text-sm text-gray-500 mt-1 line-clamp-2">
                              {template.description}
                            </Text>
                            <Flex className="mt-3 gap-2 flex-wrap">
                              {template.formats.map((fmt) => (
                                <Badge key={fmt} color={fmt === 'pdf' ? 'red' : 'green'}>
                                  {fmt.toUpperCase()}
                                </Badge>
                              ))}
                            </Flex>
                            <Text className="text-xs text-gray-400 mt-2">
                              Tempo estimado: {template.estimated_time}
                            </Text>
                            <Flex className="mt-3 gap-2 flex-wrap">
                              {template.formats.slice(0, 2).map((fmt) => (
                                <Button
                                  key={fmt}
                                  size="xs"
                                  variant={fmt === 'pdf' ? 'primary' : 'secondary'}
                                  icon={generating === template.id + '-' + fmt ? Loader2 : Download}
                                  disabled={generating !== null}
                                  onClick={() => generateReport(template, fmt)}
                                >
                                  {generating === template.id + '-' + fmt ? 'Gerando...' : fmt.toUpperCase()}
                                </Button>
                              ))}
                            </Flex>
                          </div>
                        </Flex>
                      </Card>
                    );
                  })}
                </div>
              )}
            </Card>
          </TabPanel>

          {/* Generated Reports Tab */}
          <TabPanel>
            <Card className="mt-4">
              <Flex justifyContent="between" className="mb-4">
                <Title>Relatórios Gerados</Title>
                <Button icon={RefreshCw} variant="secondary" onClick={fetchData}>
                  Atualizar
                </Button>
              </Flex>

              {generatedReports.length === 0 ? (
                <div className="text-center py-8">
                  <FolderOpen className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                  <Text className="text-gray-500">Nenhum relatório gerado ainda</Text>
                  <Button
                    className="mt-4"
                    icon={Plus}
                    onClick={() => setSelectedTab(0)}
                  >
                    Gerar Primeiro Relatório
                  </Button>
                </div>
              ) : (
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableHeaderCell>Nome</TableHeaderCell>
                      <TableHeaderCell>Tipo</TableHeaderCell>
                      <TableHeaderCell>Gerado em</TableHeaderCell>
                      <TableHeaderCell>Tamanho</TableHeaderCell>
                      <TableHeaderCell>Formato</TableHeaderCell>
                      <TableHeaderCell>Status</TableHeaderCell>
                      <TableHeaderCell>Ações</TableHeaderCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {generatedReports.map((report) => (
                      <TableRow key={report.report_id}>
                        <TableCell>
                          <Flex alignItems="center" className="gap-2">
                            {getFormatIcon(report.format)}
                            <Text className="font-medium">{report.filename}</Text>
                          </Flex>
                        </TableCell>
                        <TableCell>
                          <Badge color="gray">{report.report_type}</Badge>
                        </TableCell>
                        <TableCell>
                          <Text>{formatDate(report.created_at)}</Text>
                        </TableCell>
                        <TableCell>
                          <Text>{formatFileSize(report.file_size_bytes)}</Text>
                        </TableCell>
                        <TableCell>
                          <Badge color={report.format === 'pdf' ? 'red' : 'green'}>
                            {report.format.toUpperCase()}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge color="green" icon={CheckCircle}>Concluído</Badge>
                        </TableCell>
                        <TableCell>
                          <Flex className="gap-1">
                            <button
                              className="p-1.5 hover:bg-gray-100 rounded"
                              title="Download"
                              onClick={() => downloadReport(report)}
                            >
                              <Download className="h-4 w-4 text-gray-600" />
                            </button>
                            {report.format === 'pdf' && (
                              <button
                                className="p-1.5 hover:bg-gray-100 rounded"
                                title="Visualizar"
                                onClick={() => viewReport(report)}
                              >
                                <Eye className="h-4 w-4 text-gray-600" />
                              </button>
                            )}
                          </Flex>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </Card>
          </TabPanel>
        </TabPanels>
      </TabGroup>
    </div>
  );
}
