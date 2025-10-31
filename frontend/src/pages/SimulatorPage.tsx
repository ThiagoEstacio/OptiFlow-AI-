import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Grid,
  Paper,
  Typography,
  Button,
  IconButton,
  Chip,
  Alert,
  AlertTitle,
  Tabs,
  Tab,
  LinearProgress,
  Card,
  CardContent,
  CardHeader,
  Divider,
  Stack,
  Badge,
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  Refresh,
  Warning,
  Error as ErrorIcon,
  CheckCircle,
  Speed,
  Settings,
  Assessment,
  Notifications,
} from '@mui/icons-material';
import { useSimulator } from '../hooks/useSimulator';
import SystemOverview from '../components/simulator/SystemOverview';
import EquipmentControls from '../components/simulator/EquipmentControls';
import AlarmsPanel from '../components/simulator/AlarmsPanel';
import TrendsPanel from '../components/simulator/TrendsPanel';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simulator-tabpanel-${index}`}
      aria-labelledby={`simulator-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export default function SimulatorPage() {
  const {
    status,
    loading,
    error,
    startSystem,
    stopSystem,
    resetSystem,
    setGateSetpoint,
    setAllGatesSetpoint,
    setShipload erSetpoint,
    acknowledgeAllAlarms,
    refreshStatus,
  } = useSimulator();

  const [activeTab, setActiveTab] = useState(0);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Auto-refresh every 2 seconds
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      refreshStatus();
    }, 2000);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshStatus]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  // Count active alarms and trips
  const activeAlarms = status?.alarms?.filter(a => a.active).length || 0;
  const activeTrips = status?.trips?.filter(t => t.active).length || 0;

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Grid container alignItems="center" justifyContent="space-between">
          <Grid item>
            <Typography variant="h4" component="h1" gutterBottom>
              🏭 Simulador de Terminal Exportador
            </Typography>
            <Typography variant="subtitle1" color="text.secondary">
              Terminal de Grãos - Linha 1500 t/h
            </Typography>
          </Grid>
          <Grid item>
            <Stack direction="row" spacing={2}>
              <Button
                variant={status?.system?.running ? "outlined" : "contained"}
                color="success"
                startIcon={<PlayArrow />}
                onClick={startSystem}
                disabled={loading || status?.system?.running}
              >
                Iniciar
              </Button>
              <Button
                variant={status?.system?.running ? "contained" : "outlined"}
                color="error"
                startIcon={<Stop />}
                onClick={stopSystem}
                disabled={loading || !status?.system?.running}
              >
                Parar
              </Button>
              <Button
                variant="outlined"
                startIcon={<Refresh />}
                onClick={resetSystem}
                disabled={loading}
              >
                Reset
              </Button>
            </Stack>
          </Grid>
        </Grid>
      </Box>

      {/* System Status Bar */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={3}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="body2" color="text.secondary">
                Status:
              </Typography>
              <Chip
                icon={status?.system?.running ? <CheckCircle /> : <Stop />}
                label={status?.system?.running ? 'OPERANDO' : 'PARADO'}
                color={status?.system?.running ? 'success' : 'default'}
                size="small"
              />
            </Box>
          </Grid>
          <Grid item xs={12} md={2}>
            <Typography variant="body2" color="text.secondary">
              Tempo: {status?.system?.time_s?.toFixed(0) || 0}s
            </Typography>
          </Grid>
          <Grid item xs={12} md={2}>
            <Typography variant="body2" color="text.secondary">
              Armazém: {status?.system?.warehouse_level_pct?.toFixed(1) || 0}%
            </Typography>
            <LinearProgress
              variant="determinate"
              value={status?.system?.warehouse_level_pct || 0}
              sx={{ mt: 0.5 }}
            />
          </Grid>
          <Grid item xs={12} md={2}>
            <Typography variant="body2" color="text.secondary">
              Energia: {status?.system?.total_kWh?.toFixed(1) || 0} kWh
            </Typography>
          </Grid>
          <Grid item xs={12} md={3}>
            <Stack direction="row" spacing={1} justifyContent="flex-end">
              <Badge badgeContent={activeAlarms} color="warning">
                <Chip
                  icon={<Warning />}
                  label="Alarmes"
                  size="small"
                  color={activeAlarms > 0 ? 'warning' : 'default'}
                />
              </Badge>
              <Badge badgeContent={activeTrips} color="error">
                <Chip
                  icon={<ErrorIcon />}
                  label="Trips"
                  size="small"
                  color={activeTrips > 0 ? 'error' : 'default'}
                />
              </Badge>
            </Stack>
          </Grid>
        </Grid>
      </Paper>

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => {}}>
          <AlertTitle>Erro</AlertTitle>
          {error}
        </Alert>
      )}

      {/* Main Content Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          aria-label="simulator tabs"
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab icon={<Speed />} label="Overview" />
          <Tab icon={<Settings />} label="Controles" />
          <Tab icon={<Assessment />} label="Tendências" />
          <Tab
            icon={
              <Badge badgeContent={activeAlarms + activeTrips} color="error">
                <Notifications />
              </Badge>
            }
            label="Alarmes"
          />
        </Tabs>

        <TabPanel value={activeTab} index={0}>
          <SystemOverview status={status} />
        </TabPanel>

        <TabPanel value={activeTab} index={1}>
          <EquipmentControls
            status={status}
            onSetGate={setGateSetpoint}
            onSetAllGates={setAllGatesSetpoint}
            onSetShiploader={setShiploaderSetpoint}
            loading={loading}
          />
        </TabPanel>

        <TabPanel value={activeTab} index={2}>
          <TrendsPanel status={status} />
        </TabPanel>

        <TabPanel value={activeTab} index={3}>
          <AlarmsPanel
            alarms={status?.alarms || []}
            trips={status?.trips || []}
            onAcknowledgeAll={acknowledgeAllAlarms}
          />
        </TabPanel>
      </Paper>

      {/* KPIs Footer */}
      <Grid container spacing={2}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom variant="body2">
                Produção Total
              </Typography>
              <Typography variant="h5">
                {status?.system?.total_mass_t?.toFixed(1) || 0} t
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom variant="body2">
                Consumo Energético
              </Typography>
              <Typography variant="h5">
                {status?.system?.total_kWh?.toFixed(1) || 0} kWh
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom variant="body2">
                Eficiência
              </Typography>
              <Typography variant="h5">
                {status?.system?.kWh_per_ton?.toFixed(2) || 0} kWh/t
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom variant="body2">
                Custo Total
              </Typography>
              <Typography variant="h5">
                R$ {status?.system?.cost_BRL?.toFixed(2) || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
}
