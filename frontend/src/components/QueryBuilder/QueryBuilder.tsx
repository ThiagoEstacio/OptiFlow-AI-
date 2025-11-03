/**
 * QueryBuilder Component
 *
 * Main query builder interface that combines all sub-components
 * Allows users to visually construct complex analytics queries
 */

import React, { useState, useEffect } from 'react';
import { Play, Save, Code, Download, History, Radio } from 'lucide-react';
import TagSelector, { Tag } from './TagSelector';
import TimeRangePicker, { TimeRange } from './TimeRangePicker';
import FilterBuilder, { QueryFilter } from './FilterBuilder';
import AggregationBuilder, { QueryAggregation } from './AggregationBuilder';
import StreamControls from './StreamControls';
import { useAnalyticsStream } from '../../hooks/useAnalyticsStream';

export interface AnalyticsQuery {
  tags: string[];
  start: string;
  end: string;
  filters?: QueryFilter[];
  aggregations: QueryAggregation[];
  group_by?: string[];
  limit?: number;
  include_raw_data?: boolean;
}

export interface QueryBuilderProps {
  onExecute: (query: AnalyticsQuery) => void;
  onStreamData?: (data: any) => void; // Callback for streaming data
  loading?: boolean;
  initialQuery?: Partial<AnalyticsQuery>;
  enableStreaming?: boolean; // Enable/disable streaming mode
}

