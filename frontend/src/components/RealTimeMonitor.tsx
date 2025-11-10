/**
 * Real-time Tag Monitor Component
 * Uses WebSocket for live updates without database polling
 */
import React from 'react';
import { Box, Paper, Typography, Chip, Stack } from '@mui/material';
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
        Portões (Gates)
      </Typography>
      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 4 }}>
        <Box sx={{ flex: '1 1 calc(33.333% - 11px)', minWidth: '250px' }}>
          <TagDisplay
            label="GATE01 - Posição"
            nodeId="ns=2;i=8"
            unit="%"
            format={(v) => parseFloat(v).toFixed(1)}
          />
        </Box>
        <Box sx={{ flex: '1 1 calc(33.333% - 11px)', minWidth: '250px' }}>
          <TagDisplay
            label="GATE01 - Vazão"
            nodeId="ns=2;i=10"
            unit="t/h"
            format={(v) => parseFloat(v).toFixed(2)}
          />
        </Box>
        <Box sx={{ flex: '1 1 calc(33.333% - 11px)', minWidth: '250px' }}>
          <TagDisplay
            label="GATE02 - Posição"
            nodeId="ns=2;i=13"
            unit="%"
            format={(v) => parseFloat(v).toFixed(1)}
          />
        </Box>
        <Box sx={{ flex: '1 1 calc(33.333% - 11px)', minWidth: '250px' }}>
          <TagDisplay
            label="GATE02 - Vazão"
            nodeId="ns=2;i=15"
            unit="t/h"
            format={(v) => parseFloat(v).toFixed(2)}
          />
        </Box>
        <Box sx={{ flex: '1 1 calc(33.333% - 11px)', minWidth: '250px' }}>
          <TagDisplay
            label="GATE03 - Posição"
            nodeId="ns=2;i=18"
            unit="%"
            format={(v) => parseFloat(v).toFixed(1)}
          />
        </Box>
        <Box sx={{ flex: '1 1 calc(33.333% - 11px)', minWidth: '250px' }}>
          <TagDisplay
            label="GATE03 - Vazão"
            nodeId="ns=2;i=20"
            unit="t/h"
            format={(v) => parseFloat(v).toFixed(2)}
          />
        </Box>
      </Box>

      {/* Conveyor 1 */}
      <Typography variant="h6" gutterBottom>
        Transportador 01 (CORR01)
      </Typography>
      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 4 }}>
        <Box sx={{ flex: '1 1 calc(25% - 12px)', minWidth: '200px' }}>
          <TagDisplay
            label="Status"
            nodeId="ns=2;i=58"
            format={(v) => (v === '1' || v.toLowerCase() === 'true' ? 'LIGADO' : 'DESLIGADO')}
          />
        </Box>
        <Box sx={{ flex: '1 1 calc(25% - 12px)', minWidth: '200px' }}>
          <TagDisplay
            label="Velocidade"
            nodeId="ns=2;i=60"
            unit="m/s"
            format={(v) => parseFloat(v).toFixed(2)}
          />
        </Box>
        <Box sx={{ flex: '1 1 calc(25% - 12px)', minWidth: '200px' }}>
          <TagDisplay
            label="Vazão"
            nodeId="ns=2;i=61"
            unit="t/h"
            format={(v) => parseFloat(v).toFixed(2)}
          />
        </Box>
        <Box sx={{ flex: '1 1 calc(25% - 12px)', minWidth: '200px' }}>
          <TagDisplay
            label="Temperatura Correia"
            nodeId="ns=2;i=66"
            unit="°C"
            format={(v) => parseFloat(v).toFixed(1)}
          />
        </Box>
      </Box>

      {/* KPIs */}
      <Typography variant="h6" gutterBottom>
        KPIs do Sistema
      </Typography>
      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <Box sx={{ flex: '1 1 calc(33.333% - 11px)', minWidth: '250px' }}>
          <TagDisplay
            label="Energia Total"
            nodeId="ns=2;i=130"
            unit="kWh"
            format={(v) => parseFloat(v).toFixed(2)}
          />
        </Box>
        <Box sx={{ flex: '1 1 calc(33.333% - 11px)', minWidth: '250px' }}>
          <TagDisplay
            label="Produção Total"
            nodeId="ns=2;i=131"
            unit="t"
            format={(v) => parseFloat(v).toFixed(2)}
          />
        </Box>
        <Box sx={{ flex: '1 1 calc(33.333% - 11px)', minWidth: '250px' }}>
          <TagDisplay
            label="Eficiência Energética"
            nodeId="ns=2;i=132"
            unit="kWh/t"
            format={(v) => parseFloat(v).toFixed(3)}
          />
        </Box>
      </Box>

      {/* Debug Info */}
      <Paper sx={{ p: 2, mt: 4, bgcolor: 'grey.900' }}>
        <Typography variant="caption" color="text.secondary">
          Arquitetura: OPC UA → WebSocket → React (Tempo Real sem Banco de Dados)
        </Typography>
      </Paper>
    </Box>
  );
}
