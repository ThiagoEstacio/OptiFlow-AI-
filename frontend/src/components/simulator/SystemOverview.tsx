import React from 'react';
import { Box, Paper, Typography, Chip, LinearProgress, Stack } from '@mui/material';
import { SimulatorStatus } from '../../hooks/useSimulator';

interface SystemOverviewProps {
  status: SimulatorStatus | null;
}

export default function SystemOverview({ status }: SystemOverviewProps) {
  if (!status) return <Typography>Carregando...</Typography>;

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      {/* Gates */}
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>Comportas (Gates)</Typography>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          {status.gates?.filter(gate => gate && gate.id !== undefined).map((gate) => (
            <Box key={gate.id} sx={{ flex: '1 1 calc(20% - 16px)', minWidth: 150, p: 1, border: '1px solid #ddd', borderRadius: 1 }}>
              <Typography variant="caption">GATE{gate.id.toString().padStart(2, '0')}</Typography>
              <Typography variant="h6">{gate.open_pct?.toFixed(0) ?? 0}%</Typography>
              <LinearProgress variant="determinate" value={gate.open_pct ?? 0} />
              <Typography variant="caption" color="text.secondary">
                {gate.flow_tph?.toFixed(0) ?? 0} t/h
              </Typography>
              {gate.plugged && <Chip label="ENTUPIDO" color="error" size="small" />}
            </Box>
          ))}
        </Box>
      </Paper>

      {/* Belts */}
      <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
        <Box sx={{ flex: '1 1 calc(33.33% - 16px)', minWidth: 280 }}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
              <Typography variant="h6">CORR01</Typography>
              <Chip 
                label={status.belts?.CORR01?.running ? '● LIGADO' : '○ PARADO'} 
                color={status.belts?.CORR01?.running ? 'success' : 'default'} 
                size="small" 
              />
            </Box>
            <Stack spacing={1}>
              <Box><Typography variant="body2">Carga: {status.belts?.CORR01?.load_pct?.toFixed(1) ?? 0}%</Typography>
                <LinearProgress variant="determinate" value={Math.min(status.belts?.CORR01?.load_pct ?? 0, 100)} color={(status.belts?.CORR01?.load_pct ?? 0) > 80 ? 'warning' : 'primary'} />
              </Box>
              <Typography variant="body2">Fluxo: {status.belts?.CORR01?.flow_tph?.toFixed(0) ?? 0} t/h</Typography>
              <Typography variant="body2">RPM: {status.belts?.CORR01?.rpm?.toFixed(0) ?? 0}</Typography>
              <Typography variant="body2">Temp: {status.belts?.CORR01?.temp_bearing_C?.toFixed(1) ?? 0}°C</Typography>
              <Typography variant="body2">Potência: {status.belts?.CORR01?.power_kW?.toFixed(1) ?? 0} kW</Typography>
              {status.belts?.CORR01?.chute_plugged && <Chip label="CHUTE ENTUPIDO" color="error" size="small" />}
              {status.belts?.CORR01?.underspeed_alarm && <Chip label="UNDERSPEED" color="error" size="small" />}
            </Stack>
          </Paper>
        </Box>

        <Box sx={{ flex: '1 1 calc(33.33% - 16px)', minWidth: 280 }}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
              <Typography variant="h6">CORR02</Typography>
              <Chip 
                label={status.belts?.CORR02?.running ? '● LIGADO' : '○ PARADO'} 
                color={status.belts?.CORR02?.running ? 'success' : 'default'} 
                size="small" 
              />
            </Box>
            <Stack spacing={1}>
              <Box><Typography variant="body2">Carga: {status.belts?.CORR02?.load_pct?.toFixed(1) ?? 0}%</Typography>
                <LinearProgress variant="determinate" value={Math.min(status.belts?.CORR02?.load_pct ?? 0, 100)} color={(status.belts?.CORR02?.load_pct ?? 0) > 80 ? 'warning' : 'primary'} />
              </Box>
              <Typography variant="body2">Fluxo: {status.belts?.CORR02?.flow_tph?.toFixed(0) ?? 0} t/h</Typography>
              <Typography variant="body2">RPM: {status.belts?.CORR02?.rpm?.toFixed(0) ?? 0}</Typography>
              <Typography variant="body2">Temp: {status.belts?.CORR02?.temp_bearing_C?.toFixed(1) ?? 0}°C</Typography>
              <Typography variant="body2">Potência: {status.belts?.CORR02?.power_kW?.toFixed(1) ?? 0} kW</Typography>
              {status.belts?.CORR02?.chute_plugged && <Chip label="CHUTE ENTUPIDO" color="error" size="small" />}
              {status.belts?.CORR02?.underspeed_alarm && <Chip label="UNDERSPEED" color="error" size="small" />}
            </Stack>
          </Paper>
        </Box>

        <Box sx={{ flex: '1 1 calc(33.33% - 16px)', minWidth: 280 }}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
              <Typography variant="h6">CORR03</Typography>
              <Chip 
                label={status.belts?.CORR03?.running ? '● LIGADO' : '○ PARADO'} 
                color={status.belts?.CORR03?.running ? 'success' : 'default'} 
                size="small" 
              />
            </Box>
            <Stack spacing={1}>
              <Box><Typography variant="body2">Carga: {status.belts?.CORR03?.load_pct?.toFixed(1) ?? 0}%</Typography>
                <LinearProgress variant="determinate" value={Math.min(status.belts?.CORR03?.load_pct ?? 0, 100)} color={(status.belts?.CORR03?.load_pct ?? 0) > 80 ? 'warning' : 'primary'} />
              </Box>
              <Typography variant="body2">Fluxo: {status.belts?.CORR03?.flow_tph?.toFixed(0) ?? 0} t/h</Typography>
              <Typography variant="body2">RPM: {status.belts?.CORR03?.rpm?.toFixed(0) ?? 0}</Typography>
              <Typography variant="body2">Temp: {status.belts?.CORR03?.temp_bearing_C?.toFixed(1) ?? 0}°C</Typography>
              <Typography variant="body2">Potência: {status.belts?.CORR03?.power_kW?.toFixed(1) ?? 0} kW</Typography>
              {status.belts?.CORR03?.chute_plugged && <Chip label="CHUTE ENTUPIDO" color="error" size="small" />}
              {status.belts?.CORR03?.underspeed_alarm && <Chip label="UNDERSPEED" color="error" size="small" />}
            </Stack>
          </Paper>
        </Box>
      </Box>

      {/* Elevator, Balance, Shiploader */}
      <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
        <Box sx={{ flex: '1 1 calc(33.33% - 16px)', minWidth: 280 }}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
              <Typography variant="h6">Elevador (ELV01)</Typography>
              <Chip 
                label={status.elevator?.running ? '● LIGADO' : '○ PARADO'} 
                color={status.elevator?.running ? 'success' : 'default'} 
                size="small" 
              />
            </Box>
            <Stack spacing={1}>
              <Typography variant="body2">Fluxo: {status.elevator?.flow_tph?.toFixed(0) ?? 0} t/h</Typography>
              <Typography variant="body2">Velocidade: {status.elevator?.speed_mps?.toFixed(2) ?? 0} m/s</Typography>
              <Typography variant="body2">Temp Motor: {status.elevator?.temp_motor_C?.toFixed(1) ?? 0}°C</Typography>
              <Typography variant="body2">Potência: {status.elevator?.power_kW?.toFixed(1) ?? 0} kW</Typography>
              {status.elevator?.slip && <Chip label="ESCORREGAMENTO" color="warning" size="small" />}
            </Stack>
          </Paper>
        </Box>

        <Box sx={{ flex: '1 1 calc(33.33% - 16px)', minWidth: 280 }}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
              <Typography variant="h6">Balança (BAL01)</Typography>
              <Chip 
                label={status.balance?.running ? '● LIGADO' : '○ PARADO'} 
                color={status.balance?.running ? 'success' : 'default'} 
                size="small" 
              />
            </Box>
            <Stack spacing={1}>
              <Typography variant="body2">Peso: {status.balance?.weight_kg?.toFixed(1) ?? 0} kg</Typography>
              <Typography variant="body2">Target: {status.balance?.target_kg?.toFixed(0) ?? 0} kg</Typography>
              <Box>
                <Typography variant="body2">Progresso Batch:</Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={Math.min(((status.balance?.weight_kg ?? 0) / (status.balance?.target_kg || 1)) * 100, 100)} 
                />
              </Box>
              <Typography variant="body2">Fluxo Médio: {status.balance?.avg_flow_tph?.toFixed(0) ?? 0} t/h</Typography>
              <Chip 
                label={status.balance?.cycle_state === 'WEIGHING' ? 'PESANDO' : status.balance?.cycle_state || 'AGUARDANDO'} 
                color={status.balance?.cycle_state === 'WEIGHING' ? 'primary' : 'default'} 
                size="small" 
              />
            </Stack>
          </Paper>
        </Box>

        <Box sx={{ flex: '1 1 calc(33.33% - 16px)', minWidth: 280 }}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
              <Typography variant="h6">Shiploader (SLD01)</Typography>
              <Chip 
                label={status.shiploader?.running ? '● OPERANDO' : '○ PARADO'} 
                color={status.shiploader?.running ? 'success' : 'default'} 
                size="small" 
              />
            </Box>
            <Stack spacing={1}>
              <Typography variant="body2">SP: {status.shiploader?.flow_sp_tph?.toFixed(0) ?? 0} t/h</Typography>
              <Typography variant="body2">PV: {status.shiploader?.flow_pv_tph?.toFixed(0) ?? 0} t/h</Typography>
              <Typography variant="body2">Erro: {((status.shiploader?.flow_sp_tph ?? 0) - (status.shiploader?.flow_pv_tph ?? 0)).toFixed(0)} t/h</Typography>
              <Typography variant="body2">Potência: {status.shiploader?.power_kW?.toFixed(1) ?? 0} kW</Typography>
            </Stack>
          </Paper>
        </Box>
      </Box>
    </Box>
  );
}
