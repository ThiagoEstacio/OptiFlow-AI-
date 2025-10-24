/**
 * ChatBot API Client
 *
 * API functions for AI ChatBot interactions
 */
import api from './client';

// ============================================================================
// Types
// ============================================================================

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
}

export interface ChatRequest {
  message: string;
  include_context?: boolean;
}

export interface ChatResponse {
  response: string;
}

export interface ChatHistory {
  history: ChatMessage[];
}

// ============================================================================
// ChatBot API
// ============================================================================

export const chatbotApi = {
  /**
   * Send a message to the chatbot
   */
  chat: async (message: string, includeContext: boolean = true) => {
    const response = await api.post<ChatResponse>('/api/v1/chatbot/chat', {
      message,
      include_context: includeContext,
    });
    return response.data.response;
  },

  /**
   * Get conversation history
   */
  getHistory: async () => {
    const response = await api.get<ChatHistory>('/api/v1/chatbot/history');
    return response.data.history;
  },

  /**
   * Clear conversation history
   */
  clearHistory: async () => {
    await api.delete('/api/v1/chatbot/history');
  },
};

export default chatbotApi;
