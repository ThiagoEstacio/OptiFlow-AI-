/**
 * BerthStatusGrid Component
 *
 * Grid view of all berths with their status and information
 */
import React from 'react';
import { Berth, BerthStatus, BerthType } from '../../api/smartport';
import { Anchor, Ship, Package, Circle } from 'lucide-react';

interface BerthStatusGridProps {
  berths: Berth[];
  onBerthClick?: (berth: Berth) => void;
}

const statusColors: Record<BerthStatus, string> = {
  [BerthStatus.AVAILABLE]: 'border-green-500 bg-green-50',
  [BerthStatus.OCCUPIED]: 'border-red-500 bg-red-50',
  [BerthStatus.RESERVED]: 'border-yellow-500 bg-yellow-50',
  [BerthStatus.MAINTENANCE]: 'border-gray-500 bg-gray-50',
  [BerthStatus.UNAVAILABLE]: 'border-gray-300 bg-gray-100',
};

const statusBadgeColors: Record<BerthStatus, string> = {
  [BerthStatus.AVAILABLE]: 'bg-green-100 text-green-800',
  [BerthStatus.OCCUPIED]: 'bg-red-100 text-red-800',
  [BerthStatus.RESERVED]: 'bg-yellow-100 text-yellow-800',
  [BerthStatus.MAINTENANCE]: 'bg-gray-100 text-gray-800',
  [BerthStatus.UNAVAILABLE]: 'bg-gray-100 text-gray-600',
};

const typeIcons: Record<BerthType, React.ReactNode> = {
  [BerthType.CONTAINER]: <Package className="h-5 w-5" />,
  [BerthType.BULK]: <Ship className="h-5 w-5" />,
  [BerthType.GENERAL_CARGO]: <Package className="h-5 w-5" />,
  [BerthType.RO_RO]: <Ship className="h-5 w-5" />,
  [BerthType.TANKER]: <Circle className="h-5 w-5" />,
  [BerthType.CRUISE]: <Ship className="h-5 w-5" />,
};

export const BerthStatusGrid: React.FC<BerthStatusGridProps> = ({ berths, onBerthClick }) => {
  if (berths.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
        <div className="text-center">
          <Anchor className="mx-auto h-12 w-12 text-gray-400" />
          <p className="mt-2 text-sm text-gray-500">No berths available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Berth Status</h3>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {berths.map((berth) => (
          <div
            key={berth.id}
            onClick={() => onBerthClick?.(berth)}
            className={`border-l-4 ${statusColors[berth.status]} rounded-lg p-4 cursor-pointer hover:shadow-md transition-shadow`}
          >
            {/* Header */}
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="text-gray-600">{typeIcons[berth.berth_type]}</div>
                <div>
                  <h4 className="font-semibold text-gray-900">{berth.code}</h4>
                  <p className="text-xs text-gray-600">{berth.name}</p>
                </div>
              </div>
              <span
                className={`px-2 py-1 text-xs font-medium rounded ${
                  statusBadgeColors[berth.status]
                }`}
              >
                {berth.status === BerthStatus.AVAILABLE && 'Available'}
                {berth.status === BerthStatus.OCCUPIED && 'Occupied'}
                {berth.status === BerthStatus.RESERVED && 'Reserved'}
                {berth.status === BerthStatus.MAINTENANCE && 'Maintenance'}
                {berth.status === BerthStatus.UNAVAILABLE && 'Unavailable'}
              </span>
            </div>

            {/* Details */}
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Type:</span>
                <span className="font-medium capitalize">
                  {berth.berth_type.replace(/_/g, ' ')}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Max LOA:</span>
                <span className="font-medium">{berth.max_loa}m</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Draft:</span>
                <span className="font-medium">{berth.max_draft}m</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Cranes:</span>
                <span className="font-medium">{berth.number_of_cranes}</span>
              </div>
            </div>

            {/* Occupation info */}
            {berth.status === BerthStatus.OCCUPIED && berth.occupation_start && (
              <div className="mt-3 pt-3 border-t border-gray-200">
                <p className="text-xs text-gray-600">
                  Occupied since:{' '}
                  {new Date(berth.occupation_start).toLocaleDateString(undefined, {
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </p>
                {berth.estimated_departure && (
                  <p className="text-xs text-gray-600">
                    ETD:{' '}
                    {new Date(berth.estimated_departure).toLocaleDateString(undefined, {
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </p>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
