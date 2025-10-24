/**
 * Statistics Panel Component
 */
import React, { useEffect } from 'react';
import { TrendingUp, TrendingDown, Activity, BarChart3 } from 'lucide-react';
import { useStatistics } from '../../hooks/useAnalytics';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorMessage } from '../common/ErrorMessage';
import { StatCard } from '../common/StatCard';

interface StatisticsPanelProps {
  tagIds: string[];
  startTime: Date;
  endTime?: Date;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export const StatisticsPanel: React.FC<StatisticsPanelProps> = ({
  tagIds,
  startTime,
  endTime,
  autoRefresh = false,
  refreshInterval = 30000,
}) => {
  const { data, loading, error, fetchStatistics } = useStatistics();

  useEffect(() => {
    fetchStatistics(tagIds, startTime, endTime);

    if (autoRefresh) {
      const interval = setInterval(() => {
        fetchStatistics(tagIds, startTime, endTime);
      }, refreshInterval);

      return () => clearInterval(interval);
    }
  }, [tagIds, startTime, endTime, autoRefresh, refreshInterval]);

  if (loading && !data) {
    return <LoadingSpinner text="Loading statistics..." />;
  }

  if (error) {
    return <ErrorMessage message={error} onRetry={() => fetchStatistics(tagIds, startTime, endTime)} />;
  }

  if (!data) {
    return null;
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold text-gray-900">Statistical Analysis</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Mean Value"
          value={data.mean.toFixed(2)}
          subtitle={`Median: ${data.median.toFixed(2)}`}
          icon={Activity}
          color="blue"
        />

        <StatCard
          title="Min / Max"
          value={`${data.min.toFixed(2)} / ${data.max.toFixed(2)}`}
          subtitle={`Range: ${data.range.toFixed(2)}`}
          icon={TrendingUp}
          color="green"
        />

        <StatCard
          title="Std Deviation"
          value={data.std.toFixed(2)}
          subtitle={`Variance: ${data.variance.toFixed(2)}`}
          icon={BarChart3}
          color="purple"
        />

        <StatCard
          title="Data Points"
          value={data.count.toLocaleString()}
          subtitle={`P95: ${data.percentiles.p95.toFixed(2)}`}
          icon={Activity}
          color="yellow"
        />
      </div>

      <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Percentiles</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {Object.entries(data.percentiles).map(([key, value]) => (
            <div key={key} className="text-center">
              <p className="text-sm text-gray-600">{key.toUpperCase()}</p>
              <p className="text-lg font-semibold text-gray-900">{value.toFixed(2)}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Skewness</h3>
          <p className="text-3xl font-bold text-gray-900">{data.skewness.toFixed(3)}</p>
          <p className="text-sm text-gray-600 mt-2">
            {Math.abs(data.skewness) < 0.5
              ? 'Fairly symmetrical'
              : data.skewness > 0
              ? 'Right-skewed (positive)'
              : 'Left-skewed (negative)'}
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Kurtosis</h3>
          <p className="text-3xl font-bold text-gray-900">{data.kurtosis.toFixed(3)}</p>
          <p className="text-sm text-gray-600 mt-2">
            {Math.abs(data.kurtosis) < 0.5
              ? 'Normal (mesokurtic)'
              : data.kurtosis > 0
              ? 'Heavy tails (leptokurtic)'
              : 'Light tails (platykurtic)'}
          </p>
        </div>
      </div>
    </div>
  );
};
