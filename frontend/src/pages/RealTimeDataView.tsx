import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  LinearProgress,
  IconButton,
  Switch,
  FormControlLabel,
  TextField,
  MenuItem,
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Refresh as RefreshIcon,
  TrendingUp,
  TrendingDown,
  Remove as StableIcon,
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import apiClient from '../api/client';

interface TagReading {
  tag_name: string;
  value: number;
  unit: string;
  timestamp: string;
  quality: 'good' | 'bad' | 'uncertain';
  category: string;
  trend: 'up' | 'down' | 'stable';
  change_percent: number;
}

interface DataStream {
  tag_name: string;
  history: Array<{ timestamp: string; value: number }>;
}

const RealTimeDataView: React.FC = () => {
  const [isRunning, setIsRunning] = useState(true);
  const [readings, setReadings] = useState<TagReading[]>([]);
  const [dataStreams, setDataStreams] = useState<Map<string, DataStream>>(new Map());
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [refreshInterval, setRefreshInterval] = useState(2000); // 2 seconds
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  // Fetch real-time data
  const fetchRealtimeData = async () => {
    try {
      const response = await apiClient.get('/api/v1/demo/tags/realtime', {
        params: {
          limit: 50,
          category: selectedCategory !== 'all' ? selectedCategory : undefined,
        },
      });

      const newReadings: TagReading[] = response.data.map((item: any) => {
        // Calculate trend
        const oldReading = readings.find(r => r.tag_name === item.tag_name);
        let trend: 'up' | 'down' | 'stable' = 'stable';
        let changePercent = 0;

        if (oldReading && oldReading.value !== 0) {
          changePercent = ((item.value - oldReading.value) / oldReading.value) * 100;
          if (Math.abs(changePercent) > 0.5) {
            trend = changePercent > 0 ? 'up' : 'down';
          }
        }

        return {
          tag_name: item.name || item.tag_name,
          value: item.value,
          unit: item.unit || '',
          timestamp: item.timestamp || new Date().toISOString(),
          quality: item.quality || 'good',
          category: item.category || 'process',
          trend,
          change_percent: changePercent,
        };
      });

      setReadings(newReadings);
      setLastUpdate(new Date());

      // Update data streams for charts
      const newStreams = new Map(dataStreams);
      newReadings.forEach(reading => {
        if (!newStreams.has(reading.tag_name)) {
          newStreams.set(reading.tag_name, {
            tag_name: reading.tag_name,
            history: [],
          });
        }
        const stream = newStreams.get(reading.tag_name)!;
        stream.history.push({
          timestamp: reading.timestamp,
          value: reading.value,
        });
        // Keep only last 30 points
        if (stream.history.length > 30) {
          stream.history = stream.history.slice(-30);
        }
      });
      setDataStreams(newStreams);

    } catch (error) {
      console.error('Error fetching realtime data:', error);
    }
  };

  useEffect(() => {
    if (isRunning) {
      fetchRealtimeData();
      const interval = setInterval(fetchRealtimeData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [isRunning, refreshInterval, selectedCategory]);

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up':
        return <TrendingUp sx={{ color: 'success.main', fontSize: 18 }} />;
      case 'down':
        return <TrendingDown sx={{ color: 'error.main', fontSize: 18 }} />;
      default:
        return <StableIcon sx={{ color: 'text.secondary', fontSize: 18 }} />;
    }
  };

  const getQualityColor = (quality: string) => {
    switch (quality) {
      case 'good':
        return 'success';
      case 'bad':
        return 'error';
      case 'uncertain':
        return 'warning';
      default:
        return 'default';
    }
  };

  const categories = ['all', 'process', 'control', 'energy', 'maintenance', 'quality'];

  // Get top 6 tags for mini charts
  const topTags = Array.from(dataStreams.values()).slice(0, 6);

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" sx={{ fontWeight: 600 }}>
          Real-Time Data Stream
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <TextField
            select
            size="small"
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            sx={{ minWidth: 150 }}
          >
            {categories.map((cat) => (
              <MenuItem key={cat} value={cat}>
                {cat.charAt(0).toUpperCase() + cat.slice(1)}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            select
            size="small"
            value={refreshInterval}
            onChange={(e) => setRefreshInterval(Number(e.target.value))}
            sx={{ minWidth: 120 }}
          >
            <MenuItem value={1000}>1 second</MenuItem>
            <MenuItem value={2000}>2 seconds</MenuItem>
            <MenuItem value={5000}>5 seconds</MenuItem>
            <MenuItem value={10000}>10 seconds</MenuItem>
          </TextField>
          <IconButton
            color={isRunning ? 'primary' : 'default'}
            onClick={() => setIsRunning(!isRunning)}
          >
            {isRunning ? <PauseIcon /> : <PlayIcon />}
          </IconButton>
          <IconButton onClick={fetchRealtimeData}>
            <RefreshIcon />
          </IconButton>
        </Box>
      </Box>

      {/* Status Bar */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={3}>
            <Grid item xs={12} sm={3}>
              <Typography variant="body2" color="text.secondary">
                Status
              </Typography>
              <Typography variant="h6">
                {isRunning ? (
                  <Chip label="LIVE" color="success" size="small" />
                ) : (
                  <Chip label="PAUSED" color="default" size="small" />
                )}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={3}>
              <Typography variant="body2" color="text.secondary">
                Active Tags
              </Typography>
              <Typography variant="h6">{readings.length}</Typography>
            </Grid>
            <Grid item xs={12} sm={3}>
              <Typography variant="body2" color="text.secondary">
                Refresh Rate
              </Typography>
              <Typography variant="h6">{refreshInterval / 1000}s</Typography>
            </Grid>
            <Grid item xs={12} sm={3}>
              <Typography variant="body2" color="text.secondary">
                Last Update
              </Typography>
              <Typography variant="h6">
                {lastUpdate.toLocaleTimeString()}
              </Typography>
            </Grid>
          </Grid>
          {isRunning && <LinearProgress sx={{ mt: 2 }} />}
        </CardContent>
      </Card>

      {/* Mini Charts Grid */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {topTags.map((stream) => (
          <Grid item xs={12} sm={6} md={4} key={stream.tag_name}>
            <Card>
              <CardContent>
                <Typography variant="subtitle2" gutterBottom>
                  {stream.tag_name}
                </Typography>
                <ResponsiveContainer width="100%" height={100}>
                  <LineChart data={stream.history}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="timestamp"
                      hide
                    />
                    <YAxis hide />
                    <Tooltip
                      labelFormatter={(value) => new Date(value).toLocaleTimeString()}
                      formatter={(value: any) => [value.toFixed(2), 'Value']}
                    />
                    <Line
                      type="monotone"
                      dataKey="value"
                      stroke="#1976d2"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
                <Typography variant="h6" sx={{ mt: 1 }}>
                  {stream.history[stream.history.length - 1]?.value.toFixed(2) || 'N/A'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Data Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Live Data Feed
          </Typography>
          <TableContainer component={Paper} sx={{ maxHeight: 600 }}>
            <Table stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell>Tag Name</TableCell>
                  <TableCell align="right">Value</TableCell>
                  <TableCell>Unit</TableCell>
                  <TableCell>Trend</TableCell>
                  <TableCell>Change %</TableCell>
                  <TableCell>Quality</TableCell>
                  <TableCell>Category</TableCell>
                  <TableCell>Timestamp</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {readings.map((reading, index) => (
                  <TableRow
                    key={`${reading.tag_name}-${index}`}
                    sx={{
                      '&:hover': { bgcolor: 'action.hover' },
                      transition: 'background-color 0.3s',
                    }}
                  >
                    <TableCell>
                      <Typography variant="body2" sx={{ fontWeight: 500 }}>
                        {reading.tag_name}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {reading.value.toFixed(2)}
                      </Typography>
                    </TableCell>
                    <TableCell>{reading.unit}</TableCell>
                    <TableCell>{getTrendIcon(reading.trend)}</TableCell>
                    <TableCell>
                      <Chip
                        label={`${reading.change_percent >= 0 ? '+' : ''}${reading.change_percent.toFixed(2)}%`}
                        size="small"
                        color={
                          reading.trend === 'up'
                            ? 'success'
                            : reading.trend === 'down'
                            ? 'error'
                            : 'default'
                        }
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={reading.quality.toUpperCase()}
                        size="small"
                        color={getQualityColor(reading.quality) as any}
                      />
                    </TableCell>
                    <TableCell>
                      <Chip label={reading.category} size="small" variant="outlined" />
                    </TableCell>
                    <TableCell>
                      <Typography variant="caption">
                        {new Date(reading.timestamp).toLocaleTimeString()}
                      </Typography>
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

export default RealTimeDataView;
