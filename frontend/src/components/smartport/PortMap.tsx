/**
 * PortMap Component
 *
 * Visual map of the port showing berths and their status
 */
import React from 'react';
import { Berth, BerthStatus } from '../../api/smartport';
import { Anchor } from 'lucide-react';

interface PortMapProps {
  berths: Berth[];
  selectedBerthId?: string;
  onBerthClick?: (berth: Berth) => void;
}

const statusColors: Record<BerthStatus, string> = {
  [BerthStatus.AVAILABLE]: 'bg-green-500',
  [BerthStatus.OCCUPIED]: 'bg-red-500',
  [BerthStatus.RESERVED]: 'bg-yellow-500',
  [BerthStatus.MAINTENANCE]: 'bg-gray-500',
  [BerthStatus.UNAVAILABLE]: 'bg-gray-300',
};

const statusTextColors: Record<BerthStatus, string> = {
  [BerthStatus.AVAILABLE]: 'text-green-700',
  [BerthStatus.OCCUPIED]: 'text-red-700',
  [BerthStatus.RESERVED]: 'text-yellow-700',
  [BerthStatus.MAINTENANCE]: 'text-gray-700',
  [BerthStatus.UNAVAILABLE]: 'text-gray-500',
};

export const PortMap: React.FC<PortMapProps> = ({ berths, selectedBerthId, onBerthClick }) => {
  if (berths.length === 0) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
        <div className="text-center">
          <Anchor className="mx-auto h-12 w-12 text-gray-400" />
          <p className="mt-2 text-sm text-gray-500">No berths available</p>
        </div>
      </div>
    );
  }

  // Calculate map boundaries
  const lats = berths.map((b) => b.latitude);
  const lons = berths.map((b) => b.longitude);
  const minLat = Math.min(...lats);
  const maxLat = Math.max(...lats);
  const minLon = Math.min(...lons);
  const maxLon = Math.max(...lons);

  // Add padding
  const latPadding = (maxLat - minLat) * 0.1 || 0.01;
  const lonPadding = (maxLon - minLon) * 0.1 || 0.01;

  const mapMinLat = minLat - latPadding;
  const mapMaxLat = maxLat + latPadding;
  const mapMinLon = minLon - lonPadding;
  const mapMaxLon = maxLon + lonPadding;

  // Convert lat/lon to SVG coordinates
  const latToY = (lat: number) => {
    const normalized = (lat - mapMinLat) / (mapMaxLat - mapMinLat);
    return (1 - normalized) * 400; // Invert Y axis
  };

  const lonToX = (lon: number) => {
    const normalized = (lon - mapMinLon) / (mapMaxLon - mapMinLon);
    return normalized * 600;
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Port Map</h3>
        <div className="flex gap-4 text-xs">
          {Object.entries(statusColors).map(([status, color]) => (
            <div key={status} className="flex items-center gap-1">
              <div className={`w-3 h-3 rounded ${color}`} />
              <span className="capitalize">{status.replace('_', ' ')}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-blue-50 rounded-lg overflow-hidden border border-blue-200">
        <svg
          viewBox="0 0 600 400"
          className="w-full h-auto"
          style={{ maxHeight: '500px' }}
        >
          {/* Water background */}
          <rect x="0" y="0" width="600" height="400" fill="#e0f2fe" />

          {/* Grid lines */}
          {[...Array(6)].map((_, i) => (
            <line
              key={`v-${i}`}
              x1={i * 120}
              y1="0"
              x2={i * 120}
              y2="400"
              stroke="#cbd5e1"
              strokeWidth="0.5"
              strokeDasharray="2,2"
            />
          ))}
          {[...Array(5)].map((_, i) => (
            <line
              key={`h-${i}`}
              x1="0"
              y1={i * 100}
              x2="600"
              y2={i * 100}
              stroke="#cbd5e1"
              strokeWidth="0.5"
              strokeDasharray="2,2"
            />
          ))}

          {/* Berths */}
          {berths.map((berth) => {
            const x = lonToX(berth.longitude);
            const y = latToY(berth.latitude);
            const isSelected = berth.id === selectedBerthId;
            const color = statusColors[berth.status];

            return (
              <g
                key={berth.id}
                onClick={() => onBerthClick?.(berth)}
                className="cursor-pointer hover:opacity-80 transition-opacity"
              >
                {/* Berth marker */}
                <circle
                  cx={x}
                  cy={y}
                  r={isSelected ? 12 : 8}
                  className={color}
                  stroke={isSelected ? '#1e40af' : '#fff'}
                  strokeWidth={isSelected ? 3 : 2}
                />

                {/* Berth code label */}
                <text
                  x={x}
                  y={y - 15}
                  textAnchor="middle"
                  className="text-xs font-semibold fill-gray-700"
                >
                  {berth.code}
                </text>

                {/* Tooltip background */}
                {isSelected && (
                  <rect
                    x={x - 60}
                    y={y + 15}
                    width="120"
                    height="40"
                    rx="4"
                    fill="white"
                    stroke="#1e40af"
                    strokeWidth="2"
                  />
                )}

                {/* Tooltip text */}
                {isSelected && (
                  <>
                    <text
                      x={x}
                      y={y + 30}
                      textAnchor="middle"
                      className="text-xs font-medium fill-gray-900"
                    >
                      {berth.name}
                    </text>
                    <text
                      x={x}
                      y={y + 45}
                      textAnchor="middle"
                      className={`text-xs ${statusTextColors[berth.status]}`}
                    >
                      {berth.status.toUpperCase()}
                    </text>
                  </>
                )}
              </g>
            );
          })}
        </svg>
      </div>

      {/* Selected berth details */}
      {selectedBerthId && berths.find((b) => b.id === selectedBerthId) && (
        <div className="mt-4 p-4 bg-gray-50 rounded-lg">
          {(() => {
            const berth = berths.find((b) => b.id === selectedBerthId)!;
            return (
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-600">Type</p>
                  <p className="font-medium capitalize">{berth.berth_type.replace('_', ' ')}</p>
                </div>
                <div>
                  <p className="text-gray-600">Max LOA</p>
                  <p className="font-medium">{berth.max_loa}m</p>
                </div>
                <div>
                  <p className="text-gray-600">Max Draft</p>
                  <p className="font-medium">{berth.max_draft}m</p>
                </div>
                <div>
                  <p className="text-gray-600">Cranes</p>
                  <p className="font-medium">{berth.number_of_cranes}</p>
                </div>
              </div>
            );
          })()}
        </div>
      )}
    </div>
  );
};
