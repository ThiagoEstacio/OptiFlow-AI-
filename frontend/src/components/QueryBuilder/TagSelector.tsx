/**
 * TagSelector Component
 *
 * Multi-select tag picker with search and autocomplete
 * For selecting multiple tags to query
 */

import React, { useState, useEffect } from 'react';
import { Search, X, Tag as TagIcon } from 'lucide-react';

export interface Tag {
  id: string;
  name: string;
  address?: string;
  deviceName?: string;
  unit?: string;
  dataType?: string;
}

export interface TagSelectorProps {
  selectedTags: Tag[];
  onChange: (tags: Tag[]) => void;
  maxTags?: number;
  placeholder?: string;
}

export const TagSelector: React.FC<TagSelectorProps> = ({
  selectedTags,
  onChange,
  maxTags = 10,
  placeholder = 'Search and select tags...',
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [availableTags, setAvailableTags] = useState<Tag[]>([]);
  const [filteredTags, setFilteredTags] = useState<Tag[]>([]);
  const [isOpen, setIsOpen] = useState(false);

  // TODO: Fetch tags from API
  useEffect(() => {
    // Mock data - replace with actual API call
    const mockTags: Tag[] = [
      { id: 'temp_01', name: 'Temperature Sensor 1', deviceName: 'Reactor A', unit: '°C', dataType: 'FLOAT' },
      { id: 'press_01', name: 'Pressure Sensor 1', deviceName: 'Reactor A', unit: 'bar', dataType: 'FLOAT' },
      { id: 'flow_01', name: 'Flow Meter 1', deviceName: 'Line 1', unit: 'm³/h', dataType: 'FLOAT' },
      { id: 'level_01', name: 'Level Sensor 1', deviceName: 'Tank 1', unit: 'm', dataType: 'FLOAT' },
      { id: 'speed_01', name: 'Motor Speed 1', deviceName: 'Motor A', unit: 'rpm', dataType: 'INT' },
    ];
    setAvailableTags(mockTags);
  }, []);

  // Filter tags based on search
  useEffect(() => {
    if (!searchTerm) {
      setFilteredTags(availableTags);
      return;
    }

    const filtered = availableTags.filter(tag => {
      const searchLower = searchTerm.toLowerCase();
      return (
        tag.name.toLowerCase().includes(searchLower) ||
        tag.id.toLowerCase().includes(searchLower) ||
        tag.deviceName?.toLowerCase().includes(searchLower)
      );
    });

    setFilteredTags(filtered);
  }, [searchTerm, availableTags]);

  const handleTagSelect = (tag: Tag) => {
    if (selectedTags.length >= maxTags) {
      alert(`Maximum ${maxTags} tags allowed`);
      return;
    }

    if (!selectedTags.find(t => t.id === tag.id)) {
      onChange([...selectedTags, tag]);
    }
    setSearchTerm('');
    setIsOpen(false);
  };

  const handleTagRemove = (tagId: string) => {
    onChange(selectedTags.filter(t => t.id !== tagId));
  };

  return (
    <div className="tag-selector">
      <label className="block text-sm font-medium text-gray-700 mb-2">
        Select Tags ({selectedTags.length}/{maxTags})
      </label>

      {/* Selected tags */}
      {selectedTags.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-3">
          {selectedTags.map(tag => (
            <div
              key={tag.id}
              className="inline-flex items-center gap-2 bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm"
            >
              <TagIcon size={14} />
              <span className="font-medium">{tag.name}</span>
              {tag.unit && <span className="text-blue-600">({tag.unit})</span>}
              <button
                onClick={() => handleTagRemove(tag.id)}
                className="hover:bg-blue-200 rounded-full p-0.5 transition-colors"
              >
                <X size={14} />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Search input */}
      <div className="relative">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setIsOpen(true);
            }}
            onFocus={() => setIsOpen(true)}
            placeholder={placeholder}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            disabled={selectedTags.length >= maxTags}
          />
        </div>

        {/* Dropdown */}
        {isOpen && filteredTags.length > 0 && (
          <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
            {filteredTags
              .filter(tag => !selectedTags.find(t => t.id === tag.id))
              .slice(0, 20)
              .map(tag => (
                <button
                  key={tag.id}
                  onClick={() => handleTagSelect(tag)}
                  className="w-full text-left px-4 py-3 hover:bg-blue-50 transition-colors border-b border-gray-100 last:border-0"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium text-gray-900">{tag.name}</div>
                      <div className="text-sm text-gray-500 mt-0.5">
                        {tag.deviceName && <span>{tag.deviceName} • </span>}
                        <span className="font-mono text-xs">{tag.id}</span>
                      </div>
                    </div>
                    {tag.unit && (
                      <span className="text-sm text-gray-600 bg-gray-100 px-2 py-1 rounded">
                        {tag.unit}
                      </span>
                    )}
                  </div>
                </button>
              ))}
          </div>
        )}
      </div>

      {/* Click outside to close */}
      {isOpen && (
        <div
          className="fixed inset-0 z-0"
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
};

export default TagSelector;
