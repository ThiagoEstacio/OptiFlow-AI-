/**
 * Dashboard Manager Hook
 * Manage multiple dashboards, export/import, and sharing
 */

import { useState, useCallback } from 'react';
import type { Widget } from '../pages/DashboardBuilderPage';

export interface Dashboard {
  id: string;
  name: string;
  description?: string;
  widgets: Widget[];
  createdAt: string;
  updatedAt: string;
  tags?: string[];
  isPublic?: boolean;
  sharedWith?: string[];
}

const STORAGE_KEY = 'optiflow_dashboards';

export const useDashboardManager = () => {
  // Load dashboards from localStorage
  const loadDashboards = useCallback((): Dashboard[] => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return stored ? JSON.parse(stored) : [];
    } catch (error) {
      console.error('Error loading dashboards:', error);
      return [];
    }
  }, []);

  const [dashboards, setDashboards] = useState<Dashboard[]>(loadDashboards);

  // Save dashboards to localStorage
  const saveDashboards = useCallback((newDashboards: Dashboard[]) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(newDashboards));
      setDashboards(newDashboards);
    } catch (error) {
      console.error('Error saving dashboards:', error);
    }
  }, []);

  // Create new dashboard
  const createDashboard = useCallback(
    (name: string, widgets: Widget[] = [], description?: string): Dashboard => {
      const newDashboard: Dashboard = {
        id: `dashboard-${Date.now()}`,
        name,
        description,
        widgets,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        isPublic: false,
      };

      const updated = [...dashboards, newDashboard];
      saveDashboards(updated);
      return newDashboard;
    },
    [dashboards, saveDashboards]
  );

  // Update dashboard
  const updateDashboard = useCallback(
    (id: string, updates: Partial<Dashboard>) => {
      const updated = dashboards.map((d) =>
        d.id === id
          ? { ...d, ...updates, updatedAt: new Date().toISOString() }
          : d
      );
      saveDashboards(updated);
    },
    [dashboards, saveDashboards]
  );

  // Delete dashboard
  const deleteDashboard = useCallback(
    (id: string) => {
      const updated = dashboards.filter((d) => d.id !== id);
      saveDashboards(updated);
    },
    [dashboards, saveDashboards]
  );

  // Duplicate dashboard
  const duplicateDashboard = useCallback(
    (id: string): Dashboard | null => {
      const original = dashboards.find((d) => d.id === id);
      if (!original) return null;

      const duplicate: Dashboard = {
        ...original,
        id: `dashboard-${Date.now()}`,
        name: `${original.name} (Copy)`,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        // Generate new IDs for all widgets
        widgets: original.widgets.map((w) => ({
          ...w,
          id: `widget-${Date.now()}-${Math.random()}`,
        })),
      };

      const updated = [...dashboards, duplicate];
      saveDashboards(updated);
      return duplicate;
    },
    [dashboards, saveDashboards]
  );

  // Export dashboard to JSON
  const exportDashboard = useCallback((dashboard: Dashboard): string => {
    return JSON.stringify(dashboard, null, 2);
  }, []);

  // Export dashboard as file download
  const downloadDashboard = useCallback(
    (dashboard: Dashboard) => {
      const json = exportDashboard(dashboard);
      const blob = new Blob([json], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${dashboard.name.replace(/\s+/g, '-')}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    },
    [exportDashboard]
  );

  // Import dashboard from JSON
  const importDashboard = useCallback(
    (json: string): Dashboard | null => {
      try {
        const imported = JSON.parse(json) as Dashboard;

        // Generate new ID to avoid conflicts
        const newDashboard: Dashboard = {
          ...imported,
          id: `dashboard-${Date.now()}`,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          // Generate new widget IDs
          widgets: imported.widgets.map((w) => ({
            ...w,
            id: `widget-${Date.now()}-${Math.random()}`,
          })),
        };

        const updated = [...dashboards, newDashboard];
        saveDashboards(updated);
        return newDashboard;
      } catch (error) {
        console.error('Error importing dashboard:', error);
        return null;
      }
    },
    [dashboards, saveDashboards]
  );

  // Import dashboard from file
  const importDashboardFromFile = useCallback(
    (file: File): Promise<Dashboard | null> => {
      return new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = (e) => {
          const content = e.target?.result as string;
          const dashboard = importDashboard(content);
          resolve(dashboard);
        };
        reader.onerror = () => resolve(null);
        reader.readAsText(file);
      });
    },
    [importDashboard]
  );

  // Share dashboard (generate shareable link)
  const shareDashboard = useCallback(
    (id: string): string => {
      const dashboard = dashboards.find((d) => d.id === id);
      if (!dashboard) return '';

      // Update dashboard to be public
      updateDashboard(id, { isPublic: true });

      // In a real app, this would generate a secure share link
      // For now, we'll use the dashboard ID
      const baseUrl = window.location.origin;
      return `${baseUrl}/dashboard-builder?shared=${id}`;
    },
    [dashboards, updateDashboard]
  );

  // Get dashboard by ID
  const getDashboard = useCallback(
    (id: string): Dashboard | undefined => {
      return dashboards.find((d) => d.id === id);
    },
    [dashboards]
  );

  return {
    dashboards,
    createDashboard,
    updateDashboard,
    deleteDashboard,
    duplicateDashboard,
    exportDashboard,
    downloadDashboard,
    importDashboard,
    importDashboardFromFile,
    shareDashboard,
    getDashboard,
  };
};
