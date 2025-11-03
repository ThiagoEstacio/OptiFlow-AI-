/**
 * Asset Node - Draggable hierarchical asset node with expand/collapse
 * Represents a single asset in the tree with its attributes
 */

import React, { useState } from 'react';
import { useDrag } from 'react-dnd';
import {
  ChevronRight,
  ChevronDown,
  Building,
  MapPin,
  Boxes,
  Workflow,
  Cpu,
  Component as ComponentIcon,
  Edit2,
  Trash2,
} from 'lucide-react';
import type { AssetTreeNode, AssetType } from '../../contexts/AssetContext';

interface AssetNodeProps {
  asset: AssetTreeNode;
  level: number;
  onSelectAsset: (assetId: string) => void;
  onEditAsset?: (asset: AssetTreeNode) => void;
  onDeleteAsset?: (assetId: string) => void;
  selectedAssetId?: string | null;
  enableDrag?: boolean;
}

// Icon map for asset types
const ASSET_TYPE_ICONS: Record<AssetType, React.FC<{ className?: string }>> = {
  enterprise: Building,
  site: MapPin,
  area: Boxes,
  unit: Workflow,
  equipment: Cpu,
  component: ComponentIcon,
};

// Color map for asset types
const ASSET_TYPE_COLORS: Record<AssetType, string> = {
  enterprise: 'text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-900/20',
  site: 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20',
  area: 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20',
  unit: 'text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20',
  equipment: 'text-orange-600 dark:text-orange-400 bg-orange-50 dark:bg-orange-900/20',
  component: 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20',
};

export const AssetNode: React.FC<AssetNodeProps> = ({
  asset,
  level,
  onSelectAsset,
  onEditAsset,
  onDeleteAsset,
  selectedAssetId,
  enableDrag = true,
}) => {
  const [isExpanded, setIsExpanded] = useState(level < 2); // Auto-expand first 2 levels
  const hasChildren = asset.children && asset.children.length > 0;

  // Drag and drop
  const [{ isDragging }, drag] = useDrag(() => ({
    type: 'ASSET',
    item: {
      assetId: asset.id,
      assetName: asset.name,
      assetType: asset.asset_type,
    },
    canDrag: enableDrag,
    collect: (monitor) => ({
      isDragging: monitor.isDragging(),
    }),
  }));

  const handleToggleExpand = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (hasChildren) {
      setIsExpanded(!isExpanded);
    }
  };

  const handleSelect = () => {
    onSelectAsset(asset.id);
  };

  const handleEdit = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onEditAsset) {
      onEditAsset(asset);
    }
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onDeleteAsset && window.confirm(`Tem certeza que deseja excluir o asset "${asset.name}"? Todos os filhos também serão excluídos.`)) {
      onDeleteAsset(asset.id);
    }
  };

  const Icon = ASSET_TYPE_ICONS[asset.asset_type] || ComponentIcon;
  const colorClass = ASSET_TYPE_COLORS[asset.asset_type] || ASSET_TYPE_COLORS.component;
  const isSelected = selectedAssetId === asset.id;
  const indentWidth = level * 20;

  return (
    <div>
      {/* Asset Node */}
      <div
        ref={enableDrag ? drag : null}
        onClick={handleSelect}
        className={`
          group relative flex items-center gap-2 py-2 px-3 mb-1 rounded
          cursor-pointer transition-all
          ${isDragging ? 'opacity-50 scale-95' : 'opacity-100'}
          ${isSelected
            ? 'bg-blue-100 dark:bg-blue-900/30 border-l-4 border-blue-500'
            : 'bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 border-l-4 border-transparent'
          }
          ${!asset.is_active ? 'opacity-60' : ''}
        `}
        style={{ marginLeft: `${indentWidth}px` }}
      >
        {/* Expand/Collapse Button */}
        <button
          onClick={handleToggleExpand}
          className={`
            flex-shrink-0 w-5 h-5 flex items-center justify-center
            text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200
            ${!hasChildren ? 'invisible' : ''}
          `}
        >
          {hasChildren && (
            isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />
          )}
        </button>

        {/* Asset Icon */}
        <div className={`flex-shrink-0 p-1.5 rounded ${colorClass}`}>
          <Icon className="w-4 h-4" />
        </div>

        {/* Asset Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p className={`text-sm font-medium truncate ${isSelected ? 'text-blue-700 dark:text-blue-300' : 'text-gray-900 dark:text-white'}`}>
              {asset.name}
            </p>

            {/* Badges */}
            <div className="flex items-center gap-1">
              {hasChildren && (
                <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600 dark:bg-gray-600 dark:text-gray-300">
                  {asset.children.length}
                </span>
              )}

              {asset.attributes_count && asset.attributes_count > 0 && (
                <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300">
                  {asset.attributes_count} attr
                </span>
              )}

              {!asset.is_active && (
                <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300">
                  Inativo
                </span>
              )}
            </div>
          </div>

          {asset.description && (
            <p className="text-xs text-gray-500 dark:text-gray-400 truncate mt-0.5">
              {asset.description}
            </p>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex-shrink-0 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          {onEditAsset && (
            <button
              onClick={handleEdit}
              className="p-1 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded transition-colors"
              title="Editar asset"
            >
              <Edit2 className="w-3.5 h-3.5" />
            </button>
          )}

          {onDeleteAsset && (
            <button
              onClick={handleDelete}
              className="p-1 text-gray-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
              title="Excluir asset"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Children (Recursive) */}
      {hasChildren && isExpanded && (
        <div>
          {asset.children.map((child) => (
            <AssetNode
              key={child.id}
              asset={child}
              level={level + 1}
              onSelectAsset={onSelectAsset}
              onEditAsset={onEditAsset}
              onDeleteAsset={onDeleteAsset}
              selectedAssetId={selectedAssetId}
              enableDrag={enableDrag}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default AssetNode;
