/**
 * Analytics Hub - Centro de Análise Consolidado
 *
 * Combina:
 * - AI Insights (insights automáticos)
 * - Analytics (query builder)
 * - Anomaly Detection (detecção centralizada)
 */

import React, { useState } from 'react';
import {
  Sparkles,
  Search,
  AlertTriangle,
} from 'lucide-react';
import { AIInsightsPage } from './AIInsightsPage';
import { AnalyticsPage } from './AnalyticsPage';

type TabType = 'insights' | 'analytics' | 'anomalies';

export const AnalyticsHub: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('insights');

  const tabs = [
    {
      id: 'insights' as TabType,
      label: 'Feed de Insights',
      icon: Sparkles,
      description: 'Insights automáticos gerados pela IA',
    },
    {
      id: 'analytics' as TabType,
      label: 'Análise de Tags',
      icon: Search,
      description: 'Query builder para análise exploratória',
    },
    {
      id: 'anomalies' as TabType,
      label: 'Anomalias',
      icon: AlertTriangle,
      description: 'Central de detecção de anomalias',
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header with Tabs */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-10">
        <div className="px-6 py-4">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            Centro de Análise
          </h1>

          {/* Tab Navigation */}
          <div className="flex space-x-1 bg-gray-100 dark:bg-gray-700 p-1 rounded-lg">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;

              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-md
                    font-medium transition-all duration-200
                    ${isActive
                      ? 'bg-white dark:bg-gray-800 text-blue-600 dark:text-blue-400 shadow-sm'
                      : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                    }
                  `}
                  title={tab.description}
                >
                  <Icon className="w-5 h-5" />
                  <span className="hidden sm:inline">{tab.label}</span>
                </button>
              );
            })}
          </div>

          {/* Tab Description */}
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-3">
            {tabs.find(t => t.id === activeTab)?.description}
          </p>
        </div>
      </div>

      {/* Tab Content */}
      <div className="transition-opacity duration-200">
        {activeTab === 'insights' && <AIInsightsPage />}
        {activeTab === 'analytics' && <AnalyticsPage />}
        {activeTab === 'anomalies' && <AnomaliesView />}
      </div>
    </div>
  );
};

/**
 * Anomalies View - Central de Anomalias
 */
const AnomaliesView: React.FC = () => {
  return (
    <div className="p-6">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-8">
        <div className="text-center">
          <AlertTriangle className="w-16 h-16 mx-auto mb-4 text-yellow-500 dark:text-yellow-400 opacity-50" />
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
            Central de Anomalias
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Visualização consolidada de todas as anomalias detectadas no sistema
          </p>

          {/* Feature sections */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8 text-left">
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <h3 className="font-medium text-gray-900 dark:text-white mb-2">
                Anomalias de Tags
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Detectadas pelo sistema de análise de time-series
              </p>
            </div>

            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <h3 className="font-medium text-gray-900 dark:text-white mb-2">
                Anomalias de Assets
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Desvios estatísticos na saúde dos assets
              </p>
            </div>

            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <h3 className="font-medium text-gray-900 dark:text-white mb-2">
                Insights de IA
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Padrões incomuns identificados pela IA
              </p>
            </div>
          </div>

          <div className="mt-8 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
            <p className="text-sm text-blue-800 dark:text-blue-200">
              <strong>💡 Em Desenvolvimento:</strong> Esta central consolidará todas as anomalias
              detectadas nos diferentes módulos do sistema em uma única visualização integrada.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsHub;
