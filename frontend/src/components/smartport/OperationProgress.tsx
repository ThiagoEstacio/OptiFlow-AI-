/**
 * OperationProgress Component
 *
 * Shows progress of active port operations
 */
import React from 'react';
import { PortOperation, OperationStatus, OperationType } from '../../api/smartport';
import { Package, TrendingUp, Clock, AlertTriangle, CheckCircle } from 'lucide-react';

interface OperationProgressProps {
  operations: PortOperation[];
  onOperationClick?: (operation: PortOperation) => void;
}

const statusColors: Record<OperationStatus, string> = {
  [OperationStatus.SCHEDULED]: 'bg-blue-100 text-blue-800',
  [OperationStatus.IN_PROGRESS]: 'bg-green-100 text-green-800',
  [OperationStatus.PAUSED]: 'bg-yellow-100 text-yellow-800',
  [OperationStatus.COMPLETED]: 'bg-gray-100 text-gray-800',
  [OperationStatus.CANCELLED]: 'bg-red-100 text-red-800',
  [OperationStatus.DELAYED]: 'bg-orange-100 text-orange-800',
};

const typeIcons: Record<OperationType, React.ReactNode> = {
  [OperationType.LOADING]: <TrendingUp className="h-5 w-5" />,
  [OperationType.UNLOADING]: <TrendingUp className="h-5 w-5 rotate-180" />,
  [OperationType.BUNKERING]: <Package className="h-5 w-5" />,
  [OperationType.MAINTENANCE]: <Package className="h-5 w-5" />,
  [OperationType.INSPECTION]: <Package className="h-5 w-5" />,
  [OperationType.PASSENGER_OPERATION]: <Package className="h-5 w-5" />,
};

export const OperationProgress: React.FC<OperationProgressProps> = ({
  operations,
  onOperationClick,
}) => {
  if (operations.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Active Operations</h3>
        <div className="flex items-center justify-center h-32 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
          <div className="text-center">
            <Package className="mx-auto h-8 w-8 text-gray-400" />
            <p className="mt-2 text-sm text-gray-500">No active operations</p>
          </div>
        </div>
      </div>
    );
  }

  const calculateCompletion = (operation: PortOperation): number => {
    if (operation.containers_planned && operation.containers_planned > 0) {
      return Math.min(100, (operation.containers_completed / operation.containers_planned) * 100);
    }
    if (operation.tonnage_planned && operation.tonnage_planned > 0) {
      return Math.min(100, (operation.tonnage_completed / operation.tonnage_planned) * 100);
    }
    return 0;
  };

  const formatDuration = (start?: string, end?: string) => {
    if (!start) return '-';
    const startDate = new Date(start);
    const endDate = end ? new Date(end) : new Date();
    const hours = (endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60);
    return `${hours.toFixed(1)}h`;
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Active Operations</h3>
        <span className="text-sm text-gray-500">{operations.length} operations</span>
      </div>

      <div className="space-y-4">
        {operations.map((operation) => {
          const completion = calculateCompletion(operation);

          return (
            <div
              key={operation.id}
              onClick={() => onOperationClick?.(operation)}
              className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="text-gray-600">{typeIcons[operation.operation_type]}</div>
                  <div>
                    <h4 className="font-medium text-gray-900 capitalize">
                      {operation.operation_type.replace(/_/g, ' ')}
                    </h4>
                    <p className="text-xs text-gray-500">
                      {operation.cargo_description || 'No description'}
                    </p>
                  </div>
                </div>
                <span
                  className={`px-2.5 py-1 text-xs font-medium rounded-full ${
                    statusColors[operation.status]
                  }`}
                >
                  {operation.status.replace(/_/g, ' ').toUpperCase()}
                </span>
              </div>

              {/* Progress bar */}
              <div className="mb-3">
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">Progress</span>
                  <span className="font-medium">{completion.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div
                    className="bg-blue-600 h-2.5 rounded-full transition-all"
                    style={{ width: `${completion}%` }}
                  />
                </div>
              </div>

              {/* Details grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                {operation.containers_planned && (
                  <div>
                    <p className="text-gray-600 text-xs">Containers</p>
                    <p className="font-medium">
                      {operation.containers_completed}/{operation.containers_planned}
                    </p>
                  </div>
                )}
                {operation.tonnage_planned && (
                  <div>
                    <p className="text-gray-600 text-xs">Tonnage</p>
                    <p className="font-medium">
                      {(operation.tonnage_completed / 1000).toFixed(1)}/
                      {(operation.tonnage_planned / 1000).toFixed(1)}k
                    </p>
                  </div>
                )}
                {operation.cranes_assigned > 0 && (
                  <div>
                    <p className="text-gray-600 text-xs">Cranes</p>
                    <p className="font-medium">{operation.cranes_assigned}</p>
                  </div>
                )}
                <div>
                  <p className="text-gray-600 text-xs">Duration</p>
                  <p className="font-medium flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {formatDuration(operation.actual_start, operation.actual_end)}
                  </p>
                </div>
              </div>

              {/* Performance metrics */}
              {operation.efficiency_percentage && (
                <div className="mt-3 pt-3 border-t border-gray-200 grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-gray-600 text-xs">Efficiency</p>
                    <p className="font-medium flex items-center gap-1">
                      <CheckCircle className="h-3 w-3 text-green-600" />
                      {operation.efficiency_percentage.toFixed(1)}%
                    </p>
                  </div>
                  {operation.productivity_rate && (
                    <div>
                      <p className="text-gray-600 text-xs">Productivity</p>
                      <p className="font-medium">{operation.productivity_rate.toFixed(1)}/hr</p>
                    </div>
                  )}
                </div>
              )}

              {/* Alerts */}
              {(operation.weather_delay ||
                operation.equipment_delay ||
                operation.labor_delay) && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {operation.weather_delay && (
                    <span className="inline-flex items-center gap-1 px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded">
                      <AlertTriangle className="h-3 w-3" />
                      Weather Delay
                    </span>
                  )}
                  {operation.equipment_delay && (
                    <span className="inline-flex items-center gap-1 px-2 py-1 bg-red-100 text-red-800 text-xs rounded">
                      <AlertTriangle className="h-3 w-3" />
                      Equipment Delay
                    </span>
                  )}
                  {operation.labor_delay && (
                    <span className="inline-flex items-center gap-1 px-2 py-1 bg-orange-100 text-orange-800 text-xs rounded">
                      <AlertTriangle className="h-3 w-3" />
                      Labor Delay
                    </span>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
