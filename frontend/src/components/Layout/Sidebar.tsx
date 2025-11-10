/**
 * Sidebar Navigation
 */
import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAppSelector, useAppDispatch } from '../../store';
import { toggleSidebar } from '../../store/slices/uiSlice';

export const Sidebar: React.FC = () => {
  const sidebarOpen = useAppSelector((state) => state.ui.sidebarOpen);
  const dispatch = useAppDispatch();

  const navItems = [
    { path: '/', label: 'Dashboard', icon: '📊' },
    { path: '/dashboard-builder', label: 'Builder', icon: '🎨' },
    { path: '/analytics-hub', label: 'Centro de Análise', icon: '💡' },
    { path: '/asset-health-hub', label: 'Saúde de Assets', icon: '💚' },
    { path: '/chat', label: 'Assistente IA', icon: '💬' },
    { path: '/simulator', label: 'Simulador', icon: '⚙️' },
    { path: '/sites', label: 'Sites', icon: '🏭' },
    { path: '/gateways', label: 'Gateways', icon: '🌐' },
    { path: '/devices', label: 'Dispositivos', icon: '🔌' },
    { path: '/tags', label: 'Tags', icon: '🏷️' },
    { path: '/extended-tags', label: 'Tags PI AF', icon: '📐' },
    { path: '/alarms', label: 'Alarmes', icon: '🚨' },
    { path: '/admin', label: 'Admin', icon: '🔧' },
  ];

  return (
    <div
      className={`fixed top-0 left-0 h-full bg-gray-900 text-white transition-all duration-300 ${
        sidebarOpen ? 'w-64' : 'w-20'
      }`}
    >
      {/* Logo */}
      <div className="flex items-center justify-between p-4 border-b border-gray-800">
        {sidebarOpen && <span className="text-xl font-bold">OptiFlow AI</span>}
        <button
          onClick={() => dispatch(toggleSidebar())}
          className="p-2 rounded hover:bg-gray-800 transition-colors"
        >
          {sidebarOpen ? '◀' : '▶'}
        </button>
      </div>

      {/* Navigation */}
      <nav className="mt-4">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center px-4 py-3 hover:bg-gray-800 transition-colors ${
                isActive ? 'bg-blue-600 hover:bg-blue-700' : ''
              }`
            }
          >
            <span className="text-2xl">{item.icon}</span>
            {sidebarOpen && <span className="ml-3">{item.label}</span>}
          </NavLink>
        ))}
      </nav>
    </div>
  );
};
