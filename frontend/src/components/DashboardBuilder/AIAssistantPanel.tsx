/**
 * AI Assistant Panel for Dashboard Builder
 * 
 * Conversational interface for creating dashboards using natural language.
 */

import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, X, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import type { Widget } from '../../pages/DashboardBuilderPage';
import apiClient from '../../api/client';

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  widgets?: any[];
  timestamp: Date;
}

interface AIAssistantPanelProps {
  availableTags: any[];
  currentWidgets: Widget[];
  onAddWidgets: (widgets: Widget[]) => void;
  onClose: () => void;
}

export const AIAssistantPanel: React.FC<AIAssistantPanelProps> = ({
  availableTags,
  currentWidgets,
  onAddWidgets,
  onClose,
}) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'system',
      content: '👋 Olá! Sou seu assistente de IA para criação de dashboards. Posso ajudá-lo a criar widgets usando linguagem natural.\n\nExemplos:\n• "Crie um gauge de temperatura"\n• "Adicione um gráfico de pressão das últimas 24h"\n• "Mostre KPIs de eficiência"',
      timestamp: new Date(),
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [suggestions] = useState([
    'Criar gauge de temperatura',
    'Adicionar gráfico de série temporal',
    'Mostrar KPIs de produção',
    'Criar tabela de dados',
  ]);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await apiClient.post('/api/v1/agent/dashboard/chat', {
        message: userMessage.content,
        available_tags: availableTags.slice(0, 20),
        current_widgets: currentWidgets.map(w => ({
          type: w.type,
          title: w.config.title,
        })),
      });

      const data = response.data;

      const assistantMessage: Message = {
        role: 'assistant',
        content: data.response,
        widgets: data.widgets,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, assistantMessage]);

      // Auto-add widgets if generated
      if (data.widgets && data.widgets.length > 0) {
        const baseTime = Date.now();
        const widgetsToAdd: Widget[] = data.widgets.map((w: any, idx: number) => ({
          id: `ai-widget-${baseTime}-${idx}-${Math.random().toString(36).substr(2, 9)}`,
          type: w.type,
          position: { 
            x: 100 + (idx * 30), 
            y: 100 + (idx * 30) 
          },
          size: { width: 300, height: 250 },
          config: {
            title: w.title,
            tagId: w.tagId,
            tagIds: w.tagIds,
            ...w.config,
          },
        }));

        console.log('Adding AI widgets:', widgetsToAdd);
        onAddWidgets(widgetsToAdd);
      }

    } catch (error) {
      console.error('AI Assistant error:', error);
      
      const errorMessage: Message = {
        role: 'assistant',
        content: `❌ Erro ao processar sua solicitação.\n\n${error instanceof Error ? error.message : 'Erro desconhecido'}\n\nDicas:\n• Aguarde alguns segundos e tente novamente (primeira requisição pode demorar)\n• Verifique se o Ollama está rodando: docker logs optiflow-ollama\n• Verifique os logs: docker logs optiflow-backend`,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const useSuggestion = (suggestion: string) => {
    setInput(suggestion);
    inputRef.current?.focus();
  };

  return (
    <div className="fixed right-4 bottom-4 w-96 h-[600px] bg-white dark:bg-gray-800 rounded-lg shadow-2xl flex flex-col border border-gray-200 dark:border-gray-700 z-50">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-blue-500 to-purple-600">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-white" />
          <h3 className="font-semibold text-white">AI Dashboard Assistant</h3>
        </div>
        <button
          onClick={onClose}
          className="text-white hover:bg-white/20 rounded p-1 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg p-3 ${
                msg.role === 'user'
                  ? 'bg-blue-500 text-white'
                  : msg.role === 'system'
                  ? 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 border border-gray-200 dark:border-gray-600'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200'
              }`}
            >
              <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              
              {msg.widgets && msg.widgets.length > 0 && (
                <div className="mt-2 pt-2 border-t border-gray-300 dark:border-gray-600">
                  <div className="flex items-center gap-1 text-xs text-green-600 dark:text-green-400">
                    <CheckCircle className="w-3 h-3" />
                    <span>{msg.widgets.length} widget(s) adicionado(s)</span>
                  </div>
                </div>
              )}

              <span className="text-xs opacity-60 mt-1 block">
                {msg.timestamp.toLocaleTimeString()}
              </span>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 dark:bg-gray-700 rounded-lg p-3">
              <Loader2 className="w-5 h-5 animate-spin text-blue-500" />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggestions */}
      {messages.length === 1 && (
        <div className="px-4 py-2 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
          <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">Sugestões:</p>
          <div className="flex flex-wrap gap-2">
            {suggestions.map((suggestion, idx) => (
              <button
                key={idx}
                onClick={() => useSuggestion(suggestion)}
                className="text-xs px-2 py-1 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Digite sua solicitação..."
            disabled={isLoading}
            className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 disabled:opacity-50"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </div>

        {/* Status indicator */}
        <div className="mt-2 flex items-center gap-2 text-xs">
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            <span className="text-gray-600 dark:text-gray-400">AI Online</span>
          </div>
          <span className="text-gray-400">•</span>
          <span className="text-gray-600 dark:text-gray-400">
            {availableTags.length} tags disponíveis
          </span>
        </div>
      </div>
    </div>
  );
};

export default AIAssistantPanel;
