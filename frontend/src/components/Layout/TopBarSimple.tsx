/**
 * Simple Top Bar - No MUI Version
 */
import React, { useState, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { useAppSelector } from '../../store';
import apiClient from '../../api/client';

export const TopBarSimple: React.FC = () => {
  const { user, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const [backendStatus, setBackendStatus] = useState<'online' | 'offline' | 'checking'>('checking');
  const activeAlarms = useAppSelector((state) => state.alarms.activeAlarms);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await apiClient.get('/api/health');
        const health = response.data as { status?: string };
        setBackendStatus(health?.status === 'healthy' ? 'online' : 'offline');
      } catch {
        setBackendStatus('offline');
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
      {/* Left: Title */}
      <div className="flex items-center gap-4">
        <h1 className="text-xl font-semibold text-gray-800">OptiFlow AI</h1>

        {/* Status indicator */}
        <div className="flex items-center gap-2">
          <span
            className={`w-2 h-2 rounded-full ${
              backendStatus === 'online' ? 'bg-green-500' :
              backendStatus === 'offline' ? 'bg-red-500' : 'bg-yellow-500'
            }`}
          />
          <span className="text-xs text-gray-500">
            {backendStatus === 'online' ? 'Online' :
             backendStatus === 'offline' ? 'Offline' : 'Checking...'}
          </span>
        </div>
      </div>

      {/* Right: User menu */}
      <div className="flex items-center gap-4">
        {/* Alarms badge */}
        {activeAlarms.length > 0 && (
          <span className="bg-red-500 text-white text-xs px-2 py-1 rounded-full">
            {activeAlarms.length} alarmes
          </span>
        )}

        {/* User dropdown */}
        <div className="relative">
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-100"
          >
            <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white font-medium">
              {user?.email?.[0]?.toUpperCase() || 'U'}
            </div>
            <span className="text-sm text-gray-700">{user?.email || 'User'}</span>
          </button>

          {menuOpen && (
            <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50">
              <button
                onClick={() => {
                  logout();
                  setMenuOpen(false);
                }}
                className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
              >
                Sair
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
