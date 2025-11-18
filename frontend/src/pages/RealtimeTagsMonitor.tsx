/**
 * Real-Time Tags Monitor Page
 * 
 * Shows all tags with their current values updating in real-time
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Activity, Loader2, AlertCircle, Search, Filter } from 'lucide-react';
import { apiClient } from '../api/client';

interface Tag {
  id: number;
  name: string;
  description?: string;
  data_type: string;
  device_id: string;
}

interface TagValue {
  value: number | string | boolean;
  timestamp: string;
  quality: string;
  tag_id: string;
}

export const RealtimeTagsMonitor: React.FC = () => {
  const [tags, setTags] = useState<Tag[]>([]);
  const [tagValues, setTagValues] = useState<Record<string, TagValue>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterPrefix, setFilterPrefix] = useState<string>('ALL');

  // Load all tags on mount
  useEffect(() => {
    const fetchTags = async () => {
      try {
        const response = await apiClient.get('/api/v1/tags/');
        const allTags = response.data;
        
        // Filter to only simulator tags (not SYSTEM or ARZ_ tags)
        const simulatorTags = allTags.filter((tag: Tag) => 
          !tag.name.startsWith('SYSTEM') && 
          !tag.name.startsWith('ARZ_') && 
          !tag.name.startsWith('GATE_') &&
          !tag.name.startsWith('SHIPLOADER_')
        );
        
        setTags(simulatorTags);
        setIsLoading(false);
      } catch (err: any) {
        console.error('Error fetching tags:', err);
        setError(err.response?.data?.detail || 'Failed to fetch tags');
        setIsLoading(false);
      }
    };

    fetchTags();
  }, []);

  // Poll tag values
  useEffect(() => {
    if (tags.length === 0) return;

    const fetchTagValues = async () => {
      const newValues: Record<string, TagValue> = {};
      
      for (const tag of tags) {
        try {
          const response = await apiClient.get(`/api/v1/tags/realtime/${tag.name}`);
          newValues[tag.name] = response.data;
        } catch (err) {
          console.error(`Error fetching value for ${tag.name}:`, err);
        }
      }
      
      setTagValues(newValues);
    };

    // Initial fetch
    fetchTagValues();

    // Poll every 2 seconds
    const intervalId = setInterval(fetchTagValues, 2000);

    return () => clearInterval(intervalId);
  }, [tags]);

  const filteredTags = tags.filter(tag => {
    const matchesSearch = tag.name.toLowerCase().includes(searchTerm.toLowerCase());
    
    if (filterPrefix === 'ALL') return matchesSearch;
    return matchesSearch && tag.name.startsWith(filterPrefix);
  });

  const prefixes = ['ALL', 'CORR', 'SILO', 'ELEV', 'Energy'];

  const formatValue = (value: any, dataType: string): string => {
    if (value === null || value === undefined) return 'N/A';
    
    if (typeof value === 'boolean') return value ? 'TRUE' : 'FALSE';
    if (typeof value === 'number') return value.toFixed(2);
    return String(value);
  };

  const getStatusColor = (quality?: string): string => {
    if (!quality) return 'text-gray-400';
    return quality === 'good' ? 'text-green-500' : 'text-yellow-500';
  };

  if (isLoading) {
    return (
      <div className="container mx-auto p-6">
        <Card>
          <CardContent className="flex items-center justify-center p-8">
            <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
            <span className="ml-3 text-gray-600">Loading tags...</span>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <Activity className="h-8 w-8 text-blue-500" />
          Real-Time Tags Monitor
        </h1>
        <p className="text-gray-600 mt-2">
          Monitoring {tags.length} simulator tags in real-time
        </p>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Filters */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex gap-4 items-center">
            {/* Search */}
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search tags..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Equipment Filter */}
            <div className="flex gap-2">
              <Filter className="h-5 w-5 text-gray-400 self-center" />
              {prefixes.map(prefix => (
                <button
                  key={prefix}
                  onClick={() => setFilterPrefix(prefix)}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    filterPrefix === prefix
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {prefix}
                </button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tags Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {filteredTags.map(tag => {
          const tagValue = tagValues[tag.name];
          
          return (
            <Card key={tag.id} className="hover:shadow-lg transition-shadow">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-mono text-gray-700 flex items-center justify-between">
                  <span className="truncate">{tag.name}</span>
                  <span className={`ml-2 ${getStatusColor(tagValue?.quality)}`}>
                    <Activity className="h-4 w-4" />
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {tagValue ? (
                  <>
                    <div className="text-3xl font-bold text-gray-900 mb-2">
                      {formatValue(tagValue.value, tag.data_type)}
                    </div>
                    <div className="text-xs text-gray-500 space-y-1">
                      <div className="flex justify-between">
                        <span>Quality:</span>
                        <span className={`font-semibold ${getStatusColor(tagValue.quality)}`}>
                          {tagValue.quality.toUpperCase()}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Updated:</span>
                        <span className="font-mono">
                          {new Date(tagValue.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="text-center py-4 text-gray-400">
                    <Loader2 className="h-6 w-6 animate-spin mx-auto mb-2" />
                    <span className="text-xs">Loading...</span>
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {filteredTags.length === 0 && (
        <Card>
          <CardContent className="text-center py-12 text-gray-500">
            <AlertCircle className="h-12 w-12 mx-auto mb-4 text-gray-300" />
            <p>No tags found matching your filters</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default RealtimeTagsMonitor;
