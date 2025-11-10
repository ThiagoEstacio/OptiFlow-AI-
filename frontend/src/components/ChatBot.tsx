/**
 * ChatBot component - Main AI chatbot interface
 */
import React, { useState, useEffect, useRef } from 'react';
import { Send, Loader2, Sparkles, Trash2, MessageSquarePlus } from 'lucide-react';
import ChatMessage from './ChatMessage';
import chatApiClient from '../api/chat';
import { Message, ConversationListItem, MessageRole } from '../types/chat';

const ChatBot: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [conversations, setConversations] = useState<ConversationListItem[]>([]);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSidebar, setShowSidebar] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load conversations on mount
  useEffect(() => {
    // Skip loading conversations - using Llama agent without authentication
    // loadConversations();
  }, []);

  const loadConversations = async () => {
    // Disabled - using Llama agent mode without conversation history
    return;
    
    /* Original code commented out
    try {
      // Check if user is authenticated
      const token = localStorage.getItem('auth_token');
      if (!token) {
        // Skip loading conversations if not authenticated (demo mode)
        return;
      }
      
      const convs = await chatApiClient.listConversations();
      setConversations(convs);
    } catch (error) {
      // Silently handle 401 errors (user not authenticated)
      if ((error as any)?.response?.status === 401) {
        console.log('Not authenticated - using Llama agent mode');
      } else {
        console.error('Error loading conversations:', error);
      }
    }
    */
  };

  const loadConversation = async (conversationId: string) => {
    try {
      setIsLoading(true);
      const conversation = await chatApiClient.getConversation(conversationId);
      setMessages(conversation.messages);
      setCurrentConversationId(conversationId);
      setShowSidebar(false);
    } catch (error) {
      console.error('Error loading conversation:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendMessage = async (messageText?: string) => {
    const text = messageText || inputValue.trim();
    if (!text || isLoading) return;

    // Clear input immediately
    setInputValue('');

    // Add user message to UI immediately
    const tempUserMessage: Message = {
      id: 'temp-' + Date.now(),
      conversation_id: currentConversationId || '',
      role: MessageRole.USER,
      content: text,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, tempUserMessage]);
    setIsLoading(true);

    try {
      const response = await chatApiClient.sendMessage({
        message: text,
        conversation_id: currentConversationId || undefined,
        include_context: true,
      });

      // Update conversation ID if this is a new conversation
      if (!currentConversationId) {
        setCurrentConversationId(response.conversation_id);
        await loadConversations();
      }

      // Replace temp message with real one and add assistant response
      setMessages((prev) => {
        const filtered = prev.filter((m) => m.id !== tempUserMessage.id);
        return [
          ...filtered,
          {
            ...tempUserMessage,
            id: 'user-' + Date.now(),
            conversation_id: response.conversation_id,
          },
          response.message,
        ];
      });

      // Update suggestions
      if (response.suggestions) {
        setSuggestions(response.suggestions);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      // Remove temp message on error
      setMessages((prev) => prev.filter((m) => m.id !== tempUserMessage.id));
      alert('Erro ao enviar mensagem. Por favor, tente novamente.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewConversation = () => {
    setMessages([]);
    setCurrentConversationId(null);
    setSuggestions([
      'Quais dispositivos estão offline?',
      'Mostre-me os alarmes ativos',
      'Como está a performance do sistema?',
      'Quais são as tendências de dados nas últimas 24 horas?',
    ]);
    setShowSidebar(false);
  };

  const handleDeleteConversation = async (conversationId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Tem certeza que deseja excluir esta conversa?')) return;

    try {
      await chatApiClient.deleteConversation(conversationId);
      await loadConversations();
      if (currentConversationId === conversationId) {
        handleNewConversation();
      }
    } catch (error) {
      console.error('Error deleting conversation:', error);
      alert('Erro ao excluir conversa.');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex h-full bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Sidebar - Conversation List */}
      {showSidebar && (
        <div className="w-64 bg-gray-50 border-r border-gray-200 flex flex-col">
          <div className="p-4 border-b border-gray-200">
            <button
              onClick={handleNewConversation}
              className="w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors flex items-center justify-center gap-2"
            >
              <MessageSquarePlus size={18} />
              Nova Conversa
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-2">
            {conversations.map((conv) => (
              <div
                key={conv.id}
                onClick={() => loadConversation(conv.id)}
                className={`p-3 mb-2 rounded-lg cursor-pointer transition-colors group hover:bg-gray-200 ${
                  currentConversationId === conv.id ? 'bg-gray-200' : 'bg-white'
                }`}
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-sm truncate text-gray-900">
                      {conv.title}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {conv.message_count} mensagens
                    </div>
                  </div>
                  <button
                    onClick={(e) => handleDeleteConversation(conv.id, e)}
                    className="ml-2 p-1 text-gray-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 bg-gradient-to-r from-purple-500 to-pink-500 text-white">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowSidebar(!showSidebar)}
              className="p-2 hover:bg-white/20 rounded-lg transition-colors"
            >
              <MessageSquarePlus size={20} />
            </button>
            <Sparkles size={24} />
            <div>
              <h2 className="text-xl font-bold">OptiFlow AI Assistant</h2>
              <p className="text-sm text-white/80">
                Seu assistente inteligente para insights industriais
              </p>
            </div>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-6 bg-gray-50">
          {messages.length === 0 && (
            <div className="text-center text-gray-500 mt-12">
              <Sparkles size={48} className="mx-auto mb-4 text-purple-400" />
              <h3 className="text-lg font-semibold mb-2">
                Bem-vindo ao OptiFlow AI Assistant
              </h3>
              <p className="mb-6">
                Como posso ajudá-lo com seus dispositivos e dados industriais hoje?
              </p>

              {/* Suggestion chips */}
              {suggestions.length > 0 && (
                <div className="flex flex-wrap gap-2 justify-center max-w-2xl mx-auto">
                  {suggestions.map((suggestion, index) => (
                    <button
                      key={index}
                      onClick={() => handleSendMessage(suggestion)}
                      className="px-4 py-2 bg-white border border-gray-200 rounded-full text-sm text-gray-700 hover:bg-gray-50 hover:border-purple-300 transition-colors"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}

          {isLoading && (
            <div className="flex gap-3 mb-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white">
                <Loader2 size={18} className="animate-spin" />
              </div>
              <div className="flex-1">
                <div className="inline-block px-4 py-2 bg-gray-100 rounded-lg rounded-tl-none border border-gray-200">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span>
                    <span
                      className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                      style={{ animationDelay: '0.1s' }}
                    ></span>
                    <span
                      className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                      style={{ animationDelay: '0.2s' }}
                    ></span>
                  </div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Suggestions (shown after AI response) */}
        {!isLoading && messages.length > 0 && suggestions.length > 0 && (
          <div className="px-6 py-2 bg-gray-50 border-t border-gray-200">
            <div className="flex flex-wrap gap-2">
              <span className="text-xs text-gray-500 py-2">Sugestões:</span>
              {suggestions.slice(0, 3).map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => handleSendMessage(suggestion)}
                  className="px-3 py-1 bg-white border border-gray-200 rounded-full text-xs text-gray-700 hover:bg-gray-50 hover:border-purple-300 transition-colors"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input Area */}
        <div className="px-6 py-4 bg-white border-t border-gray-200">
          <div className="flex gap-3">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Digite sua mensagem..."
              disabled={isLoading}
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
            <button
              onClick={() => handleSendMessage()}
              disabled={!inputValue.trim() || isLoading}
              className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:from-purple-600 hover:to-pink-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2"
            >
              {isLoading ? (
                <Loader2 size={20} className="animate-spin" />
              ) : (
                <Send size={20} />
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatBot;
