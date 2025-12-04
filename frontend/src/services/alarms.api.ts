/**
 * 🚨 Alarms API Service
 * ====================
 * Complete integration with backend /api/v1/alarms endpoints
 */

import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const ALARMS_API = `${API_BASE}/api/v1/alarms`;

// ========================================
// 📊 TYPES
// ========================================

export interface AlarmDefinition {
  id: string;
  name: string;
  description?: string;
  tag_id: string;
  alarm_type: 'high_limit' | 'low_limit' | 'rate_of_change' | 'deviation' | 'predictive' | 'custom';
  severity: 'critical' | 'high' | 'medium' | 'low';
  threshold?: number;
  deadband?: number;
  delay_seconds?: number;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface AlarmEvent {
  id: string;
  definition_id: string;
  tag_id: string;
  state: 'active' | 'acknowledged' | 'cleared';
  severity: 'critical' | 'high' | 'medium' | 'low';
  message: string; // ⚠️ Deprecated: use alarm_name for display
  trigger_value?: number;
  trigger_timestamp: string;
  acknowledged_at?: string;
  acknowledged_by?: string;
  cleared_at?: string;
  clear_value?: number;
  duration_seconds?: number;

  // ✨ NEW: Enriched fields from backend
  alarm_name?: string;      // Real alarm name from definition
  alarm_type?: string;      // Alarm type (HIGH_LIMIT, LOW_LIMIT, etc)
  description?: string;     // Real description from definition
  high_limit?: number;      // High threshold
  low_limit?: number;       // Low threshold
}

export interface AlarmStatistics {
  total: number;
  active: number;
  acknowledged: number;
  cleared: number;
  by_severity: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  by_type: Record<string, number>;
  average_duration_minutes: number;
}

export interface TopAlarm {
  alarm_definition_id: string;
  name: string;
  severity: string;
  count: number;
}

export interface AcknowledgeRequest {
  comment?: string;
  user_id?: string;
}

// ========================================
// 📡 ALARM DEFINITIONS (Configuration)
// ========================================

export const alarmsApi = {
  // Create new alarm definition
  createDefinition: async (data: Omit<AlarmDefinition, 'id' | 'created_at' | 'updated_at'>) => {
    const response = await axios.post<AlarmDefinition>(`${ALARMS_API}/definitions`, data);
    return response.data;
  },

  // Get all alarm definitions with filters
  getDefinitions: async (params?: {
    tag_id?: string;
    severity?: string;
    is_active?: boolean;
    skip?: number;
    limit?: number;
  }) => {
    const response = await axios.get<AlarmDefinition[]>(`${ALARMS_API}/definitions`, { params });
    return response.data;
  },

  // Get single alarm definition
  getDefinition: async (id: string) => {
    const response = await axios.get<AlarmDefinition>(`${ALARMS_API}/definitions/${id}`);
    return response.data;
  },

  // Update alarm definition
  updateDefinition: async (id: string, data: Partial<AlarmDefinition>) => {
    const response = await axios.put<AlarmDefinition>(`${ALARMS_API}/definitions/${id}`, data);
    return response.data;
  },

  // Delete alarm definition
  deleteDefinition: async (id: string) => {
    await axios.delete(`${ALARMS_API}/definitions/${id}`);
  },

  // ========================================
  // 🔔 ALARM EVENTS
  // ========================================

  // Get active alarms (real-time)
  getActiveAlarms: async (params?: {
    severity?: string;
    tag_id?: string;
    limit?: number;
    offset?: number;
  }): Promise<AlarmEvent[]> => {
    const response = await axios.get<{ total: number; limit: number; offset: number; items: any[] } | any[]>(
      `${ALARMS_API}/active`,
      { params }
    );

    // Handle both old array format and new paginated format
    const items = Array.isArray(response.data) ? response.data : response.data.items;

    // ✨ Map enriched backend response to AlarmEvent interface
    return items.map((alarm: any) => ({
      ...alarm,
      message: alarm.alarm_name || alarm.description || 'No message', // Map alarm_name to message for compatibility
    }));
  },

  // Get active alarms with pagination info
  getActiveAlarmsWithTotal: async (params?: {
    severity?: string;
    tag_id?: string;
    limit?: number;
    offset?: number;
  }): Promise<{ total: number; items: AlarmEvent[] }> => {
    const response = await axios.get<{ total: number; limit: number; offset: number; items: any[] }>(
      `${ALARMS_API}/active`,
      { params }
    );

    const items = response.data.items.map((alarm: any) => ({
      ...alarm,
      message: alarm.alarm_name || alarm.description || 'No message',
    }));

    return {
      total: response.data.total,
      items,
    };
  },

  // Get alarm history with filters
  getHistory: async (params?: {
    start_date?: string;
    end_date?: string;
    state?: string;
    severity?: string;
    tag_id?: string;
    skip?: number;
    limit?: number;
  }) => {
    const response = await axios.get<any[]>(`${ALARMS_API}/history`, { params });
    // ✨ Map enriched backend response to AlarmEvent interface
    return response.data.map((alarm: any) => ({
      ...alarm,
      message: alarm.alarm_name || alarm.description || 'No message', // Map alarm_name to message for compatibility
    }));
  },

  // Get specific alarm event
  getEvent: async (id: string) => {
    const response = await axios.get<AlarmEvent>(`${ALARMS_API}/events/${id}`);
    return response.data;
  },

  // Acknowledge alarm
  acknowledgeAlarm: async (id: string, data?: AcknowledgeRequest) => {
    const response = await axios.post<AlarmEvent>(
      `${ALARMS_API}/events/${id}/acknowledge`,
      data || {}
    );
    return response.data;
  },

  // Clear alarm
  clearAlarm: async (id: string) => {
    const response = await axios.post<AlarmEvent>(`${ALARMS_API}/events/${id}/clear`);
    return response.data;
  },

  // ========================================
  // 📊 STATISTICS & ANALYTICS
  // ========================================

  // Get comprehensive statistics
  getStatistics: async () => {
    const response = await axios.get<AlarmStatistics>(`${ALARMS_API}/statistics`);
    return response.data;
  },

  // Get top/most frequent alarms
  getTopAlarms: async (limit: number = 10) => {
    const response = await axios.get<{ top_alarms: TopAlarm[]; period_days: number }>(
      `${ALARMS_API}/top-alarms`,
      { params: { limit } }
    );
    return response.data.top_alarms; // Extract just the array
  },
};

// ========================================
// 🎨 UTILITY FUNCTIONS
// ========================================

export const getSeverityColor = (severity: string) => {
  // ✅ FIXED: Check if severity is defined before calling toLowerCase
  if (!severity) return 'bg-gray-100 text-gray-800 border-gray-200';

  switch (severity.toLowerCase()) {
    case 'critical':
      return 'bg-red-100 text-red-800 border-red-200';
    case 'high':
      return 'bg-orange-100 text-orange-800 border-orange-200';
    case 'medium':
      return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    case 'low':
      return 'bg-blue-100 text-blue-800 border-blue-200';
    default:
      return 'bg-gray-100 text-gray-800 border-gray-200';
  }
};

export const getSeverityIcon = (severity: string) => {
  // ✅ FIXED: Check if severity is defined before calling toLowerCase
  if (!severity) return '⚪';

  switch (severity.toLowerCase()) {
    case 'critical':
      return '🔴';
    case 'high':
      return '🟠';
    case 'medium':
      return '🟡';
    case 'low':
      return '🔵';
    default:
      return '⚪';
  }
};

export const getStateColor = (state: string) => {
  // ✅ FIXED: Check if state is defined before calling toLowerCase
  if (!state) return 'bg-gray-100 text-gray-800';

  switch (state.toLowerCase()) {
    case 'active':
      return 'bg-red-100 text-red-800';
    case 'acknowledged':
      return 'bg-yellow-100 text-yellow-800';
    case 'cleared':
      return 'bg-green-100 text-green-800';
    case 'resolved':
      return 'bg-green-100 text-green-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

export const formatDuration = (seconds?: number): string => {
  if (!seconds) return '-';
  
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  
  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }
  return `${minutes}m`;
};
