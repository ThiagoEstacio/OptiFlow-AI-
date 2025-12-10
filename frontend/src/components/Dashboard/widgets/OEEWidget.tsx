/**
 * OEE Widget - Overall Equipment Effectiveness
 * Displays OEE with breakdown: Availability, Performance, Quality
 */
import React, { useState, useEffect } from 'react';
import apiClient from '../../../api/client';

interface Widget {
  id: string;
  title: string;
  config: any;
  data_config: any;
  display_config: any;
}

interface OEEData {
  oee: number;
  availability: number;
  performance: number;
  quality: number;
  target: number;
}

interface OEEWidgetProps {
  widget: Widget;
}

const OEEWidget: React.FC<OEEWidgetProps> = ({ widget }) => {
  const [data, setData] = useState<OEEData>({
    oee: 0,
    availability: 0,
    performance: 0,
    quality: 0,
    target: widget.config?.targetOEE || 85,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchOEE = async () => {
      try {
        const response = await apiClient.get('/api/v1/oee/current');
        if (response.data) {
          setData({
            oee: response.data.oee || 0,
            availability: response.data.availability || 0,
            performance: response.data.performance || 0,
            quality: response.data.quality || 0,
            target: widget.config?.targetOEE || 85,
          });
        }
      } catch (error) {
        // Use fallback data
        setData({
          oee: 78.5,
          availability: 92.3,
          performance: 88.1,
          quality: 96.5,
          target: widget.config?.targetOEE || 85,
        });
      } finally {
        setLoading(false);
      }
    };

    fetchOEE();
    const interval = setInterval(fetchOEE, 30000);
    return () => clearInterval(interval);
  }, [widget.config?.targetOEE]);

  const getOEEColor = (value: number) => {
    if (value >= 85) return '#10B981'; // Green
    if (value >= 65) return '#F59E0B'; // Yellow
    return '#EF4444'; // Red
  };

  const showComponents = widget.config?.showComponents ?? true;

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col p-2">
      {/* Main OEE Circle */}
      <div className="flex-1 flex items-center justify-center">
        <div className="relative">
          <svg className="w-32 h-32" viewBox="0 0 100 100">
            {/* Background circle */}
            <circle
              cx="50"
              cy="50"
              r="45"
              fill="none"
              stroke="#E5E7EB"
              strokeWidth="8"
            />
            {/* Progress circle */}
            <circle
              cx="50"
              cy="50"
              r="45"
              fill="none"
              stroke={getOEEColor(data.oee)}
              strokeWidth="8"
              strokeLinecap="round"
              strokeDasharray={`${(data.oee / 100) * 283} 283`}
              transform="rotate(-90 50 50)"
              className="transition-all duration-500"
            />
            {/* Target marker */}
            <circle
              cx="50"
              cy="5"
              r="3"
              fill="#6B7280"
              transform={`rotate(${(data.target / 100) * 360 - 90} 50 50)`}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-3xl font-bold" style={{ color: getOEEColor(data.oee) }}>
              {data.oee.toFixed(1)}%
            </span>
            <span className="text-xs text-gray-500">OEE</span>
          </div>
        </div>
      </div>

      {/* Components breakdown */}
      {showComponents && (
        <div className="grid grid-cols-3 gap-2 mt-2">
          <div className="text-center p-2 bg-blue-50 rounded-lg">
            <div className="text-lg font-semibold text-blue-600">
              {data.availability.toFixed(1)}%
            </div>
            <div className="text-xs text-gray-500">Disponibilidade</div>
          </div>
          <div className="text-center p-2 bg-green-50 rounded-lg">
            <div className="text-lg font-semibold text-green-600">
              {data.performance.toFixed(1)}%
            </div>
            <div className="text-xs text-gray-500">Performance</div>
          </div>
          <div className="text-center p-2 bg-purple-50 rounded-lg">
            <div className="text-lg font-semibold text-purple-600">
              {data.quality.toFixed(1)}%
            </div>
            <div className="text-xs text-gray-500">Qualidade</div>
          </div>
        </div>
      )}

      {/* Target indicator */}
      <div className="mt-2 flex items-center justify-center gap-2 text-xs text-gray-500">
        <span className="w-2 h-2 rounded-full bg-gray-400"></span>
        <span>Meta: {data.target}%</span>
        {data.oee >= data.target ? (
          <span className="text-green-600 font-medium">Atingida</span>
        ) : (
          <span className="text-amber-600 font-medium">
            -{(data.target - data.oee).toFixed(1)}%
          </span>
        )}
      </div>
    </div>
  );
};

export default OEEWidget;
