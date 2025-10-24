/**
 * RealTimePLCViewer Component
 *
 * Displays real-time PLC tag values with WebSocket updates
 */
import React, { useEffect } from 'react';
import { usePLC } from '../../hooks/usePLC';
import { Activity, Wifi, WifiOff, TrendingUp, AlertCircle } from 'lucide-react';

interface RealTimePLCViewerProps {
  tagNames?: string[];
  showAllTags?: boolean;
  refreshInterval?: number;
}

export const RealTimePLCViewer: React.FC<RealTimePLCViewerProps> = ({
  tagNames,
  showAllTags = false,
  refreshInterval = 1000,
}) => {
  const {
    tags,
    tagValues,
    connected,
    loading,
    subscribeToTag,
    subscribeToAll,
    unsubscribeFromAll,
  } = usePLC({
    autoConnect: true,
    enableWebSocket: true,
  });

  // Subscribe to tags on mount
  useEffect(() => {
    if (showAllTags) {
      subscribeToAll();
    } else if (tagNames && tagNames.length > 0) {
      tagNames.forEach((tagName) => subscribeToTag(tagName));
    }

    return () => {
      unsubscribeFromAll();
    };
  }, [showAllTags, tagNames, subscribeToTag, subscribeToAll, unsubscribeFromAll]);

  // Filter tags to display
  const displayTags = showAllTags
    ? tags
    : tags.filter((tag) => tagNames?.includes(tag.name));

  const getQualityColor = (quality: string) => {
    switch (quality) {
      case 'GOOD':
        return 'text-green-600';
      case 'BAD':
        return 'text-red-600';
      case 'UNCERTAIN':
        return 'text-yellow-600';
      default:
        return 'text-gray-600';
    }
  };

  const getQualityBadge = (quality: string) => {
    const colors = {
      GOOD: 'bg-green-100 text-green-800',
      BAD: 'bg-red-100 text-red-800',
      UNCERTAIN: 'bg-yellow-100 text-yellow-800',
    };
    return colors[quality as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };

  const formatValue = (value: any, dataType: string) => {
    if (value === null || value === undefined) return 'N/A';

    switch (dataType) {
      case 'Float':
        return typeof value === 'number' ? value.toFixed(2) : value;
      case 'Int32':
        return Math.round(Number(value));
      case 'Boolean':
        return value ? 'ON' : 'OFF';
      default:
        return String(value);
    }
  };

  if (loading && tags.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-600">Loading PLC tags...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm">
      {/* Header */}
      <div className="border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Activity className="h-5 w-5 text-blue-600" />
            <h2 className="text-lg font-semibold text-gray-900">Real-time PLC Data</h2>
          </div>

          <div className="flex items-center gap-2">
            {connected ? (
              <>
                <Wifi className="h-4 w-4 text-green-500" />
                <span className="text-sm text-green-600 font-medium">Live</span>
                <div className="animate-pulse h-2 w-2 bg-green-500 rounded-full"></div>
              </>
            ) : (
              <>
                <WifiOff className="h-4 w-4 text-red-500" />
                <span className="text-sm text-red-600 font-medium">Disconnected</span>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Tag Grid */}
      <div className="p-6">
        {displayTags.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <AlertCircle className="h-12 w-12 mx-auto mb-3 text-gray-400" />
            <p>No PLC tags available</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {displayTags.map((tag) => {
              const currentValue = tagValues[tag.name];
              const quality = currentValue?.quality || tag.quality || 'UNCERTAIN';
              const value = currentValue?.value ?? tag.value;

              return (
                <div
                  key={tag.name}
                  className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                >
                  {/* Tag Header */}
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1 min-w-0">
                      <h3 className="text-sm font-semibold text-gray-900 truncate">
                        {tag.name}
                      </h3>
                      <p className="text-xs text-gray-500 truncate">{tag.description}</p>
                    </div>
                    <span
                      className={`ml-2 px-2 py-0.5 text-xs font-medium rounded ${getQualityBadge(
                        quality
                      )}`}
                    >
                      {quality}
                    </span>
                  </div>

                  {/* Value Display */}
                  <div className="mt-3">
                    <div className="flex items-baseline gap-2">
                      <span className={`text-2xl font-bold ${getQualityColor(quality)}`}>
                        {formatValue(value, tag.data_type)}
                      </span>
                      {tag.unit && (
                        <span className="text-sm text-gray-600">{tag.unit}</span>
                      )}
                    </div>

                    {/* Timestamp */}
                    {currentValue?.timestamp && (
                      <p className="text-xs text-gray-400 mt-1">
                        Updated: {new Date(currentValue.timestamp).toLocaleTimeString()}
                      </p>
                    )}
                  </div>

                  {/* Min/Max Range (if available) */}
                  {tag.min_value !== undefined && tag.max_value !== undefined && (
                    <div className="mt-3 pt-3 border-t border-gray-100">
                      <div className="flex items-center justify-between text-xs text-gray-500">
                        <span>Min: {tag.min_value}</span>
                        <span>Max: {tag.max_value}</span>
                      </div>
                      {/* Progress bar */}
                      {typeof value === 'number' && (
                        <div className="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-blue-500 transition-all duration-300"
                            style={{
                              width: `${
                                ((value - tag.min_value) / (tag.max_value - tag.min_value)) *
                                100
                              }%`,
                            }}
                          />
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Footer Info */}
      <div className="border-t border-gray-200 px-6 py-3 bg-gray-50 rounded-b-lg">
        <div className="flex items-center justify-between text-xs text-gray-600">
          <span>{displayTags.length} tags displayed</span>
          <div className="flex items-center gap-2">
            <TrendingUp className="h-3 w-3" />
            <span>Updates every {refreshInterval / 1000}s</span>
          </div>
        </div>
      </div>
    </div>
  );
};
