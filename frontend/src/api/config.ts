/**
 * API Configuration
 */

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
export const API_VERSION = '/api/v1';

export const API_ENDPOINTS = {
  // Auth
  LOGIN: `${API_VERSION}/auth/login`,
  REFRESH: `${API_VERSION}/auth/refresh`,

  // Organizations
  ORGANIZATIONS: `${API_VERSION}/organizations`,

  // Sites
  SITES: `${API_VERSION}/sites`,

  // Devices
  DEVICES: `${API_VERSION}/devices`,

  // Tags
  TAGS: `${API_VERSION}/tags`,

  // Time Series
  TIMESERIES: `${API_VERSION}/timeseries`,
  TIMESERIES_QUERY: `${API_VERSION}/timeseries/query`,

  // Analytics
  ANALYTICS_STATS: `${API_VERSION}/analytics/timeseries/statistics`,
  ANALYTICS_ANOMALIES: `${API_VERSION}/analytics/timeseries/anomalies`,
  ANALYTICS_TRENDS: `${API_VERSION}/analytics/timeseries/trends`,
  ANALYTICS_FORECAST: `${API_VERSION}/analytics/timeseries/forecast`,
  ANALYTICS_CORRELATION: `${API_VERSION}/analytics/timeseries/correlation`,

  // Export
  EXPORT_CSV: `${API_VERSION}/export/csv`,
  EXPORT_JSON: `${API_VERSION}/export/json`,
  EXPORT_EXCEL: `${API_VERSION}/export/excel`,
  EXPORT_TIMESERIES_CSV: `${API_VERSION}/export/timeseries/csv`,
  EXPORT_TIMESERIES_EXCEL: `${API_VERSION}/export/timeseries/excel`,

  // Annotations
  ANNOTATIONS: `${API_VERSION}/annotations`,

  // PLC
  PLC_TAGS: `${API_VERSION}/plc/tags`,
  PLC_TAG: (tagName: string) => `${API_VERSION}/plc/tags/${tagName}`,
  PLC_TAG_HISTORY: (tagName: string) => `${API_VERSION}/plc/tags/${tagName}/history`,
  PLC_TAG_STATS: (tagName: string) => `${API_VERSION}/plc/tags/${tagName}/stats`,

  // ChatBot
  CHATBOT_CHAT: `${API_VERSION}/chatbot/chat`,
  CHATBOT_HISTORY: `${API_VERSION}/chatbot/history`,

  // WebSocket
  WS_REALTIME: `${API_VERSION}/ws/realtime`,
  WS_DASHBOARD: `${API_VERSION}/ws/dashboard`,
  WS_PLC: `/ws/plc`,
} as const;

export const WEBSOCKET_EVENTS = {
  CONNECT: 'connect',
  DISCONNECT: 'disconnect',
  CONNECTION: 'connection',
  TAG_UPDATE: 'tag_update',
  DEVICE_UPDATE: 'device_update',
  SUBSCRIPTION: 'subscription',
  ROOM: 'room',
  ERROR: 'error',
  PING: 'ping',
  PONG: 'pong',
} as const;
