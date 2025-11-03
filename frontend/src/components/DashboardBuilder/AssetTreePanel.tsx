/**
 * Asset Tree Panel - Hierarchical asset browser (PI Vision AF-style)
 * Replaces/enhances flat TagsPanel with tree navigation
 */

import React, { useState, useMemo, useEffect } from 'react';
import {
  Search,
  Plus,
  RefreshCw,
  FolderTree,
  ChevronDown,
  ChevronRight,
  Eye,
  EyeOff,
  PlusCircle,
} from 'lucide-react';
import { useAssets, AssetType } from '../../contexts/AssetContext';
import { AssetNode } from './AssetNode';
import { AssetModal } from './AssetModal';
import { AssetAttributeEditor } from './AssetAttributeEditor';

interface AssetTreePanelProps {
  onClose: () => void;
  onEditAsset?: (asset: any) => void;
  showInactive?: boolean;
}

export const AssetTreePanel: React.FC<AssetTreePanelProps> = ({
  onClose,
  onEditAsset,
  showInactive: initialShowInactive = false,
}) => {
  const {
    assetTree,
    loading,
    error,
    selectedAsset,
    selectedAssetAttributes,
    fetchAssetTree,
    selectAsset,
    deleteAsset,
  } = useAssets();

  const [search, setSearch] = useState('');
  const [filterType, setFilterType] = useState<string>('all');
  const [showInactive, setShowInactive] = useState(initialShowInactive);
  const [expandedPaths, setExpandedPaths] = useState<Set<string>>(new Set());

  // Modal states
  const [showAssetModal, setShowAssetModal] = useState(false);
  const [editingAsset, setEditingAsset] = useState<any>(null);
  const [showAttributeEditor, setShowAttributeEditor] = useState(false);

  // Asset types for filter
  const assetTypes: Array<{ value: string; label: string }> = [
    { value: 'all', label: 'Todos os Tipos' },
    { value: 'enterprise', label: 'Empresa' },
    { value: 'site', label: 'Site/Planta' },
    { value: 'area', label: 'Área' },
    { value: 'unit', label: 'Unidade' },
    { value: 'equipment', label: 'Equipamento' },
    { value: 'component', label: 'Componente' },
  ];

  // Filter tree based on search and filters
  const filteredTree = useMemo(() => {
    if (!search && filterType === 'all' && showInactive) {
      return assetTree;
    }

    const filterNode = (node: any): any | null => {
      // Check if node matches filters
      const matchesSearch = !search ||
        node.name.toLowerCase().includes(search.toLowerCase()) ||
        node.description?.toLowerCase().includes(search.toLowerCase());

      const matchesType = filterType === 'all' || node.asset_type === filterType;

      const matchesActive = showInactive || node.is_active;

      // Filter children recursively
      const filteredChildren = node.children
        ? node.children.map(filterNode).filter(Boolean)
        : [];

      // Include node if it matches OR if any children match
      const shouldInclude = (matchesSearch && matchesType && matchesActive) || filteredChildren.length > 0;

      if (!shouldInclude) {
        return null;
      }

      return {
        ...node,
        children: filteredChildren,
      };
    };

    return assetTree.map(filterNode).filter(Boolean);
  }, [assetTree, search, filterType, showInactive]);

  // Count total assets in tree
  const countAssets = (nodes: any[]): number => {
    let count = 0;
    for (const node of nodes) {
      count += 1;
      if (node.children) {
        count += countAssets(node.children);
      }
    }
    return count;
  };

  const totalAssets = useMemo(() => countAssets(filteredTree), [filteredTree]);

  const handleRefresh = () => {
    fetchAssetTree();
  };

  const handleSelectAsset = (assetId: string) => {
    selectAsset(assetId);
  };

  const handleDeleteAsset = async (assetId: string) => {
    const success = await deleteAsset(assetId);
    if (success) {
      // Refresh tree after delete
      await fetchAssetTree();
    }
  };

  const handleEditAsset = (asset: any) => {
    setEditingAsset(asset);
    setShowAssetModal(true);
  };

  const handleCreateAsset = () => {
    setEditingAsset(null);
    setShowAssetModal(true);
  };

  const handleCreateAttribute = () => {
    if (selectedAsset) {
      setShowAttributeEditor(true);
    }
  };

  const toggleShowInactive = () => {
    setShowInactive(!showInactive);
  };

  return (
    <div className="w-96 bg-gray-50 dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 flex flex-col">
      {/* Header */}
      <div className="px-4 py-3 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <FolderTree className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Asset Framework
            </h2>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleCreateAsset}
              className="p-1.5 text-gray-400 hover:text-green-600 dark:hover:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20 rounded transition-colors"
              title="Criar novo asset"
            >
              <Plus className="w-4 h-4" />
            </button>

            <button
              onClick={handleRefresh}
              disabled={loading}
              className="p-1.5 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded transition-colors disabled:opacity-50"
              title="Atualizar árvore"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>

            <button
              onClick={onClose}
              className="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
              title="Fechar painel"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Buscar assets..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
          />
        </div>

        {/* Filters */}
        <div className="flex items-center gap-2 mt-2">
          {/* Type Filter */}
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
          >
            {assetTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>

          {/* Show Inactive Toggle */}
          <button
            onClick={toggleShowInactive}
            className={`
              p-2 rounded border transition-colors
              ${showInactive
                ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-300 dark:border-blue-700 text-blue-600 dark:text-blue-400'
                : 'bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'
              }
            `}
            title={showInactive ? 'Ocultar inativos' : 'Mostrar inativos'}
          >
            {showInactive ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
          </button>
        </div>

        {/* Stats */}
        <div className="mt-2 flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
          <span>
            {totalAssets} asset{totalAssets !== 1 ? 's' : ''}
            {search && ' (filtrado)'}
          </span>

          {selectedAsset && (
            <span className="text-blue-600 dark:text-blue-400">
              {selectedAssetAttributes.length} atributo{selectedAssetAttributes.length !== 1 ? 's' : ''}
            </span>
          )}
        </div>
      </div>

      {/* Asset Tree */}
      <div className="flex-1 overflow-y-auto p-3">
        {loading && assetTree.length === 0 ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
            Carregando assets...
          </div>
        ) : error ? (
          <div className="text-center py-8 text-red-500 dark:text-red-400">
            <p className="font-medium">Erro ao carregar assets</p>
            <p className="text-sm mt-1">{error}</p>
            <button
              onClick={handleRefresh}
              className="mt-3 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
            >
              Tentar novamente
            </button>
          </div>
        ) : filteredTree.length === 0 ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <FolderTree className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p className="font-medium">Nenhum asset encontrado</p>
            {search && (
              <p className="text-sm mt-2">
                Tente outro termo de busca
              </p>
            )}
            {!search && assetTree.length === 0 && (
              <p className="text-sm mt-2">
                Comece criando um asset raiz
              </p>
            )}
          </div>
        ) : (
          <div>
            {filteredTree.map((rootAsset) => (
              <AssetNode
                key={rootAsset.id}
                asset={rootAsset}
                level={0}
                onSelectAsset={handleSelectAsset}
                onEditAsset={handleEditAsset}
                onDeleteAsset={handleDeleteAsset}
                selectedAssetId={selectedAsset?.id}
                enableDrag={true}
              />
            ))}
          </div>
        )}
      </div>

      {/* Selected Asset Details */}
      {selectedAsset && (
        <div className="px-4 py-3 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
          <div className="mb-2">
            <p className="text-sm font-medium text-gray-900 dark:text-white">
              {selectedAsset.name}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {selectedAsset.full_path}
            </p>
          </div>

          <div className="mt-2">
            <div className="flex items-center justify-between mb-1">
              <p className="text-xs font-medium text-gray-700 dark:text-gray-300">
                Atributos:
              </p>
              <button
                onClick={handleCreateAttribute}
                className="p-1 text-green-600 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20 rounded transition-colors"
                title="Adicionar atributo"
              >
                <PlusCircle className="w-3.5 h-3.5" />
              </button>
            </div>

            {selectedAssetAttributes.length > 0 ? (
              <div className="space-y-1 max-h-32 overflow-y-auto">
                {selectedAssetAttributes.map((attr) => (
                  <div
                    key={attr.id}
                    className="flex items-center justify-between px-2 py-1 bg-gray-50 dark:bg-gray-700 rounded text-xs"
                  >
                    <span className="font-medium text-gray-700 dark:text-gray-300">
                      {attr.name}
                    </span>
                    {attr.unit && (
                      <span className="text-gray-500 dark:text-gray-400">
                        {attr.unit}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-gray-500 dark:text-gray-400 text-center py-2">
                Nenhum atributo. Clique em + para adicionar.
              </p>
            )}
          </div>
        </div>
      )}

      {/* Help */}
      <div className="px-4 py-3 bg-blue-50 dark:bg-blue-900/20 border-t border-blue-200 dark:border-blue-800 text-sm text-blue-800 dark:text-blue-200">
        <p className="font-medium">💡 Como usar:</p>
        <ol className="list-decimal list-inside mt-1 text-xs space-y-1">
          <li>Navegue pela hierarquia de assets</li>
          <li>Arraste um asset para um widget</li>
          <li>Atributos do asset serão vinculados automaticamente</li>
          <li>Use os filtros para encontrar assets específicos</li>
        </ol>
      </div>

      {/* Modals */}
      <AssetModal
        isOpen={showAssetModal}
        onClose={() => {
          setShowAssetModal(false);
          setEditingAsset(null);
        }}
        asset={editingAsset}
        defaultParentId={selectedAsset?.id}
      />

      <AssetAttributeEditor
        isOpen={showAttributeEditor}
        onClose={() => setShowAttributeEditor(false)}
        assetId={selectedAsset?.id || ''}
      />
    </div>
  );
};

export default AssetTreePanel;
