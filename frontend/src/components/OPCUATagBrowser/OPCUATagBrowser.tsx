import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Checkbox,
  TextField,
  Alert,
  CircularProgress,
  Chip,
  IconButton,
  Tooltip,
  Divider,
  Stack,
  FormControlLabel,
} from '@mui/material';
import {
  ChevronRight,
  ExpandMore,
  Folder,
  FolderOpen,
  InsertDriveFile,
  Refresh,
  Save,
  Settings,
} from '@mui/icons-material';
import { apiClient } from '../../api/client';

interface OPCUANode {
  node_id: string;
  browse_name: string;
  display_name: string;
  node_class: string;
  data_type?: string;
  value?: any;
  children?: OPCUANode[];
  has_children: boolean;
}

interface SelectedTag {
  tag_name: string;
  description?: string;
  node_id: string;
  data_type: string;
  unit?: string;
  sample_interval_ms: number;
  enabled: boolean;
}

interface OPCUATagBrowserProps {
  deviceId: number;
  deviceName: string;
  onTagsConfigured?: () => void;
}

const TreeNode: React.FC<{
  node: OPCUANode;
  level: number;
  selectedTags: Map<string, SelectedTag>;
  onToggleTag: (node: OPCUANode) => void;
}> = ({ node, level, selectedTags, onToggleTag }) => {
  const [expanded, setExpanded] = useState(level === 0);
  const isVariable = node.node_class === 'Variable';
  const hasChildren = node.children && node.children.length > 0;
  const isSelected = selectedTags.has(node.node_id);

  const handleToggle = () => {
    if (hasChildren) {
      setExpanded(!expanded);
    }
  };

  const handleCheckboxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.stopPropagation();
    if (isVariable) {
      onToggleTag(node);
    }
  };

  return (
    <Box>
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          py: 0.5,
          px: 1,
          ml: level * 3,
          cursor: hasChildren ? 'pointer' : 'default',
          '&:hover': {
            bgcolor: 'action.hover',
          },
          borderRadius: 1,
        }}
        onClick={handleToggle}
      >
        {/* Expand/Collapse Icon */}
        {hasChildren ? (
          <IconButton size="small" sx={{ mr: 0.5 }}>
            {expanded ? <ExpandMore /> : <ChevronRight />}
          </IconButton>
        ) : (
          <Box sx={{ width: 32 }} />
        )}

        {/* Node Icon */}
        {hasChildren ? (
          expanded ? (
            <FolderOpen sx={{ mr: 1, color: 'primary.main' }} />
          ) : (
            <Folder sx={{ mr: 1, color: 'action.active' }} />
          )
        ) : (
          <InsertDriveFile sx={{ mr: 1, color: 'text.secondary', fontSize: 20 }} />
        )}

        {/* Checkbox for Variables */}
        {isVariable && (
          <Checkbox
            size="small"
            checked={isSelected}
            onChange={handleCheckboxChange}
            onClick={(e) => e.stopPropagation()}
            sx={{ mr: 1 }}
          />
        )}

        {/* Node Name */}
        <Typography
          variant="body2"
          sx={{
            flex: 1,
            fontWeight: isVariable ? 400 : 500,
            color: isVariable ? 'text.primary' : 'text.secondary',
          }}
        >
          {node.display_name}
        </Typography>

        {/* Node Class Badge */}
        <Chip
          label={node.node_class}
          size="small"
          sx={{ mr: 1, height: 20, fontSize: '0.7rem' }}
          color={isVariable ? 'primary' : 'default'}
        />

        {/* Data Type */}
        {isVariable && node.data_type && (
          <Chip
            label={node.data_type.split(';').pop() || 'Unknown'}
            size="small"
            sx={{ mr: 1, height: 20, fontSize: '0.7rem' }}
            variant="outlined"
          />
        )}

        {/* Current Value */}
        {isVariable && node.value !== undefined && (
          <Typography variant="caption" sx={{ color: 'success.main', minWidth: 80, textAlign: 'right' }}>
            {typeof node.value === 'boolean' ? (node.value ? 'TRUE' : 'FALSE') : node.value}
          </Typography>
        )}
      </Box>

      {/* Render children */}
      {expanded && hasChildren && (
        <Box>
          {node.children!.map((child) => (
            <TreeNode
              key={child.node_id}
              node={child}
              level={level + 1}
              selectedTags={selectedTags}
              onToggleTag={onToggleTag}
            />
          ))}
        </Box>
      )}
    </Box>
  );
};