export const QueryBuilder: React.FC<QueryBuilderProps> = ({
  onExecute,
  onStreamData,
  loading = false,
  initialQuery,
  enableStreaming = true,
}) => {
  // State
  const [selectedTags, setSelectedTags] = useState<Tag[]>([]);
  const [timeRange, setTimeRange] = useState<TimeRange>({
    start: new Date(Date.now() - 24 * 60 * 60 * 1000), // 24h ago
    end: new Date(),
    preset: '24h',
  });
  const [filters, setFilters] = useState<QueryFilter[]>([]);
  const [aggregations, setAggregations] = useState<QueryAggregation[]>([
    { function: 'mean', field: 'value', window: '1h' },
  ]);
  const [showJSON, setShowJSON] = useState(false);
  const [includeRawData, setIncludeRawData] = useState(false);

  // Streaming state
  const [streamingMode, setStreamingMode] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState(5); // seconds

  // WebSocket streaming hook
  const streamHook = useAnalyticsStream();

  // Forward streaming data to parent component
  useEffect(() => {
    if (streamHook.data && onStreamData) {
      onStreamData(streamHook.data);
    }
  }, [streamHook.data, onStreamData]);

  // Build query object
  const buildQuery = (): AnalyticsQuery => {
    return {
      tags: selectedTags.map(t => t.id),
      start: timeRange.start.toISOString(),
      end: timeRange.end.toISOString(),
      filters: filters.length > 0 ? filters : undefined,
      aggregations,
      limit: 1000,
      include_raw_data: includeRawData,
    };
  };

  const handleExecute = () => {
    const query = buildQuery();

    // Validation
    if (query.tags.length === 0) {
      alert('Please select at least one tag');
      return;
    }

    if (query.aggregations.length === 0) {
      alert('Please add at least one aggregation');
      return;
    }

    onExecute(query);
  };

  const handleSave = () => {
    const query = buildQuery();
    const queryName = prompt('Enter a name for this query:');

    if (queryName) {
      // TODO: Save to backend
      localStorage.setItem(`query_${queryName}`, JSON.stringify(query));
      alert(`Query "${queryName}" saved!`);
    }
  };

  const handleExport = () => {
    const query = buildQuery();
    const blob = new Blob([JSON.stringify(query, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `analytics-query-${Date.now()}.json`;
    a.click();
  };

  // Streaming controls
  const handleStartStream = () => {
    const query = buildQuery();

    // Validation
    if (query.tags.length === 0) {
      alert('Please select at least one tag');
      return;
    }

    if (query.aggregations.length === 0) {
      alert('Please add at least one aggregation');
      return;
    }

    // Start streaming
    streamHook.start({
      query,
      refresh_interval: refreshInterval,
      mode: 'continuous',
    });
  };

  const handlePauseStream = () => {
    streamHook.pause();
  };

  const handleResumeStream = () => {
    streamHook.resume();
  };

  const handleStopStream = () => {
    streamHook.stop();
  };

  const query = buildQuery();

  return (
    <div className="query-builder bg-white rounded-lg shadow-lg p-6">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-gray-200">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Query Builder</h2>
            <p className="text-sm text-gray-600 mt-1">
              Build advanced analytics queries visually
            </p>
          </div>

          <div className="flex items-center gap-2">
            {enableStreaming && (
              <div className="flex items-center gap-2 mr-2 px-3 py-2 bg-gray-50 rounded-lg border border-gray-200">
                <span className="text-sm text-gray-700">Mode:</span>
                <button
                  onClick={() => setStreamingMode(false)}
                  className={`px-3 py-1 text-sm rounded transition-colors ${
                    !streamingMode
                      ? 'bg-blue-600 text-white'
                      : 'bg-white text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <Play size={14} className="inline mr-1" />
                  Execute Once
                </button>
                <button
                  onClick={() => setStreamingMode(true)}
                  className={`px-3 py-1 text-sm rounded transition-colors ${
                    streamingMode
                      ? 'bg-red-600 text-white'
                      : 'bg-white text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <Radio size={14} className="inline mr-1" />
                  Stream Live
                </button>
              </div>
            )}

            <button
              onClick={() => setShowJSON(!showJSON)}
              className="flex items-center gap-2 px-3 py-2 text-sm text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            >
              <Code size={16} />
              {showJSON ? 'Hide' : 'Show'} JSON
            </button>
          </div>
        </div>

        {/* Stream Controls (shown in streaming mode) */}
        {enableStreaming && streamingMode && (
          <StreamControls
            status={streamHook.status}
            refreshInterval={refreshInterval}
            onRefreshIntervalChange={setRefreshInterval}
            onStart={handleStartStream}
            onPause={handlePauseStream}
            onResume={handleResumeStream}
            onStop={handleStopStream}
            disabled={selectedTags.length === 0 || aggregations.length === 0}
          />
        )}

        {/* Tag Selection */}
        <TagSelector selectedTags={selectedTags} onChange={setSelectedTags} />

        {/* Time Range */}
        <TimeRangePicker value={timeRange} onChange={setTimeRange} />

        {/* Filters */}
        <FilterBuilder filters={filters} onChange={setFilters} />

        {/* Aggregations */}
        <AggregationBuilder aggregations={aggregations} onChange={setAggregations} />

        {/* Advanced Options */}
        <div className="pt-4 border-t border-gray-200">
          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input
              type="checkbox"
              checked={includeRawData}
              onChange={(e) => setIncludeRawData(e.target.checked)}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            Include raw time-series data in response (in addition to aggregations)
          </label>
        </div>

        {/* JSON Preview */}
        {showJSON && (
          <div className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto">
            <div className="text-xs font-mono">
              <pre>{JSON.stringify(query, null, 2)}</pre>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        {!streamingMode && (
          <div className="flex items-center justify-between pt-4 border-t border-gray-200">
            <div className="flex items-center gap-2">
              <button
                onClick={handleSave}
                className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                disabled={loading}
              >
                <Save size={16} />
                Save Query
              </button>

              <button
                onClick={handleExport}
                className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                disabled={loading}
              >
                <Download size={16} />
                Export
              </button>
            </div>

            <button
              onClick={handleExecute}
              disabled={loading || selectedTags.length === 0 || aggregations.length === 0}
              className="flex items-center gap-2 px-6 py-3 text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                  Executing...
                </>
              ) : (
                <>
                  <Play size={18} />
                  Execute Query
                </>
              )}
            </button>
          </div>
        )}

        {/* Query Summary */}
        <div className="bg-blue-50 p-4 rounded-lg text-sm">
          <div className="font-medium text-blue-900 mb-2">Query Summary:</div>
          <ul className="space-y-1 text-blue-800">
            <li>• <strong>{selectedTags.length}</strong> tag(s) selected</li>
            <li>
              • Time range: <strong>{timeRange.preset || 'custom'}</strong>
              {' '}({Math.round((timeRange.end.getTime() - timeRange.start.getTime()) / (1000 * 60 * 60))} hours)
            </li>
            <li>• <strong>{filters.length}</strong> filter(s) applied</li>
            <li>• <strong>{aggregations.length}</strong> aggregation(s) configured</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default QueryBuilder;
