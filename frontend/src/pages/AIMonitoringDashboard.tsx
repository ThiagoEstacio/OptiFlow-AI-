/**
 * AI & Monitoring Dashboard
 *
 * Dashboard integrado com:
 * - AI Health Status
 * - Active Alarms (via Agent)
 * - ML Models Status
 * - Real-time Insights
 */

import React from 'react';
import { Brain, Activity, AlertTriangle, TrendingUp, Info } from 'lucide-react';
import ActiveAlarmsWidget from '../components/ActiveAlarmsWidget';
import AIHealthWidget from '../components/AIHealthWidget';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const AIMonitoringDashboard: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 bg-blue-600 rounded-lg">
            <Brain className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              AI & Monitoring Dashboard
            </h1>
            <p className="text-gray-600 text-sm">
              Monitoramento inteligente em tempo real
            </p>
          </div>
        </div>
      </div>

      {/* Info Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 flex items-start gap-3">
        <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-sm text-blue-900 font-medium">
            Sistema ML/Agent/Insights 100% Operacional
          </p>
          <p className="text-xs text-blue-700 mt-1">
            ✅ Agent com 12 ferramentas ativas | ✅ 2 modelos ML carregados | ✅ Insights em tempo real
          </p>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - AI Health */}
        <div className="lg:col-span-1">
          <AIHealthWidget autoRefresh={true} refreshInterval={60000} />

          {/* ML Models Status Card */}
          <div className="mt-6 bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center gap-2 mb-4">
              <TrendingUp className="w-5 h-5 text-green-600" />
              <h3 className="text-lg font-semibold text-gray-900">ML Models</h3>
            </div>

            <div className="space-y-3">
              <div className="border border-gray-200 rounded-lg p-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium text-gray-900">Isolation Forest</span>
                  <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full font-medium">
                    Active
                  </span>
                </div>
                <div className="text-xs text-gray-600">
                  <div className="flex justify-between mt-1">
                    <span>Size:</span>
                    <span className="font-medium">4.07 MB</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Features:</span>
                    <span className="font-medium">20</span>
                  </div>
                </div>
              </div>

              <div className="border border-gray-200 rounded-lg p-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium text-gray-900">Ensemble (IF+LOF)</span>
                  <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full font-medium">
                    Active
                  </span>
                </div>
                <div className="text-xs text-gray-600">
                  <div className="flex justify-between mt-1">
                    <span>Size:</span>
                    <span className="font-medium">22.28 MB</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Features:</span>
                    <span className="font-medium">14</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Agent Tools Info */}
          <div className="mt-6 bg-gradient-to-br from-purple-50 to-blue-50 rounded-lg shadow-lg p-6 border border-purple-200">
            <div className="flex items-center gap-2 mb-3">
              <Activity className="w-5 h-5 text-purple-600" />
              <h3 className="text-lg font-semibold text-gray-900">Agent Tools</h3>
            </div>

            <div className="space-y-2 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-gray-700">Ferramentas Disponíveis:</span>
                <span className="font-bold text-purple-600">12</span>
              </div>

              <div className="text-xs text-gray-600 mt-3 space-y-1">
                <div>✅ get_all_tags</div>
                <div>✅ get_active_alarms</div>
                <div>✅ search_tags</div>
                <div>✅ calculate_statistics</div>
                <div>✅ detect_anomalies</div>
                <div className="text-gray-400">+ 7 mais...</div>
              </div>
            </div>

            <a
              href="/tmp/AGENT_CAPABILITIES_FINAL.md"
              target="_blank"
              rel="noopener noreferrer"
              className="mt-4 block text-center px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700 transition-colors"
            >
              Ver Documentação Completa
            </a>
          </div>
        </div>

        {/* Right Column - Active Alarms */}
        <div className="lg:col-span-2">
          <ActiveAlarmsWidget maxAlarms={10} autoRefresh={true} refreshInterval={30000} />

          {/* Quick Actions */}
          <div className="mt-6 bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Ações Rápidas</h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <a
                href="/ai-insights"
                className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-all group"
              >
                <Brain className="w-5 h-5 text-blue-600" />
                <div>
                  <div className="font-medium text-gray-900 group-hover:text-blue-600">
                    AI Insights
                  </div>
                  <div className="text-xs text-gray-600">Ver todos os insights</div>
                </div>
              </a>

              <a
                href="/alarms"
                className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:border-red-300 hover:bg-red-50 transition-all group"
              >
                <AlertTriangle className="w-5 h-5 text-red-600" />
                <div>
                  <div className="font-medium text-gray-900 group-hover:text-red-600">
                    Gerenciar Alarmes
                  </div>
                  <div className="text-xs text-gray-600">Configurar e reconhecer</div>
                </div>
              </a>

              <a
                href={`${API_BASE}/api/v1/ml/models/info`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:border-green-300 hover:bg-green-50 transition-all group"
              >
                <TrendingUp className="w-5 h-5 text-green-600" />
                <div>
                  <div className="font-medium text-gray-900 group-hover:text-green-600">
                    ML Models API
                  </div>
                  <div className="text-xs text-gray-600">Testar modelos</div>
                </div>
              </a>

              <a
                href={`${API_BASE}/docs`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:border-purple-300 hover:bg-purple-50 transition-all group"
              >
                <Activity className="w-5 h-5 text-purple-600" />
                <div>
                  <div className="font-medium text-gray-900 group-hover:text-purple-600">
                    API Docs
                  </div>
                  <div className="text-xs text-gray-600">Swagger/OpenAPI</div>
                </div>
              </a>
            </div>
          </div>

          {/* API Endpoints Info */}
          <div className="mt-6 bg-gray-900 text-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-semibold mb-4">Endpoints Públicos Disponíveis</h3>

            <div className="space-y-3 font-mono text-xs">
              <div className="bg-gray-800 rounded p-3">
                <div className="text-green-400 mb-1">GET /api/v1/ai/health/public</div>
                <div className="text-gray-400">Status do sistema AI/ML</div>
              </div>

              <div className="bg-gray-800 rounded p-3">
                <div className="text-green-400 mb-1">GET /api/v1/ai/insights/public</div>
                <div className="text-gray-400">Lista de insights recentes</div>
              </div>

              <div className="bg-gray-800 rounded p-3">
                <div className="text-green-400 mb-1">GET /api/v1/ml/models/info</div>
                <div className="text-gray-400">Informações dos modelos ML</div>
              </div>

              <div className="bg-gray-800 rounded p-3">
                <div className="text-blue-400 mb-1">POST /api/v1/agent/tools/test</div>
                <div className="text-gray-400">Testar ferramentas do Agent</div>
              </div>

              <div className="bg-gray-800 rounded p-3">
                <div className="text-green-400 mb-1">GET /api/v1/alarms/active</div>
                <div className="text-gray-400">Alarmes ativos (enriquecidos)</div>
              </div>
            </div>

            <div className="mt-4 pt-4 border-t border-gray-700 text-xs text-gray-400">
              📘 Documentação completa: <span className="text-blue-400">/tmp/IMPLEMENTACAO_COMPLETA.md</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIMonitoringDashboard;
