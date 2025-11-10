import React from 'react';
import { Box, Paper, Typography } from '@mui/material';
import { SimulatorStatus } from '../../hooks/useSimulator';

interface TrendsPanelProps {
  status: SimulatorStatus | null;
}

export default function TrendsPanel({ status }: TrendsPanelProps) {
  if (!status) return <Typography>Carregando...</Typography>;

  // TODO: Implement real-time trends with charts library (recharts, chart.js, etc)
  return (
    <Box>
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Gráficos de Tendências
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Recurso em desenvolvimento - será implementado com biblioteca de gráficos em tempo real
        </Typography>
        <Box sx={{ mt: 2, p: 4, bgcolor: '#f5f5f5', borderRadius: 1 }}>
          <Typography variant="body2" align="center">
            📈 Área reservada para gráficos de tendência:
          </Typography>
          <ul>
            <li>Fluxo vs Tempo</li>
            <li>Temperatura vs Tempo</li>
            <li>Potência vs Tempo</li>
            <li>Carga das correias vs Tempo</li>
          </ul>
        </Box>
      </Paper>
    </Box>
  );
}
