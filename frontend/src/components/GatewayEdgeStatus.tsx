/**
 * Gateway Edge Status Component
 *
 * Displays real-time status of the Gateway Edge microservice
 * including health, compression stats, formula engine, and adapters
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  LinearProgress,
  IconButton,
  Tooltip,
  Alert,
  Skeleton,
  Paper,
  Divider,
} from '@mui/material';
import { Grid } from './GridWrapper';
import {
  Refresh as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Speed as SpeedIcon,
  Storage as StorageIcon,
  Functions as FunctionsIcon,
  Timeline as TimelineIcon,
  Memory as MemoryIcon,
} from '@mui/icons-material';
import {
  gatewayEdgeApi,
  type GatewayHealthResponse,
  type CompressionStats,
  type FormulaEngineStats,
} from '../api/gatewayEdge';

interface GatewayEdgeStatusProps {
  compact?: boolean;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export const GatewayEdgeStatus: React.FC<GatewayEdgeStatusProps> = ({
  compact = false,
  autoRefresh = true,
  refreshInterval = 5000,
}) => {
  const [health, setHealth] = useState<GatewayHealthResponse | null>(null);
  const [compression, setCompression] = useState<CompressionStats | null>(null);
  const [formulaEngine, setFormulaEngine] = useState<FormulaEngineStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const [healthData, compressionData, formulaData] = await Promise.all([
        gatewayEdgeApi.getHealth().catch(() => null),
        gatewayEdgeApi.getCompressionStats().catch(() => null),
        gatewayEdgeApi.getFormulaEngineStatus().catch(() => null),
      ]);

      if (healthData) {
        setHealth(healthData);
        setError(null);
      } else {
        setError('Gateway Edge não está respondendo');
      }

      if (compressionData) setCompression(compressionData);
      if (formulaData) setFormulaEngine(formulaData);

      setLastUpdate(new Date());
    } catch (err: any) {
      setError(err.message || 'Falha ao conectar com Gateway Edge');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();

    if (autoRefresh) {
      const interval = setInterval(fetchStatus, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [fetchStatus, autoRefresh, refreshInterval]);

  const formatUptime = (seconds: number): string => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (days > 0) return `${days}d ${hours}h ${minutes}m`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  if (loading) {
    return (
      <Card>
        <CardContent>
          <Skeleton variant="text" width="60%" height={32} />
          <Skeleton variant="rectangular" height={100} sx={{ mt: 2 }} />
        </CardContent>
      </Card>
    );
  }

  if (error && !health) {
    return (
      <Alert
        severity="error"
        action={
          <IconButton size="small" onClick={fetchStatus}>
            <RefreshIcon />
          </IconButton>
        }
      >
        {error}
      </Alert>
    );
  }

  if (compact) {
    return (
      <Paper sx={{ p: 2 }}>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box display="flex" alignItems="center" gap={1}>
            {health?.status === 'healthy' ? (
              <CheckCircleIcon color="success" />
            ) : (
              <ErrorIcon color="error" />
            )}
            <Typography variant="subtitle2">
              Gateway Edge: {health?.gateway_name || 'N/A'}
            </Typography>
          </Box>
          <Box display="flex" alignItems="center" gap={1}>
            <Chip
              size="small"
              label={`Uptime: ${health ? formatUptime(health.uptime_seconds) : 'N/A'}`}
              color="primary"
              variant="outlined"
            />
            {compression && (
              <Chip
                size="small"
                label={`Compressão: ${compression.compression_ratio_percent}%`}
                color="success"
                variant="outlined"
              />
            )}
            <Tooltip title="Atualizar">
              <IconButton size="small" onClick={fetchStatus}>
                <RefreshIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
      </Paper>
    );
  }

  return (
    <Card>
      <CardContent>
        {/* Header */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Box>
            <Typography variant="h6" component="h2">
              Gateway Edge Status
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {health?.gateway_name || 'Gateway Edge'} - {health?.gateway_id || 'N/A'}
            </Typography>
          </Box>
          <Box display="flex" alignItems="center" gap={1}>
            {health?.status === 'healthy' ? (
              <Chip
                icon={<CheckCircleIcon />}
                label="Healthy"
                color="success"
                size="small"
              />
            ) : (
              <Chip
                icon={<ErrorIcon />}
                label="Unhealthy"
                color="error"
                size="small"
              />
            )}
            <Tooltip title="Atualizar">
              <IconButton onClick={fetchStatus} size="small">
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        <Grid container spacing={2}>
          {/* Health Card */}
          <Grid item xs={12} md={6} lg={3}>
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Box display="flex" alignItems="center" gap={1} mb={1}>
                <MemoryIcon color="primary" />
                <Typography variant="subtitle2">Sistema</Typography>
              </Box>
              <Typography variant="h4" color="primary">
                {health ? formatUptime(health.uptime_seconds) : 'N/A'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Uptime
              </Typography>
              <Box mt={1}>
                <Chip
                  size="small"
                  label={`Mode: ${health?.mode || 'N/A'}`}
                  variant="outlined"
                />
                <Chip
                  size="small"
                  label={`v${health?.version || 'N/A'}`}
                  variant="outlined"
                  sx={{ ml: 0.5 }}
                />
              </Box>
            </Paper>
          </Grid>

          {/* Compression Stats Card */}
          <Grid item xs={12} md={6} lg={3}>
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Box display="flex" alignItems="center" gap={1} mb={1}>
                <StorageIcon color="secondary" />
                <Typography variant="subtitle2">Compressão SDT</Typography>
              </Box>
              <Typography variant="h4" color="secondary">
                {compression?.compression_ratio_percent?.toFixed(1) || '0'}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Taxa de compressão
              </Typography>
              <LinearProgress
                variant="determinate"
                value={compression?.compression_ratio_percent || 0}
                color="secondary"
                sx={{ mt: 1, height: 8, borderRadius: 1 }}
              />
              <Box mt={1} display="flex" justifyContent="space-between">
                <Typography variant="caption" color="text.secondary">
                  Recebidos: {compression?.total_received?.toLocaleString() || 0}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Arquivados: {compression?.total_archived?.toLocaleString() || 0}
                </Typography>
              </Box>
            </Paper>
          </Grid>

          {/* Formula Engine Card */}
          <Grid item xs={12} md={6} lg={3}>
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Box display="flex" alignItems="center" gap={1} mb={1}>
                <FunctionsIcon color="info" />
                <Typography variant="subtitle2">Formula Engine</Typography>
              </Box>
              <Typography variant="h4" color="info.main">
                {formulaEngine?.registered_formulas || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Fórmulas registradas
              </Typography>
              <Box mt={1}>
                <Typography variant="caption" color="text.secondary">
                  Avaliações: {formulaEngine?.evaluations?.toLocaleString() || 0}
                </Typography>
                <br />
                <Typography variant="caption" color="text.secondary">
                  Tempo médio: {formulaEngine?.avg_eval_time_ms?.toFixed(2) || 0}ms
                </Typography>
                {formulaEngine?.errors ? (
                  <Chip
                    size="small"
                    label={`${formulaEngine.errors} erros`}
                    color="error"
                    sx={{ ml: 1 }}
                  />
                ) : null}
              </Box>
            </Paper>
          </Grid>

          {/* Kafka Status Card */}
          <Grid item xs={12} md={6} lg={3}>
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Box display="flex" alignItems="center" gap={1} mb={1}>
                <TimelineIcon color="success" />
                <Typography variant="subtitle2">Kafka Pipeline</Typography>
              </Box>
              <Typography variant="h4" color="success.main">
                {health?.kafka_status?.messages_sent?.toLocaleString() || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Mensagens enviadas
              </Typography>
              <Box mt={1}>
                <Chip
                  size="small"
                  icon={
                    health?.kafka_status?.connected ? (
                      <CheckCircleIcon />
                    ) : (
                      <ErrorIcon />
                    )
                  }
                  label={health?.kafka_status?.connected ? 'Conectado' : 'Desconectado'}
                  color={health?.kafka_status?.connected ? 'success' : 'error'}
                />
              </Box>
            </Paper>
          </Grid>
        </Grid>

        {/* Adapters Status */}
        {health?.adapters_status && Object.keys(health.adapters_status).length > 0 && (
          <>
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle2" gutterBottom>
              Adaptadores
            </Typography>
            <Grid container spacing={1}>
              {Object.entries(health.adapters_status).map(([adapterId, status]) => (
                <Grid item key={adapterId}>
                  <Chip
                    icon={status.connected ? <CheckCircleIcon /> : <ErrorIcon />}
                    label={adapterId}
                    color={status.connected ? 'success' : 'error'}
                    variant="outlined"
                    size="small"
                  />
                </Grid>
              ))}
            </Grid>
          </>
        )}

        {/* Last Update */}
        {lastUpdate && (
          <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
            Última atualização: {lastUpdate.toLocaleTimeString()}
          </Typography>
        )}
      </CardContent>
    </Card>
  );
};

export default GatewayEdgeStatus;
