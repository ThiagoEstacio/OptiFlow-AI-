/**
 * 🎯 Sidebar Navigation - Estrutura Profissional v3.0
 * ====================================================
 *
 * Arquitetura limpa e intuitiva:
 * 1. Dashboard - Visão operacional e KPIs
 * 2. Executivo - Relatórios, ML e insights gerenciais
 * 3. Monitoramento - Supervisão tempo real
 * 4. Alarmes - Central unificada
 *
 * + Configurações
 * + AI Assistant (FloatingChat disponível em todas telas)
 */
import React, { useState, useEffect } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useAppSelector, useAppDispatch } from '../../store';
import { toggleSidebar } from '../../store/slices/uiSlice';
import { alarmsApi } from '../../services/alarms.api';

interface NavItem {
  path: string;
  label: string;
  icon: string;
  badge?: string | number;
  children?: NavItem[];
}

export const SimplifiedSidebar: React.FC = () => {
  const sidebarOpen = useAppSelector((state) => state.ui.sidebarOpen);
  const dispatch = useAppDispatch();
  const location = useLocation();
  const [expandedGroups, setExpandedGroups] = useState<string[]>([]);
  const [activeAlarmsCount, setActiveAlarmsCount] = useState<number>(0);

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

  // ========================================
  // 📋 ESTRUTURA PROFISSIONAL v3.0
  // ========================================
  const navItems: NavItem[] = [
    {
      path: '/dashboard',
      label: 'Dashboard',
      icon: '📊',
      children: [
        { path: '/dashboard', label: 'Operacional', icon: '📈' },
        { path: '/dashboards', label: 'Meus Dashboards', icon: '📋' },
        { path: '/dashboards/builder', label: 'Construtor', icon: '🛠️' },
      ],
    },
    {
      path: '/executive',
      label: 'Executivo',
      icon: '👔',
      children: [
        { path: '/executive', label: 'Visão Geral', icon: '🎯' },
        { path: '/executive/analytics', label: 'Análises ML', icon: '🧠' },
        { path: '/executive/oee', label: 'OEE', icon: '🏭' },
        { path: '/executive/energy', label: 'Energia', icon: '⚡' },
        { path: '/executive/quality', label: 'Qualidade (SPC)', icon: '📏' },
        { path: '/executive/reports', label: 'Relatórios', icon: '📄' },
      ],
    },
    {
      path: '/monitoring',
      label: 'Monitoramento',
      icon: '⚡',
      children: [
        { path: '/monitoring', label: 'Supervisão', icon: '🏭' },
        { path: '/monitoring/trends', label: 'Tendências', icon: '📉' },
        { path: '/monitoring/history', label: 'Histórico', icon: '📊' },
      ],
    },
    {
      path: '/alarms',
      label: 'Alarmes',
      icon: '🚨',
      badge: activeAlarmsCount > 0 ? activeAlarmsCount : undefined,
    },
  ];

  const toggleGroup = (groupPath: string) => {
    setExpandedGroups((prev) =>
      prev.includes(groupPath)
        ? prev.filter((p) => p !== groupPath)
        : [...prev, groupPath]
    );
  };

  const isGroupActive = (item: NavItem): boolean => {
    if (location.pathname === item.path) return true;
    if (item.children) {
      return item.children.some((child) => location.pathname.startsWith(child.path));
    }
    return location.pathname.startsWith(item.path);
  };

  const isGroupExpanded = (groupPath: string): boolean => {
    if (expandedGroups.includes(groupPath)) return true;

    const item = navItems.find(i => i.path === groupPath);
    if (item?.children) {
      return item.children.some(child => location.pathname === child.path || location.pathname.startsWith(child.path + '/'));
    }
    return false;
  };

  return (
    <div
      className={`fixed top-0 left-0 h-full bg-gradient-to-b from-gray-900 to-gray-800 text-white transition-all duration-300 shadow-2xl z-40 ${
        sidebarOpen ? 'w-64' : 'w-20'
      }`}
    >
      {/* ========================================
          HEADER / LOGO
          ======================================== */}
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
          className="p-2 rounded-lg hover:bg-gray-700 transition-colors text-gray-300 hover:text-white"
          title={sidebarOpen ? 'Recolher menu' : 'Expandir menu'}
        >
          {sidebarOpen ? '◀' : '▶'}
        </button>
      </div>

      {/* ========================================
          NAVIGATION MENU
          ======================================== */}
      <nav className="mt-4 px-2 overflow-y-auto h-[calc(100vh-180px)]">
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
                  className={`w-full flex items-center justify-between px-4 py-3 rounded-lg transition-all ${
                    isActive
                      ? 'bg-blue-600 text-white shadow-lg'
                      : 'hover:bg-gray-700/50 text-gray-300'
                  }`}
                >
                  <div className="flex items-center">
                    <span className="text-2xl">{item.icon}</span>
                    {sidebarOpen && (
                      <>
                        <span className="ml-3 font-medium">{item.label}</span>
                        {item.badge && (
                          <span className="ml-2 px-2 py-0.5 text-xs font-bold bg-red-500 text-white rounded-full">
                            {item.badge}
                          </span>
                        )}
                      </>
                    )}
                  </div>
                  {sidebarOpen && (
                    <span className={`transform transition-transform ${isExpanded ? 'rotate-90' : ''}`}>
                      ▶
                    </span>
                  )}
                </button>
              ) : (
                <NavLink
                  to={item.path}
                  className={({ isActive: linkActive }) =>
                    `flex items-center px-4 py-3 rounded-lg transition-all ${
                      linkActive || isActive
                        ? 'bg-blue-600 text-white shadow-lg'
                        : 'hover:bg-gray-700/50 text-gray-300'
                    }`
                  }
                  title={!sidebarOpen ? item.label : undefined}
                >
                  <span className="text-2xl">{item.icon}</span>
                  {sidebarOpen && (
                    <>
                      <span className="ml-3 font-medium">{item.label}</span>
                      {item.badge && (
                        <span className="ml-2 px-2 py-0.5 text-xs font-bold bg-red-500 text-white rounded-full">
                          {item.badge}
                        </span>
                      )}
                    </>
                  )}
                </NavLink>
              )}

              {/* Children (submenu) */}
              {hasChildren && isExpanded && sidebarOpen && (
                <div className="ml-4 mt-1 space-y-1 border-l-2 border-gray-700 pl-2">
                  {item.children!.map((child) => (
                    <NavLink
                      key={child.path}
                      to={child.path}
                      className={({ isActive: childActive }) =>
                        `flex items-center px-3 py-2 text-sm rounded-lg transition-all ${
                          childActive
                            ? 'bg-blue-500/20 text-blue-300 border-l-2 border-blue-400'
                            : 'hover:bg-gray-700/30 text-gray-400 hover:text-gray-200'
                        }`
                      }
                    >
                      <span className="text-lg">{child.icon}</span>
                      <span className="ml-2">{child.label}</span>
                    </NavLink>
                  ))}
                </div>
              )}
            </div>
          );
        })}

        {/* ========================================
            🔗 GATEWAY EDGE - EXTERNAL LINK
            ======================================== */}
        <div className="mt-4 pt-4 border-t border-gray-700">
          <a
            href="http://localhost:8080/ui/index.html"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center px-4 py-3 rounded-lg transition-all hover:bg-gray-700/50 text-gray-300 hover:text-white group"
            title="Abrir Gateway Edge UI (nova aba)"
          >
            <span className="text-2xl">🔗</span>
            {sidebarOpen && (
              <>
                <span className="ml-3 font-medium">Gateway Edge</span>
                <span className="ml-auto text-xs text-gray-500 group-hover:text-gray-400">↗</span>
              </>
            )}
          </a>
        </div>

        {/* ========================================
            ⚙️ CONFIGURAÇÕES
            ======================================== */}
        <div className="mt-2">
          <NavLink
            to="/settings"
            className={({ isActive }) =>
              `flex items-center px-4 py-3 rounded-lg transition-all ${
                isActive
                  ? 'bg-gray-700 text-white'
                  : 'hover:bg-gray-700/50 text-gray-400 hover:text-gray-200'
              }`
            }
            title={!sidebarOpen ? 'Configurações' : undefined}
          >
            <span className="text-2xl">⚙️</span>
            {sidebarOpen && <span className="ml-3 font-medium">Configurações</span>}
          </NavLink>
        </div>
      </nav>

      {/* ========================================
          FOOTER / STATUS
          ======================================== */}
      {sidebarOpen && (
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-700 bg-gray-900">
          <div className="text-xs text-gray-400 space-y-1">
            <div className="flex items-center justify-between">
              <span>Status:</span>
              <span className="flex items-center text-green-400">
                <span className="w-2 h-2 bg-green-400 rounded-full mr-1 animate-pulse"></span>
                Online
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span>Version:</span>
              <span className="text-gray-300">v3.0.0</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
