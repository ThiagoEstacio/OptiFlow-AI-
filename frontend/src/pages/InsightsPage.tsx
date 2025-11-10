/**
 * Insights Page
 * Dedicated page to view all AI-generated insights
 */

import React from 'react';
import { Breadcrumbs } from '../components/Breadcrumbs';
import { InsightsFeed } from '../components/InsightsFeed';
import { Sparkles } from 'lucide-react';

const InsightsPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <Breadcrumbs />

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-3 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg text-white">
              <Sparkles size={24} />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Insights do Autonomous Agent
              </h1>
              <p className="text-gray-600 mt-1">
                IA autônoma monitorando o processo 24/7 e gerando insights em tempo real
              </p>
            </div>
          </div>
        </div>

        {/* Info Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
            <div className="flex items-center gap-3">
              <span className="text-2xl">🔍</span>
              <div>
                <p className="text-sm text-gray-600">Anomalias</p>
                <p className="text-xs text-gray-500">Padrões incomuns detectados</p>
              </div>
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
            <div className="flex items-center gap-3">
              <span className="text-2xl">⚡</span>
              <div>
                <p className="text-sm text-gray-600">Otimizações</p>
                <p className="text-xs text-gray-500">Oportunidades de melhoria</p>
              </div>
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
            <div className="flex items-center gap-3">
              <span className="text-2xl">🔮</span>
              <div>
                <p className="text-sm text-gray-600">Previsões</p>
                <p className="text-xs text-gray-500">Tendências futuras</p>
              </div>
            </div>
          </div>
        </div>

        {/* Insights Feed */}
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
          <InsightsFeed
            compact={false}
            limit={50}
            autoRefresh={true}
            refreshInterval={60}
            showFilters={true}
          />
        </div>

        {/* How it Works */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="font-bold text-blue-900 mb-3 flex items-center gap-2">
            <span>🤖</span>
            Como Funciona o Autonomous Agent
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-blue-800">
            <div>
              <p className="font-medium mb-2">Monitoramento Contínuo:</p>
              <ul className="list-disc list-inside space-y-1 text-blue-700">
                <li>Analisa 60+ tags em tempo real</li>
                <li>Ciclos de análise a cada 60 segundos</li>
                <li>Detecta anomalias automaticamente</li>
              </ul>
            </div>
            <div>
              <p className="font-medium mb-2">Inteligência Proativa:</p>
              <ul className="list-disc list-inside space-y-1 text-blue-700">
                <li>Identifica oportunidades de otimização</li>
                <li>Prevê estados futuros</li>
                <li>Recomenda ações corretivas</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InsightsPage;
