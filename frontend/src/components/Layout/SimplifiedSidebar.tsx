/**
 * Sidebar Navigation - Professional v4.0
 * =======================================
 *
 * Improvements:
 * - Lucide icons instead of emojis (ISA-101 compliance)
 * - Enhanced accessibility (focus-visible, aria-labels)
 * - Dynamic status indicator (ping backend)
 * - Mobile-responsive drawer
 * - Higher contrast for industrial environments
 */
import React, { useState, useEffect, useCallback } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useAppSelector, useAppDispatch } from '../../store';
import { toggleSidebar } from '../../store/slices/uiSlice';
import { alarmsApi } from '../../services/alarms.api';
import {
  LayoutDashboard,
  TrendingUp,
  ClipboardList,
  Wrench,
  Briefcase,
  Target,
  Brain,
  Factory,
  Zap,
  Ruler,
  FileText,
  Activity,
  History,
  Bell,
  ExternalLink,
  Settings,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  Wifi,
  WifiOff,
  X,
  Menu,
  Network,
} from 'lucide-react';

interface NavItem {
  path: string;
  label: string;
  icon: React.ReactNode;
  badge?: string | number;
  children?: NavItem[];
}

// Backend health check
const checkBackendHealth = async (): Promise<boolean> => {
  try {
    const response = await fetch('/api/health', {
      method: 'GET',
      signal: AbortSignal.timeout(3000)
    });
    return response.ok;
  } catch {
    return false;
  }
};

