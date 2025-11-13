import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  MenuItem,
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  CircularProgress,
} from '@mui/material';
import { Grid } from '../components/GridWrapper';
import {
  Timeline as TimelineIcon,
  Analytics as AnalyticsIcon,
  Download as DownloadIcon,
  CalendarToday as CalendarIcon,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import apiClient from '../api/client';

interface HistoricalData {
  timestamp: string;
  value: number;
  tag_name: string;
  quality: string;
}

interface StatisticalSummary {
  tag_name: string;
  mean: number;
  median: number;
  std: number;
  min: number;
  max: number;
  count: number;
  p25: number;
  p75: number;
  p95: number;
}

const HistoricalDataAnalysis: React.FC = () => {
  const [timeRange, setTimeRange] = useState<string>('last_7_days');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [availableTags, setAvailableTags] = useState<string[]>([]);
  const [historicalData, setHistoricalData] = useState<HistoricalData[]>([]);
  const [statistics, setStatistics] = useState<StatisticalSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [aggregationType, setAggregationType] = useState<string>('raw');

  // Fetch available tags
  useEffect(() => {
    const fetchTags = async () => {
      try {
        // ✅ FIXED: Use correct endpoint
        const response = await apiClient.get('/api/v1/tags/?limit=100');
        const tagNames = response.data.map((tag: any) => tag.name);
        setAvailableTags(tagNames);
        if (tagNames.length > 0) {
          setSelectedTags([tagNames[0]]);
        }
      } catch (error) {
        console.error('Error fetching tags:', error);
        // Set empty array on error to prevent crash
        setAvailableTags([]);
      }
    };
    fetchTags();
  }, []);

  // Fetch historical data
  const fetchHistoricalData = async () => {
    if (selectedTags.length === 0) return;

    setLoading(true);
    try {
      // ✅ FIXED: Convert time_range to actual start_time and end_time
      const end_time = new Date();
      let start_time = new Date();

      switch (timeRange) {
        case 'last_1_hour':
          start_time = new Date(end_time.getTime() - 1 * 60 * 60 * 1000);
          break;
        case 'last_6_hours':
          start_time = new Date(end_time.getTime() - 6 * 60 * 60 * 1000);
          break;
        case 'last_24_hours':
          start_time = new Date(end_time.getTime() - 24 * 60 * 60 * 1000);
          break;
        case 'last_7_days':
          start_time = new Date(end_time.getTime() - 7 * 24 * 60 * 60 * 1000);
          break;
        case 'last_30_days':
          start_time = new Date(end_time.getTime() - 30 * 24 * 60 * 60 * 1000);
          break;
        default:
          start_time = new Date(end_time.getTime() - 7 * 24 * 60 * 60 * 1000);
      }

      // ✅ FIXED: Use correct endpoint for each tag
      const promises = selectedTags.map((tagName) =>
        apiClient.get(`/api/v1/timeseries/tags/${tagName}`, {
          params: {
            start_time: start_time.toISOString(),
            end_time: end_time.toISOString(),
            aggregation: aggregationType !== 'raw' ? aggregationType : undefined,
          },
        })
      );

      const responses = await Promise.all(promises);
      const allData: HistoricalData[] = [];
      const stats: StatisticalSummary[] = [];

      responses.forEach((response, index) => {
        // ✅ FIXED: Handle response format from timeseries endpoint
        const tagData = Array.isArray(response.data) ? response.data : response.data.data || [];

        // Map to HistoricalData format
        const mappedData = tagData.map((point: any) => ({
          timestamp: point.timestamp || point._time,
          value: point.value || point._value,
          tag_name: selectedTags[index],
          quality: point.quality || 'good',
        }));

        allData.push(...mappedData);

        // Calculate statistics
        if (mappedData.length > 0) {
          const values = mappedData.map((d: HistoricalData) => d.value).sort((a: number, b: number) => a - b);
          const mean = values.reduce((a: number, b: number) => a + b, 0) / values.length;
          const median = values[Math.floor(values.length / 2)];
          const std = Math.sqrt(
            values.reduce((sum: number, val: number) => sum + Math.pow(val - mean, 2), 0) / values.length
          );

          stats.push({
            tag_name: selectedTags[index],
            mean,
            median,
            std,
            min: values[0],
            max: values[values.length - 1],
            count: values.length,
            p25: values[Math.floor(values.length * 0.25)],
            p75: values[Math.floor(values.length * 0.75)],
            p95: values[Math.floor(values.length * 0.95)],
          });
        }
      });

      setHistoricalData(allData);
      setStatistics(stats);
    } catch (error) {
      console.error('Error fetching historical data:', error);
      // ✅ ADDED: Set empty arrays on error to prevent crash
      setHistoricalData([]);
      setStatistics([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistoricalData();
  }, [selectedTags, timeRange, aggregationType]);

  // Prepare chart data
  const chartData = historicalData.reduce((acc: any[], item) => {
    const existingPoint = acc.find((p) => p.timestamp === item.timestamp);
    if (existingPoint) {
      existingPoint[item.tag_name] = item.value;
    } else {
      acc.push({
        timestamp: item.timestamp,
        [item.tag_name]: item.value,
      });
    }
    return acc;
  }, []);

  // Sort by timestamp
  chartData.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());

  // Colors for different tags
  const colors = ['#1976d2', '#d32f2f', '#388e3c', '#f57c00', '#7b1fa2', '#0097a7'];

  // Export data
  const handleExport = () => {
    const csv = [
      ['Timestamp', 'Tag Name', 'Value', 'Quality'].join(','),
      ...historicalData.map((d) =>
        [d.timestamp, d.tag_name, d.value, d.quality].join(',')
      ),
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `historical_data_${new Date().toISOString()}.csv`;
    a.click();
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" sx={{ fontWeight: 600 }}>
          Historical Data Analysis
        </Typography>
        <Button
          variant="contained"
          startIcon={<DownloadIcon />}
          onClick={handleExport}
          disabled={historicalData.length === 0}
        >
          Export CSV
        </Button>
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <TextField
                select
                fullWidth
                label="Time Range"
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value)}
                InputProps={{
                  startAdornment: <CalendarIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                }}
              >
                <MenuItem value="last_24h">Last 24 Hours</MenuItem>
                <MenuItem value="last_7_days">Last 7 Days</MenuItem>
                <MenuItem value="last_30_days">Last 30 Days</MenuItem>
                <MenuItem value="last_90_days">Last 90 Days</MenuItem>
              </TextField>
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                select
                fullWidth
                label="Aggregation"
                value={aggregationType}
                onChange={(e) => setAggregationType(e.target.value)}
                InputProps={{
                  startAdornment: <AnalyticsIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                }}
              >
                <MenuItem value="raw">Raw Data</MenuItem>
                <MenuItem value="1m">1 Minute Average</MenuItem>
                <MenuItem value="5m">5 Minutes Average</MenuItem>
                <MenuItem value="1h">1 Hour Average</MenuItem>
                <MenuItem value="1d">Daily Average</MenuItem>
              </TextField>
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                select
                fullWidth
                label="Select Tags"
                value={selectedTags[0] || ''}
                onChange={(e) => setSelectedTags([e.target.value])}
                SelectProps={{
                  multiple: false,
                }}
              >
                {availableTags.map((tag) => (
                  <MenuItem key={tag} value={tag}>
                    {tag}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 5 }}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          {/* Time Series Chart */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Time Series Analysis
              </Typography>
              <ResponsiveContainer width="100%" height={400}>
                <AreaChart data={chartData}>
                  <defs>
                    {selectedTags.map((tag, index) => (
                      <linearGradient key={tag} id={`color-${index}`} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={colors[index % colors.length]} stopOpacity={0.8} />
                        <stop offset="95%" stopColor={colors[index % colors.length]} stopOpacity={0} />
                      </linearGradient>
                    ))}
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="timestamp"
                    tickFormatter={(value) => new Date(value).toLocaleDateString()}
                  />
                  <YAxis />
                  <Tooltip
                    labelFormatter={(value) => new Date(value).toLocaleString()}
                    formatter={(value: any) => [value.toFixed(2), 'Value']}
                  />
                  <Legend />
                  {selectedTags.map((tag, index) => (
                    <Area
                      key={tag}
                      type="monotone"
                      dataKey={tag}
                      stroke={colors[index % colors.length]}
                      fillOpacity={1}
                      fill={`url(#color-${index})`}
                    />
                  ))}
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Statistical Summary */}
          <Grid container spacing={3} sx={{ mb: 3 }}>
            {statistics.map((stat, index) => (
              <Grid item xs={12} md={6} key={stat.tag_name}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      {stat.tag_name} - Statistical Summary
                    </Typography>
                    <Grid container spacing={2}>
                      <Grid item xs={6}>
                        <Typography variant="body2" color="text.secondary">
                          Mean
                        </Typography>
                        <Typography variant="h6">{stat.mean.toFixed(2)}</Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="body2" color="text.secondary">
                          Median
                        </Typography>
                        <Typography variant="h6">{stat.median.toFixed(2)}</Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="body2" color="text.secondary">
                          Std Dev
                        </Typography>
                        <Typography variant="h6">{stat.std.toFixed(2)}</Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="body2" color="text.secondary">
                          Count
                        </Typography>
                        <Typography variant="h6">{stat.count}</Typography>
                      </Grid>
                      <Grid item xs={12}>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          Range
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                          <Chip label={`Min: ${stat.min.toFixed(2)}`} size="small" />
                          <Chip label={`P25: ${stat.p25.toFixed(2)}`} size="small" />
                          <Chip label={`P75: ${stat.p75.toFixed(2)}`} size="small" />
                          <Chip label={`P95: ${stat.p95.toFixed(2)}`} size="small" />
                          <Chip label={`Max: ${stat.max.toFixed(2)}`} size="small" />
                        </Box>
                      </Grid>
                    </Grid>

                    {/* Distribution Chart */}
                    <Box sx={{ mt: 3 }}>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Distribution
                      </Typography>
                      <ResponsiveContainer width="100%" height={150}>
                        <BarChart
                          data={[
                            { name: 'Min', value: stat.min },
                            { name: 'P25', value: stat.p25 },
                            { name: 'Median', value: stat.median },
                            { name: 'Mean', value: stat.mean },
                            { name: 'P75', value: stat.p75 },
                            { name: 'P95', value: stat.p95 },
                            { name: 'Max', value: stat.max },
                          ]}
                        >
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="name" />
                          <YAxis />
                          <Tooltip formatter={(value: any) => value.toFixed(2)} />
                          <Bar dataKey="value" fill={colors[index % colors.length]} />
                          <ReferenceLine y={stat.mean} stroke="red" strokeDasharray="3 3" label="Mean" />
                        </BarChart>
                      </ResponsiveContainer>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>

          {/* Data Quality Analysis */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Data Quality Overview
              </Typography>
              <Grid container spacing={3}>
                <Grid item xs={12} md={4}>
                  <Typography variant="body2" color="text.secondary">
                    Total Records
                  </Typography>
                  <Typography variant="h4">{historicalData.length}</Typography>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Typography variant="body2" color="text.secondary">
                    Good Quality
                  </Typography>
                  <Typography variant="h4" sx={{ color: 'success.main' }}>
                    {historicalData.filter((d) => d.quality === 'good').length}
                  </Typography>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Typography variant="body2" color="text.secondary">
                    Bad/Uncertain
                  </Typography>
                  <Typography variant="h4" sx={{ color: 'error.main' }}>
                    {historicalData.filter((d) => d.quality !== 'good').length}
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          {/* Raw Data Table (Sample) */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Data Points (Last 50)
              </Typography>
              <TableContainer component={Paper} sx={{ maxHeight: 400 }}>
                <Table stickyHeader size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Timestamp</TableCell>
                      <TableCell>Tag Name</TableCell>
                      <TableCell align="right">Value</TableCell>
                      <TableCell>Quality</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {historicalData.slice(0, 50).map((row, index) => (
                      <TableRow key={index}>
                        <TableCell>{new Date(row.timestamp).toLocaleString()}</TableCell>
                        <TableCell>{row.tag_name}</TableCell>
                        <TableCell align="right">{row.value.toFixed(2)}</TableCell>
                        <TableCell>
                          <Chip
                            label={row.quality}
                            size="small"
                            color={row.quality === 'good' ? 'success' : 'error'}
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </>
      )}
    </Box>
  );
};

export default HistoricalDataAnalysis;
