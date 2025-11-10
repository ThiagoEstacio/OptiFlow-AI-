import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Alert,
  Tab,
  Tabs,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  ShowChart as ShowChartIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import ParetoChart from '../components/quality/ParetoChart';
import apiClient from '../api/client';

interface ParetoItem {
  rank: number;
  failure_type: string;
  count: number;
  percentage: number;
  cumulative_percentage: number;
  is_vital_few: boolean;
}

interface ParetoAnalysis {
  status: string;
  message?: string;
  items: ParetoItem[];
  analysis_period_days: number;
  total_failures: number;
  vital_few_count: number;
  vital_few_percentage: number;
  generated_at: string;
}

interface QualityInsight {
  id: string;
  title: string;
  description: string;
  category: string;
  severity: string;
  tags: string[];
  metrics: any;
  recommendations: string[];
  timestamp: string;
  data?: any;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => {
  return (
    <div hidden={value !== index} style={{ paddingTop: 24 }}>
      {value === index && <Box>{children}</Box>}
    </div>
  );
};

const QualityDashboard: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Pareto data
  const [paretoData, setParetoData] = useState<ParetoAnalysis | null>(null);
  const [paretoTimeRange, setParetoTimeRange] = useState<number>(7);

  // Quality insights
  const [qualityInsights, setQualityInsights] = useState<QualityInsight[]>([]);

  // KPIs
  const [kpis, setKpis] = useState({
    totalIssues: 0,
    vitalFewCount: 0,
    avgResolutionTime: 0,
    qualityScore: 0,
  });

  useEffect(() => {
    fetchQualityData();
  }, [paretoTimeRange]);

  const fetchQualityData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch Pareto analysis
      const paretoResponse = await apiClient.get(
        `/api/v1/quality/pareto?days=${paretoTimeRange}`
      );
      setParetoData(paretoResponse.data);

      // Fetch quality insights from autonomous agent
      const insightsResponse = await apiClient.get('/api/v1/demo/ai-agent/insights', {
        params: { limit: 50 },
      });

      // Filter for quality-related insights
      const qualityFiltered = insightsResponse.data.filter(
        (insight: QualityInsight) =>
          insight.tags?.includes('quality') ||
          insight.tags?.includes('pareto') ||
          insight.tags?.includes('spc') ||
          insight.title.includes('Pareto') ||
          insight.title.includes('Variabilidade') ||
          insight.title.includes('Padrão')
      );

      setQualityInsights(qualityFiltered);

