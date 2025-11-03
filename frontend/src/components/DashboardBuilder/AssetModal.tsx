/**
 * Asset Modal - Create/Edit Asset
 * Modal dialog for creating new assets or editing existing ones
 */

import React, { useState, useEffect } from 'react';
import {
  X,
  Save,
  Building,
  MapPin,
  Boxes,
  Workflow,
  Cpu,
  Component as ComponentIcon,
  AlertCircle,
} from 'lucide-react';
import { useAssets, Asset, AssetType } from '../../contexts/AssetContext';
import { showToast } from '../../utils/toast';

interface AssetModalProps {
  isOpen: boolean;
  onClose: () => void;
  asset?: Asset | null; // If provided, edit mode; otherwise, create mode
  defaultParentId?: string | null;
}

const ASSET_TYPE_OPTIONS: Array<{ value: AssetType; label: string; icon: React.FC<{ className?: string }> }> = [
  { value: 'enterprise', label: 'Empresa', icon: Building },
  { value: 'site', label: 'Site/Planta', icon: MapPin },
  { value: 'area', label: 'Área', icon: Boxes },
  { value: 'unit', label: 'Unidade', icon: Workflow },
  { value: 'equipment', label: 'Equipamento', icon: Cpu },
  { value: 'component', label: 'Componente', icon: ComponentIcon },
];

