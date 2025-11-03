/**
 * Real-time Tag Monitor Component
 * Uses WebSocket for live updates without database polling
 */
import React from 'react';
import { Box, Paper, Typography, Chip, Grid, Stack } from '@mui/material';
import { SignalCellularAlt, WifiOff } from '@mui/icons-material';
import { useTagStream } from '../hooks/useTagStream';

interface TagDisplayProps {
  label: string;
  nodeId: string;
  unit?: string;
  format?: (value: string) => string;
}

function TagDisplay({ label, nodeId, unit, format }: TagDisplayProps) {
  const { getTagValue, isConnected } = useTagStream();
  const tagValue = getTagValue(nodeId);

  const displayValue = tagValue?.value
    ? format
      ? format(tagValue.value)
      : tagValue.value
    : '---';

  const qualityColor =
    tagValue?.quality === 'Good'
      ? 'success'
      : tagValue?.quality === 'Bad'
      ? 'error'
      : 'warning';

  return (
    <Paper sx={{ p: 2, height: '100%' }}>
      <Typography variant="caption" color="text.secondary" gutterBottom>
        {label}
      </Typography>
      <Stack direction="row" spacing={1} alignItems="baseline">
        <Typography variant="h4" component="div">
          {displayValue}
        </Typography>
        {unit && (
          <Typography variant="body2" color="text.secondary">
            {unit}
          </Typography>
        )}
      </Stack>
      {tagValue && (
        <Chip
          label={tagValue.quality}
          color={qualityColor}
          size="small"
          sx={{ mt: 1 }}
        />
      )}
    </Paper>
  );
}

export default function RealTimeMonitor() {
  const { isConnected, lastMessage, error } = useTagStream();

  return (
    <Box>
      {/* Connection Status */}
      <Paper sx={{ p: 2, mb: 3, bgcolor: isConnected ? 'success.dark' : 'error.dark' }}>
        <Stack direction="row" spacing={2} alignItems="center">
          {isConnected ? (
            <>
              <SignalCellularAlt />
              <Typography variant="h6">
                🟢 Conectado ao OPC UA (Tempo Real via WebSocket)
              </Typography>
            </>
          ) : (
            <>
              <WifiOff />
              <Typography variant="h6">🔴 Desconectado</Typography>
            </>
          )}
          {lastMessage && (
            <Typography variant="caption" sx={{ ml: 'auto' }}>
              Última atualização: {new Date(lastMessage.timestamp).toLocaleTimeString()}
            </Typography>
          )}
        </Stack>
        {error && (
          <Typography variant="body2" color="error" sx={{ mt: 1 }}>
            Erro: {error}
          </Typography>
        )}
      </Paper>

      {/* Gates */}
      <Typography variant="h6" gutterBottom>
        📍 Portões (Gates)
      </Typography>
      <Grid container spacing={2} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={4}>
          <TagDisplay
            label="GATE01 - Posição"
            nodeId="ns=2;i=8"
            unit="%"
            format={(v) => parseFloat(v).toFixed(1)}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <TagDisplay
            label="GATE01 - Vazão"
            nodeId="ns=2;i=10"
            unit="t/h"
            format={(v) => parseFloat(v).toFixed(2)}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <TagDisplay
            label="GATE02 - Posição"
            nodeId="ns=2;i=13"
            unit="%"
            format={(v) => parseFloat(v).toFixed(1)}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <TagDisplay
            label="GATE02 - Vazão"
            nodeId="ns=2;i=15"
            unit="t/h"
            format={(v) => parseFloat(v).toFixed(2)}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <TagDisplay
            label="GATE03 - Posição"
            nodeId="ns=2;i=18"
            unit="%"
            format={(v) => parseFloat(v).toFixed(1)}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <TagDisplay
            label="GATE03 - Vazão"
            nodeId="ns=2;i=20"
            unit="t/h"
            format={(v) => parseFloat(v).toFixed(2)}
          />
        </Grid>
      </Grid>

      {/* Conveyor 1 */}
      <Typography variant="h6" gutterBottom>
        🔄 Transportador 01 (CORR01)
      </Typography>
      <Grid container spacing={2} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <TagDisplay
            label="Status"
            nodeId="ns=2;i=58"
            format={(v) => (v === '1' || v.toLowerCase() === 'true' ? '▶️ LIGADO' : '⏸️ DESLIGADO')}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <TagDisplay
            label="Velocidade"
            nodeId="ns=2;i=60"
            unit="m/s"
            format={(v) => parseFloat(v).toFixed(2)}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <TagDisplay
            label="Vazão"
            nodeId="ns=2;i=61"
            unit="t/h"
            format={(v) => parseFloat(v).toFixed(2)}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <TagDisplay
            label="Temperatura Correia"
            nodeId="ns=2;i=66"
            unit="°C"
            format={(v) => parseFloat(v).toFixed(1)}
          />
        </Grid>
      </Grid>

      {/* KPIs */}
      <Typography variant="h6" gutterBottom>
        📈 KPIs do Sistema
      </Typography>
      <Grid container spacing={2}>
        <Grid item xs={12} sm={6} md={4}>
          <TagDisplay
            label="Energia Total"
            nodeId="ns=2;i=130"
            unit="kWh"
            format={(v) => parseFloat(v).toFixed(2)}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <TagDisplay
            label="Produção Total"
            nodeId="ns=2;i=131"
            unit="t"
            format={(v) => parseFloat(v).toFixed(2)}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <TagDisplay
            label="Eficiência Energética"
            nodeId="ns=2;i=132"
            unit="kWh/t"
            format={(v) => parseFloat(v).toFixed(3)}
          />
        </Grid>
      </Grid>

      {/* Debug Info */}
      <Paper sx={{ p: 2, mt: 4, bgcolor: 'grey.900' }}>
        <Typography variant="caption" color="text.secondary">
          💡 Arquitetura: OPC UA → WebSocket → React (Tempo Real sem Banco de Dados)
        </Typography>
      </Paper>
    </Box>
  );
}