export const SimplifiedSidebar: React.FC = () => {
  const sidebarOpen = useAppSelector((state) => state.ui.sidebarOpen);
  const dispatch = useAppDispatch();
  const location = useLocation();
  const [expandedGroups, setExpandedGroups] = useState<string[]>([]);
  const [activeAlarmsCount, setActiveAlarmsCount] = useState<number>(0);
  const [isOnline, setIsOnline] = useState<boolean>(true);
  const [lastChecked, setLastChecked] = useState<Date>(new Date());
  const [mobileOpen, setMobileOpen] = useState(false);

  // Fetch active alarms count
  useEffect(() => {
    const fetchAlarmsCount = async () => {
      try {
        const alarms = await alarmsApi.getActiveAlarms();
        setActiveAlarmsCount(alarms.length);
      } catch (error) {
        console.error('Failed to fetch active alarms count:', error);
      }
    };

    fetchAlarmsCount();
    const interval = setInterval(fetchAlarmsCount, 30000);
    return () => clearInterval(interval);
  }, []);

  // Backend health check
  useEffect(() => {
    const checkHealth = async () => {
      const healthy = await checkBackendHealth();
      setIsOnline(healthy);
      setLastChecked(new Date());
    };

    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  // Close mobile menu on route change
  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  // Navigation structure with Lucide icons
  const navItems: NavItem[] = [
    {
      path: '/dashboard',
      label: 'Dashboard',
      icon: <LayoutDashboard className="w-5 h-5" />,
      children: [
        { path: '/dashboard', label: 'Operacional', icon: <TrendingUp className="w-4 h-4" /> },
        { path: '/dashboards', label: 'Meus Dashboards', icon: <ClipboardList className="w-4 h-4" /> },
        { path: '/dashboards/builder', label: 'Construtor', icon: <Wrench className="w-4 h-4" /> },
      ],
    },
    {
      path: '/executive',
      label: 'Executivo',
      icon: <Briefcase className="w-5 h-5" />,
      children: [
        { path: '/executive', label: 'Visão Geral', icon: <Target className="w-4 h-4" /> },
        { path: '/executive/analytics', label: 'Análises ML', icon: <Brain className="w-4 h-4" /> },
        { path: '/executive/oee', label: 'OEE', icon: <Factory className="w-4 h-4" /> },
        { path: '/executive/energy', label: 'Energia', icon: <Zap className="w-4 h-4" /> },
        { path: '/executive/quality', label: 'Qualidade (SPC)', icon: <Ruler className="w-4 h-4" /> },
        { path: '/executive/reports', label: 'Relatórios', icon: <FileText className="w-4 h-4" /> },
      ],
    },
    {
      path: '/monitoring',
      label: 'Monitoramento',
      icon: <Activity className="w-5 h-5" />,
      children: [
        { path: '/monitoring', label: 'Supervisão', icon: <Factory className="w-4 h-4" /> },
        { path: '/monitoring/history', label: 'Histórico', icon: <History className="w-4 h-4" /> },
      ],
    },
    {
      path: '/maintenance',
      label: 'Manutenção',
      icon: <Wrench className="w-5 h-5" />,
      children: [
        { path: '/maintenance', label: 'Saúde dos Ativos', icon: <Activity className="w-4 h-4" /> },
        { path: '/maintenance/kpis', label: 'KPIs (MTBF/MTTR)', icon: <TrendingUp className="w-4 h-4" /> },
        { path: '/maintenance/backlog', label: 'Backlog', icon: <ClipboardList className="w-4 h-4" /> },
        { path: '/maintenance/analysis', label: 'Análise de Falhas', icon: <Target className="w-4 h-4" /> },
      ],
    },
    {
      path: '/alarms',
      label: 'Alarmes',
      icon: <Bell className="w-5 h-5" />,
      badge: activeAlarmsCount > 0 ? activeAlarmsCount : undefined,
    },
    {
      path: '/assets',
      label: 'Asset Tree',
      icon: <Network className="w-5 h-5" />,
    },
  ];

  const toggleGroup = useCallback((groupPath: string) => {
    setExpandedGroups((prev) =>
      prev.includes(groupPath)
        ? prev.filter((p) => p !== groupPath)
        : [...prev, groupPath]
    );
  }, []);

  const isGroupActive = useCallback((item: NavItem): boolean => {
    if (location.pathname === item.path) return true;
    if (item.children) {
      return item.children.some((child) => location.pathname.startsWith(child.path));
    }
    return location.pathname.startsWith(item.path);
  }, [location.pathname]);

  const isGroupExpanded = useCallback((groupPath: string): boolean => {
    if (expandedGroups.includes(groupPath)) return true;

    const item = navItems.find(i => i.path === groupPath);
    if (item?.children) {
      return item.children.some(child =>
        location.pathname === child.path ||
        location.pathname.startsWith(child.path + '/')
      );
    }
    return false;
  }, [expandedGroups, location.pathname, navItems]);

  const formatLastChecked = () => {
    return lastChecked.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
  };

  // Sidebar content (shared between desktop and mobile)
  const SidebarContent = () => (
    <>
      {/* Header / Logo */}
      <div className="flex items-center justify-between p-4 border-b border-gray-700 bg-gray-900">
        {sidebarOpen && (
          <div className="flex items-center">
            <span className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
              OptiFlow AI
            </span>
          </div>
        )}
        <button
          onClick={() => dispatch(toggleSidebar())}
          className="p-2 rounded-lg hover:bg-gray-700 transition-colors text-gray-300 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
          aria-label={sidebarOpen ? 'Recolher menu' : 'Expandir menu'}
        >
          {sidebarOpen ? <ChevronLeft className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
        </button>
      </div>

      {/* Navigation Menu */}
      <nav className="mt-4 px-2 overflow-y-auto h-[calc(100vh-180px)]" role="navigation" aria-label="Menu principal">
        {navItems.map((item) => {
          const hasChildren = item.children && item.children.length > 0;
          const isActive = isGroupActive(item);
          const isExpanded = isGroupExpanded(item.path);

          return (
            <div key={item.path} className="mb-1">
              {/* Main nav item */}
              {hasChildren ? (
                <button
                  onClick={() => toggleGroup(item.path)}
                  className={`w-full flex items-center justify-between px-4 py-3 rounded-lg transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 ${
                    isActive
                      ? 'bg-blue-600 text-white shadow-lg'
                      : 'hover:bg-gray-700/50 text-gray-300 hover:text-white'
                  }`}
                  aria-expanded={isExpanded}
                  aria-controls={`submenu-${item.path.replace('/', '')}`}
                >
                  <div className="flex items-center">
                    <span aria-hidden="true">{item.icon}</span>
                    {sidebarOpen && (
                      <>
                        <span className="ml-3 font-medium">{item.label}</span>
                        {item.badge && (
                          <span
                            className="ml-2 px-2 py-0.5 text-xs font-bold bg-red-500 text-white rounded-full"
                            aria-label={`${item.badge} alarmes ativos`}
                          >
                            {item.badge}
                          </span>
                        )}
                      </>
                    )}
                  </div>
                  {sidebarOpen && (
                    <ChevronDown
                      className={`w-4 h-4 transform transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                      aria-hidden="true"
                    />
                  )}
                </button>
              ) : (
                <NavLink
                  to={item.path}
                  className={({ isActive: linkActive }) =>
                    `flex items-center px-4 py-3 rounded-lg transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 ${
                      linkActive || isActive
                        ? 'bg-blue-600 text-white shadow-lg'
                        : 'hover:bg-gray-700/50 text-gray-300 hover:text-white'
                    }`
                  }
                  title={!sidebarOpen ? item.label : undefined}
                  aria-label={item.label}
                >
                  <span aria-hidden="true">{item.icon}</span>
                  {sidebarOpen && (
                    <>
                      <span className="ml-3 font-medium">{item.label}</span>
                      {item.badge && (
                        <span
                          className="ml-2 px-2 py-0.5 text-xs font-bold bg-red-500 text-white rounded-full animate-pulse"
                          aria-label={`${item.badge} alarmes ativos`}
                        >
                          {item.badge}
                        </span>
                      )}
                    </>
                  )}
                </NavLink>
              )}

              {/* Children (submenu) */}
              {hasChildren && isExpanded && sidebarOpen && (
                <div
                  id={`submenu-${item.path.replace('/', '')}`}
                  className="ml-4 mt-1 space-y-1 border-l-2 border-gray-600 pl-2"
                  role="menu"
                >
                  {item.children!.map((child) => (
                    <NavLink
                      key={child.path}
                      to={child.path}
                      className={({ isActive: childActive }) =>
                        `flex items-center px-3 py-2 text-sm rounded-lg transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 ${
                          childActive
                            ? 'bg-blue-500/20 text-blue-300 border-l-2 border-blue-400 font-medium'
                            : 'hover:bg-gray-700/50 text-gray-300 hover:text-white'
                        }`
                      }
                      role="menuitem"
                    >
                      <span aria-hidden="true">{child.icon}</span>
                      <span className="ml-2">{child.label}</span>
                    </NavLink>
                  ))}
                </div>
              )}
            </div>
          );
        })}

        {/* Gateway Edge - External Link */}
        <div className="mt-4 pt-4 border-t border-gray-700">
          <a
            href="http://localhost:8080/ui/index.html"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center px-4 py-3 rounded-lg transition-all hover:bg-gray-700/50 text-gray-300 hover:text-white group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
            aria-label="Abrir Gateway Edge UI em nova aba"
          >
            <ExternalLink className="w-5 h-5" aria-hidden="true" />
            {sidebarOpen && (
              <>
                <span className="ml-3 font-medium">Gateway Edge</span>
                <span className="ml-auto text-xs text-gray-500 group-hover:text-gray-400" aria-hidden="true">↗</span>
              </>
            )}
          </a>
        </div>

        {/* Settings */}
        <div className="mt-2">
          <NavLink
            to="/settings"
            className={({ isActive }) =>
              `flex items-center px-4 py-3 rounded-lg transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 ${
                isActive
                  ? 'bg-gray-700 text-white'
                  : 'hover:bg-gray-700/50 text-gray-400 hover:text-white'
              }`
            }
            title={!sidebarOpen ? 'Configurações' : undefined}
            aria-label="Configurações"
          >
            <Settings className="w-5 h-5" aria-hidden="true" />
            {sidebarOpen && <span className="ml-3 font-medium">Configurações</span>}
          </NavLink>
        </div>
      </nav>

      {/* Footer / Status */}
      {sidebarOpen && (
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-700 bg-gray-900">
          <div className="text-xs text-gray-400 space-y-1.5">
            <div className="flex items-center justify-between">
              <span>Status:</span>
              <span className={`flex items-center ${isOnline ? 'text-green-400' : 'text-red-400'}`}>
                {isOnline ? (
                  <>
                    <Wifi className="w-3 h-3 mr-1" aria-hidden="true" />
                    <span className="w-2 h-2 bg-green-400 rounded-full mr-1 animate-pulse" aria-hidden="true"></span>
                    Online
                  </>
                ) : (
                  <>
                    <WifiOff className="w-3 h-3 mr-1" aria-hidden="true" />
                    Offline
                  </>
                )}
              </span>
            </div>
            <div className="flex items-center justify-between text-gray-500">
              <span>Última verificação:</span>
              <span>{formatLastChecked()}</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Versão:</span>
              <span className="text-gray-300">v4.0.0</span>
            </div>
          </div>
        </div>
      )}
    </>
  );

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={() => setMobileOpen(true)}
        className="fixed top-4 left-4 z-50 p-2 rounded-lg bg-gray-900 text-white shadow-lg md:hidden focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
        aria-label="Abrir menu"
      >
        <Menu className="w-6 h-6" />
      </button>

      {/* Mobile Overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={() => setMobileOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Mobile Sidebar */}
      <div
        className={`fixed top-0 left-0 h-full w-64 bg-gradient-to-b from-gray-900 to-gray-800 text-white shadow-2xl z-50 transform transition-transform duration-300 md:hidden ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <button
          onClick={() => setMobileOpen(false)}
          className="absolute top-4 right-4 p-2 rounded-lg hover:bg-gray-700 text-gray-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
          aria-label="Fechar menu"
        >
          <X className="w-5 h-5" />
        </button>
        <SidebarContent />
      </div>

      {/* Desktop Sidebar */}
      <div
        className={`hidden md:block fixed top-0 left-0 h-full bg-gradient-to-b from-gray-900 to-gray-800 text-white transition-all duration-300 shadow-2xl z-40 ${
          sidebarOpen ? 'w-64' : 'w-20'
        }`}
      >
        <SidebarContent />
      </div>
    </>
  );
};
