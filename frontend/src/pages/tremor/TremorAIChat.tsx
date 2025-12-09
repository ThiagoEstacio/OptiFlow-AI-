/**
 * AI Chat Page - Full Screen Chat Interface
 * ==========================================
 *
 * Dedicated AI chat page for in-depth conversations with the OptiFlow AI assistant.
 * Features:
 * - Full conversation history
 * - Context-aware responses (knows about tags, alarms, OEE, etc.)
 * - Quick action suggestions
 * - Export conversation
 * - Integration with real-time data
 */
import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  Card,
  Title,
  Text,
  Button,
  Badge,
  Flex,
  Grid,
} from '@tremor/react';
import {
  Send,
  Bot,
  User,
  Lightbulb,
  TrendingUp,
  AlertTriangle,
  Zap,
  Wrench,
  Factory,
  Loader2,
  Trash2,
  Download,
  RefreshCw,
  Clock,
  Brain,
  BarChart3,
  Activity,
  ThermometerSun,
  Gauge,
} from 'lucide-react';
import apiClient from '../../api/client';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  toolsUsed?: string[];
}

interface QuickAction {
  label: string;
  icon: React.ReactNode;
  prompt: string;
  category: string;
}

const quickActions: QuickAction[] = [
  {
    label: 'Resumo do Dia',
    icon: <TrendingUp className="w-4 h-4" />,
    prompt: 'Faça um resumo completo das operações de hoje, incluindo OEE, alarmes ativos e indicadores de produção.',
    category: 'Operações',
  },
  {
    label: 'Alarmes Críticos',
    icon: <AlertTriangle className="w-4 h-4" />,
    prompt: 'Quais são os alarmes críticos ativos no momento? Analise as causas prováveis e sugira ações corretivas.',
    category: 'Alarmes',
  },
  {
    label: 'Otimizar Energia',
    icon: <Zap className="w-4 h-4" />,
    prompt: 'Analise o consumo de energia das últimas 24 horas e sugira otimizações para reduzir custos operacionais.',
    category: 'Energia',
  },
  {
    label: 'Status OEE',
    icon: <Factory className="w-4 h-4" />,
    prompt: 'Qual o OEE atual de todos os equipamentos? Identifique os gargalos e sugira melhorias.',
    category: 'OEE',
  },
  {
    label: 'Manutenção Preditiva',
    icon: <Wrench className="w-4 h-4" />,
    prompt: 'Quais equipamentos estão com risco de falha? Analise os indicadores de saúde e sugira manutenções preventivas.',
    category: 'Manutenção',
  },
  {
    label: 'Insights ML',
    icon: <Brain className="w-4 h-4" />,
    prompt: 'Quais são os principais insights de machine learning detectados? Há anomalias ou padrões importantes?',
    category: 'Analytics',
  },
  {
    label: 'Análise de Tendências',
    icon: <BarChart3 className="w-4 h-4" />,
    prompt: 'Analise as tendências dos principais sensores nas últimas 24 horas. Há desvios significativos?',
    category: 'Monitoramento',
  },
  {
    label: 'Temperatura Crítica',
    icon: <ThermometerSun className="w-4 h-4" />,
    prompt: 'Quais são as temperaturas atuais dos equipamentos críticos? Alguma está fora dos limites?',
    category: 'Sensores',
  },
];

