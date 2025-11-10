import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Alert, AlertDescription } from './ui/alert';
import { Activity, Loader2, AlertCircle } from 'lucide-react';
import { apiClient } from '../api/client';

interface TagData {
  tag_name: string;
  timestamp: string;
  value: number;
  quality: string;
  source: string;
}

interface RealtimeTagViewerProps {
  tagName?: string;
  pollInterval?: number;
}

export const RealtimeTagViewer: React.FC<RealtimeTagViewerProps> = ({
  tagName = 'TEST_COUNTER_PV',
  pollInterval = 1000
}) => {
  const [tagData, setTagData] = useState<TagData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  useEffect(() => {
    let intervalId: NodeJS.Timeout;

    const fetchTagValue = async () => {
      try {
        const response = await apiClient.get(`/api/v1/tags/realtime/${tagName}`);
        setTagData(response.data);
        setLastUpdate(new Date());
        setError(null);
        setIsLoading(false);
      } catch (err: any) {
        console.error('Error fetching tag value:', err);
        setError(err.response?.data?.detail || 'Failed to fetch tag value');
        setIsLoading(false);
      }
    };

    // Initial fetch
    fetchTagValue();

    // Poll every interval
    intervalId = setInterval(fetchTagValue, pollInterval);

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [tagName, pollInterval]);

  const formatTimestamp = (timestamp: string) => {
    try {
      return new Date(timestamp).toLocaleString();
    } catch {
      return timestamp;
    }
  };

  const getValueColor = (value: number) => {
    // Visual feedback based on value
    const hue = (value / 10) * 120; // 0 = red, 10 = green
    return `hsl(${hue}, 70%, 50%)`;
  };

  if (isLoading && !tagData) {
    return (
      <Card className="w-full max-w-2xl mx-auto">
        <CardContent className="flex items-center justify-center p-8">
          <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
          <span className="ml-3 text-gray-600">Loading tag data...</span>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="w-full max-w-2xl mx-auto space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-blue-500" />
            Real-Time Tag Monitor
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {tagData && (
            <>
              {/* Tag Name */}
              <div className="border-b pb-3">
                <p className="text-sm text-gray-500">Tag Name</p>
                <p className="text-lg font-mono font-semibold">{tagData.tag_name}</p>
              </div>

              {/* Current Value - Large Display */}
              <div className="text-center py-8 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500 mb-2">Current Value</p>
                <div
                  className="text-7xl font-bold transition-colors duration-300"
                  style={{ color: getValueColor(tagData.value) }}
                >
                  {tagData.value.toFixed(1)}
                </div>
                <div className="mt-4 w-full max-w-md mx-auto h-4 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full transition-all duration-300"
                    style={{
                      width: `${(tagData.value / 10) * 100}%`,
                      backgroundColor: getValueColor(tagData.value)
                    }}
                  />
                </div>
              </div>

              {/* Metadata */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-500">Quality</p>
                  <p className={`font-semibold ${
                    tagData.quality === 'good' ? 'text-green-600' : 'text-yellow-600'
                  }`}>
                    {tagData.quality.toUpperCase()}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Source</p>
                  <p className="font-semibold">{tagData.source}</p>
                </div>
                <div className="col-span-2">
                  <p className="text-sm text-gray-500">Timestamp</p>
                  <p className="font-mono text-sm">{formatTimestamp(tagData.timestamp)}</p>
                </div>
                {lastUpdate && (
                  <div className="col-span-2">
                    <p className="text-sm text-gray-500">Last Update</p>
                    <p className="text-sm text-gray-600">{lastUpdate.toLocaleTimeString()}</p>
                  </div>
                )}
              </div>

              {/* Polling Indicator */}
              <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                <span>Polling every {pollInterval}ms</span>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Info Card */}
      <Card className="bg-blue-50 border-blue-200">
        <CardContent className="p-4">
          <h3 className="font-semibold text-blue-900 mb-2">About This Tag</h3>
          <p className="text-sm text-blue-800">
            TEST_COUNTER_PV is a test tag that increments from 0 to 10 every second,
            automatically resetting to 0. This validates the complete data flow:
            Simulator → Kafka → InfluxDB → API → Frontend.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};
