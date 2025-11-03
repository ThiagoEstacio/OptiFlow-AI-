/**
 * Tag Details Page with Time Series Chart
 */
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../store';
import { fetchTag } from '../store/slices/tagsSlice';
import { fetchTagTimeseries } from '../store/slices/tagsSlice';
import { TimeSeriesChart } from '../components/Charts/TimeSeriesChart';
import { apiClient } from '../api/client';
import { showToast } from '../utils/toast';

export const TagDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { selectedTag, loading } = useAppSelector((state) => state.tags);

  const [timeseriesData, setTimeseriesData] = useState<any[]>([]);
  const [timeRange, setTimeRange] = useState<string>('1h');
  const [loadingData, setLoadingData] = useState(false);

  useEffect(() => {
    if (id) {
      dispatch(fetchTag(id));
    }
  }, [id, dispatch]);

  useEffect(() => {
    if (id) {
      loadTimeseriesData();
    }
  }, [id, timeRange]);

  const loadTimeseriesData = async () => {
    if (!id) return;

    setLoadingData(true);
    try {
      const now = new Date();
      let startTime = new Date();

      switch (timeRange) {
        case '1h':
          startTime = new Date(now.getTime() - 60 * 60 * 1000);
          break;
        case '6h':
          startTime = new Date(now.getTime() - 6 * 60 * 60 * 1000);
          break;
        case '24h':
          startTime = new Date(now.getTime() - 24 * 60 * 60 * 1000);
          break;
        case '7d':
          startTime = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
          break;
      }

      const data = await apiClient.getTagTimeseries(id, {
        start_time: startTime.toISOString(),
        end_time: now.toISOString(),
      });

      setTimeseriesData(data);
    } catch (error: any) {
      showToast.error('Failed to load timeseries data');
    } finally {
      setLoadingData(false);
    }
  };

  if (loading || !selectedTag) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => navigate('/tags')}
            className="text-gray-600 hover:text-gray-900"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 19l-7-7 7-7"
              />
            </svg>
          </button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{selectedTag.name}</h1>
            <p className="text-gray-600 mt-1">{selectedTag.description || 'Tag Details'}</p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="1h">Last 1 Hour</option>
            <option value="6h">Last 6 Hours</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
          </select>
          <button
            onClick={loadTimeseriesData}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Tag Information */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-semibold text-gray-500 uppercase mb-4">Configuration</h3>
          <div className="space-y-3">
            <div>
              <span className="text-sm text-gray-600">Address:</span>
              <p className="font-medium font-mono">{selectedTag.address}</p>
            </div>
            <div>
              <span className="text-sm text-gray-600">Data Type:</span>
              <p className="font-medium">{selectedTag.data_type}</p>
            </div>
            {selectedTag.unit && (
              <div>
                <span className="text-sm text-gray-600">Unit:</span>
                <p className="font-medium">{selectedTag.unit}</p>
              </div>
            )}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-semibold text-gray-500 uppercase mb-4">Scaling</h3>
          <div className="space-y-3">
            <div>
              <span className="text-sm text-gray-600">Scale Factor:</span>
              <p className="font-medium">{selectedTag.scale_factor || 1.0}</p>
            </div>
            <div>
              <span className="text-sm text-gray-600">Offset:</span>
              <p className="font-medium">{selectedTag.offset || 0.0}</p>
            </div>
            {(selectedTag.min_value !== null || selectedTag.max_value !== null) && (
              <div>
                <span className="text-sm text-gray-600">Range:</span>
                <p className="font-medium">
                  {selectedTag.min_value ?? '-∞'} to {selectedTag.max_value ?? '∞'}
                </p>
              </div>
            )}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-semibold text-gray-500 uppercase mb-4">Status</h3>
          <div className="space-y-3">
            <div>
              <span className="text-sm text-gray-600">Enabled:</span>
              <p className="font-medium">
                <span
                  className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                    selectedTag.enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {selectedTag.enabled ? 'Yes' : 'No'}
                </span>
              </p>
            </div>
            <div>
              <span className="text-sm text-gray-600">Logging:</span>
              <p className="font-medium">
                <span
                  className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                    selectedTag.log_enabled
                      ? 'bg-blue-100 text-blue-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {selectedTag.log_enabled ? 'Enabled' : 'Disabled'}
                </span>
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Time Series Chart */}
      <div className="bg-white rounded-lg shadow p-6">
        {loadingData ? (
          <div className="flex items-center justify-center h-96">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : timeseriesData.length === 0 ? (
          <div className="flex items-center justify-center h-96 text-gray-500">
            No data available for the selected time range
          </div>
        ) : (
          <TimeSeriesChart
            data={timeseriesData}
            dataKey="value"
            xAxisKey="timestamp"
            title={`${selectedTag.name} - Time Series Data`}
            type="line"
            color="#3B82F6"
            height={400}
            unit={selectedTag.unit}
          />
        )}
      </div>
    </div>
  );
};
