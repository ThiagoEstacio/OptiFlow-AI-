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
    { path: '/sites', label: 'Sites', icon: '🏭' },
    { path: '/devices', label: 'Devices', icon: '🔌' },
    { path: '/tags', label: 'Tags', icon: '🏷️' },
    { path: '/alarms', label: 'Alarms', icon: '🚨' },
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
