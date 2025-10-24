/**
 * EquipmentCard - Display equipment status and health
 */
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { EquipmentStatusIndicator } from './StatusIndicator';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { Skeleton } from '@/components/ui/Skeleton';
import type { PortEquipment } from '@/types/port';
import {
  Activity,
  AlertTriangle,
  Wrench,
  TrendingUp,
  Calendar,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { formatNumber } from '@/lib/utils';

export interface EquipmentCardProps {
  equipment: PortEquipment;
  loading?: boolean;
  onClick?: () => void;
  className?: string;
}

export function EquipmentCard({
  equipment,
  loading = false,
  onClick,
  className,
}: EquipmentCardProps) {
  const healthScore = equipment.health_score || 0;
  const failureProbability = equipment.failure_probability || 0;

  // Determine health status
  const healthVariant =
    healthScore >= 90
      ? 'success'
      : healthScore >= 70
      ? 'warning'
      : 'danger';

  const isHighRisk = failureProbability > 20;
  const isCritical = failureProbability > 40 || healthScore < 60;

  if (loading) {
    return (
      <Card className={className} noPadding>
        <div className="p-6">
          <Skeleton variant="text" width="50%" className="mb-2" />
          <Skeleton variant="text" width="70%" className="mb-4" />
          <Skeleton variant="rectangular" height={80} />
        </div>
      </Card>
    );
  }

  return (
    <Card
      className={cn(
        className,
        onClick && 'cursor-pointer transition-transform hover:scale-[1.02]',
        isCritical && 'border-danger-500/30'
      )}
      noPadding
      hover={!!onClick}
      onClick={onClick}
    >
      <div className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-dark-100">{equipment.code}</h3>
              <EquipmentStatusIndicator status={equipment.status} />
              {isCritical && (
                <Badge variant="danger" size="sm">
                  Critical
                </Badge>
              )}
            </div>
            <p className="mt-1 text-sm text-dark-400">{equipment.name}</p>
          </div>

          {/* Status Icon */}
          <div
            className={cn(
              'flex h-12 w-12 items-center justify-center rounded-lg',
              equipment.status === 'operating' && 'bg-success-500/10 text-success-500',
              equipment.status === 'idle' && 'bg-dark-700 text-dark-400',
              equipment.status === 'maintenance' && 'bg-purple-500/10 text-purple-500',
              equipment.status === 'fault' && 'bg-danger-500/10 text-danger-500',
              equipment.status === 'offline' && 'bg-dark-700 text-dark-500'
            )}
          >
            {equipment.status === 'operating' ? (
              <Activity className="h-6 w-6" />
            ) : equipment.status === 'maintenance' ? (
              <Wrench className="h-6 w-6" />
            ) : equipment.status === 'fault' ? (
              <AlertTriangle className="h-6 w-6" />
            ) : (
              <Activity className="h-6 w-6" />
            )}
          </div>
        </div>

        {/* Health Score */}
        <div className="mt-4 space-y-3">
          <div>
            <div className="mb-2 flex items-center justify-between">
              <span className="text-sm text-dark-400">Health Score</span>
              <span
                className={cn(
                  'text-sm font-semibold',
                  healthVariant === 'success' && 'text-success-500',
                  healthVariant === 'warning' && 'text-warning-500',
                  healthVariant === 'danger' && 'text-danger-500'
                )}
              >
                {formatNumber(healthScore, 1)}%
              </span>
            </div>
            <ProgressBar
              value={healthScore}
              variant={healthVariant}
              size="sm"
              animated={equipment.status === 'operating'}
            />
          </div>

          {/* Failure Probability */}
          {isHighRisk && (
            <div className="rounded-lg bg-danger-500/10 p-3">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-danger-500" />
                <div className="flex-1">
                  <p className="text-xs font-medium text-danger-500">
                    High Failure Risk
                  </p>
                  <p className="mt-0.5 text-xs text-dark-400">
                    {formatNumber(failureProbability, 1)}% probability
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Equipment Info */}
        <div className="mt-4 grid grid-cols-2 gap-3">
          <div>
            <p className="text-xs text-dark-400">Type</p>
            <p className="mt-0.5 text-sm font-medium text-dark-200">
              {equipment.equipment_type
                .split('_')
                .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
                .join(' ')}
            </p>
          </div>
          {equipment.berth_id && (
            <div>
              <p className="text-xs text-dark-400">Location</p>
              <p className="mt-0.5 text-sm font-medium text-dark-200">
                {equipment.location || 'Berth'}
              </p>
            </div>
          )}
        </div>

        {/* Maintenance Info */}
        {equipment.next_maintenance_date && (
          <div className="mt-4 flex items-center gap-2 rounded-lg bg-dark-700/50 p-3">
            <Calendar className="h-4 w-4 text-dark-400" />
            <div>
              <p className="text-xs text-dark-400">Next Maintenance</p>
              <p className="mt-0.5 text-sm font-medium text-dark-200">
                {new Date(equipment.next_maintenance_date).toLocaleDateString('pt-BR')}
              </p>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}

/**
 * Compact equipment card showing just status and health
 */
export function EquipmentCardCompact({
  equipment,
  className,
}: {
  equipment: PortEquipment;
  className?: string;
}) {
  const healthScore = equipment.health_score || 0;
  const isHighRisk = (equipment.failure_probability || 0) > 20;

  return (
    <div
      className={cn(
        'flex items-center justify-between rounded-lg border border-dark-700 bg-dark-800 p-4',
        isHighRisk && 'border-danger-500/30',
        className
      )}
    >
      <div className="flex items-center gap-3">
        <div
          className={cn(
            'flex h-10 w-10 items-center justify-center rounded-lg',
            equipment.status === 'operating' && 'bg-success-500/10 text-success-500',
            equipment.status === 'idle' && 'bg-dark-700 text-dark-400',
            equipment.status === 'maintenance' && 'bg-purple-500/10 text-purple-500',
            equipment.status === 'fault' && 'bg-danger-500/10 text-danger-500'
          )}
        >
          <Activity className="h-5 w-5" />
        </div>
        <div>
          <p className="font-medium text-dark-100">{equipment.code}</p>
          <p className="text-xs text-dark-400">{equipment.name}</p>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <div className="text-right">
          <p className="text-xs text-dark-400">Health</p>
          <p
            className={cn(
              'text-sm font-semibold',
              healthScore >= 90 && 'text-success-500',
              healthScore < 90 && healthScore >= 70 && 'text-warning-500',
              healthScore < 70 && 'text-danger-500'
            )}
          >
            {formatNumber(healthScore, 0)}%
          </p>
        </div>
        {isHighRisk && <AlertTriangle className="h-5 w-5 text-danger-500" />}
      </div>
    </div>
  );
}
