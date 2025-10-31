import React from 'react';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Chip,
  Grid,
  Paper,
  Stack,
  Typography,
  Alert,
  Divider,
  LinearProgress,
} from '@mui/material';
import {
  Bolt,
  Speed,
  TrendingUp,
  AttachMoney,
  ElectricBolt,
  PowerSettingsNew,
} from '@mui/icons-material';

interface EnergyData {
  total_power_kW: number;
  avg_power_factor: number;
  total_kWh: number;
  cost_peak_BRL: number;
  cost_offpeak_BRL: number;
  cost_total_BRL: number;
  equipment: {
    [key: string]: {
      voltage_V: number;
      current_A: number;
      power_kW: number;
      reactive_kvar: number;
      apparent_kVA: number;
      power_factor: number;
      kwh: number;
    };
  };
}

interface EnergyDashboardProps {
  energy?: EnergyData;
}

const getPowerFactorColor = (pf: number): 'success' | 'warning' | 'error' => {
  if (pf >= 0.92) return 'success';
  if (pf >= 0.85) return 'warning';
  return 'error';
};

const getPowerFactorStatus = (pf: number): string => {
  if (pf >= 0.92) return 'Excelente';
  if (pf >= 0.85) return 'Adequado';
  return 'Baixo';
};

const formatEquipmentName = (key: string): string => {
  const names: { [key: string]: string } = {
    'CORR01': 'Correia 01',
    'CORR02': 'Correia 02',
    'CORR03': 'Correia 03',
    'ELV01': 'Elevador 01',
    'BAL01': 'Balança 01',
    'SLD01': 'Shiploader',
  };
  return names[key] || key;
};

