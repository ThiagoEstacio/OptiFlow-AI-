/**
 * GeoMap Component
 *
 * Geographic map for site/asset location visualization
 * Using Plotly.js with Mapbox
 *
 * Use cases:
 * - Site location overview
 * - Equipment status by location
 * - Distribution network visualization
 * - Regional performance comparison
 * - Fleet tracking
 */

import React from 'react';
import Plot from 'react-plotly.js';

export interface MapMarker {
  lat: number;
  lon: number;
  name: string;
  status?: 'online' | 'offline' | 'warning' | 'critical';
  value?: number;
  metadata?: Record<string, any>;
}

export interface GeoMapProps {
  markers: MapMarker[];
  title?: string;
  center?: { lat: number; lon: number };
  zoom?: number;
  height?: number;
  width?: number | string;
  mapStyle?: 'light' | 'dark' | 'satellite' | 'outdoors';
  showScale?: boolean;
  clusterMarkers?: boolean;
  metric?: string;  // Optional metric name being displayed
  unit?: string;    // Optional unit for the metric
}

export const GeoMap: React.FC<GeoMapProps> = ({
  markers,
  title,
  center,
  zoom = 4,
  height = 500,
  width = '100%',
  mapStyle = 'light',
  showScale = true,
  clusterMarkers = false,
}) => {
  // Default center (Brazil center if not specified)
  const defaultCenter = center || {
    lat: -15.7801,  // Brazil center
    lon: -47.9292,
  };

  // Auto-calculate center from markers if not specified and markers available
  const calculatedCenter = center || (markers.length > 0 ? {
    lat: markers.reduce((sum, m) => sum + m.lat, 0) / markers.length,
    lon: markers.reduce((sum, m) => sum + m.lon, 0) / markers.length,
  } : defaultCenter);

  // Map status to colors
  const getStatusColor = (status?: string): string => {
    switch (status) {
      case 'online': return '#10b981';    // green
      case 'offline': return '#6b7280';   // gray
      case 'warning': return '#f59e0b';   // amber
      case 'critical': return '#ef4444';  // red
      default: return '#3b82f6';          // blue
    }
  };

  // Map status to symbols
  const getStatusSymbol = (status?: string): string => {
    switch (status) {
      case 'online': return 'circle';
      case 'offline': return 'circle-open';
      case 'warning': return 'triangle';
      case 'critical': return 'square';
      default: return 'circle';
    }
  };

  // Map style to Mapbox style
  const getMapboxStyle = (): string => {
    switch (mapStyle) {
      case 'dark': return 'dark';
      case 'satellite': return 'satellite-streets';
      case 'outdoors': return 'outdoors';
      default: return 'open-street-map';  // Use OSM instead of Mapbox (no API key required)
    }
  };

  const trace: Plotly.Data = {
    type: 'scattermapbox',
    lat: markers.map(m => m.lat),
    lon: markers.map(m => m.lon),
    mode: 'markers',
    marker: {
      size: markers.map(m => m.value ? Math.sqrt(m.value) + 8 : 14),
      color: markers.map(m => getStatusColor(m.status)),
      opacity: 0.8,
      symbol: markers.map(m => getStatusSymbol(m.status)) as any,
      line: {
        color: 'white',
        width: 2,
      },
    },
    text: markers.map(m => m.name),
    customdata: markers.map(m => ({
      status: m.status || 'unknown',
      value: m.value || 0,
      ...m.metadata,
    })),
    hovertemplate: '<b>%{text}</b><br>' +
      'Location: (%{lat:.4f}, %{lon:.4f})<br>' +
      'Status: %{customdata.status}<br>' +
      'Value: %{customdata.value:.2f}<extra></extra>',
    cluster: clusterMarkers ? { enabled: true } : undefined,
  } as any;

  const layout: Partial<Plotly.Layout> = {
    title: title ? {
      text: title,
      font: { size: 18, color: '#374151' },
    } : undefined,
    height: height,
    width: typeof width === 'number' ? width : undefined,
    margin: { t: title ? 60 : 20, r: 20, l: 20, b: 20 },
    paper_bgcolor: 'rgba(0,0,0,0)',

    mapbox: {
      style: getMapboxStyle(),
      center: calculatedCenter,
      zoom: zoom,
    },

    showlegend: false,

    font: { family: 'Inter, system-ui, sans-serif' },
  };

  const config: Partial<Plotly.Config> = {
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['lasso2d', 'select2d'],
    responsive: true,
    scrollZoom: true,
  };

  // Calculate status summary
  const statusCounts = markers.reduce((acc, marker) => {
    const status = marker.status || 'unknown';
    acc[status] = (acc[status] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return (
    <div className="geo-map-container">
      <Plot
        data={[trace]}
        layout={layout}
        config={config}
        style={{ width: width === '100%' ? '100%' : width }}
        useResizeHandler={true}
      />

      {/* Status legend */}
      <div className="map-legend mt-4 flex justify-center gap-3 text-sm">
        {Object.entries(statusCounts).map(([status, count]) => (
          <div key={status} className="flex items-center gap-2 bg-gray-50 px-3 py-2 rounded">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: getStatusColor(status) }}
            />
            <span className="text-gray-700 capitalize">{status}</span>
            <span className="font-semibold text-gray-900">({count})</span>
          </div>
        ))}
      </div>

      {/* Summary statistics */}
      <div className="map-summary mt-3 grid grid-cols-3 gap-3 text-sm">
        <div className="stat-card bg-blue-50 p-3 rounded text-center">
          <div className="text-gray-600 text-xs">Total Sites</div>
          <div className="text-lg font-semibold text-blue-900">{markers.length}</div>
        </div>

        <div className="stat-card bg-green-50 p-3 rounded text-center">
          <div className="text-gray-600 text-xs">Online</div>
          <div className="text-lg font-semibold text-green-900">
            {statusCounts.online || 0}
          </div>
        </div>

        <div className="stat-card bg-red-50 p-3 rounded text-center">
          <div className="text-gray-600 text-xs">Issues</div>
          <div className="text-lg font-semibold text-red-900">
            {(statusCounts.warning || 0) + (statusCounts.critical || 0) + (statusCounts.offline || 0)}
          </div>
        </div>
      </div>
    </div>
  );
};

export default GeoMap;
