/**
 * 📊 Dashboard API Service
 * =========================
 * Complete integration with backend /api/v1/dashboards endpoints
 */

import apiClient from '../api/client';

const DASHBOARDS_API = '/api/v1/dashboards';

// ========================================
// 📊 TYPES
// ========================================

export interface Widget {
  id?: string;
  type: string;
  title: string;
  config: Record<string, any>;
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface Dashboard {
  id?: string;
  name: string;
  description?: string;
  module: string;
  theme: string;
  layout: Widget[];
  auto_refresh: boolean;
  refresh_interval: number;
  is_favorite?: boolean;
  is_public: boolean;
  created_at?: string;
  updated_at?: string;
  owner_id?: string;
}

export interface DashboardShare {
  id?: string;
  dashboard_id: string;
  user_id: string;
  can_edit: boolean;
  created_at?: string;
}

export interface DashboardTemplate {
  id: string;
  name: string;
  description?: string;
  module: string;
  thumbnail_url?: string;
  is_system: boolean;
  layout: Widget[];
  created_at: string;
}

// ========================================
// 🔧 API METHODS
// ========================================

/**
 * Create a new dashboard
 */
export const createDashboard = async (data: Partial<Dashboard>): Promise<Dashboard> => {
  const response = await apiClient.post<Dashboard>(DASHBOARDS_API, data);
  return response.data;
};

/**
 * Get all dashboards accessible to the current user
 */
export const getDashboards = async (params?: {
  module?: string;
  is_favorite?: boolean;
  is_public?: boolean;
}): Promise<Dashboard[]> => {
  const response = await apiClient.get<Dashboard[]>(DASHBOARDS_API, { params });
  return response.data;
};

/**
 * Get a specific dashboard by ID
 */
export const getDashboard = async (id: string): Promise<Dashboard> => {
  const response = await apiClient.get<Dashboard>(`${DASHBOARDS_API}/${id}`);
  return response.data;
};

/**
 * Update an existing dashboard
 */
export const updateDashboard = async (
  id: string,
  data: Partial<Dashboard>
): Promise<Dashboard> => {
  const response = await apiClient.put<Dashboard>(`${DASHBOARDS_API}/${id}`, data);
  return response.data;
};

/**
 * Delete a dashboard
 */
export const deleteDashboard = async (id: string): Promise<void> => {
  await apiClient.delete(`${DASHBOARDS_API}/${id}`);
};

/**
 * Clone an existing dashboard
 */
export const cloneDashboard = async (
  id: string,
  newName: string
): Promise<Dashboard> => {
  const response = await apiClient.post<Dashboard>(
    `${DASHBOARDS_API}/${id}/clone`,
    { new_name: newName }
  );
  return response.data;
};

/**
 * Toggle favorite status
 */
export const toggleFavorite = async (id: string): Promise<Dashboard> => {
  const response = await apiClient.post<Dashboard>(`${DASHBOARDS_API}/${id}/favorite`);
  return response.data;
};

// ========================================
// 🧩 WIDGET OPERATIONS
// ========================================

/**
 * Add a widget to a dashboard
 */
export const addWidget = async (
  dashboardId: string,
  widget: Partial<Widget>
): Promise<Widget> => {
  const response = await apiClient.post<Widget>(
    `${DASHBOARDS_API}/${dashboardId}/widgets`,
    widget
  );
  return response.data;
};

/**
 * Update a widget
 */
export const updateWidget = async (
  dashboardId: string,
  widgetId: string,
  data: Partial<Widget>
): Promise<Widget> => {
  const response = await apiClient.put<Widget>(
    `${DASHBOARDS_API}/${dashboardId}/widgets/${widgetId}`,
    data
  );
  return response.data;
};

/**
 * Delete a widget
 */
export const deleteWidget = async (
  dashboardId: string,
  widgetId: string
): Promise<void> => {
  await apiClient.delete(`${DASHBOARDS_API}/${dashboardId}/widgets/${widgetId}`);
};

/**
 * Bulk update widget positions (after drag-and-drop)
 */
export const bulkUpdateWidgets = async (
  dashboardId: string,
  updates: Array<{
    widget_id: string;
    x: number;
    y: number;
    w: number;
    h: number;
  }>
): Promise<void> => {
  await apiClient.post(`${DASHBOARDS_API}/${dashboardId}/widgets/bulk-update`, {
    updates,
  });
};

// ========================================
// 👥 SHARING OPERATIONS
// ========================================

/**
 * Share a dashboard with a user
 */
export const shareDashboard = async (
  dashboardId: string,
  userId: string,
  canEdit: boolean = false
): Promise<DashboardShare> => {
  const response = await apiClient.post<DashboardShare>(
    `${DASHBOARDS_API}/${dashboardId}/share`,
    { user_id: userId, can_edit: canEdit }
  );
  return response.data;
};

/**
 * Get all shares for a dashboard
 */
export const getDashboardShares = async (
  dashboardId: string
): Promise<DashboardShare[]> => {
  const response = await apiClient.get<DashboardShare[]>(
    `${DASHBOARDS_API}/${dashboardId}/shares`
  );
  return response.data;
};

/**
 * Remove a share
 */
export const removeDashboardShare = async (
  dashboardId: string,
  shareId: string
): Promise<void> => {
  await apiClient.delete(`${DASHBOARDS_API}/${dashboardId}/shares/${shareId}`);
};

// ========================================
// 📋 TEMPLATE OPERATIONS
// ========================================

/**
 * Get all available dashboard templates
 */
export const getDashboardTemplates = async (params?: {
  module?: string;
}): Promise<DashboardTemplate[]> => {
  const response = await apiClient.get<DashboardTemplate[]>(
    `${DASHBOARDS_API}/templates`,
    { params }
  );
  return response.data;
};

/**
 * Create a dashboard from a template
 */
export const createFromTemplate = async (
  templateId: string,
  name: string
): Promise<Dashboard> => {
  const response = await apiClient.post<Dashboard>(
    `${DASHBOARDS_API}/templates/${templateId}/use`,
    { name }
  );
  return response.data;
};

/**
 * Save current dashboard as a template
 */
export const saveAsTemplate = async (
  dashboardId: string,
  name: string,
  description?: string
): Promise<DashboardTemplate> => {
  const response = await apiClient.post<DashboardTemplate>(
    `${DASHBOARDS_API}/${dashboardId}/save-as-template`,
    { name, description }
  );
  return response.data;
};

// ========================================
// 🔄 UTILITY METHODS
// ========================================

/**
 * Export dashboard configuration as JSON
 */
export const exportDashboard = async (id: string): Promise<Dashboard> => {
  const dashboard = await getDashboard(id);
  return dashboard;
};

/**
 * Import dashboard from JSON
 */
export const importDashboard = async (data: Dashboard): Promise<Dashboard> => {
  const { id, created_at, updated_at, owner_id, ...importData } = data;
  return createDashboard(importData);
};

export default {
  // Dashboard CRUD
  createDashboard,
  getDashboards,
  getDashboard,
  updateDashboard,
  deleteDashboard,
  cloneDashboard,
  toggleFavorite,
  
  // Widget operations
  addWidget,
  updateWidget,
  deleteWidget,
  bulkUpdateWidgets,
  
  // Sharing
  shareDashboard,
  getDashboardShares,
  removeDashboardShare,
  
  // Templates
  getDashboardTemplates,
  createFromTemplate,
  saveAsTemplate,
  
  // Utilities
  exportDashboard,
  importDashboard,
};
