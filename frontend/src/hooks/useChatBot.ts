/**
 * useChatBot Hook
 *
 * Custom hook for AI ChatBot interactions with conversation history
 */
import { useState, useCallback, useEffect } from 'react';
import { chatbotApi, ChatMessage } from '../api/chatbot';

interface UseChatBotOptions {
  autoLoadHistory?: boolean;
  includeContext?: boolean;
}

interface UseChatBotReturn {
  // Data
  messages: ChatMessage[];

  // Loading states
  loading: boolean;
  sending: boolean;

  // Methods
  sendMessage: (message: string, includeContext?: boolean) => Promise<void>;
  loadHistory: () => Promise<void>;
  clearHistory: () => Promise<void>;
}

export const useChatBot = (options: UseChatBotOptions = {}): UseChatBotReturn => {
  const { autoLoadHistory = true, includeContext = true } = options;

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);

  // Load conversation history
  const loadHistory = useCallback(async () => {
    setLoading(true);
    try {
      const history = await chatbotApi.getHistory();
      setMessages(history);
    } catch (error) {
      console.error('Error loading chat history:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  // Send message to chatbot
  const sendMessage = useCallback(
    async (message: string, useContext: boolean = includeContext) => {
      if (!message.trim()) return;

      setSending(true);

      // Add user message to UI immediately
      const userMessage: ChatMessage = {
        role: 'user',
        content: message,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);

      try {
        const response = await chatbotApi.chat(message, useContext);

        // Add assistant response
        const assistantMessage: ChatMessage = {
          role: 'assistant',
          content: response,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, assistantMessage]);
      } catch (error) {
        console.error('Error sending message:', error);

        // Add error message
        const errorMessage: ChatMessage = {
          role: 'assistant',
          content: 'Sorry, I encountered an error processing your message. Please try again.',
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, errorMessage]);
      } finally {
        setSending(false);
      }
    },
    [includeContext]
  );

  // Clear conversation history
  const clearHistory = useCallback(async () => {
    try {
      await chatbotApi.clearHistory();
      setMessages([]);
      console.log('✅ Chat history cleared');
    } catch (error) {
      console.error('Error clearing history:', error);
    }
  }, []);

  // Auto-load history on mount
  useEffect(() => {
    if (autoLoadHistory) {
      loadHistory();
    }
  }, [autoLoadHistory, loadHistory]);

  return {
    messages,
    loading,
    sending,
    sendMessage,
    loadHistory,
    clearHistory,
  };
};