export const OPCUATagBrowser: React.FC<OPCUATagBrowserProps> = ({
  deviceId,
  deviceName,
  onTagsConfigured,
}) => {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [nodes, setNodes] = useState<OPCUANode[]>([]);
  const [selectedTags, setSelectedTags] = useState<Map<string, SelectedTag>>(new Map());
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [maxDepth, setMaxDepth] = useState(3);
  const [defaultInterval, setDefaultInterval] = useState(1000);

  const loadOPCUATags = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.get(`/api/v1/opcua/devices/${deviceId}/opcua/browse`, {
        params: { max_depth: maxDepth },
      });
      setNodes(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to browse OPC UA tags');
      console.error('Error browsing OPC UA tags:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOPCUATags();
  }, [deviceId]);

  const handleToggleTag = (node: OPCUANode) => {
    const newSelected = new Map(selectedTags);

    if (newSelected.has(node.node_id)) {
      newSelected.delete(node.node_id);
    } else {
      // Infer data type from OPC UA data type
      let dataType = 'float';
      if (node.data_type) {
        const typeStr = node.data_type.toLowerCase();
        if (typeStr.includes('boolean')) dataType = 'boolean';
        else if (typeStr.includes('string')) dataType = 'string';
        else if (typeStr.includes('int')) dataType = 'int';
      }

      newSelected.set(node.node_id, {
        tag_name: node.browse_name,
        description: node.display_name,
        node_id: node.node_id,
        data_type: dataType,
        unit: '',
        sample_interval_ms: defaultInterval,
        enabled: true,
      });
    }

    setSelectedTags(newSelected);
  };

  const handleSaveTags = async () => {
    if (selectedTags.size === 0) {
      setError('Please select at least one tag');
      return;
    }

    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await apiClient.post(
        `/api/v1/opcua/devices/${deviceId}/opcua/configure-tags`,
        {
          device_id: deviceId,
          tags: Array.from(selectedTags.values()),
        }
      );

      setSuccess(
        `✅ ${response.data.message}\n` +
        `Created: ${response.data.created_count}, ` +
        `Skipped: ${response.data.skipped_count}, ` +
        `Errors: ${response.data.error_count}`
      );

      // Clear selection after successful save
      setSelectedTags(new Map());

      if (onTagsConfigured) {
        onTagsConfigured();
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to configure tags');
      console.error('Error configuring tags:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleSelectAll = () => {
    const collectVariables = (nodes: OPCUANode[]): OPCUANode[] => {
      let variables: OPCUANode[] = [];
      for (const node of nodes) {
        if (node.node_class === 'Variable') {
          variables.push(node);
        }
        if (node.children) {
          variables = variables.concat(collectVariables(node.children));
        }
      }
      return variables;
    };

    const allVariables = collectVariables(nodes);
    const newSelected = new Map<string, SelectedTag>();

    allVariables.forEach((node) => {
      let dataType = 'float';
      if (node.data_type) {
        const typeStr = node.data_type.toLowerCase();
        if (typeStr.includes('boolean')) dataType = 'boolean';
        else if (typeStr.includes('string')) dataType = 'string';
        else if (typeStr.includes('int')) dataType = 'int';
      }

      newSelected.set(node.node_id, {
        tag_name: node.browse_name,
        description: node.display_name,
        node_id: node.node_id,
        data_type: dataType,
        unit: '',
        sample_interval_ms: defaultInterval,
        enabled: true,
      });
    });

    setSelectedTags(newSelected);
  };

  const handleClearSelection = () => {
    setSelectedTags(new Map());
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Stack direction="row" alignItems="center" justifyContent="space-between" mb={2}>
          <Box>
            <Typography variant="h6">OPC UA Tag Browser</Typography>
            <Typography variant="body2" color="text.secondary">
              Device: {deviceName} (ID: {deviceId})
            </Typography>
          </Box>
          <Stack direction="row" spacing={1}>
            <Tooltip title="Refresh tag tree">
              <IconButton onClick={loadOPCUATags} disabled={loading}>
                <Refresh />
              </IconButton>
            </Tooltip>
          </Stack>
        </Stack>

        <Divider sx={{ my: 2 }} />

        {/* Configuration Options */}
        <Stack direction="row" spacing={2} alignItems="center">
          <TextField
            label="Max Depth"
            type="number"
            size="small"
            value={maxDepth}
            onChange={(e) => setMaxDepth(parseInt(e.target.value) || 3)}
            sx={{ width: 120 }}
          />
          <TextField
            label="Sample Interval (ms)"
            type="number"
            size="small"
            value={defaultInterval}
            onChange={(e) => setDefaultInterval(parseInt(e.target.value) || 1000)}
            sx={{ width: 180 }}
          />
          <Button variant="outlined" onClick={loadOPCUATags} disabled={loading}>
            Reload Tree
          </Button>
        </Stack>
      </Paper>

      {/* Alerts */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert severity="success" onClose={() => setSuccess(null)} sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      {/* Tree View */}
      <Paper sx={{ flex: 1, overflow: 'auto', p: 2, mb: 2 }}>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 200 }}>
            <CircularProgress />
          </Box>
        ) : nodes.length === 0 ? (
          <Alert severity="info">
            No OPC UA nodes found. Make sure the OPC UA server is running and accessible.
          </Alert>
        ) : (
          <Box>
            {nodes.map((node) => (
              <TreeNode
                key={node.node_id}
                node={node}
                level={0}
                selectedTags={selectedTags}
                onToggleTag={handleToggleTag}
              />
            ))}
          </Box>
        )}
      </Paper>

      {/* Actions */}
      <Paper sx={{ p: 2 }}>
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Stack direction="row" spacing={1}>
            <Button variant="outlined" onClick={handleSelectAll} disabled={loading || nodes.length === 0}>
              Select All Variables
            </Button>
            <Button variant="outlined" onClick={handleClearSelection} disabled={selectedTags.size === 0}>
              Clear Selection
            </Button>
          </Stack>

          <Stack direction="row" spacing={2} alignItems="center">
            <Typography variant="body2" color="text.secondary">
              Selected: <strong>{selectedTags.size}</strong> tags
            </Typography>
            <Button
              variant="contained"
              startIcon={saving ? <CircularProgress size={20} /> : <Save />}
              onClick={handleSaveTags}
              disabled={selectedTags.size === 0 || saving}
            >
              {saving ? 'Saving...' : 'Configure Tags'}
            </Button>
          </Stack>
        </Stack>
      </Paper>
    </Box>
  );
};