export default function EnergyDashboard({ energy }: EnergyDashboardProps) {
  if (!energy) {
    return (
      <Alert severity="info">
        Dados de energia não disponíveis. Aguarde conexão com simulador.
      </Alert>
    );
  }

  const equipmentList = Object.entries(energy.equipment || {});

  return (
    <Box>
      {/* Summary Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={2}>
                <Box
                  sx={{
                    width: 60,
                    height: 60,
                    borderRadius: 2,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    bgcolor: 'error.light',
                  }}
                >
                  <Bolt sx={{ fontSize: 32, color: 'error.dark' }} />
                </Box>
                <Box>
                  <Typography variant="h4" fontWeight="bold">
                    {energy.total_power_kW.toFixed(1)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Potência Total (kW)
                  </Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={2}>
                <Box
                  sx={{
                    width: 60,
                    height: 60,
                    borderRadius: 2,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    bgcolor: getPowerFactorColor(energy.avg_power_factor) + '.light',
                  }}
                >
                  <Speed sx={{ fontSize: 32, color: getPowerFactorColor(energy.avg_power_factor) + '.dark' }} />
                </Box>
                <Box>
                  <Typography variant="h4" fontWeight="bold">
                    {energy.avg_power_factor.toFixed(3)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Fator de Potência
                  </Typography>
                  <Chip
                    label={getPowerFactorStatus(energy.avg_power_factor)}
                    color={getPowerFactorColor(energy.avg_power_factor)}
                    size="small"
                    sx={{ mt: 0.5 }}
                  />
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={2}>
                <Box
                  sx={{
                    width: 60,
                    height: 60,
                    borderRadius: 2,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    bgcolor: 'info.light',
                  }}
                >
                  <TrendingUp sx={{ fontSize: 32, color: 'info.dark' }} />
                </Box>
                <Box>
                  <Typography variant="h4" fontWeight="bold">
                    {energy.total_kWh.toFixed(1)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Energia Total (kWh)
                  </Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={2}>
                <Box
                  sx={{
                    width: 60,
                    height: 60,
                    borderRadius: 2,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    bgcolor: 'success.light',
                  }}
                >
                  <AttachMoney sx={{ fontSize: 32, color: 'success.dark' }} />
                </Box>
                <Box>
                  <Typography variant="h4" fontWeight="bold">
                    {energy.cost_total_BRL.toFixed(2)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Custo Total (R$)
                  </Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Cost Breakdown */}
      <Card sx={{ mb: 3 }}>
        <CardHeader title="Detalhamento de Custos" />
        <CardContent>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 2, bgcolor: 'warning.lighter' }}>
                <Stack spacing={1}>
                  <Stack direction="row" justifyContent="space-between" alignItems="center">
                    <Typography variant="body2" color="text.secondary">
                      Horário de Pico
                    </Typography>
                    <Chip label="Pico" color="warning" size="small" />
                  </Stack>
                  <Typography variant="h5" fontWeight="bold">
                    R$ {energy.cost_peak_BRL.toFixed(2)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Tarifa mais alta (17h-22h)
                  </Typography>
                </Stack>
              </Paper>
            </Grid>

            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 2, bgcolor: 'success.lighter' }}>
                <Stack spacing={1}>
                  <Stack direction="row" justifyContent="space-between" alignItems="center">
                    <Typography variant="body2" color="text.secondary">
                      Horário Fora de Pico
                    </Typography>
                    <Chip label="Fora Pico" color="success" size="small" />
                  </Stack>
                  <Typography variant="h5" fontWeight="bold">
                    R$ {energy.cost_offpeak_BRL.toFixed(2)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Tarifa reduzida (demais horários)
                  </Typography>
                </Stack>
              </Paper>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Equipment Electrical Measurements */}
      <Grid container spacing={2}>
        {equipmentList.map(([equipId, data]) => (
          <Grid item xs={12} md={6} key={equipId}>
            <Card>
              <CardHeader
                title={
                  <Stack direction="row" spacing={1} alignItems="center">
                    <ElectricBolt color="primary" />
                    <Typography variant="h6">{formatEquipmentName(equipId)}</Typography>
                    <Chip
                      label={`FP: ${data.power_factor.toFixed(3)}`}
                      color={getPowerFactorColor(data.power_factor)}
                      size="small"
                    />
                  </Stack>
                }
                subheader={`ID: ${equipId}`}
              />
              <CardContent>
                <Stack spacing={2}>
                  {/* Power Bar */}
                  <Box>
                    <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 0.5 }}>
                      <Typography variant="body2" color="text.secondary">
                        Potência Ativa (kW)
                      </Typography>
                      <Typography variant="body2" fontWeight="bold">
                        {data.power_kW.toFixed(2)} kW
                      </Typography>
                    </Stack>
                    <LinearProgress
                      variant="determinate"
                      value={Math.min((data.power_kW / 100) * 100, 100)}
                      color="error"
                      sx={{ height: 8, borderRadius: 1 }}
                    />
                  </Box>

                  <Divider />

                  {/* Electrical Measurements Grid */}
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Paper sx={{ p: 1.5, bgcolor: 'background.default' }}>
                        <Stack>
                          <Typography variant="caption" color="text.secondary">
                            Tensão (V)
                          </Typography>
                          <Typography variant="h6" fontWeight="bold">
                            {data.voltage_V.toFixed(0)} V
                          </Typography>
                        </Stack>
                      </Paper>
                    </Grid>

                    <Grid item xs={6}>
                      <Paper sx={{ p: 1.5, bgcolor: 'background.default' }}>
                        <Stack>
                          <Typography variant="caption" color="text.secondary">
                            Corrente (A)
                          </Typography>
                          <Typography variant="h6" fontWeight="bold">
                            {data.current_A.toFixed(1)} A
                          </Typography>
                        </Stack>
                      </Paper>
                    </Grid>

                    <Grid item xs={6}>
                      <Paper sx={{ p: 1.5, bgcolor: 'background.default' }}>
                        <Stack>
                          <Typography variant="caption" color="text.secondary">
                            Potência Reativa (kvar)
                          </Typography>
                          <Typography variant="h6" fontWeight="bold">
                            {data.reactive_kvar.toFixed(2)} kvar
                          </Typography>
                        </Stack>
                      </Paper>
                    </Grid>

                    <Grid item xs={6}>
                      <Paper sx={{ p: 1.5, bgcolor: 'background.default' }}>
                        <Stack>
                          <Typography variant="caption" color="text.secondary">
                            Potência Aparente (kVA)
                          </Typography>
                          <Typography variant="h6" fontWeight="bold">
                            {data.apparent_kVA.toFixed(2)} kVA
                          </Typography>
                        </Stack>
                      </Paper>
                    </Grid>

                    <Grid item xs={12}>
                      <Paper sx={{ p: 1.5, bgcolor: 'info.lighter' }}>
                        <Stack direction="row" justifyContent="space-between" alignItems="center">
                          <Typography variant="body2" color="text.secondary">
                            Energia Acumulada
                          </Typography>
                          <Typography variant="h6" fontWeight="bold" color="primary">
                            {data.kwh.toFixed(2)} kWh
                          </Typography>
                        </Stack>
                      </Paper>
                    </Grid>
                  </Grid>

                  {/* Power Factor Warning */}
                  {data.power_factor < 0.92 && (
                    <Alert
                      severity={data.power_factor < 0.85 ? 'error' : 'warning'}
                      variant="outlined"
                      icon={<PowerSettingsNew />}
                    >
                      {data.power_factor < 0.85 ? (
                        <Typography variant="body2">
                          ⚠️ <strong>Fator de Potência Baixo:</strong> Risco de multa. Instale banco de capacitores.
                        </Typography>
                      ) : (
                        <Typography variant="body2">
                          ⚡ <strong>FP Adequado mas Melhorável:</strong> Considere otimização.
                        </Typography>
                      )}
                    </Alert>
                  )}
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Legend */}
      <Box sx={{ mt: 3 }}>
        <Typography variant="caption" color="text.secondary" gutterBottom display="block">
          <strong>Fator de Potência (FP):</strong>
        </Typography>
        <Stack direction="row" spacing={2} flexWrap="wrap" useFlexGap>
          <Chip
            label="FP ≥ 0.92 - Excelente (sem multa)"
            size="small"
            color="success"
            variant="outlined"
          />
          <Chip
            label="0.85 ≤ FP < 0.92 - Adequado (atenção)"
            size="small"
            color="warning"
            variant="outlined"
          />
          <Chip
            label="FP < 0.85 - Baixo (risco de multa)"
            size="small"
            color="error"
            variant="outlined"
          />
        </Stack>
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          💡 <strong>Dica:</strong> FP baixo indica excesso de potência reativa. Considere instalar banco de capacitores para correção.
        </Typography>
      </Box>
    </Box>
  );
}
