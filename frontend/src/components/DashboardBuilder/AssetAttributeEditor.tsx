/**
 * Asset Attribute Editor - Create/Edit Asset Attributes
 * Modal dialog for managing asset attributes (tag references, static, calculated)
 */

import React, { useState, useEffect } from 'react';
import { X, Save, Tag as TagIcon, Hash, Calculator, AlertCircle } from 'lucide-react';
import { useAssets, AssetAttribute } from '../../contexts/AssetContext';
import { useAppSelector } from '../../store';
import { showToast } from '../../utils/toast';

interface AssetAttributeEditorProps {
  isOpen: boolean;
  onClose: () => void;
  assetId: string;
  attribute?: AssetAttribute | null; // If provided, edit mode; otherwise, create mode
}

type AttributeType = 'tag_reference' | 'static' | 'calculated';

const ATTRIBUTE_TYPES: Array<{ value: AttributeType; label: string; icon: React.FC<{ className?: string }>; description: string }> = [
  {
    value: 'tag_reference',
    label: 'Referência a Tag',
    icon: TagIcon,
    description: 'Vincula a um tag do sistema para dados em tempo real',
  },
  {
    value: 'static',
    label: 'Valor Estático',
    icon: Hash,
    description: 'Valor fixo que não muda (ex: capacidade, modelo)',
  },
  {
    value: 'calculated',
    label: 'Calculado',
    icon: Calculator,
    description: 'Calculado por fórmula baseada em outros atributos',
  },
];

