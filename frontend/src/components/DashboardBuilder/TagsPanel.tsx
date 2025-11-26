/**
 * Tags Panel - Drag Source
 * Shows all available tags that can be dragged to widgets
 */

import React, { useState, useMemo } from 'react';
import { useDrag } from 'react-dnd';
import { Edit2 } from 'lucide-react';

// Generic tag interface compatible with Gateway tags
export interface Tag {
  id: string;
  name: string;
  description?: string;
  unit?: string;
  data_type?: string;
  category?: string;
  adapter_id?: string;
  protocol?: string;
  enabled?: boolean;
}

interface TagItemProps {
  tag: Tag;
  onEdit: (tag: Tag) => void;
}

const TagItem: React.FC<TagItemProps> = ({ tag, onEdit }) => {
  const [{ isDragging }, drag] = useDrag(() => ({
    type: 'TAG',
    item: { tagId: tag.id, tagName: tag.name },
    collect: (monitor) => ({
      isDragging: monitor.isDragging(),
    }),
  }));

  const handleEditClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onEdit(tag);
  };

  return (
    <div
      ref={drag}
      className={`
        px-3 py-2 mb-2 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded cursor-move
        hover:border-blue-400 hover:shadow-md transition-all
        ${isDragging ? 'opacity-50 scale-95' : 'opacity-100'}
      `}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
            {tag.name}
          </p>
          {tag.description && (
            <p className="text-xs text-gray-500 dark:text-gray-400 truncate">{tag.description}</p>
          )}
        </div>
        <div className="ml-2 flex-shrink-0 flex items-center gap-1">
          {tag.unit && (
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
              {tag.unit}
            </span>
          )}
          <button
            onClick={handleEditClick}
            className="p-1 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded transition-colors"
            title="Editar tag"
          >
            <Edit2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
      {/* Show adapter/protocol info instead of category for Gateway tags */}
      {(tag.adapter_id || tag.protocol) && (
        <div className="flex gap-1 mt-1">
          {tag.protocol && (
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300">
              {tag.protocol}
            </span>
          )}
          {tag.adapter_id && (
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700 dark:bg-gray-600 dark:text-gray-300 truncate max-w-[150px]" title={tag.adapter_id}>
              {tag.adapter_id.split('-')[0]}
            </span>
          )}
        </div>
      )}
    </div>
  );
};

interface TagsPanelProps {
  tags: Tag[];
  loading: boolean;
  onClose: () => void;
  onEditTag: (tag: Tag) => void;
}

export const TagsPanel: React.FC<TagsPanelProps> = ({ tags, loading, onClose, onEditTag }) => {
  const [search, setSearch] = useState('');
  const [filterProtocol, setFilterProtocol] = useState<string>('all');

  // Get unique protocols from tags
  const protocols = useMemo(() => {
    const protos = new Set(tags.map(t => t.protocol).filter(Boolean));
    return ['all', ...Array.from(protos)];
  }, [tags]);

  // Filter tags
  const filteredTags = useMemo(() => {
    return tags.filter(tag => {
      const matchesSearch = tag.name.toLowerCase().includes(search.toLowerCase()) ||
                           (tag.description?.toLowerCase().includes(search.toLowerCase()) ?? false);
      const matchesProtocol = filterProtocol === 'all' || tag.protocol === filterProtocol;
      return matchesSearch && matchesProtocol;
    });
  }, [tags, search, filterProtocol]);

  return (
    <div className="w-80 bg-gray-50 dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 flex flex-col">
      {/* Header */}
      <div className="px-4 py-3 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Tags</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            title="Fechar painel"
          >
            ✕
          </button>
        </div>

        {/* Search */}
        <input
          type="text"
          placeholder="Buscar tags..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
        />

        {/* Protocol Filter */}
        <select
          value={filterProtocol}
          onChange={(e) => setFilterProtocol(e.target.value)}
          className="w-full mt-2 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
        >
          {protocols.map(proto => (
            <option key={proto} value={proto}>
              {proto === 'all' ? 'Todos os Protocolos' : proto.toUpperCase()}
            </option>
          ))}
        </select>
      </div>

      {/* Tags List */}
      <div className="flex-1 overflow-y-auto p-4">
        {loading ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
            Carregando tags do Gateway...
          </div>
        ) : filteredTags.length === 0 ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <p>Nenhuma tag encontrada</p>
            {search && (
              <p className="text-sm mt-2">Tente outro termo de busca</p>
            )}
            {tags.length === 0 && (
              <p className="text-sm mt-2">Verifique se o Gateway está conectado</p>
            )}
          </div>
        ) : (
          <>
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
              {filteredTags.length} tag{filteredTags.length !== 1 ? 's' : ''} gerenciada{filteredTags.length !== 1 ? 's' : ''}
              {search && ' (filtrado)'}
            </p>
            {filteredTags.map(tag => (
              <TagItem key={tag.id} tag={tag} onEdit={onEditTag} />
            ))}
          </>
        )}
      </div>

      {/* Help */}
      <div className="px-4 py-3 bg-blue-50 dark:bg-blue-900/20 border-t border-blue-200 dark:border-blue-800 text-sm text-blue-800 dark:text-blue-200">
        <p className="font-medium">Gateway Tags</p>
        <p className="text-xs mt-1 text-blue-600 dark:text-blue-300">
          Tags gerenciados pelo Gateway Edge (porta 8080)
        </p>
        <ol className="list-decimal list-inside mt-2 text-xs space-y-1">
          <li>Arraste uma tag desta lista</li>
          <li>Solte sobre um widget</li>
          <li>Clique em <Edit2 className="w-3 h-3 inline" /> para editar</li>
        </ol>
      </div>
    </div>
  );
};
