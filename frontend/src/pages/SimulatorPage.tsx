import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
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
  Lock,
  Build,
  Bolt,
} from '@mui/icons-material';
import { useSimulator } from '../hooks/useSimulator';
import { useKafkaTags } from '../hooks/useKafkaTags';
import SystemOverview from '../components/simulator/SystemOverview';
import EquipmentControls from '../components/simulator/EquipmentControls';
import AlarmsPanel from '../components/simulator/AlarmsPanel';
import TrendsPanel from '../components/simulator/TrendsPanel';
import InterlockMonitor from '../components/simulator/InterlockMonitor';
import MaintenanceDashboard from '../components/simulator/MaintenanceDashboard';
import EnergyDashboard from '../components/simulator/EnergyDashboard';
import ModernScadaView from '../components/simulator/ModernScadaView';

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
    setShiploaderSetpoint,
    acknowledgeAllAlarms,
    refreshStatus,
  } = useSimulator();

  // Kafka real-time streaming hook
  const { tags: kafkaTags, connected: kafkaConnected, messageCount } = useKafkaTags();

  const [activeTab, setActiveTab] = useState(0);

  // Load initial status on mount
  useEffect(() => {
    refreshStatus().catch((err) => {
      console.error('Failed to load initial status:', err);
    });
  }, [refreshStatus]);

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
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
          <Box>
            <Typography variant="h4" component="h1" gutterBottom>
              🏭 Simulador de Terminal Exportador
            </Typography>
            <Typography variant="subtitle1" color="text.secondary">
              Terminal de Grãos - Linha 1500 t/h
            </Typography>
          </Box>
          <Box>
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
          </Box>
        </Box>
      </Box>

      {/* System Status Bar */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'center' }}>
          <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 20%' } }}>
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
          </Box>
          <Box sx={{ flex: { xs: '1 1 50%', md: '0 1 auto' }, minWidth: 100 }}>
            <Typography variant="body2" color="text.secondary">
              Tempo: {status?.system?.time_s?.toFixed(0) || 0}s
            </Typography>
          </Box>
          <Box sx={{ flex: { xs: '1 1 50%', md: '1 1 15%' } }}>
            <Typography variant="body2" color="text.secondary">
              Armazém: {status?.system?.warehouse_level_pct?.toFixed(1) || 0}%
            </Typography>
            <LinearProgress
              variant="determinate"
              value={status?.system?.warehouse_level_pct || 0}
              sx={{ mt: 0.5 }}
            />
          </Box>
          <Box sx={{ flex: { xs: '1 1 50%', md: '0 1 auto' }, minWidth: 120 }}>
            <Typography variant="body2" color="text.secondary">
              Energia: {status?.system?.total_kWh?.toFixed(1) || 0} kWh
            </Typography>
          </Box>
          <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 20%' }, display: 'flex', justifyContent: { xs: 'flex-start', md: 'flex-end' } }}>
            <Stack direction="row" spacing={1}>
              <Chip
                icon={<Speed />}
                label={kafkaConnected ? `Kafka Live (${messageCount})` : 'Kafka Offline'}
                size="small"
                color={kafkaConnected ? 'success' : 'default'}
                variant={kafkaConnected ? 'filled' : 'outlined'}
              />
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
          </Box>
        </Box>
      </Paper>

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => {}}>
          <AlertTitle>Erro</AlertTitle>
          {typeof error === 'string' ? error : JSON.stringify(error)}
        </Alert>
      )}

      {/* Main Content Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          aria-label="simulator tabs"
          sx={{ borderBottom: 1, borderColor: 'divider' }}
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab icon={<Assessment />} label="Visão Geral" />
          <Tab icon={<Speed />} label="SCADA Animado" />
          <Tab icon={<Settings />} label="Controles" />
          <Tab
            icon={
              <Badge badgeContent={status?.interlocks?.active_count || 0} color="error">
                <Lock />
              </Badge>
            }
            label="Interlocks"
          />
          <Tab
            icon={
              <Badge badgeContent={activeAlarms + activeTrips} color="error">
                <Notifications />
              </Badge>
            }
            label="Alarmes"
          />
          <Tab icon={<Build />} label="Manutenção" />
          <Tab icon={<Bolt />} label="Energia" />
          <Tab icon={<Assessment />} label="Tendências" />
        </Tabs>

        <TabPanel value={activeTab} index={0}>
          <SystemOverview status={status} />
        </TabPanel>

        <TabPanel value={activeTab} index={1}>
          <ModernScadaView
            status={status}
            onEquipmentClick={(equipmentId) => {
              console.log('Equipment clicked:', equipmentId);
              // TODO: Show equipment detail modal
            }}
          />
        </TabPanel>

        <TabPanel value={activeTab} index={2}>
          <EquipmentControls
            status={status}
            onSetGate={setGateSetpoint}
            onSetAllGates={setAllGatesSetpoint}
            onSetShiploader={setShiploaderSetpoint}
            loading={loading}
          />
        </TabPanel>

        <TabPanel value={activeTab} index={3}>
          <InterlockMonitor
            interlocks={status?.interlocks}
            loading={loading}
          />
        </TabPanel>

        <TabPanel value={activeTab} index={4}>
          <AlarmsPanel
            alarms={status?.alarms || []}
            trips={status?.trips || []}
            onAcknowledgeAll={acknowledgeAllAlarms}
          />
        </TabPanel>

        <TabPanel value={activeTab} index={4}>
          <MaintenanceDashboard maintenance={status?.maintenance} />
        </TabPanel>

        <TabPanel value={activeTab} index={5}>
          <MaintenanceDashboard maintenance={status?.maintenance} />
        </TabPanel>

        <TabPanel value={activeTab} index={6}>
          <EnergyDashboard energy={status?.energy} />
        </TabPanel>

        <TabPanel value={activeTab} index={7}>
          <TrendsPanel status={status} />
        </TabPanel>
      </Paper>

      {/* KPIs Footer */}
      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <Box sx={{ flex: '1 1 calc(25% - 16px)', minWidth: 250 }}>
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
        </Box>
        <Box sx={{ flex: '1 1 calc(25% - 16px)', minWidth: 250 }}>
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
        </Box>
        <Box sx={{ flex: '1 1 calc(25% - 16px)', minWidth: 250 }}>
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
        </Box>
        <Box sx={{ flex: '1 1 calc(25% - 16px)', minWidth: 250 }}>
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
        </Box>
      </Box>
    </Container>
  );
}
