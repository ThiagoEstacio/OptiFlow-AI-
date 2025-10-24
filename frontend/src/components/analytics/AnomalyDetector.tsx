/**
 * Anomaly Detector Component
 */
import React, { useState, useEffect } from 'react';
import { AlertTriangle, Settings } from 'lucide-react';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { useAnomalies } from '../../hooks/useAnalytics';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorMessage } from '../common/ErrorMessage';

interface AnomalyDetectorProps {
  tagId: string;
  startTime: Date;
  endTime?: Date;
}

export const AnomalyDetector: React.FC<AnomalyDetectorProps> = ({
  tagId,
  startTime,
  endTime,
}) => {
  const { data, loading, error, detectAnomalies } = useAnomalies();
  const [method, setMethod] = useState<'zscore' | 'iqr' | 'mad'>('zscore');
  const [threshold, setThreshold] = useState(3.0);
  const [showSettings, setShowSettings] = useState(false);

  useEffect(() => {
    detectAnomalies(tagId, startTime, endTime, method, threshold);
  }, [tagId, startTime, endTime, method, threshold]);

  if (loading) {
    return <LoadingSpinner text="Detecting anomalies..." />;
  }

  if (error) {
    return <ErrorMessage message={error} />;
  }

  const chartData = data.map((anomaly) => ({
    timestamp: new Date(anomaly.timestamp).getTime(),
    value: anomaly.value,
    score: anomaly.anomaly_score,
  }));

  return (
    <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <AlertTriangle className="w-6 h-6 text-yellow-500" />
          <h3 className="text-lg font-semibold text-gray-900">Anomaly Detection</h3>
        </div>
        <button
          onClick={() => setShowSettings(!showSettings)}
          className="p-2 hover:bg-gray-100 rounded-md transition-colors"
        >
          <Settings className="w-5 h-5 text-gray-600" />
        </button>
      </div>

      {showSettings && (
        <div className="mb-4 p-4 bg-gray-50 rounded-md border border-gray-200">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Detection Method
              </label>
              <select
                value={method}
                onChange={(e) => setMethod(e.target.value as any)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="zscore">Z-Score</option>
                <option value="iqr">IQR (Interquartile Range)</option>
                <option value="mad">MAD (Median Absolute Deviation)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Threshold
              </label>
              <input
                type="number"
                value={threshold}
                onChange={(e) => setThreshold(parseFloat(e.target.value))}
                step="0.1"
                min="0"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>
        </div>
      )}

      <div className="mb-4">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Anomalies Found:</span>
          <span className="text-2xl font-bold text-red-600">{data.length}</span>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <ScatterChart>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="timestamp"
            type="number"
            domain={['dataMin', 'dataMax']}
            tickFormatter={(value) => new Date(value).toLocaleTimeString()}
          />
          <YAxis dataKey="value" />
          <Tooltip
            labelFormatter={(value) => new Date(value).toLocaleString()}
            formatter={(value: any) => value.toFixed(2)}
          />
          <Legend />
          <Scatter
            name="Anomalies"
            data={chartData}
            fill="#ef4444"
            shape="circle"
          />
        </ScatterChart>
      </ResponsiveContainer>

      {data.length > 0 && (
        <div className="mt-4 max-h-48 overflow-y-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                  Timestamp
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                  Value
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                  Score
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.slice(0, 10).map((anomaly, index) => (
                <tr key={index}>
                  <td className="px-4 py-2 text-sm text-gray-900">
                    {new Date(anomaly.timestamp).toLocaleString()}
                  </td>
                  <td className="px-4 py-2 text-sm text-gray-900">
                    {anomaly.value.toFixed(2)}
                  </td>
                  <td className="px-4 py-2 text-sm font-medium text-red-600">
                    {anomaly.anomaly_score.toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