      // Calculate KPIs
      if (paretoResponse.data.items) {
        const vitalFew = paretoResponse.data.items.filter(
          (item: ParetoItem) => item.is_vital_few
        ).length;

        setKpis({
          totalIssues: paretoResponse.data.total_failures || 0,
          vitalFewCount: vitalFew,
          avgResolutionTime: 24, // Mock data
          qualityScore: 100 - (paretoResponse.data.vital_few_percentage || 0),
        });
      }
    } catch (err: any) {
      console.error('Error fetching quality data:', err);
      setError(err.response?.data?.detail || 'Erro ao carregar dados de qualidade');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    fetchQualityData();
  };

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const getSeverityColor = (severity: string) => {
    const colors: Record<string, string> = {
      critical: '#d32f2f',
      high: '#f57c00',
      medium: '#ffa726',
      low: '#4caf50',
      info: '#2196f3',
    };
    return colors[severity.toLowerCase()] || '#757575';
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 1 }}>
            📊 Dashboard de Qualidade
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Ferramentas de gestão da qualidade e análise de dados
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={handleRefresh}
          disabled={loading}
        >
          Atualizar
        </Button>
      </Box>

      {/* KPI Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ height: '100%', backgroundColor: '#e3f2fd' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <WarningIcon sx={{ mr: 1, color: '#1976d2' }} />
                <Typography variant="subtitle2" color="text.secondary">
                  Problemas Totais
                </Typography>
              </Box>
              <Typography variant="h3" sx={{ fontWeight: 'bold', color: '#1976d2' }}>
                {kpis.totalIssues}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Últimos {paretoTimeRange} dias
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ height: '100%', backgroundColor: '#ffebee' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <TrendingUpIcon sx={{ mr: 1, color: '#d32f2f' }} />
                <Typography variant="subtitle2" color="text.secondary">
                  Vital Few (80/20)
                </Typography>
              </Box>
              <Typography variant="h3" sx={{ fontWeight: 'bold', color: '#d32f2f' }}>
                {kpis.vitalFewCount}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Problemas prioritários
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ height: '100%', backgroundColor: '#f3e5f5' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <ShowChartIcon sx={{ mr: 1, color: '#7b1fa2' }} />
                <Typography variant="subtitle2" color="text.secondary">
                  Insights de Qualidade
                </Typography>
              </Box>
              <Typography variant="h3" sx={{ fontWeight: 'bold', color: '#7b1fa2' }}>
                {qualityInsights.length}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Gerados pelo Agent
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ height: '100%', backgroundColor: '#e8f5e9' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <CheckCircleIcon sx={{ mr: 1, color: '#388e3c' }} />
                <Typography variant="subtitle2" color="text.secondary">
                  Score de Qualidade
                </Typography>
              </Box>
              <Typography variant="h3" sx={{ fontWeight: 'bold', color: '#388e3c' }}>
                {kpis.qualityScore.toFixed(0)}%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Baseado em Pareto
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Error display */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange} sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tab label="📊 Análise de Pareto" />
          <Tab label="💡 Insights de Qualidade" />
          <Tab label="📈 Controle Estatístico (SPC)" />
          <Tab label="🔍 Causa Raiz" />
        </Tabs>
      </Paper>

      {/* Tab 1: Pareto Analysis */}
      <TabPanel value={tabValue} index={0}>
        <Paper sx={{ p: 3 }}>
          <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
              🎯 Análise de Pareto (Princípio 80/20)
            </Typography>
            <FormControl size="small" sx={{ minWidth: 200 }}>
              <InputLabel>Período de Análise</InputLabel>
              <Select
                value={paretoTimeRange}
                label="Período de Análise"
                onChange={(e) => setParetoTimeRange(Number(e.target.value))}
              >
                <MenuItem value={7}>Últimos 7 dias</MenuItem>
                <MenuItem value={14}>Últimos 14 dias</MenuItem>
                <MenuItem value={30}>Últimos 30 dias</MenuItem>
                <MenuItem value={60}>Últimos 60 dias</MenuItem>
                <MenuItem value={90}>Últimos 90 dias</MenuItem>
              </Select>
            </FormControl>
          </Box>

          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
              <CircularProgress />
            </Box>
          ) : paretoData?.status === 'success' && paretoData.items.length > 0 ? (
            <>
              <ParetoChart data={paretoData.items} showVitalFewLine={true} />

              {/* Vital Few Recommendations */}
              {paretoData.items.filter((item) => item.is_vital_few).length > 0 && (
                <Box sx={{ mt: 4, p: 3, backgroundColor: '#fff3e0', borderRadius: 1 }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 2 }}>
                    🎯 Recomendações Prioritárias (Vital Few):
                  </Typography>
                  <Grid container spacing={2}>
                    {paretoData.items
                      .filter((item) => item.is_vital_few)
                      .slice(0, 3)
                      .map((item, index) => (
                        <Grid item xs={12} md={4} key={item.rank}>
                          <Card sx={{ backgroundColor: '#fff', borderLeft: '4px solid #ff6b6b' }}>
                            <CardContent>
                              <Typography
                                variant="subtitle2"
                                sx={{ fontWeight: 'bold', mb: 1 }}
                              >
                                #{index + 1}: {item.failure_type}
                              </Typography>
                              <Typography variant="body2" color="text.secondary">
                                {item.count} ocorrências ({item.percentage.toFixed(1)}%)
                              </Typography>
                              <Typography
                                variant="caption"
                                sx={{ display: 'block', mt: 1, fontWeight: 'bold' }}
                              >
                                Acumulado: {item.cumulative_percentage.toFixed(1)}%
                              </Typography>
                            </CardContent>
                          </Card>
                        </Grid>
                      ))}
                  </Grid>
                  <Alert severity="warning" sx={{ mt: 2 }}>
                    <Typography variant="body2">
                      <strong>Ação Recomendada:</strong> Focar esforços de correção nos{' '}
                      {paretoData.items.filter((item) => item.is_vital_few).length} problemas
                      acima pode eliminar <strong>{paretoData.vital_few_percentage.toFixed(1)}%</strong>{' '}
                      das falhas totais.
                    </Typography>
                  </Alert>
                </Box>
              )}
            </>
          ) : (
            <Alert severity="info">
              {paretoData?.message || 'Nenhum dado de falha disponível para análise de Pareto.'}
            </Alert>
          )}
        </Paper>
      </TabPanel>

      {/* Tab 2: Quality Insights */}
      <TabPanel value={tabValue} index={1}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 3 }}>
            💡 Insights de Qualidade (Autonomous Agent)
          </Typography>

          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : qualityInsights.length > 0 ? (
            <Grid container spacing={2}>
              {qualityInsights.map((insight) => (
                <Grid item xs={12} key={insight.id}>
                  <Card
                    sx={{
                      borderLeft: `4px solid ${getSeverityColor(insight.severity)}`,
                    }}
                  >
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                          {insight.title}
                        </Typography>
                        <Chip
                          label={insight.severity.toUpperCase()}
                          size="small"
                          sx={{
                            backgroundColor: getSeverityColor(insight.severity),
                            color: 'white',
                            fontWeight: 'bold',
                          }}
                        />
                      </Box>

                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        {insight.description}
                      </Typography>

                      {/* Tags */}
                      <Box sx={{ mb: 2 }}>
                        {insight.tags?.map((tag) => (
                          <Chip
                            key={tag}
                            label={tag}
                            size="small"
                            sx={{ mr: 1, mb: 1 }}
                            variant="outlined"
                          />
                        ))}
                      </Box>

                      {/* Recommendations */}
                      {insight.recommendations && insight.recommendations.length > 0 && (
                        <Box sx={{ mt: 2, p: 2, backgroundColor: '#f5f5f5', borderRadius: 1 }}>
                          <Typography
                            variant="subtitle2"
                            sx={{ fontWeight: 'bold', mb: 1 }}
                          >
                            💡 Recomendações:
                          </Typography>
                          <ul style={{ margin: 0, paddingLeft: 20 }}>
                            {insight.recommendations.map((rec, idx) => (
                              <li key={idx}>
                                <Typography variant="body2">{rec}</Typography>
                              </li>
                            ))}
                          </ul>
                        </Box>
                      )}

                      <Typography
                        variant="caption"
                        color="text.secondary"
                        sx={{ display: 'block', mt: 2 }}
                      >
                        {new Date(insight.timestamp).toLocaleString('pt-BR')}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          ) : (
            <Alert severity="info">
              Nenhum insight de qualidade disponível no momento. O Autonomous Agent gerará
              insights automaticamente conforme detecta padrões e anomalias.
            </Alert>
          )}
        </Paper>
      </TabPanel>

      {/* Tab 3: SPC (Statistical Process Control) */}
      <TabPanel value={tabValue} index={2}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2 }}>
            📈 Controle Estatístico de Processo (SPC)
          </Typography>
          <Alert severity="info">
            Cartas de controle e análise de variabilidade em desenvolvimento. O Autonomous
            Agent já detecta alta variabilidade (CV {'>'} 15%) e gera insights automaticamente.
          </Alert>

          {/* Show SPC-related insights */}
          {qualityInsights.filter((i) => i.title.includes('Variabilidade')).length > 0 && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 2 }}>
                Alertas de Variabilidade Detectados:
              </Typography>
              {qualityInsights
                .filter((i) => i.title.includes('Variabilidade'))
                .map((insight) => (
                  <Card key={insight.id} sx={{ mb: 2 }}>
                    <CardContent>
                      <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
                        {insight.title}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {insight.description}
                      </Typography>
                      {insight.metrics && (
                        <Box sx={{ mt: 1 }}>
                          <Typography variant="caption" display="block">
                            CV: {insight.metrics.coefficient_of_variation?.toFixed(1)}%
                          </Typography>
                          <Typography variant="caption" display="block">
                            Média: {insight.metrics.mean?.toFixed(2)}
                          </Typography>
                          <Typography variant="caption" display="block">
                            Desvio Padrão: {insight.metrics.stddev?.toFixed(2)}
                          </Typography>
                        </Box>
                      )}
                    </CardContent>
                  </Card>
                ))}
            </Box>
          )}
        </Paper>
      </TabPanel>

      {/* Tab 4: Root Cause Analysis */}
      <TabPanel value={tabValue} index={3}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2 }}>
            🔍 Análise de Causa Raiz
          </Typography>
          <Alert severity="info">
            Diagrama de Ishikawa (Espinha de Peixe) e análise de 5 Porquês em desenvolvimento.
            Insights de padrões recorrentes estão disponíveis na aba "Insights de Qualidade".
          </Alert>

          {/* Show pattern-related insights */}
          {qualityInsights.filter((i) => i.title.includes('Padrão')).length > 0 && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 2 }}>
                Padrões Recorrentes Detectados:
              </Typography>
              {qualityInsights
                .filter((i) => i.title.includes('Padrão'))
                .map((insight) => (
                  <Card
                    key={insight.id}
                    sx={{ mb: 2, borderLeft: '4px solid #f57c00' }}
                  >
                    <CardContent>
                      <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
                        {insight.title}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {insight.description}
                      </Typography>
                      {insight.metrics && (
                        <Box sx={{ mt: 1, p: 1, backgroundColor: '#fff3e0', borderRadius: 1 }}>
                          <Typography variant="caption" display="block">
                            Tipo de Falha: {insight.metrics.failure_type}
                          </Typography>
                          <Typography variant="caption" display="block">
                            Ocorrências: {insight.metrics.occurrence_count}
                          </Typography>
                          <Typography variant="caption" display="block">
                            Percentual: {insight.metrics.percentage?.toFixed(1)}%
                          </Typography>
                        </Box>
                      )}
                    </CardContent>
                  </Card>
                ))}
            </Box>
          )}
        </Paper>
      </TabPanel>
    </Container>
  );
};

export default QualityDashboard;
