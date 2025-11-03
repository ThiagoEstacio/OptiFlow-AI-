/**
 * Type definitions for chat and AI assistant functionality
 */

export enum MessageRole {
  USER = 'user',
  ASSISTANT = 'assistant',
  SYSTEM = 'system',
}

export interface Message {
  id: string;
  conversation_id: string;
  role: MessageRole;
  content: string;
  metadata?: Record<string, any>;
  created_at: string;
}

export interface Conversation {
  id: string;
  user_id: string;
  organization_id: string;
  title: string;
  context?: Record<string, any>;
  created_at: string;
  updated_at: string;
  messages: Message[];
}

export interface ConversationListItem {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  include_context?: boolean;
  context_filters?: Record<string, any>;
}

export interface ChatResponse {
  conversation_id: string;
  message: Message;
  suggestions?: string[];
}

export interface InsightRequest {
  query: string;
  scope?: 'organization' | 'site' | 'device';
  entity_id?: string;
  time_range?: string;
}

export interface InsightResponse {
  insights: string[];
  data_summary?: Record<string, any>;
  recommendations?: string[];
  visualizations?: Record<string, any>[];
}
