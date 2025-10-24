/**
 * VesselList Component
 *
 * List of vessels with status and information
 */
import React from 'react';
import { Vessel, VesselStatus, VesselType } from '../../api/smartport';
import { Ship, TrendingUp, Anchor, Navigation, CheckCircle, XCircle } from 'lucide-react';

interface VesselListProps {
  vessels: Vessel[];
  onVesselClick?: (vessel: Vessel) => void;
  title?: string;
}

const statusColors: Record<VesselStatus, string> = {
  [VesselStatus.APPROACHING]: 'bg-blue-100 text-blue-800',
  [VesselStatus.ANCHORED]: 'bg-yellow-100 text-yellow-800',
  [VesselStatus.BERTHED]: 'bg-green-100 text-green-800',
  [VesselStatus.LOADING]: 'bg-purple-100 text-purple-800',
  [VesselStatus.UNLOADING]: 'bg-indigo-100 text-indigo-800',
  [VesselStatus.DEPARTING]: 'bg-orange-100 text-orange-800',
  [VesselStatus.DEPARTED]: 'bg-gray-100 text-gray-800',
};

const statusIcons: Record<VesselStatus, React.ReactNode> = {
  [VesselStatus.APPROACHING]: <Navigation className="h-4 w-4" />,
  [VesselStatus.ANCHORED]: <Anchor className="h-4 w-4" />,
  [VesselStatus.BERTHED]: <Ship className="h-4 w-4" />,
  [VesselStatus.LOADING]: <TrendingUp className="h-4 w-4" />,
  [VesselStatus.UNLOADING]: <TrendingUp className="h-4 w-4 rotate-180" />,
  [VesselStatus.DEPARTING]: <Navigation className="h-4 w-4 rotate-90" />,
  [VesselStatus.DEPARTED]: <CheckCircle className="h-4 w-4" />,
};

export const VesselList: React.FC<VesselListProps> = ({
  vessels,
  onVesselClick,
  title = 'Vessels',
}) => {
  if (vessels.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">{title}</h3>
        <div className="flex items-center justify-center h-32 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
          <div className="text-center">
            <Ship className="mx-auto h-8 w-8 text-gray-400" />
            <p className="mt-2 text-sm text-gray-500">No vessels found</p>
          </div>
        </div>
      </div>
    );
  }

  const formatDateTime = (dateString?: string) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const isDelayed = (eta?: string, ata?: string) => {
    if (!eta || ata) return false;
    return new Date(eta) < new Date();
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">{title}</h3>
        <span className="text-sm text-gray-500">{vessels.length} vessels</span>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Vessel
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                IMO
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Type
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                ETA/ATA
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                ETD/ATD
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Port
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {vessels.map((vessel) => (
              <tr
                key={vessel.id}
                onClick={() => onVesselClick?.(vessel)}
                className="hover:bg-gray-50 cursor-pointer transition-colors"
              >
                <td className="px-4 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <Ship className="h-5 w-5 text-gray-400 mr-2" />
                    <div>
                      <div className="text-sm font-medium text-gray-900">{vessel.name}</div>
                      {vessel.flag && (
                        <div className="text-xs text-gray-500">{vessel.flag}</div>
                      )}
                    </div>
                  </div>
                </td>
                <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-600">
                  {vessel.imo}
                </td>
                <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-600 capitalize">
                  {vessel.vessel_type.replace(/_/g, ' ')}
                </td>
                <td className="px-4 py-4 whitespace-nowrap">
                  <span
                    className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      statusColors[vessel.status]
                    }`}
                  >
                    {statusIcons[vessel.status]}
                    <span className="capitalize">{vessel.status.replace(/_/g, ' ')}</span>
                  </span>
                </td>
                <td className="px-4 py-4 whitespace-nowrap text-sm">
                  <div className="flex items-center gap-1">
                    {isDelayed(vessel.eta, vessel.ata) && (
                      <XCircle className="h-4 w-4 text-red-500" />
                    )}
                    <span className={isDelayed(vessel.eta, vessel.ata) ? 'text-red-600' : 'text-gray-600'}>
                      {formatDateTime(vessel.ata || vessel.eta)}
                    </span>
                  </div>
                </td>
                <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-600">
                  {formatDateTime(vessel.atd || vessel.etd)}
                </td>
                <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-600">
                  {vessel.origin_port || '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
