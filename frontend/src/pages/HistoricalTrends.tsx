import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Tab,
  Tabs,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
} from 'recharts';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Remove as FlatIcon,
} from '@mui/icons-material';
import axios from 'axios';
import { LoadingState } from '../components/ui/LoadingState';
import { EmptyState } from '../components/ui/EmptyState';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div role="tabpanel" hidden={value !== index} {...other}>
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

const HistoricalTrends: React.FC = () => {
  const { siteId } = useParams<{ siteId: string }>();
  const [tabValue, setTabValue] = useState(0);
  const [monthlyData, setMonthlyData] = useState<any>(null);
  const [trendData, setTrendData] = useState<any>(null);
  const [seasonalData, setSeasonalData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [monthsToShow, setMonthsToShow] = useState(12);
  const [selectedMetric, setSelectedMetric] = useState('tonnage');

  useEffect(() => {
    fetchData();
  }, [siteId, monthsToShow, selectedMetric]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      const headers = { Authorization: `Bearer ${token}` };

      const [monthlyRes, trendRes, seasonalRes] = await Promise.all([
        axios.get(
          `${import.meta.env.VITE_API_URL}/api/v1/historical/monthly-comparison/${siteId}`,
          { headers, params: { months: monthsToShow } }
        ),
        axios.get(
          `${import.meta.env.VITE_API_URL}/api/v1/historical/trend-analysis/${siteId}`,
          { headers, params: { metric: selectedMetric, period_days: 90 } }
        ),
        axios.get(
          `${import.meta.env.VITE_API_URL}/api/v1/historical/seasonal-analysis/${siteId}`,
          { headers, params: { years: 2 } }
        ),
      ]);

      setMonthlyData(monthlyRes.data);
      setTrendData(trendRes.data);
      setSeasonalData(seasonalRes.data);
      setError(null);
    } catch (err: any) {
      console.error('Error fetching historical data:', err);
      setError(err.response?.data?.detail || 'Erro ao carregar dados históricos');
    } finally {
      setLoading(false);
    }
  };

  const getTrendIcon = (direction: string) => {
    switch (direction) {
      case 'up':
        return <TrendingUpIcon color="success" />;
      case 'down':
        return <TrendingDownIcon color="error" />;
      default:
        return <FlatIcon color="disabled" />;
    }
  };

  const formatChange = (value: number) => {
    if (value === 0) return '0%';
    return `${value > 0 ? '+' : ''}${value.toFixed(1)}%`;
  };

  const getChangeColor = (value: number) => {
    if (value > 0) return 'success.main';
    if (value < 0) return 'error.main';
    return 'text.secondary';
  };

  if (loading) {
    return <LoadingState message="Carregando análise histórica..." />;
  }

  if (error) {
    return (
      <Container>
        <Alert severity="error">{error}</Alert>
      </Container>
    );
  }

  if (!monthlyData || monthlyData.status !== 'success') {
    return (
      <Container>
        <EmptyState
          title="Sem dados históricos"
          description="Importe dados GBM para visualizar tendências históricas"
        />
      </Container>
    );
  }

  const monthly = monthlyData.monthly_data || [];
  const summary = monthlyData.summary || {};

  return (
    <Container maxWidth="xl">
      <Box sx={{ py: 4 }}>
        {/* Header */}
        <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography variant="h4" gutterBottom fontWeight="bold">
              Análise Histórica e Tendências
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Visualize tendências, compare períodos e identifique padrões sazonais
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', gap: 2 }}>
            <FormControl sx={{ minWidth: 150 }}>
              <InputLabel>Período</InputLabel>
              <Select
                value={monthsToShow}
                onChange={(e) => setMonthsToShow(e.target.value as number)}
                label="Período"
              >
                <MenuItem value={6}>6 meses</MenuItem>
                <MenuItem value={12}>12 meses</MenuItem>
                <MenuItem value={24}>24 meses</MenuItem>
                <MenuItem value={36}>36 meses</MenuItem>
              </Select>
            </FormControl>

            <FormControl sx={{ minWidth: 150 }}>
              <InputLabel>Métrica</InputLabel>
              <Select
                value={selectedMetric}
                onChange={(e) => setSelectedMetric(e.target.value)}
                label="Métrica"
              >
                <MenuItem value="tonnage">Tonelagem</MenuItem>
                <MenuItem value="operations">Operações</MenuItem>
                <MenuItem value="loading_time">Tempo de Carga</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </Box>

        {/* Summary Stats */}
        <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap', mb: 4 }}>
          <Box sx={{ flex: '1 1 calc(25% - 24px)', minWidth: 200 }}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Média Mensal (Operações)
                </Typography>
                <Typography variant="h4" fontWeight="bold">
                  {summary.avg_monthly_operations?.toLocaleString(undefined, {
                    maximumFractionDigits: 0,
                  })}
                </Typography>
              </CardContent>
            </Card>
          </Box>

          <Box sx={{ flex: '1 1 calc(25% - 24px)', minWidth: 200 }}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Média Mensal (Toneladas)
                </Typography>
                <Typography variant="h4" fontWeight="bold">
                  {summary.avg_monthly_tonnage?.toLocaleString(undefined, {
                    maximumFractionDigits: 0,
                  })}
                  {' t'}
                </Typography>
              </CardContent>
            </Card>
          </Box>

          <Box sx={{ flex: '1 1 calc(25% - 24px)', minWidth: 200 }}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Melhor Mês
                </Typography>
                <Typography variant="h6" fontWeight="bold">
                  {summary.best_month?.month_name || '-'}
                </Typography>
                <Typography variant="body2" color="success.main">
                  {summary.best_month?.total_tonnage?.toLocaleString(undefined, {
                    maximumFractionDigits: 0,
                  })}
                  {' t'}
                </Typography>
              </CardContent>
            </Card>
          </Box>

          <Box sx={{ flex: '1 1 calc(25% - 24px)', minWidth: 200 }}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Total do Período
                </Typography>
                <Typography variant="h4" fontWeight="bold">
                  {summary.total_tonnage?.toLocaleString(undefined, {
                    maximumFractionDigits: 0,
                  })}
                  {' t'}
                </Typography>
              </CardContent>
            </Card>
          </Box>
        </Box>

        {/* Tabs */}
        <Paper sx={{ mb: 3 }}>
          <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)} variant="fullWidth">
            <Tab label="📈 Comparativo Mensal" />
            <Tab label="📊 Gráfico de Tendência" />
            <Tab label="🌍 Análise Sazonal" />
            <Tab label="📋 Tabela Comparativa" />
          </Tabs>
        </Paper>

        {/* Tab 1: Monthly Comparison Chart */}
        <TabPanel value={tabValue} index={0}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Evolução Mês a Mês
              </Typography>
              <ResponsiveContainer width="100%" height={400}>
                <ComposedChart data={monthly}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Legend />
                  <Area
                    yAxisId="left"
                    type="monotone"
                    dataKey="total_tonnage"
                    fill="#8884d8"
                    stroke="#8884d8"
                    name="Tonelagem (t)"
                    fillOpacity={0.3}
                  />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="operations"
                    stroke="#82ca9d"
                    name="Operações"
                    strokeWidth={2}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabPanel>

        {/* Tab 2: Trend Analysis */}
        <TabPanel value={tabValue} index={1}>
          <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
            <Box sx={{ flex: '1 1 calc(66.67% - 16px)', minWidth: 400 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Análise de Tendência ({selectedMetric})
                  </Typography>
                  {trendData && trendData.status === 'success' && (
                    <>
                      <ResponsiveContainer width="100%" height={350}>
                        <LineChart data={trendData.daily_data}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="date" />
                          <YAxis />
                          <Tooltip />
                          <Legend />
                          <Line
                            type="monotone"
                            dataKey="value"
                            stroke="#8884d8"
                            name="Valor Real"
                            strokeWidth={2}
                            dot={false}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </>
                  )}
                </CardContent>
              </Card>
            </Box>

            <Box sx={{ flex: '1 1 calc(33.33% - 16px)', minWidth: 300 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Indicadores de Tendência
                  </Typography>
                  {trendData && trendData.status === 'success' && (
                    <Box>
                      <Box sx={{ mb: 3, textAlign: 'center' }}>
                        {getTrendIcon(trendData.trend.direction)}
                        <Typography variant="h5" fontWeight="bold" sx={{ mt: 1 }}>
                          {trendData.trend.direction === 'up'
                            ? 'Crescimento'
                            : trendData.trend.direction === 'down'
                            ? 'Queda'
                            : 'Estável'}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Força: {trendData.trend.strength.toFixed(1)}%
                        </Typography>
                      </Box>

                      <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                        <Typography variant="body2" gutterBottom>
                          <strong>Estatísticas:</strong>
                        </Typography>
                        <Typography variant="body2">
                          Média: {trendData.statistics.mean.toFixed(2)}
                        </Typography>
                        <Typography variant="body2">
                          Mediana: {trendData.statistics.median.toFixed(2)}
                        </Typography>
                        <Typography variant="body2">
                          Mín: {trendData.statistics.min.toFixed(2)}
                        </Typography>
                        <Typography variant="body2">
                          Máx: {trendData.statistics.max.toFixed(2)}
                        </Typography>
                        <Typography variant="body2">
                          Atual: {trendData.statistics.current.toFixed(2)}
                        </Typography>
                      </Paper>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Box>
          </Box>
        </TabPanel>

        {/* Tab 3: Seasonal Analysis */}
        <TabPanel value={tabValue} index={2}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Padrões Sazonais (Médias por Mês)
              </Typography>
              {seasonalData && seasonalData.status === 'success' && (
                <>
                  <ResponsiveContainer width="100%" height={400}>
                    <BarChart data={seasonalData.seasonal_patterns}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="month_name" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="avg_tonnage" fill="#8884d8" name="Tonelagem Média (t)" />
                      <Bar dataKey="avg_operations" fill="#82ca9d" name="Operações Médias" />
                    </BarChart>
                  </ResponsiveContainer>

                  {seasonalData.peak_month && (
                    <Alert severity="info" sx={{ mt: 2 }}>
                      <strong>Pico:</strong> {seasonalData.peak_month.month_name} com{' '}
                      {seasonalData.peak_month.avg_tonnage.toFixed(0)} t em média
                    </Alert>
                  )}
                </>
              )}
            </CardContent>
          </Card>
        </TabPanel>

        {/* Tab 4: Comparative Table */}
        <TabPanel value={tabValue} index={3}>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>
                    <strong>Mês</strong>
                  </TableCell>
                  <TableCell align="right">
                    <strong>Operações</strong>
                  </TableCell>
                  <TableCell align="right">
                    <strong>Var. MoM</strong>
                  </TableCell>
                  <TableCell align="right">
                    <strong>Tonelagem (t)</strong>
                  </TableCell>
                  <TableCell align="right">
                    <strong>Var. MoM</strong>
                  </TableCell>
                  <TableCell align="right">
                    <strong>Receita (R$)</strong>
                  </TableCell>
                  <TableCell align="right">
                    <strong>Var. MoM</strong>
                  </TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {monthly.map((row: any, index: number) => (
                  <TableRow key={index} hover>
                    <TableCell>{row.month_name}</TableCell>
                    <TableCell align="right">{row.operations.toLocaleString()}</TableCell>
                    <TableCell align="right">
                      <Typography color={getChangeColor(row.mom_operations)} fontWeight="bold">
                        {formatChange(row.mom_operations)}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      {row.total_tonnage.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    </TableCell>
                    <TableCell align="right">
                      <Typography color={getChangeColor(row.mom_tonnage)} fontWeight="bold">
                        {formatChange(row.mom_tonnage)}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      {row.total_revenue.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    </TableCell>
                    <TableCell align="right">
                      <Typography color={getChangeColor(row.mom_revenue)} fontWeight="bold">
                        {formatChange(row.mom_revenue)}
                      </Typography>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </TabPanel>
      </Box>
    </Container>
  );
};

export default HistoricalTrends;
