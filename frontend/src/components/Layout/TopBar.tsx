/**
 * Top Bar with User Menu
 */
import React, { useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { useAppSelector } from '../../store';

export const TopBar: React.FC = () => {
  const { user, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const activeAlarms = useAppSelector((state) => state.alarms.activeAlarms);

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="flex items-center justify-between px-6 py-4">
        {/* Left side - could add breadcrumbs here */}
        <div className="flex items-center space-x-4">
          <h2 className="text-xl font-semibold text-gray-800">SmartPort Platform</h2>
        </div>

        {/* Right side */}
        <div className="flex items-center space-x-4">
          {/* Alarms Badge */}
          {activeAlarms.length > 0 && (
            <div className="relative">
              <button className="p-2 text-gray-600 hover:text-gray-800 relative">
                <span className="text-2xl">🔔</span>
                <span className="absolute top-0 right-0 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                  {activeAlarms.length}
                </span>
              </button>
            </div>
          )}

          {/* User Menu */}
          <div className="relative">
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              className="flex items-center space-x-2 p-2 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white">
                {user?.full_name?.[0] || 'U'}
              </div>
              <span className="text-sm font-medium text-gray-700">{user?.full_name}</span>
              <span className="text-gray-400">▼</span>
            </button>

            {/* Dropdown Menu */}
            {menuOpen && (
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50">
                <div className="px-4 py-2 border-b border-gray-200">
                  <p className="text-sm font-medium text-gray-900">{user?.full_name}</p>
                  <p className="text-xs text-gray-500">{user?.email}</p>
                </div>
                <button
                  onClick={() => {
                    logout();
                    setMenuOpen(false);
                  }}
                  className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  Sign Out
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
