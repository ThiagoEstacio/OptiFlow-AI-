import React from 'react';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Chip,
  Grid,
  LinearProgress,
  Paper,
  Stack,
  Typography,
  Alert,
  Divider,
} from '@mui/material';
import {
  Build,
  Thermostat,
  Vibration,
  Timer,
  Warning,
  CheckCircle,
  Error as ErrorIcon,
} from '@mui/icons-material';

interface MaintenanceData {
  avg_health_pct: number;
  equipment: {
    [key: string]: {
      health_pct: number;
      vibration_mm_s: number;
      oil_temp_C: number;
      hours_running: number;
      alarm_count: number;
      trip_count: number;
    };
  };
}

interface MaintenanceDashboardProps {
  maintenance?: MaintenanceData;
}

const getHealthColor = (health: number): 'success' | 'warning' | 'error' => {
  if (health >= 80) return 'success';
  if (health >= 60) return 'warning';
  return 'error';
};

const getHealthStatus = (health: number): string => {
  if (health >= 80) return 'Bom';
  if (health >= 60) return 'Atenção';
  if (health >= 40) return 'Crítico';
  return 'Falha Iminente';
};

const getHealthIcon = (health: number) => {
  if (health >= 80) return <CheckCircle sx={{ color: 'success.main' }} />;
  if (health >= 60) return <Warning sx={{ color: 'warning.main' }} />;
  return <ErrorIcon sx={{ color: 'error.main' }} />;
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

export default function MaintenanceDashboard({ maintenance }: MaintenanceDashboardProps) {
  if (!maintenance) {
    return (
      <Alert severity="info">
        Dados de manutenção não disponíveis. Aguarde conexão com simulador.
      </Alert>
    );
  }

  const equipmentList = Object.entries(maintenance.equipment || {});
  const criticalEquipment = equipmentList.filter(([_, data]) => data.health_pct < 60);

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
                    bgcolor: getHealthColor(maintenance.avg_health_pct) + '.light',
                  }}
                >
                  <Build sx={{ fontSize: 32, color: getHealthColor(maintenance.avg_health_pct) + '.dark' }} />
                </Box>
                <Box>
                  <Typography variant="h4" fontWeight="bold">
                    {maintenance.avg_health_pct.toFixed(1)}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Saúde Média
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
                    bgcolor: 'info.light',
                  }}
                >
                  <Build sx={{ fontSize: 32, color: 'info.dark' }} />
                </Box>
                <Box>
                  <Typography variant="h4" fontWeight="bold">
                    {equipmentList.length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Equipamentos
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
                    bgcolor: criticalEquipment.length > 0 ? 'error.light' : 'success.light',
                  }}
                >
                  <Warning sx={{ fontSize: 32, color: criticalEquipment.length > 0 ? 'error.dark' : 'success.dark' }} />
                </Box>
                <Box>
                  <Typography variant="h4" fontWeight="bold">
                    {criticalEquipment.length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Críticos
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
                    bgcolor: 'warning.light',
                  }}
                >
                  <Timer sx={{ fontSize: 32, color: 'warning.dark' }} />
                </Box>
                <Box>
                  <Typography variant="h4" fontWeight="bold">
                    {equipmentList.reduce((sum, [_, data]) => sum + data.hours_running, 0).toFixed(0)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Horas Totais
                  </Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Equipment Details */}
      <Grid container spacing={2}>
        {equipmentList.map(([equipId, data]) => (
          <Grid item xs={12} md={6} key={equipId}>
            <Card>
              <CardHeader
                title={
                  <Stack direction="row" spacing={1} alignItems="center">
                    <Typography variant="h6">{formatEquipmentName(equipId)}</Typography>
                    {getHealthIcon(data.health_pct)}
                    <Chip
                      label={getHealthStatus(data.health_pct)}
                      color={getHealthColor(data.health_pct)}
                      size="small"
                    />
                  </Stack>
                }
                subheader={`ID: ${equipId}`}
              />
              <CardContent>
                <Stack spacing={2}>
                  {/* Health Bar */}
                  <Box>
                    <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 0.5 }}>
                      <Typography variant="body2" color="text.secondary">
                        Saúde do Equipamento
                      </Typography>
                      <Typography variant="body2" fontWeight="bold">
                        {data.health_pct.toFixed(1)}%
                      </Typography>
                    </Stack>
                    <LinearProgress
                      variant="determinate"
                      value={data.health_pct}
                      color={getHealthColor(data.health_pct)}
                      sx={{ height: 8, borderRadius: 1 }}
                    />
                  </Box>

                  <Divider />

                  {/* Sensors Grid */}
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Paper sx={{ p: 1.5, bgcolor: 'background.default' }}>
                        <Stack direction="row" spacing={1} alignItems="center">
                          <Vibration fontSize="small" color="primary" />
                          <Box>
                            <Typography variant="caption" color="text.secondary">
                              Vibração
                            </Typography>
                            <Typography variant="body2" fontWeight="bold">
                              {data.vibration_mm_s.toFixed(2)} mm/s
                            </Typography>
                          </Box>
                        </Stack>
                      </Paper>
                    </Grid>

                    <Grid item xs={6}>
                      <Paper sx={{ p: 1.5, bgcolor: 'background.default' }}>
                        <Stack direction="row" spacing={1} alignItems="center">
                          <Thermostat fontSize="small" color="error" />
                          <Box>
                            <Typography variant="caption" color="text.secondary">
                              Temp. Óleo
                            </Typography>
                            <Typography variant="body2" fontWeight="bold">
                              {data.oil_temp_C.toFixed(1)} °C
                            </Typography>
                          </Box>
                        </Stack>
                      </Paper>
                    </Grid>

                    <Grid item xs={6}>
                      <Paper sx={{ p: 1.5, bgcolor: 'background.default' }}>
                        <Stack direction="row" spacing={1} alignItems="center">
                          <Timer fontSize="small" color="info" />
                          <Box>
                            <Typography variant="caption" color="text.secondary">
                              Horímetro
                            </Typography>
                            <Typography variant="body2" fontWeight="bold">
                              {data.hours_running.toFixed(0)} h
                            </Typography>
                          </Box>
                        </Stack>
                      </Paper>
                    </Grid>

                    <Grid item xs={6}>
                      <Paper sx={{ p: 1.5, bgcolor: 'background.default' }}>
                        <Stack direction="row" spacing={1} alignItems="center">
                          <Warning fontSize="small" color="warning" />
                          <Box>
                            <Typography variant="caption" color="text.secondary">
                              Alarmes/Trips
                            </Typography>
                            <Typography variant="body2" fontWeight="bold">
                              {data.alarm_count} / {data.trip_count}
                            </Typography>
                          </Box>
                        </Stack>
                      </Paper>
                    </Grid>
                  </Grid>

                  {/* Recommendations */}
                  {data.health_pct < 80 && (
                    <Alert
                      severity={data.health_pct < 60 ? 'error' : 'warning'}
                      variant="outlined"
                      sx={{ mt: 1 }}
                    >
                      {data.health_pct < 40 && (
                        <Typography variant="body2">
                          ⚠️ <strong>Manutenção Urgente:</strong> Equipamento em condição crítica. Parada para inspeção recomendada.
                        </Typography>
                      )}
                      {data.health_pct >= 40 && data.health_pct < 60 && (
                        <Typography variant="body2">
                          📋 <strong>Manutenção Planejada:</strong> Agende intervenção preventiva.
                        </Typography>
                      )}
                      {data.health_pct >= 60 && data.health_pct < 80 && (
                        <Typography variant="body2">
                          👁️ <strong>Monitoramento:</strong> Acompanhe evolução dos sensores.
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
          <strong>Thresholds de Saúde:</strong>
        </Typography>
        <Stack direction="row" spacing={2} flexWrap="wrap" useFlexGap>
          <Chip
            icon={<CheckCircle fontSize="small" />}
            label="≥ 80% - Bom"
            size="small"
            color="success"
            variant="outlined"
          />
          <Chip
            icon={<Warning fontSize="small" />}
            label="60-80% - Atenção (Manutenção Preventiva)"
            size="small"
            color="warning"
            variant="outlined"
          />
          <Chip
            icon={<ErrorIcon fontSize="small" />}
            label="< 60% - Crítico (Manutenção Urgente)"
            size="small"
            color="error"
            variant="outlined"
          />
        </Stack>
      </Box>
    </Box>
  );
}
