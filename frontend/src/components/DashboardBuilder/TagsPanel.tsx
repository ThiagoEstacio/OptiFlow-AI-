/**
 * Tags Panel - Drag Source
 * Shows all available tags that can be dragged to widgets
 */

import React, { useState, useMemo } from 'react';
import { useDrag } from 'react-dnd';
import type { Tag } from '../../types';

interface TagItemProps {
  tag: Tag;
}

const TagItem: React.FC<TagItemProps> = ({ tag }) => {
  const [{ isDragging }, drag] = useDrag(() => ({
    type: 'TAG',
    item: { tagId: tag.id, tagName: tag.name },
    collect: (monitor) => ({
      isDragging: monitor.isDragging(),
    }),
  }));

  return (
    <div
      ref={drag}
      className={`
        px-3 py-2 mb-2 bg-white border border-gray-200 rounded cursor-move
        hover:border-blue-400 hover:shadow-md transition-all
        ${isDragging ? 'opacity-50 scale-95' : 'opacity-100'}
      `}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-900 truncate">
            {tag.name}
          </p>
          {tag.description && (
            <p className="text-xs text-gray-500 truncate">{tag.description}</p>
          )}
        </div>
        <div className="ml-2 flex-shrink-0">
          {tag.unit && (
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
              {tag.unit}
            </span>
          )}
        </div>
      </div>
      {tag.category && (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700 mt-1">
          {tag.category}
        </span>
      )}
    </div>
  );
};

interface TagsPanelProps {
  tags: Tag[];
  loading: boolean;
  onClose: () => void;
}

export const TagsPanel: React.FC<TagsPanelProps> = ({ tags, loading, onClose }) => {
  const [search, setSearch] = useState('');
  const [filterCategory, setFilterCategory] = useState<string>('all');

  // Get unique categories
  const categories = useMemo(() => {
    const cats = new Set(tags.map(t => t.category).filter(Boolean));
    return ['all', ...Array.from(cats)];
  }, [tags]);

  // Filter tags
  const filteredTags = useMemo(() => {
    return tags.filter(tag => {
      const matchesSearch = tag.name.toLowerCase().includes(search.toLowerCase()) ||
                           (tag.description?.toLowerCase().includes(search.toLowerCase()) ?? false);
      const matchesCategory = filterCategory === 'all' || tag.category === filterCategory;
      return matchesSearch && matchesCategory;
    });
  }, [tags, search, filterCategory]);

  return (
    <div className="w-80 bg-gray-50 border-r border-gray-200 flex flex-col">
      {/* Header */}
      <div className="px-4 py-3 bg-white border-b border-gray-200">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-gray-900">Tags</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
            title="Close panel"
          >
            ✕
          </button>
        </div>

        {/* Search */}
        <input
          type="text"
          placeholder="Search tags..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />

        {/* Category Filter */}
        <select
          value={filterCategory}
          onChange={(e) => setFilterCategory(e.target.value)}
          className="w-full mt-2 px-3 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {categories.map(cat => (
            <option key={cat} value={cat}>
              {cat === 'all' ? 'All Categories' : cat}
            </option>
          ))}
        </select>
      </div>

      {/* Tags List */}
      <div className="flex-1 overflow-y-auto p-4">
        {loading ? (
          <div className="text-center py-8 text-gray-500">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
            Loading tags...
          </div>
        ) : filteredTags.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>No tags found</p>
            {search && (
              <p className="text-sm mt-2">Try a different search term</p>
            )}
          </div>
        ) : (
          <>
            <p className="text-xs text-gray-500 mb-2">
              {filteredTags.length} tag{filteredTags.length !== 1 ? 's' : ''}
              {search && ' (filtered)'}
            </p>
            {filteredTags.map(tag => (
              <TagItem key={tag.id} tag={tag} />
            ))}
          </>
        )}
      </div>

      {/* Help */}
      <div className="px-4 py-3 bg-blue-50 border-t border-blue-200 text-sm text-blue-800">
        <p className="font-medium">💡 How to use:</p>
        <ol className="list-decimal list-inside mt-1 text-xs space-y-1">
          <li>Drag a tag from this list</li>
          <li>Drop it onto a widget</li>
          <li>Watch live data appear!</li>
        </ol>
      </div>
    </div>
  );
};
