import React, { useState } from 'react';
import { Box, Paper, Typography, Slider, Button, TextField, Stack } from '@mui/material';
import { SimulatorStatus } from '../../hooks/useSimulator';

interface EquipmentControlsProps {
  status: SimulatorStatus | null;
  onSetGate: (gateId: number, value: number) => void;
  onSetAllGates: (value: number) => void;
  onSetShiploader: (value: number) => void;
  loading: boolean;
}

export default function EquipmentControls({ status, onSetGate, onSetAllGates, onSetShiploader, loading }: EquipmentControlsProps) {
  const [allGatesValue, setAllGatesValue] = useState(50);
  const [shiploaderValue, setShiploaderValue] = useState(1500);

  return (
    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
      <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 calc(50% - 12px)' } }}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>Controle de Comportas</Typography>
          <Stack spacing={2}>
            <Box>
              <Typography>Todas as Comportas: {allGatesValue}%</Typography>
              <Slider value={allGatesValue} onChange={(e, v) => setAllGatesValue(v as number)} min={0} max={100} />
              <Button variant="contained" onClick={() => onSetAllGates(allGatesValue)} disabled={loading} fullWidth>
                Aplicar a Todas
              </Button>
            </Box>
          </Stack>
        </Paper>
      </Box>

      <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 calc(50% - 12px)' } }}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>Controle do Shiploader</Typography>
          <Stack spacing={2}>
            <TextField
              label="Setpoint (t/h)"
              type="number"
              value={shiploaderValue}
              onChange={(e) => setShiploaderValue(Number(e.target.value))}
              InputProps={{ inputProps: { min: 0, max: 1500 } }}
            />
            <Button variant="contained" onClick={() => onSetShiploader(shiploaderValue)} disabled={loading} fullWidth>
              Aplicar Setpoint
            </Button>
          </Stack>
        </Paper>
      </Box>
    </Box>
  );
}
