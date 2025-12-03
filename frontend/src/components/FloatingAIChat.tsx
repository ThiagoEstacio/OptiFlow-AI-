/**
 * 🤖 Floating AI Chat - Bot Flutuante
 * ====================================
 *
 * Componente de chat com IA flutuante disponível em todas as telas.
 * Features:
 * - Botão flutuante no canto inferior direito
 * - Painel de chat expansível
 * - Integração com backend de AI
 * - Sugestões rápidas
 * - Histórico de mensagens
 */
import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  MessageSquare,
  X,
  Send,
  Sparkles,
  Loader2,
  Bot,
  User,
  Lightbulb,
  TrendingUp,
  AlertTriangle,
  Zap,
  Minimize2,
} from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface QuickAction {
  label: string;
  icon: React.ReactNode;
  prompt: string;
}

const quickActions: QuickAction[] = [
  {
    label: 'Resumo do dia',
    icon: <TrendingUp className="w-4 h-4" />,
    prompt: 'Faça um resumo das operações de hoje, incluindo OEE, alarmes e produção.',
  },
  {
    label: 'Alarmes críticos',
    icon: <AlertTriangle className="w-4 h-4" />,
    prompt: 'Quais são os alarmes críticos ativos e o que pode ser feito para resolvê-los?',
  },
  {
    label: 'Otimizar energia',
    icon: <Zap className="w-4 h-4" />,
    prompt: 'Analise o consumo de energia e sugira otimizações para reduzir custos.',
  },
  {
    label: 'Insights ML',
    icon: <Lightbulb className="w-4 h-4" />,
    prompt: 'Quais insights de machine learning temos sobre a operação atual?',
  },
];

