/**
 * Asset Tree View - Hierarchical Navigation
 *
 * Tree view for navigating asset hierarchy with:
 * - Expandable/collapsible nodes
 * - Asset icons and status
 * - Tag count indicators
 * - Drag & drop support (future)
 * - Search and filter
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Chip,
  IconButton,
  TextField,
  InputAdornment,
  CircularProgress,
  Tooltip
} from '@mui/material';
import { SimpleTreeView } from '@mui/x-tree-view/SimpleTreeView';
import { TreeItem } from '@mui/x-tree-view/TreeItem';
import {
  ExpandMore as ExpandMoreIcon,
  ChevronRight as ChevronRightIcon,
  Folder as FolderIcon,
  FolderOpen as FolderOpenIcon,
  Business as SiteIcon,
  ViewModule as AreaIcon,
  Factory as UnitIcon,
  Settings as EquipmentIcon,
  Label as TagIcon,
  Search as SearchIcon,
  FilterList as FilterIcon
} from '@mui/icons-material';
import axios from 'axios';

interface Asset {
  id: string;
  name: string;
  asset_type: 'site' | 'area' | 'unit' | 'equipment' | 'tag_group';
  parent_id?: string;
  description?: string;
  is_active: boolean;
  children?: Asset[];
  tags_count?: number;
}

interface AssetTreeViewProps {
  onAssetSelect?: (asset: Asset) => void;
  onTagsRequest?: (assetId: string) => void;
  selectedAssetId?: string;
}

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Create axios instance with auth
const client = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const AssetTreeView: React.FC<AssetTreeViewProps> = ({
  onAssetSelect,
  onTagsRequest,
  selectedAssetId
}) => {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState<string[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredAssets, setFilteredAssets] = useState<Asset[]>([]);

  // Load assets from API
  useEffect(() => {
    loadAssets();
  }, []);

  const loadAssets = async () => {
    setLoading(true);
    try {
      const response = await client.get('/api/v1/assets/');
      const assetsData = response.data;

      // Build tree structure
      const tree = buildTree(assetsData);
      setAssets(tree);
      setFilteredAssets(tree);
    } catch (error) {
      console.error('Error loading assets:', error);
    } finally {
      setLoading(false);
    }
  };

  // Build hierarchical tree from flat list
  const buildTree = (flatList: Asset[]): Asset[] => {
    const map = new Map<string, Asset>();
    const roots: Asset[] = [];

    // Create map of all assets
    flatList.forEach(asset => {
      map.set(asset.id, { ...asset, children: [] });
    });

    // Build tree
    flatList.forEach(asset => {
      const node = map.get(asset.id)!;
      if (asset.parent_id) {
        const parent = map.get(asset.parent_id);
        if (parent) {
          if (!parent.children) parent.children = [];
          parent.children.push(node);
        } else {
          roots.push(node);
        }
      } else {
        roots.push(node);
      }
    });

    return roots;
  };

  // Filter assets by search term
  useEffect(() => {
    if (!searchTerm.trim()) {
      setFilteredAssets(assets);
      return;
    }

    const filterTree = (nodes: Asset[]): Asset[] => {
      return nodes
        .map(node => {
          const matches = node.name.toLowerCase().includes(searchTerm.toLowerCase());
          const filteredChildren = node.children ? filterTree(node.children) : [];

          if (matches || filteredChildren.length > 0) {
            return {
              ...node,
              children: filteredChildren
            };
          }
          return null;
        })
        .filter((node): node is Asset => node !== null);
    };

    const filtered = filterTree(assets);
    setFilteredAssets(filtered);

    // Auto-expand all nodes when searching
    if (searchTerm.trim()) {
      const allIds = getAllAssetIds(filtered);
      setExpanded(allIds);
    }
  }, [searchTerm, assets]);

  // Get all asset IDs recursively
  const getAllAssetIds = (nodes: Asset[]): string[] => {
    const ids: string[] = [];
    nodes.forEach(node => {
      ids.push(node.id);
      if (node.children) {
        ids.push(...getAllAssetIds(node.children));
      }
    });
    return ids;
  };

  // Get icon for asset type
  const getAssetIcon = (type: string, hasChildren: boolean, isExpanded: boolean) => {
    if (type === 'site') return <SiteIcon color="primary" />;
    if (type === 'area') return <AreaIcon color="secondary" />;
    if (type === 'unit') return <UnitIcon color="action" />;
    if (type === 'equipment') return <EquipmentIcon color="action" />;
    if (type === 'tag_group') return <TagIcon color="action" />;

    return hasChildren ? (
      isExpanded ? <FolderOpenIcon /> : <FolderIcon />
    ) : <FolderIcon />;
  };

  // Handle node toggle
  const handleToggle = (event: React.SyntheticEvent, nodeIds: string[]) => {
    setExpanded(nodeIds);
  };

  // Handle node select
  const handleSelect = (event: React.SyntheticEvent, nodeId: string | null) => {
    if (!nodeId) return;
    const asset = findAssetById(assets, nodeId);
    if (asset) {
      onAssetSelect?.(asset);
      if (asset.tags_count && asset.tags_count > 0) {
        onTagsRequest?.(asset.id);
      }
    }
  };

  // Find asset by ID in tree
  const findAssetById = (nodes: Asset[], id: string): Asset | null => {
    for (const node of nodes) {
      if (node.id === id) return node;
      if (node.children) {
        const found = findAssetById(node.children, id);
        if (found) return found;
      }
    }
    return null;
  };

  // Render tree recursively
  const renderTree = (nodes: Asset[]) => {
    return nodes.map((node) => {
      const hasChildren = node.children && node.children.length > 0;
      const isExpanded = expanded.includes(node.id);

      return (
        <TreeItem
          key={node.id}
          nodeId={node.id}
          label={
            <Box sx={{ display: 'flex', alignItems: 'center', py: 0.5 }}>
              <Box sx={{ mr: 1 }}>
                {getAssetIcon(node.asset_type, hasChildren || false, isExpanded)}
              </Box>
              <Typography variant="body2" sx={{ flexGrow: 1 }}>
                {node.name}
              </Typography>
              {node.tags_count !== undefined && node.tags_count > 0 && (
                <Tooltip title={`${node.tags_count} tag(s)`}>
                  <Chip
                    label={node.tags_count}
                    size="small"
                    color="primary"
                    sx={{ ml: 1, height: 20, fontSize: '0.7rem' }}
                  />
                </Tooltip>
              )}
              {!node.is_active && (
                <Chip
                  label="Inativo"
                  size="small"
                  color="error"
                  variant="outlined"
                  sx={{ ml: 1, height: 20, fontSize: '0.7rem' }}
                />
              )}
            </Box>
          }
          sx={{
            '& .MuiTreeItem-content': {
              py: 0.5,
              backgroundColor: selectedAssetId === node.id ? 'action.selected' : 'transparent',
              '&:hover': {
                backgroundColor: 'action.hover'
              },
              '&.Mui-selected': {
                backgroundColor: 'action.selected',
                '&:hover': {
                  backgroundColor: 'action.selected'
                }
              }
            }
          }}
        >
          {hasChildren && renderTree(node.children!)}
        </TreeItem>
      );
    });
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Search */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <TextField
          fullWidth
          size="small"
          placeholder="Buscar assets..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon fontSize="small" />
              </InputAdornment>
            )
          }}
        />
      </Box>

      {/* Tree */}
      <Box sx={{ flex: 1, overflow: 'auto', p: 1 }}>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : filteredAssets.length === 0 ? (
          <Box sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              {searchTerm ? 'Nenhum asset encontrado' : 'Nenhum asset cadastrado'}
            </Typography>
          </Box>
        ) : (
          <SimpleTreeView
            aria-label="asset navigator"
            defaultCollapseIcon={<ExpandMoreIcon />}
            defaultExpandIcon={<ChevronRightIcon />}
            expanded={expanded}
            selected={selectedAssetId || ''}
            onNodeToggle={handleToggle}
            onNodeSelect={handleSelect}
            sx={{
              flexGrow: 1,
              overflowY: 'auto',
              minHeight: 200
            }}
          >
            {renderTree(filteredAssets)}
          </SimpleTreeView>
        )}
      </Box>

      {/* Footer Stats */}
      <Box
        sx={{
          p: 1,
          borderTop: 1,
          borderColor: 'divider',
          backgroundColor: 'background.default'
        }}
      >
        <Typography variant="caption" color="text.secondary">
          {filteredAssets.length} asset(s) {searchTerm && '(filtrado)'}
        </Typography>
      </Box>
    </Box>
  );
};

export default AssetTreeView;
