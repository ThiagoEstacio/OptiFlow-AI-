import React from 'react';
import { Box, Grid, Paper, Typography, Chip, LinearProgress, Stack } from '@mui/material';
import { SimulatorStatus } from '../../hooks/useSimulator';

interface SystemOverviewProps {
  status: SimulatorStatus | null;
}

export default function SystemOverview({ status }: SystemOverviewProps) {
  if (!status) return <Typography>Carregando...</Typography>;

  return (
    <Grid container spacing={3}>
      {/* Gates */}
      <Grid item xs={12}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>Comportas (Gates)</Typography>
          <Grid container spacing={2}>
            {status.gates.map((gate) => (
              <Grid item xs={6} md={2.4} key={gate.id}>
                <Box sx={{ p: 1, border: '1px solid #ddd', borderRadius: 1 }}>
                  <Typography variant="caption">GATE{gate.id.toString().padStart(2, '0')}</Typography>
                  <Typography variant="h6">{gate.open_pct.toFixed(0)}%</Typography>
                  <LinearProgress variant="determinate" value={gate.open_pct} />
                  <Typography variant="caption" color="text.secondary">
                    {gate.flow_tph.toFixed(0)} t/h
                  </Typography>
                  {gate.plugged && <Chip label="ENTUPIDO" color="error" size="small" />}
                </Box>
              </Grid>
            ))}
          </Grid>
        </Paper>
      </Grid>

      {/* Belts */}
      <Grid item xs={12} md={4}>
        <Paper sx={{ p: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
            <Typography variant="h6">CORR01</Typography>
            <Chip 
              label={status.belts.CORR01.running ? '● LIGADO' : '○ PARADO'} 
              color={status.belts.CORR01.running ? 'success' : 'default'} 
              size="small" 
            />
          </Box>
          <Stack spacing={1}>
            <Box><Typography variant="body2">Carga: {status.belts.CORR01.load_pct.toFixed(1)}%</Typography>
              <LinearProgress variant="determinate" value={Math.min(status.belts.CORR01.load_pct, 100)} color={status.belts.CORR01.load_pct > 80 ? 'warning' : 'primary'} />
            </Box>
            <Typography variant="body2">Fluxo: {status.belts.CORR01.flow_tph.toFixed(0)} t/h</Typography>
            <Typography variant="body2">RPM: {status.belts.CORR01.rpm.toFixed(0)}</Typography>
            <Typography variant="body2">Temp: {status.belts.CORR01.temp_bearing_C.toFixed(1)}°C</Typography>
            <Typography variant="body2">Potência: {status.belts.CORR01.power_kW.toFixed(1)} kW</Typography>
            {status.belts.CORR01.chute_plugged && <Chip label="CHUTE ENTUPIDO" color="error" size="small" />}
            {status.belts.CORR01.underspeed_alarm && <Chip label="UNDERSPEED" color="error" size="small" />}
          </Stack>
        </Paper>
      </Grid>

      <Grid item xs={12} md={4}>
        <Paper sx={{ p: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
            <Typography variant="h6">CORR02</Typography>
            <Chip 
              label={status.belts.CORR02.running ? '● LIGADO' : '○ PARADO'} 
              color={status.belts.CORR02.running ? 'success' : 'default'} 
              size="small" 
            />
          </Box>
          <Stack spacing={1}>
            <Box><Typography variant="body2">Carga: {status.belts.CORR02.load_pct.toFixed(1)}%</Typography>
              <LinearProgress variant="determinate" value={Math.min(status.belts.CORR02.load_pct, 100)} color={status.belts.CORR02.load_pct > 80 ? 'warning' : 'primary'} />
            </Box>
            <Typography variant="body2">Fluxo: {status.belts.CORR02.flow_tph.toFixed(0)} t/h</Typography>
            <Typography variant="body2">RPM: {status.belts.CORR02.rpm.toFixed(0)}</Typography>
            <Typography variant="body2">Temp: {status.belts.CORR02.temp_bearing_C.toFixed(1)}°C</Typography>
            <Typography variant="body2">Potência: {status.belts.CORR02.power_kW.toFixed(1)} kW</Typography>
            {status.belts.CORR02.chute_plugged && <Chip label="CHUTE ENTUPIDO" color="error" size="small" />}
            {status.belts.CORR02.underspeed_alarm && <Chip label="UNDERSPEED" color="error" size="small" />}
          </Stack>
        </Paper>
      </Grid>

      <Grid item xs={12} md={4}>
        <Paper sx={{ p: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
            <Typography variant="h6">CORR03</Typography>
            <Chip 
              label={status.belts.CORR03.running ? '● LIGADO' : '○ PARADO'} 
              color={status.belts.CORR03.running ? 'success' : 'default'} 
              size="small" 
            />
          </Box>
          <Stack spacing={1}>
            <Box><Typography variant="body2">Carga: {status.belts.CORR03.load_pct.toFixed(1)}%</Typography>
              <LinearProgress variant="determinate" value={Math.min(status.belts.CORR03.load_pct, 100)} color={status.belts.CORR03.load_pct > 80 ? 'warning' : 'primary'} />
            </Box>
            <Typography variant="body2">Fluxo: {status.belts.CORR03.flow_tph.toFixed(0)} t/h</Typography>
            <Typography variant="body2">RPM: {status.belts.CORR03.rpm.toFixed(0)}</Typography>
            <Typography variant="body2">Temp: {status.belts.CORR03.temp_bearing_C.toFixed(1)}°C</Typography>
            <Typography variant="body2">Potência: {status.belts.CORR03.power_kW.toFixed(1)} kW</Typography>
            {status.belts.CORR03.chute_plugged && <Chip label="CHUTE ENTUPIDO" color="error" size="small" />}
            {status.belts.CORR03.underspeed_alarm && <Chip label="UNDERSPEED" color="error" size="small" />}
          </Stack>
        </Paper>
      </Grid>

      {/* Elevator */}
      <Grid item xs={12} md={4}>
        <Paper sx={{ p: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
            <Typography variant="h6">Elevador (ELV01)</Typography>
            <Chip 
              label={status.elevator.running ? '● LIGADO' : '○ PARADO'} 
              color={status.elevator.running ? 'success' : 'default'} 
              size="small" 
            />
          </Box>
          <Stack spacing={1}>
            <Typography variant="body2">Fluxo: {status.elevator.flow_tph.toFixed(0)} t/h</Typography>
            <Typography variant="body2">Velocidade: {status.elevator.speed_mps.toFixed(2)} m/s</Typography>
            <Typography variant="body2">Temp Motor: {status.elevator.temp_motor_C.toFixed(1)}°C</Typography>
            <Typography variant="body2">Potência: {status.elevator.power_kW.toFixed(1)} kW</Typography>
            {status.elevator.slip && <Chip label="ESCORREGAMENTO" color="warning" size="small" />}
          </Stack>
        </Paper>
      </Grid>

      {/* Balance */}
      <Grid item xs={12} md={4}>
        <Paper sx={{ p: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
            <Typography variant="h6">Balança (BAL01)</Typography>
            <Chip 
              label={status.balance.running ? '● LIGADO' : '○ PARADO'} 
              color={status.balance.running ? 'success' : 'default'} 
              size="small" 
            />
          </Box>
          <Stack spacing={1}>
            <Typography variant="body2">Peso: {status.balance.weight_kg.toFixed(1)} kg</Typography>
            <Typography variant="body2">Target: {status.balance.target_kg.toFixed(0)} kg</Typography>
            <Box>
              <Typography variant="body2">Progresso Batch:</Typography>
              <LinearProgress 
                variant="determinate" 
                value={Math.min((status.balance.weight_kg / status.balance.target_kg) * 100, 100)} 
              />
            </Box>
            <Typography variant="body2">Fluxo Médio: {status.balance.avg_flow_tph.toFixed(0)} t/h</Typography>
            <Chip 
              label={status.balance.cycle_state === 'WEIGHING' ? 'PESANDO' : status.balance.cycle_state || 'AGUARDANDO'} 
              color={status.balance.cycle_state === 'WEIGHING' ? 'primary' : 'default'} 
              size="small" 
            />
          </Stack>
        </Paper>
      </Grid>

      {/* Shiploader */}
      <Grid item xs={12} md={4}>
        <Paper sx={{ p: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
            <Typography variant="h6">Shiploader (SLD01)</Typography>
            <Chip 
              label={status.shiploader.running ? '● OPERANDO' : '○ PARADO'} 
              color={status.shiploader.running ? 'success' : 'default'} 
              size="small" 
            />
          </Box>
          <Stack spacing={1}>
            <Typography variant="body2">SP: {status.shiploader.flow_sp_tph.toFixed(0)} t/h</Typography>
            <Typography variant="body2">PV: {status.shiploader.flow_pv_tph.toFixed(0)} t/h</Typography>
            <Typography variant="body2">Erro: {(status.shiploader.flow_sp_tph - status.shiploader.flow_pv_tph).toFixed(0)} t/h</Typography>
            <Typography variant="body2">Potência: {status.shiploader.power_kW.toFixed(1)} kW</Typography>
          </Stack>
        </Paper>
      </Grid>
    </Grid>
  );
}
