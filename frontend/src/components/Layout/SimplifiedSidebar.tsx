/**
 * 🎯 Sidebar Navigation - Simplificado e Focado
 * ==============================================
 * 
 * 5 módulos principais + subitens organizados
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
    // Refresh every 30 seconds
    const interval = setInterval(fetchAlarmsCount, 30000);
    return () => clearInterval(interval);
  }, []);

  // ========================================
  // 📋 ESTRUTURA DE NAVEGAÇÃO SIMPLIFICADA
  // ========================================
  const navItems: NavItem[] = [
    {
      path: '/dashboard',
      label: 'Dashboard',
      icon: '📊',
    },
    {
      path: '/realtime',
      label: 'Real-Time',
      icon: '⚡',
      children: [
        { path: '/realtime', label: 'Overview', icon: '📈' },
        { path: '/realtime/tags', label: 'Tags', icon: '🏷️' },
      ],
    },
    {
      path: '/alarms',
      label: 'Alarmes',
      icon: '🚨',
      badge: activeAlarmsCount > 0 ? activeAlarmsCount : undefined, // Dynamic badge
      children: [
        { path: '/alarms', label: 'Overview', icon: '📋' },
        { path: '/alarms/active', label: 'Ativos', icon: '🔴' },
        { path: '/alarms/history', label: 'Histórico', icon: '📜' },
      ],
    },
    {
      path: '/analytics',
      label: 'Analytics',
      icon: '🤖',
      children: [
        { path: '/analytics', label: 'Insights', icon: '💡' },
        { path: '/analytics/ml-insights', label: 'ML Models', icon: '🧠' },
        { path: '/analytics/chat', label: 'AI Assistant', icon: '💬' },
      ],
    },
    {
      path: '/settings',
      label: 'Settings',
      icon: '⚙️',
      children: [
        { path: '/settings', label: 'Geral', icon: '🔧' },
        { path: '/settings/devices', label: 'Devices', icon: '🔌' },
        { path: '/settings/tags', label: 'Tag Config', icon: '🏷️' },
        { path: '/settings/gateways', label: 'Gateways', icon: '🌐' },
        { path: '/settings/users', label: 'Users', icon: '👥' },
      ],
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
    return false;
  };

  const isGroupExpanded = (groupPath: string): boolean => {
    // Only expand groups when explicitly toggled or when a child route is active
    if (expandedGroups.includes(groupPath)) return true;
    
    const item = navItems.find(i => i.path === groupPath);
    if (item?.children) {
      return item.children.some(child => location.pathname === child.path);
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
      <nav className="mt-4 px-2 overflow-y-auto h-[calc(100vh-80px)]">
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
                  className={({ isActive }) =>
                    `flex items-center px-4 py-3 rounded-lg transition-all ${
                      isActive
                        ? 'bg-blue-600 text-white shadow-lg'
                        : 'hover:bg-gray-700/50 text-gray-300'
                    }`
                  }
                  title={!sidebarOpen ? item.label : undefined}
                >
                  <span className="text-2xl">{item.icon}</span>
                  {sidebarOpen && <span className="ml-3 font-medium">{item.label}</span>}
                </NavLink>
              )}

              {/* Children (submenu) */}
              {hasChildren && isExpanded && sidebarOpen && (
                <div className="ml-4 mt-1 space-y-1 border-l-2 border-gray-700 pl-2">
                  {item.children!.map((child) => (
                    <NavLink
                      key={child.path}
                      to={child.path}
                      className={({ isActive }) =>
                        `flex items-center px-3 py-2 text-sm rounded-lg transition-all ${
                          isActive
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
              <span className="text-gray-300">v2.0.0</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
