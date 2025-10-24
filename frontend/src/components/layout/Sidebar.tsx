/**
 * Sidebar Navigation Component
 */
import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Activity,
  BarChart3,
  Download,
  MessageSquare,
  Settings,
  Database,
} from 'lucide-react';

const navItems = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/realtime', icon: Activity, label: 'Real-time Data' },
  { path: '/analytics', icon: BarChart3, label: 'Analytics' },
  { path: '/export', icon: Download, label: 'Export Data' },
  { path: '/annotations', icon: MessageSquare, label: 'Annotations' },
  { path: '/devices', icon: Database, label: 'Devices' },
  { path: '/settings', icon: Settings, label: 'Settings' },
];

export const Sidebar: React.FC = () => {
  return (
    <div className="w-64 bg-gray-900 min-h-screen flex flex-col">
      <div className="p-6">
        <h1 className="text-2xl font-bold text-white">OptiFlow AI</h1>
        <p className="text-sm text-gray-400 mt-1">Industrial IoT Platform</p>
      </div>

      <nav className="flex-1 px-4 py-6 space-y-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                }`
              }
            >
              <Icon className="w-5 h-5" />
              <span className="font-medium">{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      <div className="p-4 border-t border-gray-800">
        <div className="flex items-center space-x-3 text-gray-400 text-sm">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          <span>System Online</span>
        </div>
      </div>
    </div>
  );
};
