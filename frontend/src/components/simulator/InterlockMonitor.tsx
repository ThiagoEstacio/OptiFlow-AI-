import React from 'react';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Chip,
  Grid,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Paper,
  Stack,
  Typography,
  Alert,
  Tooltip,
} from '@mui/material';
import {
  Lock,
  LockOpen,
  Warning,
  Error as ErrorIcon,
  Refresh,
  Info,
} from '@mui/icons-material';

interface InterlockData {
  active_count: number;
  active_interlocks: Array<{
    id: string;
    cause: string;
    type: string;
    effects: string[];
    active: boolean;
    can_reset: boolean;
  }>;
}

interface InterlockMonitorProps {
  interlocks?: InterlockData;
  onResetInterlock?: (interlockId: string) => void;
  loading?: boolean;
}

const getInterlockTypeColor = (type: string): 'error' | 'warning' | 'info' | 'default' => {
  switch (type) {
    case 'HARD_TRIP':
      return 'error';
    case 'EMERGENCY':
      return 'error';
    case 'ALARM_ACTION':
      return 'warning';
    case 'PERMISSIVE':
      return 'info';
    default:
      return 'default';
  }
};

const getInterlockTypeIcon = (type: string) => {
  switch (type) {
    case 'HARD_TRIP':
    case 'EMERGENCY':
      return <ErrorIcon fontSize="small" />;
    case 'ALARM_ACTION':
      return <Warning fontSize="small" />;
    case 'PERMISSIVE':
      return <Info fontSize="small" />;
    default:
      return <Lock fontSize="small" />;
  }
};

export default function InterlockMonitor({
  interlocks,
  onResetInterlock,
  loading,
}: InterlockMonitorProps) {
  if (!interlocks) {
    return (
      <Alert severity="info">
        Dados de interlocks não disponíveis. Aguarde conexão com simulador.
      </Alert>
    );
  }

  const activeInterlocks = interlocks.active_interlocks?.filter(i => i.active) || [];

  return (
    <Box>
      {/* Summary Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={4}>
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
                    bgcolor: activeInterlocks.length > 0 ? 'error.light' : 'success.light',
                  }}
                >
                  {activeInterlocks.length > 0 ? (
                    <Lock sx={{ fontSize: 32, color: 'error.dark' }} />
                  ) : (
                    <LockOpen sx={{ fontSize: 32, color: 'success.dark' }} />
                  )}
                </Box>
                <Box>
                  <Typography variant="h4" fontWeight="bold">
                    {activeInterlocks.length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Interlocks Ativos
                  </Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
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
                  <Warning sx={{ fontSize: 32, color: 'warning.dark' }} />
                </Box>
                <Box>
                  <Typography variant="h4" fontWeight="bold">
                    {activeInterlocks.filter(i => i.type === 'ALARM_ACTION').length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Ações de Alarme
                  </Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
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
                  <ErrorIcon sx={{ fontSize: 32, color: 'error.dark' }} />
                </Box>
                <Box>
                  <Typography variant="h4" fontWeight="bold">
                    {activeInterlocks.filter(i => i.type === 'HARD_TRIP' || i.type === 'EMERGENCY').length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Trips Críticos
                  </Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Active Interlocks List */}
      <Card>
        <CardHeader
          title="Interlocks Ativos"
          subheader={`${activeInterlocks.length} intertravamento(s) ativo(s)`}
        />
        <CardContent>
          {activeInterlocks.length === 0 ? (
            <Alert severity="success" icon={<LockOpen />}>
              ✅ Nenhum interlock ativo. Sistema operando normalmente.
            </Alert>
          ) : (
            <List>
              {activeInterlocks.map((interlock, index) => (
                <Paper
                  key={interlock.id}
                  elevation={2}
                  sx={{
                    mb: 2,
                    p: 2,
                    border: '2px solid',
                    borderColor: getInterlockTypeColor(interlock.type) + '.main',
                  }}
                >
                  <Stack spacing={2}>
                    {/* Header */}
                    <Stack direction="row" justifyContent="space-between" alignItems="center">
                      <Stack direction="row" spacing={2} alignItems="center">
                        <Chip
                          icon={getInterlockTypeIcon(interlock.type)}
                          label={interlock.id}
                          color={getInterlockTypeColor(interlock.type)}
                          size="small"
                        />
                        <Chip
                          label={interlock.type}
                          variant="outlined"
                          size="small"
                        />
                      </Stack>
                      {interlock.can_reset && onResetInterlock && (
                        <Tooltip title="Resetar Interlock">
                          <IconButton
                            size="small"
                            color="primary"
                            onClick={() => onResetInterlock(interlock.id)}
                            disabled={loading}
                          >
                            <Refresh />
                          </IconButton>
                        </Tooltip>
                      )}
                    </Stack>

                    {/* Cause */}
                    <Box>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        <strong>Causa:</strong>
                      </Typography>
                      <Typography variant="body1">{interlock.cause}</Typography>
                    </Box>

                    {/* Effects */}
                    {interlock.effects && interlock.effects.length > 0 && (
                      <Box>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          <strong>Efeitos Aplicados:</strong>
                        </Typography>
                        <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                          {interlock.effects.map((effect, idx) => (
                            <Chip
                              key={idx}
                              label={effect}
                              size="small"
                              variant="outlined"
                              color="error"
                            />
                          ))}
                        </Stack>
                      </Box>
                    )}
                  </Stack>
                </Paper>
              ))}
            </List>
          )}
        </CardContent>
      </Card>

      {/* Legend */}
      <Box sx={{ mt: 2 }}>
        <Typography variant="caption" color="text.secondary" gutterBottom display="block">
          <strong>Legenda de Tipos:</strong>
        </Typography>
        <Stack direction="row" spacing={2} flexWrap="wrap" useFlexGap>
          <Chip
            icon={<ErrorIcon fontSize="small" />}
            label="HARD_TRIP - Trip de Hardware"
            size="small"
            color="error"
            variant="outlined"
          />
          <Chip
            icon={<ErrorIcon fontSize="small" />}
            label="EMERGENCY - Emergência"
            size="small"
            color="error"
            variant="outlined"
          />
          <Chip
            icon={<Warning fontSize="small" />}
            label="ALARM_ACTION - Ação de Alarme"
            size="small"
            color="warning"
            variant="outlined"
          />
          <Chip
            icon={<Info fontSize="small" />}
            label="PERMISSIVE - Permissivo"
            size="small"
            color="info"
            variant="outlined"
          />
        </Stack>
      </Box>
    </Box>
  );
}