export const AssetAttributeEditor: React.FC<AssetAttributeEditorProps> = ({
  isOpen,
  onClose,
  assetId,
  attribute,
}) => {
  const { createAssetAttribute, fetchAssetAttributes } = useAssets();
  const tags = useAppSelector((state) => state.tags.items);

  // Form state
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [attributeType, setAttributeType] = useState<AttributeType>('tag_reference');
  const [tagId, setTagId] = useState<string>('');
  const [staticValue, setStaticValue] = useState('');
  const [formula, setFormula] = useState('');
  const [unit, setUnit] = useState('');
  const [displayOrder, setDisplayOrder] = useState(0);

  // Settings
  const [minValue, setMinValue] = useState<number | ''>('');
  const [maxValue, setMaxValue] = useState<number | ''>('');
  const [warningThreshold, setWarningThreshold] = useState<number | ''>('');
  const [criticalThreshold, setCriticalThreshold] = useState<number | ''>('');

  // UI state
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const isEditMode = !!attribute;

  // Initialize form
  useEffect(() => {
    if (isOpen) {
      if (attribute) {
        // Edit mode - populate with attribute data
        setName(attribute.name);
        setDescription(attribute.description || '');
        setAttributeType(attribute.attribute_type);
        setTagId(attribute.tag_id || '');
        setStaticValue(attribute.static_value || '');
        setFormula(attribute.formula || '');
        setUnit(attribute.unit || '');
        setDisplayOrder(attribute.display_order);

        // Parse settings
        const settings = attribute.settings || {};
        setMinValue(settings.min ?? '');
        setMaxValue(settings.max ?? '');
        setWarningThreshold(settings.warning ?? '');
        setCriticalThreshold(settings.critical ?? '');
      } else {
        // Create mode - reset to defaults
        setName('');
        setDescription('');
        setAttributeType('tag_reference');
        setTagId('');
        setStaticValue('');
        setFormula('');
        setUnit('');
        setDisplayOrder(0);
        setMinValue('');
        setMaxValue('');
        setWarningThreshold('');
        setCriticalThreshold('');
      }
      setErrors({});
    }
  }, [isOpen, attribute]);

  // Validation
  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!name.trim()) {
      newErrors.name = 'Nome é obrigatório';
    }

    if (attributeType === 'tag_reference' && !tagId) {
      newErrors.tagId = 'Tag é obrigatório para tipo "Referência a Tag"';
    }

    if (attributeType === 'static' && !staticValue.trim()) {
      newErrors.staticValue = 'Valor é obrigatório para tipo "Valor Estático"';
    }

    if (attributeType === 'calculated' && !formula.trim()) {
      newErrors.formula = 'Fórmula é obrigatória para tipo "Calculado"';
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
      const settings: Record<string, any> = {};
      if (minValue !== '') settings.min = Number(minValue);
      if (maxValue !== '') settings.max = Number(maxValue);
      if (warningThreshold !== '') settings.warning = Number(warningThreshold);
      if (criticalThreshold !== '') settings.critical = Number(criticalThreshold);

      const attributeData = {
        asset_id: assetId,
        name: name.trim(),
        description: description.trim() || undefined,
        attribute_type: attributeType,
        tag_id: attributeType === 'tag_reference' ? tagId : undefined,
        static_value: attributeType === 'static' ? staticValue.trim() : undefined,
        formula: attributeType === 'calculated' ? formula.trim() : undefined,
        unit: unit.trim() || undefined,
        display_order: displayOrder,
        settings,
      };

      if (isEditMode) {
        // TODO: Implement update attribute
        showToast.info('Edição de atributos será implementada em breve');
      } else {
        // Create new attribute
        const created = await createAssetAttribute(assetId, attributeData);
        if (created) {
          showToast.success(`Atributo "${name}" criado com sucesso!`);
          await fetchAssetAttributes(assetId); // Refresh attributes
          onClose();
        } else {
          showToast.error('Erro ao criar atributo');
        }
      }
    } catch (error: any) {
      console.error('Error saving attribute:', error);
      showToast.error(error.message || 'Erro ao salvar atributo');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const selectedType = ATTRIBUTE_TYPES.find(t => t.value === attributeType);
  const TypeIcon = selectedType?.icon || TagIcon;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <TypeIcon className="w-6 h-6 text-green-600 dark:text-green-400" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              {isEditMode ? 'Editar Atributo' : 'Criar Novo Atributo'}
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
              className={`w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-green-500 dark:bg-gray-700 dark:text-white ${
                errors.name ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
              }`}
              placeholder="Ex: Velocidade, Nível, Temperatura"
            />
            {errors.name && (
              <p className="text-sm text-red-500 mt-1 flex items-center gap-1">
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
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded focus:outline-none focus:ring-2 focus:ring-green-500 dark:bg-gray-700 dark:text-white"
              placeholder="Descrição do atributo..."
            />
          </div>

          {/* Attribute Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Tipo de Atributo <span className="text-red-500">*</span>
            </label>
            <div className="space-y-2">
              {ATTRIBUTE_TYPES.map((type) => {
                const Icon = type.icon;
                return (
                  <button
                    key={type.value}
                    type="button"
                    onClick={() => setAttributeType(type.value)}
                    className={`w-full flex items-start gap-3 px-4 py-3 rounded border transition-colors text-left ${
                      attributeType === type.value
                        ? 'bg-green-50 dark:bg-green-900/30 border-green-500 text-green-700 dark:text-green-300'
                        : 'bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600'
                    }`}
                  >
                    <Icon className="w-5 h-5 mt-0.5" />
                    <div>
                      <p className="font-medium">{type.label}</p>
                      <p className="text-xs text-gray-600 dark:text-gray-400 mt-0.5">
                        {type.description}
                      </p>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Type-specific fields */}
          {attributeType === 'tag_reference' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Tag <span className="text-red-500">*</span>
              </label>
              <select
                value={tagId}
                onChange={(e) => setTagId(e.target.value)}
                className={`w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-green-500 dark:bg-gray-700 dark:text-white ${
                  errors.tagId ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                }`}
              >
                <option value="">Selecione um tag...</option>
                {tags.map((tag) => (
                  <option key={tag.id} value={tag.id}>
                    {tag.name} {tag.unit ? `(${tag.unit})` : ''}
                  </option>
                ))}
              </select>
              {errors.tagId && (
                <p className="text-sm text-red-500 mt-1 flex items-center gap-1">
                  <AlertCircle className="w-4 h-4" />
                  {errors.tagId}
                </p>
              )}
            </div>
          )}

          {attributeType === 'static' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Valor <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={staticValue}
                onChange={(e) => setStaticValue(e.target.value)}
                className={`w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-green-500 dark:bg-gray-700 dark:text-white ${
                  errors.staticValue ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                }`}
                placeholder="Ex: 10000, 30 kW, 1200 RPM"
              />
              {errors.staticValue && (
                <p className="text-sm text-red-500 mt-1 flex items-center gap-1">
                  <AlertCircle className="w-4 h-4" />
                  {errors.staticValue}
                </p>
              )}
            </div>
          )}

          {attributeType === 'calculated' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Fórmula <span className="text-red-500">*</span>
              </label>
              <textarea
                value={formula}
                onChange={(e) => setFormula(e.target.value)}
                rows={3}
                className={`w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-green-500 dark:bg-gray-700 dark:text-white font-mono text-sm ${
                  errors.formula ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                }`}
                placeholder="Ex: (tag('CORREIA_01_VELOCIDADE') / attr('Velocidade Nominal')) * 100"
              />
              {errors.formula && (
                <p className="text-sm text-red-500 mt-1 flex items-center gap-1">
                  <AlertCircle className="w-4 h-4" />
                  {errors.formula}
                </p>
              )}
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Use tag('TAG_NAME') para tags e attr('ATTR_NAME') para outros atributos
              </p>
            </div>
          )}

          {/* Unit */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Unidade de Medida
            </label>
            <input
              type="text"
              value={unit}
              onChange={(e) => setUnit(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded focus:outline-none focus:ring-2 focus:ring-green-500 dark:bg-gray-700 dark:text-white"
              placeholder="Ex: m/s, °C, RPM, %"
            />
          </div>

          {/* Thresholds */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Limites e Thresholds (Opcional)
            </label>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">
                  Mínimo
                </label>
                <input
                  type="number"
                  value={minValue}
                  onChange={(e) => setMinValue(e.target.value === '' ? '' : Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded text-sm focus:outline-none focus:ring-2 focus:ring-green-500 dark:bg-gray-700 dark:text-white"
                  placeholder="0"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">
                  Máximo
                </label>
                <input
                  type="number"
                  value={maxValue}
                  onChange={(e) => setMaxValue(e.target.value === '' ? '' : Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded text-sm focus:outline-none focus:ring-2 focus:ring-green-500 dark:bg-gray-700 dark:text-white"
                  placeholder="100"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">
                  Warning
                </label>
                <input
                  type="number"
                  value={warningThreshold}
                  onChange={(e) => setWarningThreshold(e.target.value === '' ? '' : Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded text-sm focus:outline-none focus:ring-2 focus:ring-green-500 dark:bg-gray-700 dark:text-white"
                  placeholder="80"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">
                  Critical
                </label>
                <input
                  type="number"
                  value={criticalThreshold}
                  onChange={(e) => setCriticalThreshold(e.target.value === '' ? '' : Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded text-sm focus:outline-none focus:ring-2 focus:ring-green-500 dark:bg-gray-700 dark:text-white"
                  placeholder="95"
                />
              </div>
            </div>
          </div>

          {/* Display Order */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Ordem de Exibição
            </label>
            <input
              type="number"
              value={displayOrder}
              onChange={(e) => setDisplayOrder(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded focus:outline-none focus:ring-2 focus:ring-green-500 dark:bg-gray-700 dark:text-white"
              placeholder="0"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Ordem em que o atributo será exibido (menor = primeiro)
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 px-6 py-4 bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={onClose}
            disabled={loading}
            className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50"
          >
            Cancelar
          </button>
          <button
            onClick={handleSave}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-green-600 rounded hover:bg-green-700 disabled:opacity-50"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>Salvando...</span>
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                <span>{isEditMode ? 'Salvar' : 'Criar Atributo'}</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default AssetAttributeEditor;