export const AssetModal: React.FC<AssetModalProps> = ({
  isOpen,
  onClose,
  asset,
  defaultParentId,
}) => {
  const { assets, createAsset, updateAsset, fetchAssetTree } = useAssets();

  // Form state
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [assetType, setAssetType] = useState<AssetType>('equipment');
  const [parentId, setParentId] = useState<string | null>(null);
  const [isActive, setIsActive] = useState(true);
  const [metadata, setMetadata] = useState<Record<string, string>>({});

  // UI state
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [metadataKey, setMetadataKey] = useState('');
  const [metadataValue, setMetadataValue] = useState('');

  const isEditMode = !!asset;

  // Initialize form with asset data or defaults
  useEffect(() => {
    if (isOpen) {
      if (asset) {
        // Edit mode - populate with asset data
        setName(asset.name);
        setDescription(asset.description || '');
        setAssetType(asset.asset_type);
        setParentId(asset.parent_id || null);
        setIsActive(asset.is_active);
        setMetadata(asset.metadata || {});
      } else {
        // Create mode - reset to defaults
        setName('');
        setDescription('');
        setAssetType('equipment');
        setParentId(defaultParentId || null);
        setIsActive(true);
        setMetadata({});
      }
      setErrors({});
      setMetadataKey('');
      setMetadataValue('');
    }
  }, [isOpen, asset, defaultParentId]);

  // Validation
  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!name.trim()) {
      newErrors.name = 'Nome é obrigatório';
    }

    if (!assetType) {
      newErrors.assetType = 'Tipo de asset é obrigatório';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle save
  const handleSave = async () => {
    if (!validate()) {
      return;
    }

    setLoading(true);

    try {
      const assetData = {
        name: name.trim(),
        description: description.trim() || undefined,
        asset_type: assetType,
        parent_id: parentId || undefined,
        is_active: isActive,
        metadata,
      };

      if (isEditMode && asset) {
        // Update existing asset
        const updated = await updateAsset(asset.id, assetData);
        if (updated) {
          showToast.success(`Asset "${name}" atualizado com sucesso!`);
          await fetchAssetTree(); // Refresh tree
          onClose();
        } else {
          showToast.error('Erro ao atualizar asset');
        }
      } else {
        // Create new asset
        const created = await createAsset(assetData);
        if (created) {
          showToast.success(`Asset "${name}" criado com sucesso!`);
          await fetchAssetTree(); // Refresh tree
          onClose();
        } else {
          showToast.error('Erro ao criar asset');
        }
      }
    } catch (error: any) {
      console.error('Error saving asset:', error);
      showToast.error(error.message || 'Erro ao salvar asset');
    } finally {
      setLoading(false);
    }
  };

  // Add metadata entry
  const handleAddMetadata = () => {
    if (metadataKey.trim() && metadataValue.trim()) {
      setMetadata({
        ...metadata,
        [metadataKey.trim()]: metadataValue.trim(),
      });
      setMetadataKey('');
      setMetadataValue('');
    }
  };

  // Remove metadata entry
  const handleRemoveMetadata = (key: string) => {
    const newMetadata = { ...metadata };
    delete newMetadata[key];
    setMetadata(newMetadata);
  };

  // Get parent asset options (excluding self and descendants in edit mode)
  const getParentOptions = () => {
    if (isEditMode && asset) {
      // In edit mode, exclude self and descendants to prevent circular references
      // For simplicity, just exclude self for now
      return assets.filter(a => a.id !== asset.id);
    }
    return assets;
  };

  if (!isOpen) return null;

  const selectedTypeOption = ASSET_TYPE_OPTIONS.find(opt => opt.value === assetType);
  const TypeIcon = selectedTypeOption?.icon || ComponentIcon;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <TypeIcon className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              {isEditMode ? 'Editar Asset' : 'Criar Novo Asset'}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-4 space-y-4">
          {/* Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Nome <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className={`w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white ${
                errors.name
                  ? 'border-red-500 dark:border-red-400'
                  : 'border-gray-300 dark:border-gray-600'
              }`}
              placeholder="Ex: Correia Transportadora 01"
            />
            {errors.name && (
              <p className="text-sm text-red-500 dark:text-red-400 mt-1 flex items-center gap-1">
                <AlertCircle className="w-4 h-4" />
                {errors.name}
              </p>
            )}
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Descrição
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              placeholder="Descrição detalhada do asset..."
            />
          </div>

          {/* Asset Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Tipo de Asset <span className="text-red-500">*</span>
            </label>
            <div className="grid grid-cols-2 gap-2">
              {ASSET_TYPE_OPTIONS.map((option) => {
                const Icon = option.icon;
                return (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => setAssetType(option.value)}
                    className={`flex items-center gap-2 px-3 py-2 rounded border transition-colors ${
                      assetType === option.value
                        ? 'bg-blue-50 dark:bg-blue-900/30 border-blue-500 text-blue-700 dark:text-blue-300'
                        : 'bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span className="text-sm font-medium">{option.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Parent */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Asset Pai (Opcional)
            </label>
            <select
              value={parentId || ''}
              onChange={(e) => setParentId(e.target.value || null)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
            >
              <option value="">Nenhum (Raiz)</option>
              {getParentOptions().map((a) => (
                <option key={a.id} value={a.id}>
                  {a.full_path || a.name} ({a.asset_type})
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Selecione o asset pai para criar uma hierarquia
            </p>
          </div>

          {/* Active Status */}
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="isActive"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <label htmlFor="isActive" className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Asset ativo
            </label>
          </div>

          {/* Metadata */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Metadata (Informações Adicionais)
            </label>

            {/* Existing metadata */}
            {Object.keys(metadata).length > 0 && (
              <div className="space-y-2 mb-2">
                {Object.entries(metadata).map(([key, value]) => (
                  <div
                    key={key}
                    className="flex items-center justify-between px-3 py-2 bg-gray-50 dark:bg-gray-700 rounded"
                  >
                    <div className="flex-1">
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        {key}:
                      </span>{' '}
                      <span className="text-sm text-gray-600 dark:text-gray-400">{value}</span>
                    </div>
                    <button
                      onClick={() => handleRemoveMetadata(key)}
                      className="p-1 text-red-500 hover:text-red-700 dark:hover:text-red-400"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* Add metadata */}
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Chave (ex: capacidade)"
                value={metadataKey}
                onChange={(e) => setMetadataKey(e.target.value)}
                className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white text-sm"
              />
              <input
                type="text"
                placeholder="Valor (ex: 10000 ton)"
                value={metadataValue}
                onChange={(e) => setMetadataValue(e.target.value)}
                className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white text-sm"
              />
              <button
                onClick={handleAddMetadata}
                disabled={!metadataKey.trim() || !metadataValue.trim()}
                className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
              >
                Adicionar
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 px-6 py-4 bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={onClose}
            disabled={loading}
            className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Cancelar
          </button>
          <button
            onClick={handleSave}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>Salvando...</span>
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                <span>{isEditMode ? 'Salvar Alterações' : 'Criar Asset'}</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default AssetModal;
