import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../store';
import { fetchSites } from '../store/slices/sitesSlice';
import { fetchDevices } from '../store/slices/devicesSlice';
import { fetchActiveAlarms } from '../store/slices/alarmsSlice';
import {
  Box,
  Container,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  LinearProgress,
  IconButton,
  Paper,
  Avatar,
  Divider,
} from '@mui/material';
import {
  TrendingUp,
  CloudUpload,
  Insights,
  Dashboard as DashboardIcon,
  BarChart,
  Favorite,
  Chat,
  Speed,
  Palette,
  ArrowForward,
  CheckCircle,
  Warning,
  Error,
  Info,
} from '@mui/icons-material';

interface FeatureCard {
  title: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  path: string;
  badge?: string;
  gradient: string;
}

export const ModernDashboard: React.FC = () => {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const sites = useAppSelector((state) => state.sites.items);
  const devices = useAppSelector((state) => state.devices.items);
  const activeAlarms = useAppSelector((state) => state.alarms.activeAlarms);

  useEffect(() => {
    dispatch(fetchSites({ site_type: 'smartport' }));
    dispatch(fetchDevices());
    dispatch(fetchActiveAlarms());
  }, [dispatch]);

  const defaultSiteId = sites.length > 0 ? sites[0].id : 1;
  const activeDevices = devices.filter((d) => d.enabled && d.status === 'connected');
  const smartportSites = sites.filter((s) => s.site_type === 'smartport');

  const featureCards: FeatureCard[] = [
    {
      title: 'Dashboard Executivo',
      description: 'Visão 360° com KPIs, ROI e insights estratégicos para tomada de decisão',
      icon: <TrendingUp sx={{ fontSize: 40 }} />,
      color: '#2196F3',
      gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      path: `/executive/${defaultSiteId}`,
      badge: 'Novo',
    },
    {
      title: 'Importar Dados GBM',
      description: 'Importe dados da GBM Logística via Excel, API ou entrada manual',
      icon: <CloudUpload sx={{ fontSize: 40 }} />,
      color: '#4CAF50',
      gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
      path: `/gbm-import/${defaultSiteId}`,
      badge: 'Popular',
    },
    {
      title: 'Insights GBM',
      description: 'Análise inteligente com IA: identifique gargalos, oportunidades e reduza custos',
      icon: <Insights sx={{ fontSize: 40 }} />,
      color: '#FF9800',
      gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
      path: `/gbm-insights/${defaultSiteId}`,
    },
    {
      title: 'Centro de Análise',
      description: 'Analytics avançado, detecção de anomalias e insights operacionais',
      icon: <BarChart sx={{ fontSize: 40 }} />,
      color: '#9C27B0',
      gradient: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
      path: '/analytics-hub',
    },
    {
      title: 'Saúde de Assets',
      description: 'Monitore saúde de equipamentos, preveja falhas e otimize manutenção',
      icon: <Favorite sx={{ fontSize: 40 }} />,
      color: '#E91E63',
      gradient: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
      path: '/asset-health-hub',
    },
    {
      title: 'Assistente IA',
      description: 'Chat inteligente para análise de dados, recomendações e suporte 24/7',
      icon: <Chat sx={{ fontSize: 40 }} />,
      color: '#00BCD4',
      gradient: 'linear-gradient(135deg, #30cfd0 0%, #330867 100%)',
      path: '/chat',
    },
    {
      title: 'Simulador',
      description: 'Simule operações portuárias e teste cenários antes de implementar',
      icon: <Speed sx={{ fontSize: 40 }} />,
      color: '#FF5722',
      gradient: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
      path: '/simulator',
    },
    {
      title: 'Construtor de Dashboards',
      description: 'Crie dashboards personalizados com drag-and-drop sem código',
      icon: <Palette sx={{ fontSize: 40 }} />,
      color: '#795548',
      gradient: 'linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)',
      path: '/dashboard-builder',
    },
  ];

  const stats = [
    {
      label: 'Sites Ativos',
      value: smartportSites.length,
      icon: <DashboardIcon />,
      color: 'primary',
      change: '+2 este mês',
    },
    {
      label: 'Dispositivos Online',
      value: activeDevices.length,
      icon: <CheckCircle />,
      color: 'success',
      change: `${devices.length} total`,
    },
    {
      label: 'Alarmes Ativos',
      value: activeAlarms.length,
      icon: activeAlarms.length > 0 ? <Warning /> : <CheckCircle />,
      color: activeAlarms.length > 0 ? 'error' : 'success',
      change: activeAlarms.length > 0 ? 'Requer atenção' : 'Tudo OK',
    },
    {
      label: 'Uptime do Sistema',
      value: '99.8%',
      icon: <TrendingUp />,
      color: 'success',
      change: 'Últimos 30 dias',
    },
  ];

  return (
    <Container maxWidth="xl">
      <Box sx={{ py: 4 }}>
        {/* Hero Section */}
        <Box sx={{ mb: 6 }}>
          <Typography
            variant="h3"
            gutterBottom
            fontWeight="bold"
            sx={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            Bem-vindo ao OptiFlow AI
          </Typography>
          <Typography variant="h6" color="text.secondary" sx={{ mb: 3 }}>
            Plataforma Inteligente para Gestão de Terminais Portuários
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 800 }}>
            Revolucione a forma como você gerencia dados de manutenção e operação. Nossa ferramenta
            atua como um cientista de dados, engenheiro de IA/ML, engenheiro de confiabilidade e
            analista sênior de PCO e PCM.
          </Typography>
        </Box>

        {/* Stats Grid */}
        <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap', mb: 6 }}>
          {stats.map((stat, index) => (
            <Box key={index} sx={{ flex: '1 1 calc(25% - 24px)', minWidth: 250 }}>
              <Card
                sx={{
                  height: '100%',
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: 6,
                  },
                }}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Avatar
                      sx={{
                        bgcolor: `${stat.color}.light`,
                        color: `${stat.color}.main`,
                        mr: 2,
                      }}
                    >
                      {stat.icon}
                    </Avatar>
                    <Box>
                      <Typography variant="h4" fontWeight="bold">
                        {stat.value}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {stat.label}
                      </Typography>
                    </Box>
                  </Box>
                  <Typography variant="caption" color="text.secondary">
                    {stat.change}
                  </Typography>
                </CardContent>
              </Card>
            </Box>
          ))}
        </Box>

        {/* Feature Cards */}
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" gutterBottom fontWeight="bold" sx={{ mb: 3 }}>
            Recursos Principais
          </Typography>
          <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
            {featureCards.map((feature, index) => (
              <Box key={index} sx={{ flex: '1 1 calc(25% - 24px)', minWidth: 250 }}>
                <Card
                  sx={{
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    cursor: 'pointer',
                    transition: 'all 0.3s ease',
                    position: 'relative',
                    overflow: 'visible',
                    '&:hover': {
                      transform: 'translateY(-8px)',
                      boxShadow: 8,
                      '& .feature-icon': {
                        transform: 'scale(1.1) rotate(5deg)',
                      },
                      '& .arrow-icon': {
                        transform: 'translateX(4px)',
                      },
                    },
                  }}
                  onClick={() => navigate(feature.path)}
                >
                  {feature.badge && (
                    <Chip
                      label={feature.badge}
                      size="small"
                      color="secondary"
                      sx={{
                        position: 'absolute',
                        top: 12,
                        right: 12,
                        zIndex: 1,
                      }}
                    />
                  )}
                  <Box
                    sx={{
                      background: feature.gradient,
                      p: 3,
                      display: 'flex',
                      justifyContent: 'center',
                      alignItems: 'center',
                      minHeight: 120,
                    }}
                  >
                    <Box
                      className="feature-icon"
                      sx={{
                        color: 'white',
                        transition: 'transform 0.3s ease',
                      }}
                    >
                      {feature.icon}
                    </Box>
                  </Box>
                  <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                    <Typography variant="h6" gutterBottom fontWeight="bold">
                      {feature.title}
                    </Typography>
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{ mb: 2, flex: 1 }}
                    >
                      {feature.description}
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', color: 'primary.main' }}>
                      <Typography variant="button" fontWeight="bold">
                        Acessar
                      </Typography>
                      <ArrowForward
                        className="arrow-icon"
                        sx={{
                          ml: 1,
                          fontSize: 20,
                          transition: 'transform 0.2s',
                        }}
                      />
                    </Box>
                  </CardContent>
                </Card>
              </Box>
            ))}
          </Box>
        </Box>

        {/* Recent Activity */}
        <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
          {/* Recent Sites */}
          <Box sx={{ flex: '1 1 calc(50% - 12px)', minWidth: 400 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom fontWeight="bold">
                  Sites Recentes
                </Typography>
                <Divider sx={{ mb: 2 }} />
                {smartportSites.length === 0 ? (
                  <Box sx={{ textAlign: 'center', py: 4 }}>
                    <Info sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
                    <Typography color="text.secondary">
                      Nenhum site configurado ainda
                    </Typography>
                    <Button variant="outlined" sx={{ mt: 2 }} onClick={() => navigate('/sites')}>
                      Adicionar Site
                    </Button>
                  </Box>
                ) : (
                  <Box>
                    {smartportSites.slice(0, 5).map((site) => (
                      <Paper
                        key={site.id}
                        sx={{
                          p: 2,
                          mb: 1,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          '&:hover': { bgcolor: 'grey.50' },
                        }}
                        elevation={0}
                        variant="outlined"
                      >
                        <Box>
                          <Typography variant="subtitle1" fontWeight="bold">
                            {site.name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {site.city}, {site.country}
                          </Typography>
                        </Box>
                        <Chip
                          label={site.is_active ? 'Ativo' : 'Inativo'}
                          color={site.is_active ? 'success' : 'default'}
                          size="small"
                        />
                      </Paper>
                    ))}
                  </Box>
                )}
              </CardContent>
            </Card>
          </Box>

          {/* System Status */}
          <Box sx={{ flex: '1 1 calc(50% - 12px)', minWidth: 400 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom fontWeight="bold">
                  Status do Sistema
                </Typography>
                <Divider sx={{ mb: 2 }} />
                <Box>
                  <Box sx={{ mb: 3 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2">API Server</Typography>
                      <Chip label="Online" color="success" size="small" />
                    </Box>
                    <LinearProgress variant="determinate" value={100} color="success" />
                  </Box>
                  <Box sx={{ mb: 3 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2">Database</Typography>
                      <Chip label="Healthy" color="success" size="small" />
                    </Box>
                    <LinearProgress variant="determinate" value={98} color="success" />
                  </Box>
                  <Box sx={{ mb: 3 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2">InfluxDB</Typography>
                      <Chip label="Online" color="success" size="small" />
                    </Box>
                    <LinearProgress variant="determinate" value={100} color="success" />
                  </Box>
                  <Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2">AI Services</Typography>
                      <Chip label="Ready" color="success" size="small" />
                    </Box>
                    <LinearProgress variant="determinate" value={95} color="success" />
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Box>
        </Box>

        {/* Quick Start Guide */}
        <Card sx={{ mt: 3, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
          <CardContent>
            <Typography variant="h6" gutterBottom fontWeight="bold" color="white">
              🚀 Comece Agora
            </Typography>
            <Typography variant="body2" color="white" sx={{ mb: 2, opacity: 0.9 }}>
              Siga estes passos para aproveitar ao máximo o OptiFlow AI:
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <Box sx={{ flex: '1 1 calc(25% - 16px)', minWidth: 200 }}>
                <Paper sx={{ p: 2, textAlign: 'center', height: '100%' }}>
                  <Typography variant="h4" color="primary" fontWeight="bold">
                    1
                  </Typography>
                  <Typography variant="body2">Configure seus sites</Typography>
                </Paper>
              </Box>
              <Box sx={{ flex: '1 1 calc(25% - 16px)', minWidth: 200 }}>
                <Paper sx={{ p: 2, textAlign: 'center', height: '100%' }}>
                  <Typography variant="h4" color="primary" fontWeight="bold">
                    2
                  </Typography>
                  <Typography variant="body2">Importe dados GBM</Typography>
                </Paper>
              </Box>
              <Box sx={{ flex: '1 1 calc(25% - 16px)', minWidth: 200 }}>
                <Paper sx={{ p: 2, textAlign: 'center', height: '100%' }}>
                  <Typography variant="h4" color="primary" fontWeight="bold">
                    3
                  </Typography>
                  <Typography variant="body2">Analise insights</Typography>
                </Paper>
              </Box>
              <Box sx={{ flex: '1 1 calc(25% - 16px)', minWidth: 200 }}>
                <Paper sx={{ p: 2, textAlign: 'center', height: '100%' }}>
                  <Typography variant="h4" color="primary" fontWeight="bold">
                    4
                  </Typography>
                  <Typography variant="body2">Reduza custos!</Typography>
                </Paper>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Box>
    </Container>
  );
};
