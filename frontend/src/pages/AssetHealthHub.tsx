/**
 * Asset Health Hub - Saúde de Assets Consolidado
 *
 * Combina:
 * - Asset Health Dashboard (overview de todos)
 * - Health Trends (análise detalhada em drawer)
 */

import React, { useState } from 'react';
import {
  Activity,
  X,
  BarChart3,
  AlertCircle,
} from 'lucide-react';
import { AssetHealthDashboard } from './AssetHealthDashboard';
import { HealthTrendsDrawer } from '../components/HealthTrendsDrawer';

export const AssetHealthHub: React.FC = () => {
  const [selectedAssetId, setSelectedAssetId] = useState<string | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const handleAssetSelect = (assetId: string) => {
    setSelectedAssetId(assetId);
    setDrawerOpen(true);
  };

  const handleCloseDrawer = () => {
    setDrawerOpen(false);
    // Keep selectedAssetId for a moment to allow smooth closing animation
    setTimeout(() => setSelectedAssetId(null), 300);
  };

  return (
    <div className="relative min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Main Dashboard */}
      <AssetHealthDashboard onAssetSelect={handleAssetSelect} />

      {/* Trends Drawer - Slides from right */}
      <div
        className={`
          fixed top-0 right-0 h-full w-full md:w-2/3 lg:w-1/2 xl:w-2/5
          bg-white dark:bg-gray-800 shadow-2xl
          transform transition-transform duration-300 ease-in-out z-50
          ${drawerOpen ? 'translate-x-0' : 'translate-x-full'}
        `}
      >
        {/* Drawer Header */}
        <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-between z-10">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Análise de Tendências
            </h2>
          </div>
          <button
            onClick={handleCloseDrawer}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            <X className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </button>
        </div>

        {/* Drawer Content */}
        <div className="h-[calc(100vh-73px)] overflow-y-auto">
          {selectedAssetId ? (
            <HealthTrendsDrawer assetId={selectedAssetId} />
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center text-gray-500 dark:text-gray-400">
                <Activity className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p>Selecione um asset para ver análise detalhada</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Backdrop overlay */}
      {drawerOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
          onClick={handleCloseDrawer}
        />
      )}
    </div>
  );
};

export default AssetHealthHub;
