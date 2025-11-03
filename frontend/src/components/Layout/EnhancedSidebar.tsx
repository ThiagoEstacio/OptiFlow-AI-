import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAppSelector, useAppDispatch } from '../../store';
import { toggleSidebar } from '../../store/slices/uiSlice';
import {
  Dashboard as DashboardIcon,
  BarChart as AnalyticsIcon,
  Favorite as HealthIcon,
  Chat as ChatIcon,
  Settings as SettingsIcon,
  Storage as DevicesIcon,
  Notifications as AlarmsIcon,
  Business as SitesIcon,
  Label as TagsIcon,
  Speed as SimulatorIcon,
  AdminPanelSettings as AdminIcon,
  Palette as BuilderIcon,
  CloudUpload as ImportIcon,
  Insights as InsightsIcon,
  TrendingUp as ExecutiveIcon,
  ShowChart as TrendsIcon,
  Menu as MenuIcon,
  ChevronLeft as CollapseIcon,
} from '@mui/icons-material';
import { Box, Divider, Typography, Collapse, List, ListItem, ListItemIcon, ListItemText, IconButton, Tooltip } from '@mui/material';

interface NavItem {
  path: string;
  label: string;
  icon: React.ReactNode;
  badge?: number;
  requiresSite?: boolean;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

export const EnhancedSidebar: React.FC = () => {
  const sidebarOpen = useAppSelector((state) => state.ui.sidebarOpen);
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const sites = useAppSelector((state) => state.sites.items);
  const [expandedSections, setExpandedSections] = useState<string[]>(['main', 'data', 'management']);

  // Get first site ID for dynamic routes
  const defaultSiteId = sites.length > 0 ? sites[0].id : 1;

  const navSections: NavSection[] = [
    {
      title: 'Principal',
      items: [
        { path: '/', label: 'Dashboard', icon: <DashboardIcon /> },
        { path: '/analytics-hub', label: 'Centro de Análise', icon: <AnalyticsIcon /> },
        { path: '/asset-health-hub', label: 'Saúde de Assets', icon: <HealthIcon /> },
        { path: '/chat', label: 'Assistente IA', icon: <ChatIcon /> },
      ],
    },
    {
      title: 'Dados GBM Logística',
      items: [
        { path: `/gbm-import/${defaultSiteId}`, label: 'Importar Dados', icon: <ImportIcon />, requiresSite: true },
        { path: `/gbm-insights/${defaultSiteId}`, label: 'Insights GBM', icon: <InsightsIcon />, requiresSite: true },
        { path: `/historical-trends/${defaultSiteId}`, label: 'Tendências Históricas', icon: <TrendsIcon />, requiresSite: true },
        { path: `/executive/${defaultSiteId}`, label: 'Dashboard Executivo', icon: <ExecutiveIcon />, requiresSite: true },
      ],
    },
    {
      title: 'Ferramentas',
      items: [
        { path: '/dashboard-builder', label: 'Construtor', icon: <BuilderIcon /> },
        { path: '/simulator', label: 'Simulador', icon: <SimulatorIcon /> },
      ],
    },
    {
      title: 'Gerenciamento',
      items: [
        { path: '/sites', label: 'Sites', icon: <SitesIcon /> },
        { path: '/devices', label: 'Dispositivos', icon: <DevicesIcon /> },
        { path: '/tags', label: 'Tags', icon: <TagsIcon /> },
        { path: '/alarms', label: 'Alarmes', icon: <AlarmsIcon />, badge: 0 },
      ],
    },
    {
      title: 'Sistema',
      items: [
        { path: '/admin', label: 'Admin', icon: <AdminIcon /> },
        { path: '/settings', label: 'Configurações', icon: <SettingsIcon /> },
      ],
    },
  ];

  const toggleSection = (title: string) => {
    setExpandedSections((prev) =>
      prev.includes(title) ? prev.filter((t) => t !== title) : [...prev, title]
    );
  };

  const handleNavClick = (item: NavItem) => {
    if (item.requiresSite && sites.length === 0) {
      // If no sites, maybe show a message or navigate to sites page
      return;
    }
    navigate(item.path);
  };

  return (
    <Box
      sx={{
        position: 'fixed',
        top: 0,
        left: 0,
        height: '100vh',
        width: sidebarOpen ? 280 : 72,
        bgcolor: 'grey.900',
        color: 'white',
        transition: 'width 0.3s ease',
        display: 'flex',
        flexDirection: 'column',
        overflowY: 'auto',
        overflowX: 'hidden',
        zIndex: 1200,
        boxShadow: 3,
        '&::-webkit-scrollbar': {
          width: '6px',
        },
        '&::-webkit-scrollbar-track': {
          bgcolor: 'grey.800',
        },
        '&::-webkit-scrollbar-thumb': {
          bgcolor: 'grey.600',
          borderRadius: '3px',
          '&:hover': {
            bgcolor: 'grey.500',
          },
        },
      }}
    >
      {/* Header */}
      <Box
        sx={{
          p: 2,
          borderBottom: '1px solid',
          borderColor: 'grey.800',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          minHeight: 64,
        }}
      >
        {sidebarOpen && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box
              sx={{
                width: 36,
                height: 36,
                borderRadius: 2,
                bgcolor: 'primary.main',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 'bold',
                fontSize: '1.2rem',
              }}
            >
              OF
            </Box>
            <Typography variant="h6" fontWeight="bold">
              OptiFlow AI
            </Typography>
          </Box>
        )}
        <IconButton
          onClick={() => dispatch(toggleSidebar())}
          size="small"
          sx={{
            color: 'white',
            '&:hover': { bgcolor: 'grey.800' },
          }}
        >
          {sidebarOpen ? <CollapseIcon /> : <MenuIcon />}
        </IconButton>
      </Box>

      {/* Navigation Sections */}
      <Box sx={{ flex: 1, py: 2 }}>
        {navSections.map((section) => (
          <Box key={section.title} sx={{ mb: 1 }}>
            {sidebarOpen && (
              <Box
                sx={{
                  px: 3,
                  py: 1,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  cursor: 'pointer',
                  '&:hover': {
                    bgcolor: 'grey.800',
                  },
                }}
                onClick={() => toggleSection(section.title)}
              >
                <Typography
                  variant="caption"
                  sx={{
                    color: 'grey.400',
                    fontWeight: 600,
                    letterSpacing: 0.5,
                    textTransform: 'uppercase',
                  }}
                >
                  {section.title}
                </Typography>
              </Box>
            )}

            <Collapse in={sidebarOpen || !sidebarOpen} timeout="auto">
              <List dense disablePadding>
                {section.items.map((item) => (
                  <Tooltip
                    key={item.path}
                    title={sidebarOpen ? '' : item.label}
                    placement="right"
                    arrow
                  >
                    <ListItem
                      button
                      component={NavLink}
                      to={item.path}
                      sx={{
                        px: sidebarOpen ? 3 : 2,
                        py: 1.5,
                        mx: 1,
                        my: 0.5,
                        borderRadius: 2,
                        transition: 'all 0.2s',
                        '&.active': {
                          bgcolor: 'primary.main',
                          '&:hover': {
                            bgcolor: 'primary.dark',
                          },
                        },
                        '&:hover': {
                          bgcolor: 'grey.800',
                        },
                        justifyContent: sidebarOpen ? 'flex-start' : 'center',
                      }}
                    >
                      <ListItemIcon
                        sx={{
                          color: 'inherit',
                          minWidth: sidebarOpen ? 40 : 'auto',
                        }}
                      >
                        {item.icon}
                      </ListItemIcon>
                      {sidebarOpen && (
                        <ListItemText
                          primary={item.label}
                          primaryTypographyProps={{
                            fontSize: '0.875rem',
                            fontWeight: 500,
                          }}
                        />
                      )}
                      {sidebarOpen && item.badge !== undefined && item.badge > 0 && (
                        <Box
                          sx={{
                            bgcolor: 'error.main',
                            color: 'white',
                            borderRadius: 10,
                            px: 1,
                            py: 0.5,
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            minWidth: 20,
                            textAlign: 'center',
                          }}
                        >
                          {item.badge}
                        </Box>
                      )}
                    </ListItem>
                  </Tooltip>
                ))}
              </List>
            </Collapse>
          </Box>
        ))}
      </Box>

      {/* Footer */}
      {sidebarOpen && (
        <Box
          sx={{
            p: 2,
            borderTop: '1px solid',
            borderColor: 'grey.800',
            bgcolor: 'grey.850',
          }}
        >
          <Typography variant="caption" sx={{ color: 'grey.500', display: 'block' }}>
            OptiFlow AI v2.0
          </Typography>
          <Typography variant="caption" sx={{ color: 'grey.600', display: 'block' }}>
            Terminal Portuário Inteligente
          </Typography>
        </Box>
      )}
    </Box>
  );
};
