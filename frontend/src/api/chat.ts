/**
 * Chat API client for AI assistant functionality
 */
import axios from 'axios';
import {
  Conversation,
  ConversationListItem,
  ChatRequest,
  ChatResponse,
  InsightRequest,
  InsightResponse,
  Message,
} from '../types/chat';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const BASE_PATH = '/api/v1/chat';

// Create axios instance with auth token
const chatApi = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
chatApi.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

/**
 * Chat API functions
 */
export const chatApiClient = {
  /**
   * Send a chat message and get AI response
   * Falls back to demo endpoint if not authenticated
   */
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const token = localStorage.getItem('auth_token');
    const endpoint = token ? `${BASE_PATH}/chat` : `${BASE_PATH}/chat/demo`;
    
    const response = await chatApi.post<ChatResponse>(endpoint, request);
    return response.data;
  },

  /**
   * Get AI-powered insights
   */
  async getInsights(request: InsightRequest): Promise<InsightResponse> {
    const response = await chatApi.post<InsightResponse>(`${BASE_PATH}/insights`, request);
    return response.data;
  },

  /**
   * List all conversations
   */
  async listConversations(skip = 0, limit = 50): Promise<ConversationListItem[]> {
    const response = await chatApi.get<ConversationListItem[]>(
      `${BASE_PATH}/conversations`,
      { params: { skip, limit } }
    );
    return response.data;
  },

  /**
   * Get a specific conversation with messages
   */
  async getConversation(conversationId: string): Promise<Conversation> {
    const response = await chatApi.get<Conversation>(
      `${BASE_PATH}/conversations/${conversationId}`
    );
    return response.data;
  },

  /**
   * Create a new conversation
   */
  async createConversation(title: string, context?: Record<string, any>): Promise<Conversation> {
    const response = await chatApi.post<Conversation>(`${BASE_PATH}/conversations`, {
      title,
      context,
    });
    return response.data;
  },

  /**
   * Update a conversation
   */
  async updateConversation(
    conversationId: string,
    title?: string,
    context?: Record<string, any>
  ): Promise<Conversation> {
    const response = await chatApi.patch<Conversation>(
      `${BASE_PATH}/conversations/${conversationId}`,
      { title, context }
    );
    return response.data;
  },

  /**
   * Delete a conversation
   */
  async deleteConversation(conversationId: string): Promise<void> {
    await chatApi.delete(`${BASE_PATH}/conversations/${conversationId}`);
  },

  /**
   * Get messages for a conversation
   */
  async getMessages(conversationId: string, skip = 0, limit = 100): Promise<Message[]> {
    const response = await chatApi.get<Message[]>(
      `${BASE_PATH}/conversations/${conversationId}/messages`,
      { params: { skip, limit } }
    );
    return response.data;
  },
};

export default chatApiClient;