const TremorAIChat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: `Olá! Sou o **Assistente AI do OptiFlow** - seu analista sênior de PCO, PCM e Qualidade.

Posso ajudar você com:
- **Análise de dados em tempo real** (OEE, alarmes, tendências)
- **Diagnósticos e recomendações** baseadas em dados
- **Manutenção preditiva** e saúde dos ativos
- **Insights de Machine Learning**
- **Relatórios e estatísticas**

Use as sugestões rápidas abaixo ou faça sua pergunta!`,
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => `chat-${Date.now()}`);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const handleSend = async (messageText?: string) => {
    const text = messageText || input.trim();
    if (!text || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await apiClient.post('/api/v1/agent/dashboard/chat', {
        message: text,
        session_id: sessionId,
        context: {
          page: 'ai-chat',
          timestamp: new Date().toISOString(),
        },
      });

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.data.response || 'Desculpe, não consegui processar sua solicitação.',
        timestamp: new Date(),
        toolsUsed: response.data.tools_used,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error calling AI:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Desculpe, ocorreu um erro ao processar sua solicitação. Por favor, tente novamente.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const clearChat = () => {
    setMessages([
      {
        id: Date.now().toString(),
        role: 'assistant',
        content: 'Conversa limpa. Como posso ajudar?',
        timestamp: new Date(),
      },
    ]);
  };

  const exportChat = () => {
    const chatContent = messages
      .map((m) => `[${m.timestamp.toLocaleTimeString()}] ${m.role === 'user' ? 'Você' : 'AI'}: ${m.content}`)
      .join('\n\n');

    const blob = new Blob([chatContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `optiflow-chat-${new Date().toISOString().split('T')[0]}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const formatMessage = (content: string) => {
    // Simple markdown-like formatting
    return content
      .split('\n')
      .map((line, i) => {
        // Bold
        line = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        // Headers
        if (line.startsWith('## ')) {
          return `<h3 class="text-lg font-semibold mt-3 mb-1">${line.slice(3)}</h3>`;
        }
        if (line.startsWith('# ')) {
          return `<h2 class="text-xl font-bold mt-4 mb-2">${line.slice(2)}</h2>`;
        }
        // List items
        if (line.startsWith('- ')) {
          return `<li class="ml-4">${line.slice(2)}</li>`;
        }
        // Numbers
        if (/^\d+\)/.test(line)) {
          return `<li class="ml-4">${line}</li>`;
        }
        return line ? `<p class="mb-1">${line}</p>` : '<br/>';
      })
      .join('');
  };

  return (
    <div className="h-[calc(100vh-120px)] flex flex-col">
      {/* Header */}
      <div className="mb-4">
        <Flex justifyContent="between" alignItems="center">
          <div>
            <Title className="flex items-center gap-2">
              <Brain className="w-6 h-6 text-blue-600" />
              Assistente AI OptiFlow
            </Title>
            <Text className="text-gray-500">
              Analista sênior de PCO, PCM e Qualidade - Powered by Ollama
            </Text>
          </div>
          <Flex className="gap-2">
            <Button
              size="xs"
              variant="secondary"
              icon={Download}
              onClick={exportChat}
            >
              Exportar
            </Button>
            <Button
              size="xs"
              variant="secondary"
              icon={Trash2}
              onClick={clearChat}
              color="red"
            >
              Limpar
            </Button>
          </Flex>
        </Flex>
      </div>

      {/* Main Content */}
      <Grid numItems={1} numItemsLg={4} className="gap-4 flex-1 min-h-0">
        {/* Quick Actions - Left Panel */}
        <Card className="lg:col-span-1 overflow-y-auto">
          <Title className="text-sm mb-3">Sugestões Rápidas</Title>
          <div className="space-y-2">
            {quickActions.map((action, index) => (
              <button
                key={index}
                onClick={() => handleSend(action.prompt)}
                disabled={isLoading}
                className="w-full p-2 text-left rounded-lg border border-gray-200 hover:bg-blue-50 hover:border-blue-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Flex justifyContent="start" className="gap-2">
                  <span className="text-blue-600">{action.icon}</span>
                  <div>
                    <Text className="font-medium text-sm">{action.label}</Text>
                    <Text className="text-xs text-gray-400">{action.category}</Text>
                  </div>
                </Flex>
              </button>
            ))}
          </div>
        </Card>

        {/* Chat Area - Main Panel */}
        <Card className="lg:col-span-3 flex flex-col min-h-0">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto mb-4 space-y-4 pr-2">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-3 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
              >
                {/* Avatar */}
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                    message.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gradient-to-br from-purple-500 to-blue-600 text-white'
                  }`}
                >
                  {message.role === 'user' ? (
                    <User className="w-4 h-4" />
                  ) : (
                    <Bot className="w-4 h-4" />
                  )}
                </div>

                {/* Message Content */}
                <div
                  className={`max-w-[80%] rounded-lg p-3 ${
                    message.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  <div
                    className="text-sm prose prose-sm max-w-none"
                    dangerouslySetInnerHTML={{ __html: formatMessage(message.content) }}
                  />
                  <div className="flex items-center gap-2 mt-2">
                    <Clock className="w-3 h-3 opacity-50" />
                    <span className="text-xs opacity-50">
                      {message.timestamp.toLocaleTimeString()}
                    </span>
                    {message.toolsUsed && message.toolsUsed.length > 0 && (
                      <Badge size="xs" color="purple">
                        {message.toolsUsed.length} tools
                      </Badge>
                    )}
                  </div>
                </div>
              </div>
            ))}

            {/* Loading indicator */}
            {isLoading && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-blue-600 flex items-center justify-center">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div className="bg-gray-100 rounded-lg p-3 flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                  <span className="text-sm text-gray-600">Analisando dados...</span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="border-t pt-4">
            <Flex className="gap-2">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Digite sua pergunta... (Enter para enviar, Shift+Enter para nova linha)"
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                rows={2}
                disabled={isLoading}
              />
              <Button
                icon={Send}
                onClick={() => handleSend()}
                disabled={!input.trim() || isLoading}
                loading={isLoading}
              >
                Enviar
              </Button>
            </Flex>
            <Text className="text-xs text-gray-400 mt-2">
              O assistente tem acesso aos dados em tempo real do OptiFlow: tags, alarmes, OEE, energia e mais.
            </Text>
          </div>
        </Card>
      </Grid>
    </div>
  );
};

export default TremorAIChat;
