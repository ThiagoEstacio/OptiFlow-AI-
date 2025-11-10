/**
 * ROI Calculator Component
 * Interactive ROI calculator showing financial impact and savings breakdown
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Alert,
  CircularProgress,
  Paper,
  Divider,
  Chip,
} from '@mui/material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
} from 'recharts';
import {
  AttachMoney,
  TrendingUp,
  Build,
  Speed,
  AccessTime,
  LocalShipping,
} from '@mui/icons-material';

interface Props {
  siteId: string;
  periodDays: number;
  roiData: any;
}

const ROICalculator: React.FC<Props> = ({ siteId, periodDays, roiData }) => {
  const [trendData, setTrendData] = useState<any>(null);
  const [loadingTrend, setLoadingTrend] = useState(false);

  useEffect(() => {
    fetchTrendData();
  }, [siteId]);

  const fetchTrendData = async () => {
    try {
      setLoadingTrend(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${import.meta.env.VITE_API_URL}/api/v1/executive/roi/trend/${siteId}`,
        {
          params: { months: 6 },
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      setTrendData(response.data);
    } catch (err) {
      console.error('Error fetching ROI trend:', err);
    } finally {
      setLoadingTrend(false);
    }
  };

  if (!roiData) {
    return (
      <Box display="flex" justifyContent="center" p={4}>
        <CircularProgress />
      </Box>
    );
  }

  const totalSavings = roiData.total_savings || 0;
  const annualProjection = roiData.annual_projection || 0;
  const roiPercentage = roiData.roi_percentage || 0;
  const paybackMonths = roiData.payback_period_months || 0;

  const predictiveMaintenance = roiData.predictive_maintenance || {};
  const optimization = roiData.optimization || {};
  const efficiency = roiData.efficiency || {};
  const downtimeAvoided = roiData.downtime_avoided || {};

  // Breakdown chart data
  const breakdownData = [
    {
      category: 'Predictive Maintenance',
      amount: predictiveMaintenance.total_savings || 0,
      icon: <Build />,
      color: '#4caf50',
    },
    {
      category: 'Optimization',
      amount: optimization.total_savings || 0,
      icon: <Speed />,
      color: '#2196f3',
    },
    {
      category: 'Efficiency',
      amount: efficiency.total_savings || 0,
      icon: <LocalShipping />,
      color: '#ff9800',
    },
    {
      category: 'Downtime Avoided',
      amount: downtimeAvoided.total_cost_avoided || 0,
      icon: <AccessTime />,
      color: '#9c27b0',
    },
  ];

  const pieData = breakdownData.map((item) => ({
    name: item.category,
    value: item.amount,
  }));

  const COLORS = ['#4caf50', '#2196f3', '#ff9800', '#9c27b0'];

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  return (
    <Box>
      {/* Summary Cards */}
      <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap', mb: 3 }}>
        <Box sx={{ flex: '1 1 calc(25% - 18px)', minWidth: '200px' }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom variant="body2">
                Total Savings ({periodDays} days)
              </Typography>
              <Typography variant="h4" fontWeight="bold" color="primary">
                {formatCurrency(totalSavings)}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Daily Avg: {formatCurrency(totalSavings / periodDays)}
              </Typography>
            </CardContent>
          </Card>
        </Box>

        <Box sx={{ flex: '1 1 calc(25% - 18px)', minWidth: '200px' }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom variant="body2">
                Annual Projection
              </Typography>
              <Typography variant="h4" fontWeight="bold" color="success.main">
                {formatCurrency(annualProjection)}
              </Typography>
              <Chip
                label={`${roiPercentage.toFixed(1)}% ROI`}
                color="success"
                size="small"
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Box>

        <Box sx={{ flex: '1 1 calc(25% - 18px)', minWidth: '200px' }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom variant="body2">
                Payback Period
              </Typography>
              <Typography variant="h4" fontWeight="bold">
                {paybackMonths.toFixed(1)}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                months
              </Typography>
            </CardContent>
          </Card>
        </Box>

        <Box sx={{ flex: '1 1 calc(25% - 18px)', minWidth: '200px' }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom variant="body2">
                Failures Prevented
              </Typography>
              <Typography variant="h4" fontWeight="bold" color="error.main">
                {predictiveMaintenance.failures_prevented || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                this period
              </Typography>
            </CardContent>
          </Card>
        </Box>
      </Box>

      {/* Breakdown by Category */}
      <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap', mb: 3 }}>
        <Box sx={{ flex: '1 1 calc(58% - 12px)', minWidth: '400px' }}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" gutterBottom>
                Savings Breakdown by Category
              </Typography>
              <Box height={300} mt={2}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={breakdownData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="category" angle={-15} textAnchor="end" height={80} />
                    <YAxis
                      tickFormatter={(value) =>
                        new Intl.NumberFormat('en-US', {
                          notation: 'compact',
                          compactDisplay: 'short',
                        }).format(value)
                      }
                    />
                    <Tooltip
                      formatter={(value: any) => formatCurrency(value)}
                      contentStyle={{ backgroundColor: 'rgba(255,255,255,0.95)' }}
                    />
                    <Bar dataKey="amount" fill="#2196f3">
                      {breakdownData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Box>

        <Box sx={{ flex: '1 1 calc(42% - 12px)', minWidth: '300px' }}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" gutterBottom>
                Savings Distribution
              </Typography>
              <Box height={300} mt={2}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value: any) => formatCurrency(value)} />
                  </PieChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Box>
      </Box>

      {/* Detailed Breakdown */}
      <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
        {breakdownData.map((category, index) => (
          <Box key={index} sx={{ flex: '1 1 calc(25% - 18px)', minWidth: '250px' }}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <Box
                    sx={{
                      backgroundColor: category.color,
                      borderRadius: '50%',
                      width: 40,
                      height: 40,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'white',
                      mr: 2,
                    }}
                  >
                    {category.icon}
                  </Box>
                  <Typography variant="h6" fontWeight="medium">
                    {category.category}
                  </Typography>
                </Box>

                <Typography variant="h5" fontWeight="bold" color={category.color} gutterBottom>
                  {formatCurrency(category.amount)}
                </Typography>

                <Divider sx={{ my: 1 }} />

                {/* Show specific details for each category */}
                {category.category === 'Predictive Maintenance' && (
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      • Failures prevented: {predictiveMaintenance.failures_prevented || 0}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      • Emergency costs avoided: {formatCurrency(predictiveMaintenance.emergency_cost_avoided || 0)}
                    </Typography>
                  </Box>
                )}

                {category.category === 'Optimization' && (
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      • Ships optimized: {optimization.ships_optimized || 0}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      • Hours saved: {(optimization.waiting_hours_saved || 0).toFixed(1)}h
                    </Typography>
                  </Box>
                )}

                {category.category === 'Efficiency' && (
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      • Trucks processed: {efficiency.trucks_processed || 0}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      • Hours saved: {(efficiency.processing_hours_saved || 0).toFixed(1)}h
                    </Typography>
                  </Box>
                )}

                {category.category === 'Downtime Avoided' && (
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      • Critical alarms: {downtimeAvoided.critical_alarms_handled || 0}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      • Downtime avoided: {(downtimeAvoided.downtime_hours_avoided || 0).toFixed(1)}h
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Box>
        ))}
      </Box>

      {/* 6-Month Trend */}
      {trendData && trendData.trend_data && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              6-Month Savings Trend
            </Typography>
            <Box height={300} mt={2}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trendData.trend_data}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis
                    tickFormatter={(value) =>
                      new Intl.NumberFormat('en-US', {
                        notation: 'compact',
                        compactDisplay: 'short',
                      }).format(value)
                    }
                  />
                  <Tooltip formatter={(value: any) => formatCurrency(value)} />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="total_savings"
                    stroke="#2196f3"
                    strokeWidth={3}
                    name="Total Savings"
                  />
                  <Line
                    type="monotone"
                    dataKey="failures_prevented"
                    stroke="#4caf50"
                    strokeWidth={2}
                    name="Failures Prevented"
                    yAxisId="right"
                  />
                </LineChart>
              </ResponsiveContainer>
            </Box>

            <Alert severity="success" sx={{ mt: 2 }}>
              <Typography variant="body2">
                <strong>6-Month Total:</strong> {formatCurrency(trendData.total_savings_6months || 0)}
              </Typography>
            </Alert>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default ROICalculator;
