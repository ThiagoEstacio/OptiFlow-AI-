/**
 * Asset Context - Global state management for Asset Framework
 * Provides hierarchical asset tree data and operations
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';

// Asset types matching backend enum
export type AssetType = 'enterprise' | 'site' | 'area' | 'unit' | 'equipment' | 'component';

// Asset interface
export interface Asset {
  id: string;
  name: string;
  description?: string;
  asset_type: AssetType;
  is_active: boolean;
  parent_id?: string;
  template_id?: string;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;

  // Computed properties
  level?: number;
  full_path?: string;
  children_count?: number;
  attributes_count?: number;
}

// Asset tree node (hierarchical structure)
export interface AssetTreeNode extends Asset {
  children: AssetTreeNode[];
}

// Asset attribute interface
export interface AssetAttribute {
  id: string;
  asset_id: string;
  name: string;
  description?: string;
  attribute_type: 'tag_reference' | 'static' | 'calculated';
  tag_id?: string;
  static_value?: string;
  formula?: string;
  unit?: string;
  display_order: number;
  settings: Record<string, any>;
  created_at: string;
  updated_at: string;

  // Computed values
  current_value?: any;
  calculated_value?: number;
}

// Context state interface
interface AssetContextState {
  // Assets
  assets: Asset[];
  assetTree: AssetTreeNode[];
  loading: boolean;
  error: string | null;

  // Selected asset
  selectedAsset: Asset | null;
  selectedAssetAttributes: AssetAttribute[];

  // Operations
  fetchAssets: () => Promise<void>;
  fetchAssetTree: (rootId?: string) => Promise<void>;
  selectAsset: (assetId: string | null) => Promise<void>;
  createAsset: (asset: Partial<Asset>) => Promise<Asset | null>;
  updateAsset: (assetId: string, updates: Partial<Asset>) => Promise<Asset | null>;
  deleteAsset: (assetId: string) => Promise<boolean>;

  // Attribute operations
  fetchAssetAttributes: (assetId: string) => Promise<void>;
  createAssetAttribute: (assetId: string, attribute: Partial<AssetAttribute>) => Promise<AssetAttribute | null>;

  // Utility
  findAssetById: (assetId: string) => Asset | null;
  findAssetByIdInTree: (assetId: string, tree?: AssetTreeNode[]) => AssetTreeNode | null;
}

const AssetContext = createContext<AssetContextState | undefined>(undefined);

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const AssetProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [assetTree, setAssetTree] = useState<AssetTreeNode[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
  const [selectedAssetAttributes, setSelectedAssetAttributes] = useState<AssetAttribute[]>([]);

  // Fetch all assets (flat list)
  const fetchAssets = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.get(`${API_BASE_URL}/assets/`, {
        params: { limit: 1000 }
      });
      setAssets(response.data);
    } catch (err: any) {
      console.error('Error fetching assets:', err);
      setError(err.message || 'Failed to fetch assets');
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch asset tree (hierarchical structure)
  const fetchAssetTree = useCallback(async (rootId?: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.get(`${API_BASE_URL}/assets/tree`, {
        params: rootId ? { root_id: rootId } : {}
      });
      setAssetTree(response.data);
    } catch (err: any) {
      console.error('Error fetching asset tree:', err);
      setError(err.message || 'Failed to fetch asset tree');
    } finally {
      setLoading(false);
    }
  }, []);

  // Select an asset and fetch its attributes
  const selectAsset = useCallback(async (assetId: string | null) => {
    if (!assetId) {
      setSelectedAsset(null);
      setSelectedAssetAttributes([]);
      return;
    }

    try {
      // Fetch asset details
      const assetResponse = await axios.get(`${API_BASE_URL}/assets/${assetId}`);
      setSelectedAsset(assetResponse.data);

      // Fetch asset attributes
      await fetchAssetAttributes(assetId);
    } catch (err: any) {
      console.error('Error selecting asset:', err);
      setError(err.message || 'Failed to select asset');
    }
  }, []);

  // Fetch attributes for an asset
  const fetchAssetAttributes = useCallback(async (assetId: string) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/assets/${assetId}/attributes`);
      setSelectedAssetAttributes(response.data);
    } catch (err: any) {
      console.error('Error fetching asset attributes:', err);
      setError(err.message || 'Failed to fetch asset attributes');
    }
  }, []);

  // Create a new asset
  const createAsset = useCallback(async (asset: Partial<Asset>): Promise<Asset | null> => {
    try {
      const response = await axios.post(`${API_BASE_URL}/assets/`, asset);
      const newAsset = response.data;

      // Refresh assets and tree
      await fetchAssets();
      await fetchAssetTree();

      return newAsset;
    } catch (err: any) {
      console.error('Error creating asset:', err);
      setError(err.message || 'Failed to create asset');
      return null;
    }
  }, [fetchAssets, fetchAssetTree]);

  // Update an asset
  const updateAsset = useCallback(async (assetId: string, updates: Partial<Asset>): Promise<Asset | null> => {
    try {
      const response = await axios.put(`${API_BASE_URL}/assets/${assetId}`, updates);
      const updatedAsset = response.data;

      // Update local state
      setAssets(prev => prev.map(a => a.id === assetId ? updatedAsset : a));

      // If this is the selected asset, update it
      if (selectedAsset?.id === assetId) {
        setSelectedAsset(updatedAsset);
      }

      // Refresh tree
      await fetchAssetTree();

      return updatedAsset;
    } catch (err: any) {
      console.error('Error updating asset:', err);
      setError(err.message || 'Failed to update asset');
      return null;
    }
  }, [selectedAsset, fetchAssetTree]);

  // Delete an asset
  const deleteAsset = useCallback(async (assetId: string): Promise<boolean> => {
    try {
      await axios.delete(`${API_BASE_URL}/assets/${assetId}`);

      // Remove from local state
      setAssets(prev => prev.filter(a => a.id !== assetId));

      // If this was the selected asset, clear selection
      if (selectedAsset?.id === assetId) {
        setSelectedAsset(null);
        setSelectedAssetAttributes([]);
      }

      // Refresh tree
      await fetchAssetTree();

      return true;
    } catch (err: any) {
      console.error('Error deleting asset:', err);
      setError(err.message || 'Failed to delete asset');
      return false;
    }
  }, [selectedAsset, fetchAssetTree]);

  // Create an asset attribute
  const createAssetAttribute = useCallback(async (
    assetId: string,
    attribute: Partial<AssetAttribute>
  ): Promise<AssetAttribute | null> => {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/assets/${assetId}/attributes`,
        attribute
      );
      const newAttribute = response.data;

      // Update local state if this is the selected asset
      if (selectedAsset?.id === assetId) {
        setSelectedAssetAttributes(prev => [...prev, newAttribute]);
      }

      return newAttribute;
    } catch (err: any) {
      console.error('Error creating asset attribute:', err);
      setError(err.message || 'Failed to create asset attribute');
      return null;
    }
  }, [selectedAsset]);

  // Find asset by ID in flat list
  const findAssetById = useCallback((assetId: string): Asset | null => {
    return assets.find(a => a.id === assetId) || null;
  }, [assets]);

  // Find asset by ID in tree (recursive)
  const findAssetByIdInTree = useCallback((
    assetId: string,
    tree: AssetTreeNode[] = assetTree
  ): AssetTreeNode | null => {
    for (const node of tree) {
      if (node.id === assetId) {
        return node;
      }

      if (node.children && node.children.length > 0) {
        const found = findAssetByIdInTree(assetId, node.children);
        if (found) {
          return found;
        }
      }
    }

    return null;
  }, [assetTree]);

  // Load assets on mount
  useEffect(() => {
    // Temporarily disabled - assets feature not in use yet
    // fetchAssets();
    // fetchAssetTree();
  }, [fetchAssets, fetchAssetTree]);

  const value: AssetContextState = {
    assets,
    assetTree,
    loading,
    error,
    selectedAsset,
    selectedAssetAttributes,
    fetchAssets,
    fetchAssetTree,
    selectAsset,
    createAsset,
    updateAsset,
    deleteAsset,
    fetchAssetAttributes,
    createAssetAttribute,
    findAssetById,
    findAssetByIdInTree,
  };

  return <AssetContext.Provider value={value}>{children}</AssetContext.Provider>;
};

// Hook to use Asset Context
export const useAssets = () => {
  const context = useContext(AssetContext);
  if (context === undefined) {
    throw new Error('useAssets must be used within an AssetProvider');
  }
  return context;
};

export default AssetContext;
