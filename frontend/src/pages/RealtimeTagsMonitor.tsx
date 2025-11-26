/**
 * Real-Time Tags Monitor Page - Professional Enterprise Design
 *
 * Shows MANAGED tags (user-saved tags) from the Gateway Edge
 * These are tags configured via Gateway UI and stored in tags_config.json
 *
 * Data Source: Gateway Edge API (http://localhost:8080)
 * - Managed Tags: GET /api/tags/managed
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  Stack,
  Button,
  IconButton,
  Chip,
  TextField,
  InputAdornment,
  ToggleButton,
  ToggleButtonGroup,
  Alert,
  Tooltip,
  Skeleton,
  alpha,
  useTheme,
  Zoom,
  Divider
} from '@mui/material';
import { Grid } from '../components/GridWrapper';
import {
  Memory,
  Refresh,
  Search,
  FilterList,
  ViewModule,
  ViewList,
  Wifi,
  WifiOff,
  CheckCircle,
  Cancel,
  TrendingUp,
  ShowChart,
  Speed,
  Timer,
  OpenInNew,
  Hub,
  PlayArrow,
  Pause
} from '@mui/icons-material';
import { StatWidget } from '../components/professional/StatWidget';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

// Gateway Edge API base URL
const GATEWAY_URL = import.meta.env.VITE_GATEWAY_URL || 'http://localhost:8080';

interface ManagedTag {
  tag_id: string;
  tag_name: string;
  address: string;
  adapter_id: string;
  data_type: string;
  enabled: boolean;
  current_value?: number | string | boolean;
  current_quality?: string;
  current_timestamp?: string;
  connected?: boolean;
  metadata?: {
    description?: string;
    engineering_units?: string;
  };
  alarm?: {
    enabled?: boolean;
    hi?: number;
    hi_hi?: number;
    lo?: number;
    lo_lo?: number;
  };
}

interface ManagedTagsResponse {
  count: number;
  source: string;
  tags: ManagedTag[];
  note: string;
}

export const RealtimeTagsMonitor: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();

  // Data states
  const [tags, setTags] = useState<ManagedTag[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [gatewayConnected, setGatewayConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  // UI states
  const [searchTerm, setSearchTerm] = useState('');
  const [filterAdapter, setFilterAdapter] = useState<string>('ALL');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Load managed tags from Gateway
  const fetchManagedTags = useCallback(async () => {
    try {
      const response = await axios.get<ManagedTagsResponse>(`${GATEWAY_URL}/api/tags/managed`);
      const managedTags = response.data.tags.filter((tag: ManagedTag) => tag.enabled);
      setTags(managedTags);
      setGatewayConnected(true);
      setError(null);
      setLastUpdate(new Date());
    } catch (err: any) {
      console.error('Error fetching managed tags from Gateway:', err);
      setError(err.response?.data?.detail || 'Failed to connect to Gateway Edge. Is it running on port 8080?');
      setGatewayConnected(false);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchManagedTags();

    let intervalId: NodeJS.Timeout | null = null;
    if (autoRefresh) {
      intervalId = setInterval(fetchManagedTags, 3000);
    }
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [fetchManagedTags, autoRefresh]);

  // Get unique adapters for filter
  const adapters = ['ALL', ...new Set(tags.map(t => t.adapter_id))];

  // Filter tags
  const filteredTags = tags.filter(tag => {
    const matchesSearch =
      tag.tag_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      tag.tag_id.toLowerCase().includes(searchTerm.toLowerCase());

    if (filterAdapter === 'ALL') return matchesSearch;
    return matchesSearch && tag.adapter_id === filterAdapter;
  });

  // Format value for display
  const formatValue = (value: any, dataType: string): string => {
    if (value === null || value === undefined) return '--';
    if (typeof value === 'boolean') return value ? 'TRUE' : 'FALSE';
    if (typeof value === 'number') {
      return dataType === 'int16' || dataType === 'int32' || dataType === 'uint16'
        ? value.toFixed(0)
        : value.toFixed(2);
    }
    return String(value);
  };

  // Get quality color
  const getQualityColor = (quality?: string): 'success' | 'warning' | 'error' | 'default' => {
    if (!quality) return 'default';
    const q = quality.toLowerCase();
    if (q === 'good') return 'success';
    if (q === 'uncertain') return 'warning';
    return 'error';
  };

  // Check if value is in alarm
  const checkAlarmStatus = (tag: ManagedTag): { status: 'normal' | 'hi' | 'hi_hi' | 'lo' | 'lo_lo'; color: string } => {
    if (!tag.alarm?.enabled || typeof tag.current_value !== 'number') {
      return { status: 'normal', color: theme.palette.success.main };
    }

    const value = tag.current_value;
    if (tag.alarm.hi_hi !== undefined && value >= tag.alarm.hi_hi) {
      return { status: 'hi_hi', color: theme.palette.error.main };
    }
    if (tag.alarm.hi !== undefined && value >= tag.alarm.hi) {
      return { status: 'hi', color: theme.palette.warning.main };
    }
    if (tag.alarm.lo_lo !== undefined && value <= tag.alarm.lo_lo) {
      return { status: 'lo_lo', color: theme.palette.error.main };
    }
    if (tag.alarm.lo !== undefined && value <= tag.alarm.lo) {
      return { status: 'lo', color: theme.palette.warning.main };
    }
    return { status: 'normal', color: theme.palette.success.main };
  };

  // Stats
  const goodQualityTags = tags.filter(t => t.current_quality?.toLowerCase() === 'good').length;
  const tagsWithAlarms = tags.filter(t => checkAlarmStatus(t).status !== 'normal').length;

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <Skeleton variant="rectangular" height={180} sx={{ borderRadius: 2, mb: 3 }} />
        <Grid container spacing={3}>
          {[1, 2, 3, 4].map(i => (
            <Grid item xs={12} sm={6} md={3} key={i}>
              <Skeleton variant="rectangular" height={160} sx={{ borderRadius: 2 }} />
            </Grid>
          ))}
        </Grid>
      </Box>
    );
  }

  return (
    <Box sx={{ bgcolor: 'background.default', minHeight: '100vh', pb: 4 }}>
      {/* Header */}
      <Paper
        elevation={0}
        sx={{
          background: `linear-gradient(135deg, ${theme.palette.success.main} 0%, ${theme.palette.success.dark} 100%)`,
          color: 'white',
          borderRadius: 0,
          mb: 3
        }}
      >
        <Container maxWidth="xl">
          <Box sx={{ py: 4 }}>
            <Stack direction="row" justifyContent="space-between" alignItems="center">
              <Box>
                <Typography variant="h4" fontWeight={700} gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Memory sx={{ fontSize: 40 }} />
                  Real-Time Tags Monitor
                </Typography>
                <Typography variant="body1" sx={{ opacity: 0.9 }}>
                  Monitoring {tags.length} managed tags from Gateway Edge
                </Typography>
              </Box>

              <Stack direction="row" spacing={2} alignItems="center">
                <Tooltip title={autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}>
                  <IconButton
                    sx={{ color: 'white' }}
                    onClick={() => setAutoRefresh(!autoRefresh)}
                  >
                    {autoRefresh ? <PlayArrow /> : <Pause />}
                  </IconButton>
                </Tooltip>

                <Chip
                  icon={gatewayConnected ? <Wifi /> : <WifiOff />}
                  label={gatewayConnected ? 'Gateway Connected' : 'Gateway Offline'}
                  sx={{
                    bgcolor: gatewayConnected ? 'rgba(255, 255, 255, 0.2)' : 'rgba(244, 67, 54, 0.3)',
                    color: 'white',
                    fontWeight: 600
                  }}
                />

                <IconButton sx={{ color: 'white' }} onClick={fetchManagedTags}>
                  <Refresh />
                </IconButton>
              </Stack>
            </Stack>

            {/* Quick Stats */}
            <Stack direction="row" spacing={3} mt={3} flexWrap="wrap">
              <Chip
                icon={<Hub />}
                label={GATEWAY_URL}
                sx={{ bgcolor: 'rgba(255, 255, 255, 0.1)', color: 'white' }}
              />
              {lastUpdate && (
                <Chip
                  icon={<Timer />}
                  label={`Updated: ${lastUpdate.toLocaleTimeString()}`}
                  sx={{ bgcolor: 'rgba(255, 255, 255, 0.1)', color: 'white' }}
                />
              )}
            </Stack>
          </Box>
        </Container>
      </Paper>

      <Container maxWidth="xl">
        {/* Error Alert */}
        {error && (
          <Alert
            severity="error"
            sx={{ mb: 3 }}
            action={
              <Button
                color="inherit"
                size="small"
                href={`${GATEWAY_URL}/ui/tags.html`}
                target="_blank"
                startIcon={<OpenInNew />}
              >
                Open Gateway UI
              </Button>
            }
          >
            {error}
          </Alert>
        )}

        {/* Stats Cards */}
        <Grid container spacing={3} mb={3}>
          <Grid item xs={12} sm={6} md={3}>
            <StatWidget
              title="Total Tags"
              value={tags.length}
              icon={<Memory />}
              color="primary"
              gradient
              subtitle="Managed tags"
              footer="From tags_config.json"
              animate
            />
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <StatWidget
              title="Good Quality"
              value={goodQualityTags}
              icon={<CheckCircle />}
              color="success"
              gradient
              subtitle={`${tags.length > 0 ? ((goodQualityTags / tags.length) * 100).toFixed(0) : 0}% healthy`}
              footer="Tags with good quality"
              animate
            />
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <StatWidget
              title="Active Alarms"
              value={tagsWithAlarms}
              icon={tagsWithAlarms > 0 ? <TrendingUp /> : <Speed />}
              color={tagsWithAlarms > 0 ? 'error' : 'info'}
              gradient
              subtitle={tagsWithAlarms > 0 ? 'Needs attention' : 'All normal'}
              footer="Tags in alarm state"
              animate={tagsWithAlarms > 0}
            />
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <StatWidget
              title="Adapters"
              value={adapters.length - 1}
              icon={<Hub />}
              color="warning"
              gradient
              subtitle="Protocol adapters"
              footer="OPC-UA, Modbus"
            />
          </Grid>
        </Grid>

        {/* No Tags Alert */}
        {tags.length === 0 && !error && (
          <Paper sx={{ p: 4, textAlign: 'center', mb: 3 }}>
            <Memory sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              No managed tags found
            </Typography>
            <Typography variant="body2" color="text.secondary" mb={3}>
              Tags need to be saved via Gateway UI first. Use the Gateway Point Builder to configure tags for archiving.
            </Typography>
            <Stack direction="row" spacing={2} justifyContent="center">
              <Button
                variant="contained"
                href={`${GATEWAY_URL}/ui/tags.html`}
                target="_blank"
                startIcon={<OpenInNew />}
              >
                Open Gateway UI
              </Button>
              <Button
                variant="outlined"
                onClick={() => navigate('/gateway-edge')}
              >
                Gateway Edge Management
              </Button>
            </Stack>
          </Paper>
        )}

        {/* Filters */}
        {tags.length > 0 && (
          <Paper sx={{ p: 2, mb: 3, borderRadius: 2 }}>
            <Stack
              direction={{ xs: 'column', md: 'row' }}
              spacing={2}
              alignItems={{ xs: 'stretch', md: 'center' }}
              justifyContent="space-between"
            >
              {/* Search */}
              <TextField
                size="small"
                placeholder="Search tags..."
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Search />
                    </InputAdornment>
                  )
                }}
                sx={{ minWidth: 280 }}
              />

              {/* Adapter Filter */}
              <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                <FilterList color="action" />
                {adapters.map(adapter => (
                  <Chip
                    key={adapter}
                    label={adapter === 'ALL' ? 'All Adapters' : adapter}
                    color={filterAdapter === adapter ? 'primary' : 'default'}
                    variant={filterAdapter === adapter ? 'filled' : 'outlined'}
                    onClick={() => setFilterAdapter(adapter)}
                    sx={{ cursor: 'pointer' }}
                  />
                ))}
              </Stack>

              {/* View Mode */}
              <ToggleButtonGroup
                value={viewMode}
                exclusive
                onChange={(_, v) => v && setViewMode(v)}
                size="small"
              >
                <ToggleButton value="grid">
                  <ViewModule />
                </ToggleButton>
                <ToggleButton value="list">
                  <ViewList />
                </ToggleButton>
              </ToggleButtonGroup>
            </Stack>
          </Paper>
        )}

        {/* Tags Grid/List */}
        {viewMode === 'grid' ? (
          <Grid container spacing={3}>
            {filteredTags.map(tag => {
              const alarmStatus = checkAlarmStatus(tag);
              return (
                <Grid item xs={12} sm={6} md={4} lg={3} key={tag.tag_id}>
                  <Zoom in={true} style={{ transitionDelay: '50ms' }}>
                    <Paper
                      sx={{
                        p: 3,
                        borderRadius: 2,
                        height: '100%',
                        position: 'relative',
                        overflow: 'hidden',
                        borderTop: `4px solid ${alarmStatus.color}`,
                        transition: 'all 0.3s ease',
                        '&:hover': {
                          boxShadow: theme.shadows[8],
                          transform: 'translateY(-4px)'
                        }
                      }}
                    >
                      {/* Header */}
                      <Stack direction="row" justifyContent="space-between" alignItems="flex-start" mb={2}>
                        <Box sx={{ flex: 1, overflow: 'hidden' }}>
                          <Typography
                            variant="subtitle2"
                            fontWeight={600}
                            noWrap
                            title={tag.tag_name}
                          >
                            {tag.tag_name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary" fontFamily="monospace" noWrap>
                            {tag.tag_id}
                          </Typography>
                        </Box>
                        <Chip
                          icon={tag.current_quality?.toLowerCase() === 'good' ? <CheckCircle /> : <Cancel />}
                          label={tag.current_quality?.toUpperCase() || 'N/A'}
                          color={getQualityColor(tag.current_quality)}
                          size="small"
                        />
                      </Stack>

                      {/* Value */}
                      <Box sx={{ textAlign: 'center', py: 3 }}>
                        {tag.current_value !== undefined && tag.current_value !== null ? (
                          <>
                            <Typography
                              variant="h3"
                              fontWeight={700}
                              sx={{
                                color: alarmStatus.status !== 'normal' ? alarmStatus.color : 'text.primary'
                              }}
                            >
                              {formatValue(tag.current_value, tag.data_type)}
                            </Typography>
                            {tag.metadata?.engineering_units && (
                              <Typography variant="body2" color="text.secondary">
                                {tag.metadata.engineering_units}
                              </Typography>
                            )}
                          </>
                        ) : (
                          <Box sx={{ py: 2 }}>
                            <Typography variant="h4" color="text.disabled">
                              --
                            </Typography>
                            <Typography variant="caption" color="text.disabled">
                              Waiting for data...
                            </Typography>
                          </Box>
                        )}
                      </Box>

                      {/* Footer */}
                      <Divider sx={{ my: 2 }} />
                      <Stack spacing={1}>
                        <Box display="flex" justifyContent="space-between">
                          <Typography variant="caption" color="text.secondary">Adapter:</Typography>
                          <Chip label={tag.adapter_id} size="small" variant="outlined" sx={{ height: 20, fontSize: '0.7rem' }} />
                        </Box>
                        <Box display="flex" justifyContent="space-between">
                          <Typography variant="caption" color="text.secondary">Type:</Typography>
                          <Typography variant="caption" fontFamily="monospace">{tag.data_type}</Typography>
                        </Box>
                        {tag.current_timestamp && (
                          <Box display="flex" justifyContent="space-between">
                            <Typography variant="caption" color="text.secondary">Updated:</Typography>
                            <Typography variant="caption" fontFamily="monospace">
                              {new Date(tag.current_timestamp).toLocaleTimeString()}
                            </Typography>
                          </Box>
                        )}
                      </Stack>

                      {/* Alarm Badge */}
                      {alarmStatus.status !== 'normal' && (
                        <Chip
                          label={alarmStatus.status.toUpperCase().replace('_', ' ')}
                          size="small"
                          sx={{
                            position: 'absolute',
                            top: 12,
                            right: 12,
                            bgcolor: alarmStatus.color,
                            color: 'white',
                            fontWeight: 700,
                            animation: 'pulse 1.5s infinite'
                          }}
                        />
                      )}
                    </Paper>
                  </Zoom>
                </Grid>
              );
            })}
          </Grid>
        ) : (
          // List View
          <Paper sx={{ borderRadius: 2, overflow: 'hidden' }}>
            {filteredTags.map((tag, idx) => {
              const alarmStatus = checkAlarmStatus(tag);
              return (
                <Box
                  key={tag.tag_id}
                  sx={{
                    p: 2,
                    borderBottom: idx < filteredTags.length - 1 ? 1 : 0,
                    borderColor: 'divider',
                    borderLeft: `4px solid ${alarmStatus.color}`,
                    '&:hover': {
                      bgcolor: alpha(theme.palette.primary.main, 0.03)
                    }
                  }}
                >
                  <Grid container spacing={2} alignItems="center">
                    <Grid item xs={12} sm={3}>
                      <Typography variant="subtitle2" fontWeight={600}>{tag.tag_name}</Typography>
                      <Typography variant="caption" color="text.secondary" fontFamily="monospace">
                        {tag.tag_id}
                      </Typography>
                    </Grid>
                    <Grid item xs={6} sm={2}>
                      <Typography
                        variant="h5"
                        fontWeight={700}
                        sx={{ color: alarmStatus.status !== 'normal' ? alarmStatus.color : 'text.primary' }}
                      >
                        {formatValue(tag.current_value, tag.data_type)}
                      </Typography>
                      {tag.metadata?.engineering_units && (
                        <Typography variant="caption" color="text.secondary">
                          {tag.metadata.engineering_units}
                        </Typography>
                      )}
                    </Grid>
                    <Grid item xs={6} sm={2}>
                      <Chip
                        label={tag.current_quality?.toUpperCase() || 'N/A'}
                        color={getQualityColor(tag.current_quality)}
                        size="small"
                      />
                    </Grid>
                    <Grid item xs={6} sm={2}>
                      <Typography variant="body2" color="text.secondary">{tag.adapter_id}</Typography>
                    </Grid>
                    <Grid item xs={6} sm={2}>
                      <Typography variant="body2" color="text.secondary">{tag.data_type}</Typography>
                    </Grid>
                    <Grid item xs={12} sm={1} sx={{ textAlign: 'right' }}>
                      <Tooltip title="View in Trends">
                        <IconButton
                          size="small"
                          onClick={() => navigate(`/realtime/trends?tag=${tag.tag_id}`)}
                        >
                          <ShowChart />
                        </IconButton>
                      </Tooltip>
                    </Grid>
                  </Grid>
                </Box>
              );
            })}
          </Paper>
        )}

        {/* Empty Filter Result */}
        {filteredTags.length === 0 && tags.length > 0 && (
          <Paper sx={{ p: 4, textAlign: 'center' }}>
            <Search sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
            <Typography variant="h6" color="text.secondary">
              No tags found matching your search
            </Typography>
            <Button variant="text" onClick={() => { setSearchTerm(''); setFilterAdapter('ALL'); }}>
              Clear filters
            </Button>
          </Paper>
        )}

        {/* Link to Gateway UI */}
        {tags.length > 0 && (
          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Button
              href={`${GATEWAY_URL}/ui/tags.html`}
              target="_blank"
              startIcon={<OpenInNew />}
              color="primary"
            >
              Open Gateway UI to manage more tags
            </Button>
          </Box>
        )}
      </Container>

      {/* Pulse animation for alarms */}
      <style>{`
        @keyframes pulse {
          0% { opacity: 1; }
          50% { opacity: 0.6; }
          100% { opacity: 1; }
        }
      `}</style>
    </Box>
  );
};

export default RealtimeTagsMonitor;
