/**
 * Página de Insights de IA - OptiFlow
 *
 * Dashboard de análise inteligente em tempo real:
 * - Detecção de anomalias com IA
 * - Feed automatizado de insights
 * - Score de saúde do sistema
 * - Chat com ChatGPT para análises personalizadas
 */

import React, { useState, useEffect } from 'react';
import {
  Brain,
  Activity,
  TrendingUp,
  TrendingDown,
  AlertCircle,
  CheckCircle,
  Clock,
  Zap,
  BarChart3,
  RefreshCw,
  Download,
  MessageSquare,
  Sparkles,
  Send,
  Loader,
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Insight {
  type: string;
  severity: 'info' | 'warning' | 'critical';
  message: string;
  tag_id?: string;
  tag_name?: string;
  data?: any;
  ai_analysis?: string;
}

interface HealthScore {
  score: number;
  status: 'healthy' | 'degraded' | 'critical';
  anomaly_count: number;
  critical_insights: number;
  warning_insights: number;
  last_updated: string;
}

interface DashboardSummary {
  health_score: HealthScore;
  recent_insights: Insight[];
  anomalies_detected: number;
  tags_monitored: number;
  models_active: number;
  last_analysis: string | null;
}

export const AIInsightsPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [selectedSeverity, setSelectedSeverity] = useState<string>('all');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [chatMessage, setChatMessage] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [chatResponse, setChatResponse] = useState<string>('');
  const [showChat, setShowChat] = useState(false);

  // Buscar resumo do dashboard - USANDO ENDPOINT PÚBLICO ✨
  const fetchSummary = async () => {
    try {
      setLoading(true);
      // ✨ Tentar endpoint público primeiro (sem autenticação)
      let response = await fetch(`${API_BASE}/api/v1/ai/dashboard/summary/public`);

      if (!response.ok) {
        // Fallback para endpoint autenticado
        response = await fetch(`${API_BASE}/api/v1/ai/dashboard/summary`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          },
        });
      }

      if (response.ok) {
        const data = await response.json();
        setSummary(data);
        console.log('✅ AI Insights carregados:', data);
      } else {
        // Usar dados mock para demonstração
        console.warn('⚠️ Usando dados mock');
        setSummary(getMockSummary());
      }
    } catch (error) {
      console.error('❌ Erro ao buscar resumo AI:', error);
      setSummary(getMockSummary());
    } finally {
      setLoading(false);
    }
  };

  // Enviar mensagem para o ChatGPT
  const sendChatMessage = async () => {
    if (!chatMessage.trim()) return;

    try {
      setChatLoading(true);
      setChatResponse('');

      const response = await fetch(`${API_BASE}/api/v1/chat/conversations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          title: 'Análise de Insights',
        }),
      });

      if (!response.ok) throw new Error('Erro ao criar conversa');

      const conversation = await response.json();

      // Enviar mensagem
      const messageResponse = await fetch(
        `${API_BASE}/api/v1/chat/conversations/${conversation.id}/messages`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          },
          body: JSON.stringify({
            content: chatMessage,
            include_context: true,
          }),
        }
      );

      if (!messageResponse.ok) throw new Error('Erro ao enviar mensagem');

      const messageData = await messageResponse.json();
      setChatResponse(messageData.ai_response || 'Resposta não disponível');
      setChatMessage('');
    } catch (error) {
      console.error('Erro no chat:', error);
      setChatResponse(
        'Desculpe, não foi possível processar sua mensagem. Verifique se a API do ChatGPT está configurada corretamente.'
      );
    } finally {
      setChatLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, []);

  // Auto-refresh a cada 30 segundos
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchSummary();
    }, 30000);

    return () => clearInterval(interval);
  }, [autoRefresh]);

  // Filtrar insights por severidade
  const filteredInsights = summary?.recent_insights.filter((insight) => {
    if (selectedSeverity === 'all') return true;
    return insight.severity === selectedSeverity;
  }) || [];

  // Badge de severidade
  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'critical':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200">
            <AlertCircle className="w-3 h-3 mr-1" />
            Crítico
          </span>
        );
      case 'warning':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200">
            <AlertCircle className="w-3 h-3 mr-1" />
            Aviso
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200">
            <Sparkles className="w-3 h-3 mr-1" />
            Info
          </span>
        );
    }
  };

  // Cor do status de saúde
  const getHealthColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600 dark:text-green-400';
      case 'degraded':
        return 'text-yellow-600 dark:text-yellow-400';
      case 'critical':
        return 'text-red-600 dark:text-red-400';
      default:
        return 'text-gray-600 dark:text-gray-400';
    }
  };

  if (loading && !summary) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 text-blue-600 dark:text-blue-400 animate-spin mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Carregando Insights de IA...</p>
        </div>
      </div>
    );
  }

  const healthScore = summary?.health_score;

  return (
    <div className="space-y-6 p-6">
      {/* Cabeçalho */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-3 bg-purple-100 dark:bg-purple-900 rounded-lg">
            <Brain className="w-8 h-8 text-purple-600 dark:text-purple-400" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Insights de IA</h1>
            <p className="text-gray-600 dark:text-gray-400">
              Inteligência de processo em tempo real com detecção de anomalias
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowChat(!showChat)}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
              showChat
                ? 'bg-purple-600 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200'
            }`}
          >
            <MessageSquare className="w-4 h-4" />
            <span>Chat com IA</span>
          </button>

          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
              autoRefresh
                ? 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-200'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200'
            }`}
          >
            <RefreshCw className={`w-4 h-4 ${autoRefresh ? 'animate-spin' : ''}`} />
            <span>{autoRefresh ? 'Atualização Automática' : 'Auto-atualização OFF'}</span>
          </button>

          <button
            onClick={fetchSummary}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Atualizar</span>
          </button>
        </div>
      </div>

      {/* Chat com ChatGPT */}
      {showChat && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
            <Sparkles className="w-5 h-5 mr-2 text-purple-500" />
            Consultar ChatGPT sobre os Insights
          </h2>

          <div className="space-y-4">
            {chatResponse && (
              <div className="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-4">
                <p className="text-sm font-medium text-purple-900 dark:text-purple-100 mb-2">
                  Resposta da IA:
                </p>
                <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                  {chatResponse}
                </p>
              </div>
            )}

            <div className="flex space-x-2">
              <input
                type="text"
                value={chatMessage}
                onChange={(e) => setChatMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && sendChatMessage()}
                placeholder="Pergunte sobre os insights do sistema..."
                className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:text-white"
                disabled={chatLoading}
              />
              <button
                onClick={sendChatMessage}
                disabled={chatLoading || !chatMessage.trim()}
                className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
              >
                {chatLoading ? (
                  <>
                    <Loader className="w-4 h-4 animate-spin" />
                    <span>Processando...</span>
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4" />
                    <span>Enviar</span>
                  </>
                )}
              </button>
            </div>

            <div className="text-sm text-gray-500 dark:text-gray-400">
              <p>💡 Exemplos de perguntas:</p>
              <ul className="list-disc list-inside mt-1 space-y-1">
                <li>Quais são os problemas mais críticos no momento?</li>
                <li>Analise a tendência de temperatura dos motores</li>
                <li>O que pode estar causando o aumento de corrente em CORR01?</li>
                <li>Sugira ações preventivas baseadas nos insights</li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Card de Score de Saúde */}
      {healthScore && (
        <div className="bg-gradient-to-br from-purple-500 to-blue-600 dark:from-purple-700 dark:to-blue-800 rounded-xl shadow-lg p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold mb-2 flex items-center">
                <Activity className="w-5 h-5 mr-2" />
                Score de Saúde do Sistema
              </h2>
              <div className="flex items-baseline space-x-2">
                <span className="text-5xl font-bold">{healthScore.score.toFixed(0)}</span>
                <span className="text-2xl">/100</span>
              </div>
              <p className="text-purple-100 dark:text-purple-200 mt-2 capitalize">
                Status: {healthScore.status === 'healthy' ? 'Saudável' : healthScore.status === 'degraded' ? 'Degradado' : 'Crítico'}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4 text-right">
              <div className="bg-white/10 rounded-lg p-4">
                <div className="text-3xl font-bold">{healthScore.critical_insights}</div>
                <div className="text-sm text-purple-100 dark:text-purple-200">Críticos</div>
              </div>
              <div className="bg-white/10 rounded-lg p-4">
                <div className="text-3xl font-bold">{healthScore.warning_insights}</div>
                <div className="text-sm text-purple-100 dark:text-purple-200">Avisos</div>
              </div>
              <div className="bg-white/10 rounded-lg p-4">
                <div className="text-3xl font-bold">{summary?.tags_monitored || 0}</div>
                <div className="text-sm text-purple-100 dark:text-purple-200">Tags Monitoradas</div>
              </div>
              <div className="bg-white/10 rounded-lg p-4">
                <div className="text-3xl font-bold">{summary?.anomalies_detected || 0}</div>
                <div className="text-sm text-purple-100 dark:text-purple-200">Anomalias</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Estatísticas Rápidas */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Modelos Ativos</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {summary?.models_active || 0}
              </p>
            </div>
            <div className="p-3 bg-blue-100 dark:bg-blue-900 rounded-lg">
              <Brain className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Anomalias Detectadas</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {summary?.anomalies_detected || 0}
              </p>
            </div>
            <div className="p-3 bg-red-100 dark:bg-red-900 rounded-lg">
              <AlertCircle className="w-6 h-6 text-red-600 dark:text-red-400" />
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Tags Analisadas</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {summary?.tags_monitored || 0}
              </p>
            </div>
            <div className="p-3 bg-green-100 dark:bg-green-900 rounded-lg">
              <BarChart3 className="w-6 h-6 text-green-600 dark:text-green-400" />
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Última Análise</p>
              <p className="text-sm font-medium text-gray-900 dark:text-white mt-1">
                {summary?.last_analysis
                  ? new Date(summary.last_analysis).toLocaleTimeString('pt-BR')
                  : 'N/A'}
              </p>
            </div>
            <div className="p-3 bg-purple-100 dark:bg-purple-900 rounded-lg">
              <Clock className="w-6 h-6 text-purple-600 dark:text-purple-400" />
            </div>
          </div>
        </div>
      </div>

      {/* Feed de Insights */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
              <Zap className="w-5 h-5 mr-2 text-yellow-500" />
              Insights Recentes
            </h2>

            <div className="flex items-center space-x-2">
              <button
                onClick={() => setSelectedSeverity('all')}
                className={`px-3 py-1 rounded-md text-sm transition-colors ${
                  selectedSeverity === 'all'
                    ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-200'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                }`}
              >
                Todos
              </button>
              <button
                onClick={() => setSelectedSeverity('critical')}
                className={`px-3 py-1 rounded-md text-sm transition-colors ${
                  selectedSeverity === 'critical'
                    ? 'bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-200'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                }`}
              >
                Críticos
              </button>
              <button
                onClick={() => setSelectedSeverity('warning')}
                className={`px-3 py-1 rounded-md text-sm transition-colors ${
                  selectedSeverity === 'warning'
                    ? 'bg-yellow-100 dark:bg-yellow-900 text-yellow-700 dark:text-yellow-200'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                }`}
              >
                Avisos
              </button>
            </div>
          </div>
        </div>

        <div className="divide-y divide-gray-200 dark:divide-gray-700">
          {filteredInsights.length > 0 ? (
            filteredInsights.map((insight, idx) => (
              <div
                key={idx}
                className="px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      {getSeverityBadge(insight.severity)}
                      {insight.tag_name && (
                        <span className="text-sm font-medium text-gray-900 dark:text-white">
                          {insight.tag_name}
                        </span>
                      )}
                    </div>
                    <p className="text-gray-700 dark:text-gray-300">{insight.message}</p>
                  </div>
                  <button className="ml-4 text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 text-sm">
                    Ver Detalhes
                  </button>
                </div>
              </div>
            ))
          ) : (
            <div className="px-6 py-12 text-center">
              <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
              <p className="text-gray-600 dark:text-gray-400">
                {selectedSeverity === 'all'
                  ? 'Nenhum insight disponível no momento'
                  : `Nenhum insight ${selectedSeverity === 'critical' ? 'crítico' : 'de aviso'} no momento`}
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
                O sistema está operando dentro dos parâmetros normais
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Próximos Recursos - Fase 2 */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-gray-800 dark:to-gray-700 rounded-lg border-2 border-dashed border-blue-300 dark:border-blue-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2 flex items-center">
          <Sparkles className="w-5 h-5 mr-2 text-purple-500" />
          🚀 Em Breve - Fase 2
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-700 dark:text-gray-300">
          <div>
            <h4 className="font-semibold mb-1">Manutenção Preditiva</h4>
            <p>Previsão de falhas de equipamento e estimativa de vida útil</p>
          </div>
          <div>
            <h4 className="font-semibold mb-1">Otimização de Processo</h4>
            <p>Recomendações de setpoints otimizados por IA</p>
          </div>
          <div>
            <h4 className="font-semibold mb-1">Previsão de Demanda</h4>
            <p>Predição de produção e demanda energética</p>
          </div>
        </div>
      </div>
    </div>
  );
};

// Dados mock para demonstração
function getMockSummary(): DashboardSummary {
  return {
    health_score: {
      score: 87.5,
      status: 'healthy',
      anomaly_count: 2,
      critical_insights: 0,
      warning_insights: 3,
      last_updated: new Date().toISOString(),
    },
    recent_insights: [
      {
        type: 'trend',
        severity: 'warning',
        message: '📈 CORR01_CORRENTE está com tendência crescente (aumento de 12,5% ao longo do tempo)',
        tag_name: 'CORR01_CORRENTE',
      },
      {
        type: 'outlier',
        severity: 'warning',
        message: '⚠️ CORR01_TEMP_MOTOR tem 3 valores anômalos detectados (5,2% dos dados)',
        tag_name: 'CORR01_TEMP_MOTOR',
      },
      {
        type: 'baseline_comparison',
        severity: 'info',
        message: '✅ SLD01_VAZAO está dentro da faixa normal de operação',
        tag_name: 'SLD01_VAZAO',
      },
      {
        type: 'level_shift',
        severity: 'warning',
        message: '🔄 ELV01_CORRENTE aumentou 15,3% - possível mudança de setpoint ou alteração no processo',
        tag_name: 'ELV01_CORRENTE',
      },
      {
        type: 'trend',
        severity: 'info',
        message: '➡️ BAL01_PESO está estável',
        tag_name: 'BAL01_PESO',
      },
    ],
    anomalies_detected: 2,
    tags_monitored: 277,
    models_active: 0,
    last_analysis: new Date().toISOString(),
  };
}

export default AIInsightsPage;
