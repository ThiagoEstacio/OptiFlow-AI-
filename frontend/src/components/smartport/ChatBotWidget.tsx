/**
 * ChatBotWidget Component
 *
 * AI-powered chatbot for process insights and recommendations
 */
import React, { useState, useRef, useEffect } from 'react';
import { useChatBot } from '../../hooks/useChatBot';
import {
  MessageCircle,
  Send,
  Trash2,
  Loader2,
  Bot,
  User,
  Minimize2,
  Maximize2,
} from 'lucide-react';

interface ChatBotWidgetProps {
  includeContext?: boolean;
  className?: string;
  minimizable?: boolean;
}

export const ChatBotWidget: React.FC<ChatBotWidgetProps> = ({
  includeContext = true,
  className = '',
  minimizable = false,
}) => {
  const { messages, loading, sending, sendMessage, clearHistory } = useChatBot({
    autoLoadHistory: true,
    includeContext,
  });

  const [input, setInput] = useState('');
  const [isMinimized, setIsMinimized] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || sending) return;

    const messageText = input.trim();
    setInput('');
    await sendMessage(messageText, includeContext);

    // Focus back on input
    setTimeout(() => inputRef.current?.focus(), 100);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleClearHistory = async () => {
    if (window.confirm('Are you sure you want to clear the conversation history?')) {
      await clearHistory();
    }
  };

  if (isMinimized) {
    return (
      <div className={`${className}`}>
        <button
          onClick={() => setIsMinimized(false)}
          className="flex items-center gap-2 px-4 py-3 bg-blue-600 text-white rounded-lg shadow-lg hover:bg-blue-700 transition-colors"
        >
          <Bot className="h-5 w-5" />
          <span className="font-medium">AI Assistant</span>
          {messages.length > 0 && (
            <span className="bg-blue-500 text-white text-xs rounded-full px-2 py-0.5">
              {messages.length}
            </span>
          )}
        </button>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow-lg flex flex-col ${className}`}>
      {/* Header */}
      <div className="border-b border-gray-200 px-6 py-4 bg-gradient-to-r from-blue-600 to-blue-700 rounded-t-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-white/20 p-2 rounded-lg">
              <Bot className="h-5 w-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white">AI Process Assistant</h2>
              <p className="text-xs text-blue-100">
                {includeContext ? 'Context-aware insights' : 'General assistance'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleClearHistory}
              className="p-2 text-white/80 hover:text-white hover:bg-white/20 rounded transition-colors"
              title="Clear history"
            >
              <Trash2 className="h-4 w-4" />
            </button>
            {minimizable && (
              <button
                onClick={() => setIsMinimized(true)}
                className="p-2 text-white/80 hover:text-white hover:bg-white/20 rounded transition-colors"
                title="Minimize"
              >
                <Minimize2 className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4 min-h-[400px] max-h-[600px]">
        {loading && messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-2" />
              <p className="text-sm text-gray-600">Loading conversation...</p>
            </div>
          </div>
        ) : messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center max-w-md">
              <MessageCircle className="h-12 w-12 text-gray-400 mx-auto mb-3" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Welcome to AI Assistant
              </h3>
              <p className="text-sm text-gray-600 mb-4">
                Ask me anything about the process, PLC data, operations, or port efficiency.
              </p>
              <div className="grid grid-cols-1 gap-2 text-left">
                <button
                  onClick={() => setInput('What is the current crane efficiency?')}
                  className="px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg text-gray-700 transition-colors"
                >
                  "What is the current crane efficiency?"
                </button>
                <button
                  onClick={() => setInput('Show me the port throughput trends')}
                  className="px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg text-gray-700 transition-colors"
                >
                  "Show me the port throughput trends"
                </button>
                <button
                  onClick={() => setInput('Are there any active alarms?')}
                  className="px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg text-gray-700 transition-colors"
                >
                  "Are there any active alarms?"
                </button>
              </div>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex gap-3 ${
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                {message.role === 'assistant' && (
                  <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                    <Bot className="h-4 w-4 text-blue-600" />
                  </div>
                )}

                <div
                  className={`max-w-[80%] rounded-lg px-4 py-3 ${
                    message.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-900'
                  }`}
                >
                  <div className="text-sm whitespace-pre-wrap break-words">
                    {message.content}
                  </div>
                  {message.timestamp && (
                    <div
                      className={`text-xs mt-1 ${
                        message.role === 'user' ? 'text-blue-100' : 'text-gray-500'
                      }`}
                    >
                      {new Date(message.timestamp).toLocaleTimeString()}
                    </div>
                  )}
                </div>

                {message.role === 'user' && (
                  <div className="flex-shrink-0 w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
                    <User className="h-4 w-4 text-gray-600" />
                  </div>
                )}
              </div>
            ))}

            {sending && (
              <div className="flex gap-3 justify-start">
                <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                  <Bot className="h-4 w-4 text-blue-600" />
                </div>
                <div className="bg-gray-100 rounded-lg px-4 py-3">
                  <div className="flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin text-gray-600" />
                    <span className="text-sm text-gray-600">Thinking...</span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 p-4 bg-gray-50 rounded-b-lg">
        <div className="flex items-end gap-3">
          <div className="flex-1">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me anything about the process..."
              disabled={sending}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed transition-shadow"
            />
          </div>
          <button
            onClick={handleSend}
            disabled={!input.trim() || sending}
            className="px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            {sending ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <Send className="h-5 w-5" />
            )}
          </button>
        </div>

        {includeContext && (
          <p className="text-xs text-gray-500 mt-2">
            💡 Context includes current PLC data and operations
          </p>
        )}
      </div>
    </div>
  );
};
