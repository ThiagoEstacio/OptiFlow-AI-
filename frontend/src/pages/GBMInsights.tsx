import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Alert,
  CircularProgress,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  List,
  ListItem,
  ListItemText,
  Paper,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Warning as WarningIcon,
  Lightbulb as LightbulbIcon,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import axios from 'axios';

const GBMInsights: React.FC = () => {
  const { siteId } = useParams<{ siteId: string }>();
  const [periodDays, setPeriodDays] = useState(30);
  const [overviewData, setOverviewData] = useState<any>(null);
  const [benchmarks, setBenchmarks] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      const headers = { Authorization: `Bearer ${token}` };

      const endDate = new Date().toISOString().split('T')[0];
      const startDate = new Date(Date.now() - periodDays * 24 * 60 * 60 * 1000)
        .toISOString()
        .split('T')[0];

      const [overviewRes, benchmarksRes] = await Promise.all([
        axios.get(
          `${import.meta.env.VITE_API_URL}/api/v1/gbm/insights/${siteId}/overview`,
          {
            headers,
            params: { start_date: startDate, end_date: endDate },
          }
        ),
        axios.get(
          `${import.meta.env.VITE_API_URL}/api/v1/gbm/insights/${siteId}/benchmarks`,
          { headers }
        ),
      ]);

      setOverviewData(overviewRes.data);
      setBenchmarks(benchmarksRes.data);
      setError(null);
    } catch (err: any) {
      console.error('Error fetching insights:', err);
      setError(err.response?.data?.detail || 'Failed to load insights');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [siteId, periodDays]);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Container>
        <Alert severity="error">{error}</Alert>
      </Container>
    );
  }

  if (!overviewData || overviewData.status === 'no_data') {
    return (
      <Container>
        <Alert severity="info">
          No operational data found. Import GBM data to see insights.
        </Alert>
      </Container>
    );
  }

  const kpis = overviewData.kpis || {};
  const insights = overviewData.insights || [];
  const dailyTrends = overviewData.daily_trends || [];
  const productAnalysis = overviewData.product_analysis || [];

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'error';
      case 'medium':
        return 'warning';
      case 'low':
        return 'info';
      default:
        return 'default';
    }
  };

  const getPriorityIcon = (type: string) => {
    switch (type) {
      case 'opportunity':
        return <TrendingUpIcon />;
      case 'bottleneck':
      case 'quality':
      case 'alert':
        return <WarningIcon />;
      default:
        return <LightbulbIcon />;
    }
  };

  return (
    <Container maxWidth="xl">
      <Box sx={{ py: 4 }}>
        {/* Header */}
        <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography variant="h4" gutterBottom fontWeight="bold">
              GBM Logistics Insights
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Operational analytics and actionable insights from imported data
            </Typography>
          </Box>

          <FormControl sx={{ minWidth: 200 }}>
            <InputLabel>Period</InputLabel>
            <Select
              value={periodDays}
              onChange={(e) => setPeriodDays(e.target.value as number)}
              label="Period"
            >
              <MenuItem value={7}>Last 7 days</MenuItem>
              <MenuItem value={30}>Last 30 days</MenuItem>
              <MenuItem value={90}>Last 90 days</MenuItem>
            </Select>
          </FormControl>
        </Box>

        {/* KPI Cards */}
        <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap', mb: 4 }}>
          <Box sx={{ flex: '1 1 calc(25% - 24px)', minWidth: 200 }}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Total Operations
                </Typography>
                <Typography variant="h4" fontWeight="bold">
                  {kpis.total_operations?.toLocaleString() || 0}
                </Typography>
              </CardContent>
            </Card>
          </Box>

          <Box sx={{ flex: '1 1 calc(25% - 24px)', minWidth: 200 }}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Total Tonnage
                </Typography>
                <Typography variant="h4" fontWeight="bold">
                  {kpis.total_tonnage?.toLocaleString(undefined, {
                    maximumFractionDigits: 0,
                  }) || 0}{' '}
                  t
                </Typography>
              </CardContent>
            </Card>
          </Box>

          <Box sx={{ flex: '1 1 calc(25% - 24px)', minWidth: 200 }}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Avg Loading Time
                </Typography>
                <Typography variant="h4" fontWeight="bold">
                  {kpis.avg_loading_time_minutes?.toFixed(0) || 0} min
                </Typography>
              </CardContent>
            </Card>
          </Box>

          <Box sx={{ flex: '1 1 calc(25% - 24px)', minWidth: 200 }}>
            <Card>
              <CardContent>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Quality Approval Rate
                </Typography>
                <Typography variant="h4" fontWeight="bold" color="success.main">
                  {kpis.quality_approved_rate?.toFixed(1) || 0}%
                </Typography>
              </CardContent>
            </Card>
          </Box>
        </Box>

        {/* Performance Score */}
        {benchmarks && benchmarks.status === 'success' && (
          <Box sx={{ mb: 4 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Performance Benchmark
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="h2" fontWeight="bold" color="primary">
                      {benchmarks.overall_score}
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                      {benchmarks.rating}
                    </Typography>
                  </Box>
                  <Box sx={{ flex: 3 }}>
                    <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                      {Object.entries(benchmarks.performance_scores || {}).map(
                        ([metric, score]: [string, any]) => (
                          <Box key={metric} sx={{ flex: '1 1 calc(50% - 8px)', minWidth: 200 }}>
                            <Paper sx={{ p: 2 }}>
                              <Typography variant="body2" color="text.secondary">
                                {metric.replace('avg_', '').replace('_', ' ')}
                              </Typography>
                              <Typography variant="h6" fontWeight="bold">
                                {score.toFixed(0)}%
                              </Typography>
                            </Paper>
                          </Box>
                        )
                      )}
                    </Box>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Box>
        )}

        {/* Charts */}
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mb: 4 }}>
          {/* Daily Trends and Product Mix */}
          <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
            {/* Daily Trends */}
            <Box sx={{ flex: '1 1 calc(66.67% - 16px)', minWidth: 400 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Daily Operations Trend
                  </Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={dailyTrends}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis yAxisId="left" />
                      <YAxis yAxisId="right" orientation="right" />
                      <Tooltip />
                      <Legend />
                      <Line
                        yAxisId="left"
                        type="monotone"
                        dataKey="total_tonnage"
                        stroke="#8884d8"
                        name="Tonnage (t)"
                      />
                      <Line
                        yAxisId="right"
                        type="monotone"
                        dataKey="operations"
                        stroke="#82ca9d"
                        name="Operations"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Box>

            {/* Product Mix */}
            <Box sx={{ flex: '1 1 calc(33.33% - 16px)', minWidth: 300 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Product Mix
                  </Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={productAnalysis}
                        dataKey="total_tonnage"
                        nameKey="product_type"
                        cx="50%"
                        cy="50%"
                        outerRadius={80}
                        label
                      >
                        {productAnalysis.map((entry: any, index: number) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Box>
          </Box>

          {/* Product Performance */}
          <Box>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Product Performance
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={productAnalysis}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="product_type" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="total_tonnage" fill="#8884d8" name="Total Tonnage (t)" />
                    <Bar dataKey="count" fill="#82ca9d" name="Operations Count" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Box>
        </Box>

        {/* Insights */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Actionable Insights
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              AI-generated insights and recommendations based on operational data
            </Typography>

            {insights.length === 0 ? (
              <Alert severity="info">No insights generated yet.</Alert>
            ) : (
              <List>
                {insights.map((insight: any, index: number) => (
                  <ListItem key={index} divider sx={{ alignItems: 'flex-start' }}>
                    <Box sx={{ width: '100%' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        {getPriorityIcon(insight.type)}
                        <Typography variant="subtitle1" fontWeight="bold">
                          {insight.title}
                        </Typography>
                        <Chip
                          label={insight.priority}
                          size="small"
                          color={getPriorityColor(insight.priority)}
                        />
                        <Chip label={insight.type} size="small" variant="outlined" />
                      </Box>

                      <Typography variant="body2" paragraph>
                        {insight.description}
                      </Typography>

                      <Paper sx={{ p: 2, bgcolor: 'grey.100', mb: 1 }}>
                        <Typography variant="body2" fontWeight="bold" gutterBottom>
                          Impact:
                        </Typography>
                        <Typography variant="body2">{insight.impact}</Typography>
                      </Paper>

                      <Paper sx={{ p: 2, bgcolor: 'primary.light', color: 'primary.contrastText' }}>
                        <Typography variant="body2" fontWeight="bold" gutterBottom>
                          Recommendation:
                        </Typography>
                        <Typography variant="body2">{insight.recommendation}</Typography>
                      </Paper>

                      {insight.potential_savings && (
                        <Alert severity="success" sx={{ mt: 1 }}>
                          <Typography variant="body2" fontWeight="bold">
                            {insight.potential_savings}
                          </Typography>
                        </Alert>
                      )}
                    </Box>
                  </ListItem>
                ))}
              </List>
            )}
          </CardContent>
        </Card>
      </Box>
    </Container>
  );
};

export default GBMInsights;
