import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  Chip,
  LinearProgress,
  Card,
  CardContent,
  IconButton,
  Tooltip,
  Alert,
  Tab,
  Tabs,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Memory as MemoryIcon,
  Storage as StorageIcon,
  Speed as SpeedIcon,
  Computer as ComputerIcon,
  Cloud as CloudIcon,
  Router as RouterIcon,
  GitHub as GitHubIcon,
} from '@mui/icons-material';

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
      id={`admin-tabpanel-${index}`}
      aria-labelledby={`admin-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

interface Container {
  name: string;
  status: string;
  health: string;
  ports: string;
  image: string;
  created: string;
}

interface SystemMetrics {
  cpu_percent: number;
  memory_used_mb: number;
  memory_total_mb: number;
  disk_used_gb: number;
  disk_total_gb: number;
  uptime_hours: number;
}

interface GPUInfo {
  available: boolean;
  name?: string;
  compute_capability?: string;
  memory_total_mb?: number;
  memory_free_mb?: number;
  utilization?: number;
}

interface ServiceStatus {
  name: string;
  status: 'healthy' | 'unhealthy' | 'starting' | 'stopped';
  url?: string;
  version?: string;
  uptime?: string;
}

const AdminPage: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [containers, setContainers] = useState<Container[]>([]);
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(null);
  const [gpuInfo, setGPUInfo] = useState<GPUInfo | null>(null);
  const [services, setServices] = useState<ServiceStatus[]>([]);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const fetchSystemStatus = async () => {
    setLoading(true);
    try {
      // Fetch system metrics
      const metricsResponse = await fetch('http://localhost:8000/api/v1/admin/system/metrics');
      if (metricsResponse.ok) {
        const metricsData = await metricsResponse.json();
        setSystemMetrics(metricsData);
      }

      // Fetch Docker containers
      const containersResponse = await fetch('http://localhost:8000/api/v1/admin/docker/containers');
      if (containersResponse.ok) {
        const containersData = await containersResponse.json();
        const formattedContainers = containersData.map((c: any) => ({
          name: c.name,
          status: c.health,
          health: c.health,
          ports: c.ports,
          image: c.image,
          created: c.created,
        }));
        setContainers(formattedContainers);
      }

      // Fetch GPU info
      const gpuResponse = await fetch('http://localhost:8000/api/v1/admin/gpu/info');
      if (gpuResponse.ok) {
        const gpuData = await gpuResponse.json();
        if (gpuData.available) {
          setGPUInfo({
            available: true,
            name: gpuData.name,
            compute_capability: `${gpuData.driver_version}`,
            memory_total_mb: gpuData.memory_total_mb,
            memory_free_mb: gpuData.memory_free_mb,
            utilization: gpuData.utilization_gpu,
          });
        } else {
          setGPUInfo({ available: false });
        }
      }

      // Fetch services health
      const servicesResponse = await fetch('http://localhost:8000/api/v1/admin/services/health');
      if (servicesResponse.ok) {
        const servicesData = await servicesResponse.json();
        setServices(servicesData.map((s: any) => ({
          name: s.name,
          status: s.status,
          url: s.url,
          version: '1.0.0',
          uptime: '2h 15m',
        })));
      }

      setLastUpdate(new Date());
    } catch (error) {
      console.error('Error fetching system status:', error);
      
      // Fallback to simulator GPU info
      try {
        const simResponse = await fetch('http://localhost:8000/api/v1/simulator/status');
        const simData = await simResponse.json();

        if (simData.dem_physics?.gpu_info) {
          setGPUInfo({
            available: simData.dem_physics.gpu_available,
            name: simData.dem_physics.gpu_info.name,
            compute_capability: simData.dem_physics.gpu_info.compute_capability,
            memory_total_mb: simData.dem_physics.gpu_info.memory_total_mb,
            memory_free_mb: simData.dem_physics.gpu_info.memory_free_mb,
            utilization: 0,
          });
        }
      } catch (e) {
        console.error('Error fetching simulator status:', e);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSystemStatus();
    const interval = setInterval(fetchSystemStatus, 10000); // Update every 10s
    return () => clearInterval(interval);
  }, []);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy':
      case 'running':
        return 'success';
      case 'unhealthy':
      case 'stopped':
        return 'error';
      case 'starting':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy':
      case 'running':
        return <CheckCircleIcon color="success" />;
      case 'unhealthy':
      case 'stopped':
        return <ErrorIcon color="error" />;
      case 'starting':
        return <WarningIcon color="warning" />;
      default:
        return null;
    }
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Administração do Sistema
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            Última atualização: {lastUpdate.toLocaleTimeString()}
          </Typography>
          <Tooltip title="Atualizar">
            <IconButton onClick={fetchSystemStatus} disabled={loading}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Summary Cards */}
      <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap', mb: 3 }}>
        <Box sx={{ flex: '1 1 calc(25% - 18px)', minWidth: '220px' }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <ComputerIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">CPU</Typography>
              </Box>
              <Typography variant="h4">{systemMetrics?.cpu_percent.toFixed(1)}%</Typography>
              <LinearProgress
                variant="determinate"
                value={systemMetrics?.cpu_percent || 0}
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Box>

        <Box sx={{ flex: '1 1 calc(25% - 18px)', minWidth: '220px' }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <MemoryIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">Memória</Typography>
              </Box>
              <Typography variant="h4">
                {((systemMetrics?.memory_used_mb || 0) / 1024).toFixed(1)} GB
              </Typography>
              <LinearProgress
                variant="determinate"
                value={((systemMetrics?.memory_used_mb || 0) / (systemMetrics?.memory_total_mb || 1)) * 100}
                sx={{ mt: 1 }}
              />
              <Typography variant="caption" color="text.secondary">
                de {((systemMetrics?.memory_total_mb || 0) / 1024).toFixed(0)} GB
              </Typography>
            </CardContent>
          </Card>
        </Box>

        <Box sx={{ flex: '1 1 calc(25% - 18px)', minWidth: '220px' }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <StorageIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">Disco</Typography>
              </Box>
              <Typography variant="h4">{systemMetrics?.disk_used_gb} GB</Typography>
              <LinearProgress
                variant="determinate"
                value={((systemMetrics?.disk_used_gb || 0) / (systemMetrics?.disk_total_gb || 1)) * 100}
                sx={{ mt: 1 }}
              />
              <Typography variant="caption" color="text.secondary">
                de {systemMetrics?.disk_total_gb} GB
              </Typography>
            </CardContent>
          </Card>
        </Box>

        <Box sx={{ flex: '1 1 calc(25% - 18px)', minWidth: '220px' }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <SpeedIcon sx={{ mr: 1, color: gpuInfo?.available ? 'success.main' : 'text.secondary' }} />
                <Typography variant="h6">GPU</Typography>
              </Box>
              {gpuInfo?.available ? (
                <>
                  <Typography variant="body2" noWrap>
                    {gpuInfo.name}
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={((gpuInfo.memory_total_mb! - gpuInfo.memory_free_mb!) / gpuInfo.memory_total_mb!) * 100}
                    sx={{ mt: 1 }}
                    color="success"
                  />
                  <Typography variant="caption" color="text.secondary">
                    {((gpuInfo.memory_total_mb! - gpuInfo.memory_free_mb!) / 1024).toFixed(1)} / {(gpuInfo.memory_total_mb! / 1024).toFixed(1)} GB
                  </Typography>
                </>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  Não disponível
                </Typography>
              )}
            </CardContent>
          </Card>
        </Box>
      </Box>

      {/* GPU Acceleration Alert */}
      {gpuInfo?.available && (
        <Alert severity="success" sx={{ mb: 3 }}>
          Aceleração GPU Ativa: {gpuInfo.name} (Compute {gpuInfo.compute_capability})
        </Alert>
      )}

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="admin tabs">
          <Tab label="Containers" icon={<CloudIcon />} iconPosition="start" />
          <Tab label="Serviços" icon={<RouterIcon />} iconPosition="start" />
          <Tab label="GPU" icon={<SpeedIcon />} iconPosition="start" />
          <Tab label="Repositório" icon={<GitHubIcon />} iconPosition="start" />
        </Tabs>
      </Paper>

      {/* Containers Tab */}
      <TabPanel value={tabValue} index={0}>
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Status</TableCell>
                <TableCell>Nome</TableCell>
                <TableCell>Imagem</TableCell>
                <TableCell>Portas</TableCell>
                <TableCell>Criado</TableCell>
                <TableCell>Ações</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {containers.map((container) => (
                <TableRow key={container.name}>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {getStatusIcon(container.health)}
                      <Chip 
                        label={container.health} 
                        color={getStatusColor(container.health)} 
                        size="small" 
                      />
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium">
                      {container.name}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.secondary">
                      {container.image}
                    </Typography>
                  </TableCell>
                  <TableCell>{container.ports}</TableCell>
                  <TableCell>{container.created}</TableCell>
                  <TableCell>
                    <Button size="small" disabled>
                      Logs
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </TabPanel>

      {/* Services Tab */}
      <TabPanel value={tabValue} index={1}>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          {services.map((service) => (
            <Box key={service.name} sx={{ flex: '1 1 calc(33.333% - 11px)', minWidth: '280px' }}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 2 }}>
                    <Typography variant="h6">{service.name}</Typography>
                    {getStatusIcon(service.status)}
                  </Box>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    {service.url}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
                    <Chip label={`v${service.version}`} size="small" />
                    <Chip label={service.uptime} size="small" variant="outlined" />
                  </Box>
                </CardContent>
              </Card>
            </Box>
          ))}
        </Box>
      </TabPanel>

      {/* GPU Tab */}
      <TabPanel value={tabValue} index={2}>
        {gpuInfo?.available ? (
          <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
            <Box sx={{ flex: '1 1 calc(50% - 12px)', minWidth: '300px' }}>
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Informações da GPU
                </Typography>
                <Table size="small">
                  <TableBody>
                    <TableRow>
                      <TableCell>Nome</TableCell>
                      <TableCell>{gpuInfo.name}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Compute Capability</TableCell>
                      <TableCell>{gpuInfo.compute_capability}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>VRAM Total</TableCell>
                      <TableCell>{(gpuInfo.memory_total_mb! / 1024).toFixed(2)} GB</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>VRAM Livre</TableCell>
                      <TableCell>{(gpuInfo.memory_free_mb! / 1024).toFixed(2)} GB</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>VRAM Usada</TableCell>
                      <TableCell>
                        {((gpuInfo.memory_total_mb! - gpuInfo.memory_free_mb!) / 1024).toFixed(2)} GB
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </Paper>
            </Box>
            <Box sx={{ flex: '1 1 calc(50% - 12px)', minWidth: '300px' }}>
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Utilização
                </Typography>
                <Box sx={{ mt: 3 }}>
                  <Typography variant="body2" gutterBottom>
                    VRAM
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={((gpuInfo.memory_total_mb! - gpuInfo.memory_free_mb!) / gpuInfo.memory_total_mb!) * 100}
                    sx={{ height: 10, borderRadius: 1 }}
                    color="success"
                  />
                  <Typography variant="caption" color="text.secondary">
                    {(((gpuInfo.memory_total_mb! - gpuInfo.memory_free_mb!) / gpuInfo.memory_total_mb!) * 100).toFixed(1)}% utilizado
                  </Typography>
                </Box>
              </Paper>
            </Box>
          </Box>
        ) : (
          <Alert severity="warning">
            GPU não disponível. Verifique se o NVIDIA driver está instalado e se o container tem acesso GPU.
          </Alert>
        )}
      </TabPanel>

      {/* Repository Tab */}
      <TabPanel value={tabValue} index={3}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Informações do Repositório
          </Typography>
          <Table size="small">
            <TableBody>
              <TableRow>
                <TableCell>Branch</TableCell>
                <TableCell>claude/merged-chatbot-features-011CUdj4zT6jFFR2nKHsykcK</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Repositório</TableCell>
                <TableCell>OptiFlow-AI-</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Owner</TableCell>
                <TableCell>ThiagoEstacio</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Última Modificação</TableCell>
                <TableCell>{new Date().toLocaleString()}</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </Paper>
      </TabPanel>
    </Container>
  );
};

export default AdminPage;