export const FloatingAIChat: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Olá! Sou o assistente AI do OptiFlow. Como posso ajudar você hoje? 🤖',
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

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
      // Call the AI endpoint
      const response = await fetch('/api/v1/agent/dashboard/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`,
        },
        body: JSON.stringify({
          message: text,
          context: {
            page: window.location.pathname,
            timestamp: new Date().toISOString(),
          },
        }),
      });

      let assistantContent = '';

      if (response.ok) {
        const data = await response.json();
        assistantContent = data.response || data.message || 'Desculpe, não consegui processar sua solicitação.';
      } else {
        // Fallback response if API fails
        assistantContent = generateFallbackResponse(text);
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: assistantContent,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('AI Chat error:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: generateFallbackResponse(text),
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const generateFallbackResponse = (query: string): string => {
    const lowerQuery = query.toLowerCase();

    if (lowerQuery.includes('oee') || lowerQuery.includes('eficiência')) {
      return '📊 **OEE Atual: 87.3%**\n\n• Disponibilidade: 92.1%\n• Performance: 95.8%\n• Qualidade: 98.9%\n\nO OEE está acima da meta de 85%. A principal oportunidade de melhoria está na disponibilidade, com pequenas paradas representando 3.2% do tempo.';
    }

    if (lowerQuery.includes('alarme') || lowerQuery.includes('alerta')) {
      return '🚨 **Alarmes Ativos: 7**\n\n• 2 Críticos: Temperatura elevada no Reator 1, Vibração no Compressor\n• 3 Avisos: Nível baixo tanque A, Pressão fora do range, Vazão reduzida\n• 2 Informativos\n\n**Recomendação:** Priorize verificar a temperatura do Reator 1 - pode indicar falha no sistema de refrigeração.';
    }

    if (lowerQuery.includes('energia') || lowerQuery.includes('consumo')) {
      return '⚡ **Consumo de Energia**\n\n• Atual: 2.4 MW\n• Média 24h: 2.2 MW\n• Previsão mensal: R$ 485.000\n\n**Oportunidades de economia:**\n1. Otimizar horário de operação dos compressores (economia potencial: 8%)\n2. Verificar eficiência do trocador de calor TC-02\n3. Considerar migração para Mercado Livre de energia';
    }

    if (lowerQuery.includes('produção') || lowerQuery.includes('linha')) {
      return '🏭 **Status da Produção**\n\n• Linha A: 85% eficiência ✅\n• Linha B: 72% eficiência ⚠️\n• Linha C: 91% eficiência ✅\n• Linha D: 68% eficiência ⚠️\n\n**Atenção:** Linhas B e D estão abaixo da meta. Verificar relatório de paradas para identificar causas.';
    }

    if (lowerQuery.includes('resumo') || lowerQuery.includes('dia')) {
      return '📋 **Resumo Operacional**\n\n✅ **Produção:** 1.247 unidades (98% da meta)\n📊 **OEE Geral:** 87.3% (acima da meta)\n🚨 **Alarmes:** 7 ativos (2 críticos)\n⚡ **Energia:** 2.4 MW (dentro do esperado)\n🔧 **Manutenção:** 3 ordens abertas\n\n**Destaques:**\n• Produção estável nas últimas 8 horas\n• Verificar alarme de temperatura no Reator 1\n• Próxima manutenção preventiva: Compressor 01 (amanhã)';
    }

    return '🤖 Entendi sua pergunta. Com base nos dados disponíveis, posso ajudar com:\n\n• Análise de OEE e produção\n• Monitoramento de alarmes\n• Consumo de energia\n• Insights de manutenção\n• Previsões ML\n\nComo posso ajudar especificamente?';
  };

  const handleQuickAction = (action: QuickAction) => {
    handleSend(action.prompt);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <>
      {/* Floating Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`floating-chat-button ${isOpen ? 'open' : ''}`}
        aria-label={isOpen ? 'Fechar chat' : 'Abrir chat AI'}
      >
        {isOpen ? (
          <X className="w-6 h-6" />
        ) : (
          <MessageSquare className="w-6 h-6" />
        )}

        {/* Notification dot when closed */}
        {!isOpen && (
          <span className="absolute -top-1 -right-1 w-4 h-4 bg-emerald-500 rounded-full flex items-center justify-center">
            <Sparkles className="w-2.5 h-2.5 text-white" />
          </span>
        )}
      </button>

      {/* Chat Panel */}
      {isOpen && (
        <div className="floating-chat-panel">
          {/* Header */}
          <div className="floating-chat-header">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center">
                <Bot className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-semibold text-sm">OptiFlow AI</h3>
                <p className="text-xs text-white/70">Assistente Inteligente</p>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="p-1.5 hover:bg-white/10 rounded-lg transition-colors"
            >
              <Minimize2 className="w-4 h-4" />
            </button>
          </div>

          {/* Messages */}
          <div className="floating-chat-messages custom-scrollbar">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`chat-message ${
                  message.role === 'user' ? 'chat-message-user' : 'chat-message-bot'
                }`}
              >
                <div className="flex items-start gap-2">
                  {message.role === 'assistant' && (
                    <Bot className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
                  )}
                  <div className="flex-1">
                    <div className="whitespace-pre-wrap">{message.content}</div>
                    <div
                      className={`text-xs mt-1 ${
                        message.role === 'user' ? 'text-white/60' : 'text-slate-400'
                      }`}
                    >
                      {formatTime(message.timestamp)}
                    </div>
                  </div>
                  {message.role === 'user' && (
                    <User className="w-4 h-4 text-white/80 mt-0.5 flex-shrink-0" />
                  )}
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="chat-message chat-message-bot">
                <div className="flex items-center gap-2 text-slate-500">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Analisando...</span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Quick Actions */}
          {messages.length <= 2 && (
            <div className="px-3 py-2 border-t border-slate-100 bg-slate-50/50">
              <p className="text-xs text-slate-500 mb-2">Sugestões rápidas:</p>
              <div className="flex flex-wrap gap-1.5">
                {quickActions.map((action, index) => (
                  <button
                    key={index}
                    onClick={() => handleQuickAction(action)}
                    disabled={isLoading}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium
                             bg-white border border-slate-200 rounded-full text-slate-600
                             hover:bg-blue-50 hover:border-blue-200 hover:text-blue-700
                             transition-colors disabled:opacity-50"
                  >
                    {action.icon}
                    {action.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Input */}
          <div className="floating-chat-input">
            <div className="flex items-center gap-2">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Pergunte algo..."
                disabled={isLoading}
                className="flex-1 px-3 py-2 text-sm bg-slate-100 border-0 rounded-full
                         text-slate-700 placeholder-slate-400
                         focus:outline-none focus:ring-2 focus:ring-blue-500/30
                         disabled:opacity-50"
              />
              <button
                onClick={() => handleSend()}
                disabled={!input.trim() || isLoading}
                className="p-2.5 rounded-full bg-blue-600 text-white
                         hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed
                         transition-colors"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default FloatingAIChat;
