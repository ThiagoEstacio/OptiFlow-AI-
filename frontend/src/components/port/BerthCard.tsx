/**
 * BerthCard - Display berth status and information
 */
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { BerthStatusIndicator } from './StatusIndicator';
import { Skeleton } from '@/components/ui/Skeleton';
import type { Berth } from '@/types/port';
import { Anchor, Ship, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface BerthCardProps {
  berth: Berth;
  vesselName?: string;
  operationProgress?: number;
  loading?: boolean;
  onClick?: () => void;
  className?: string;
}

export function BerthCard({
  berth,
  vesselName,
  operationProgress,
  loading = false,
  onClick,
  className,
}: BerthCardProps) {
  const isOccupied = berth.status === 'occupied';
  const isAvailable = berth.status === 'available';
  const isMaintenance = berth.status === 'maintenance';

  if (loading) {
    return (
      <Card className={className} noPadding>
        <div className="p-6">
          <Skeleton variant="text" width="40%" className="mb-2" />
          <Skeleton variant="text" width="60%" className="mb-4" />
          <Skeleton variant="rectangular" height={60} />
        </div>
      </Card>
    );
  }

  return (
    <Card
      className={cn(
        className,
        onClick && 'cursor-pointer transition-transform hover:scale-[1.02]'
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
              <h3 className="font-semibold text-dark-100">{berth.code}</h3>
              <BerthStatusIndicator status={berth.status} />
            </div>
            <p className="mt-1 text-sm text-dark-400">{berth.name}</p>
          </div>

          {/* Status Icon */}
          <div
            className={cn(
              'flex h-12 w-12 items-center justify-center rounded-lg',
              isOccupied && 'bg-warning-500/10 text-warning-500',
              isAvailable && 'bg-success-500/10 text-success-500',
              isMaintenance && 'bg-purple-500/10 text-purple-500',
              !isOccupied &&
                !isAvailable &&
                !isMaintenance &&
                'bg-dark-700 text-dark-400'
            )}
          >
            {isOccupied ? (
              <Ship className="h-6 w-6" />
            ) : isMaintenance ? (
              <AlertCircle className="h-6 w-6" />
            ) : (
              <Anchor className="h-6 w-6" />
            )}
          </div>
        </div>

        {/* Current Vessel (if occupied) */}
        {isOccupied && vesselName && (
          <div className="mt-4 rounded-lg bg-dark-700/50 p-3">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <p className="text-xs text-dark-400">Current Vessel</p>
                <p className="mt-0.5 font-medium text-dark-100">{vesselName}</p>
              </div>
              {operationProgress !== undefined && (
                <div className="text-right">
                  <p className="text-xs text-dark-400">Progress</p>
                  <p className="mt-0.5 font-medium text-success-500">
                    {operationProgress}%
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Berth Specifications */}
        <div className="mt-4 grid grid-cols-2 gap-3">
          <div>
            <p className="text-xs text-dark-400">Type</p>
            <p className="mt-0.5 text-sm font-medium text-dark-200">
              {berth.berth_type.charAt(0).toUpperCase() + berth.berth_type.slice(1)}
            </p>
          </div>
          {berth.capacity_tons_per_hour && (
            <div>
              <p className="text-xs text-dark-400">Capacity</p>
              <p className="mt-0.5 text-sm font-medium text-dark-200">
                {berth.capacity_tons_per_hour.toLocaleString()} t/h
              </p>
            </div>
          )}
        </div>

        {/* Equipment Count */}
        {(berth.number_of_shiploaders ||
          berth.number_of_conveyors ||
          berth.number_of_unloaders) && (
          <div className="mt-3 flex gap-2">
            {berth.number_of_shiploaders && berth.number_of_shiploaders > 0 && (
              <Badge variant="info" size="sm">
                {berth.number_of_shiploaders} Shiploaders
              </Badge>
            )}
            {berth.number_of_conveyors && berth.number_of_conveyors > 0 && (
              <Badge variant="default" size="sm">
                {berth.number_of_conveyors} Conveyors
              </Badge>
            )}
            {berth.number_of_unloaders && berth.number_of_unloaders > 0 && (
              <Badge variant="default" size="sm">
                {berth.number_of_unloaders} Unloaders
              </Badge>
            )}
          </div>
        )}
      </div>
    </Card>
  );
}

/**
 * Compact berth card for dense layouts
 */
export function BerthCardCompact({ berth, className }: { berth: Berth; className?: string }) {
  const isOccupied = berth.status === 'occupied';

  return (
    <div
      className={cn(
        'flex items-center justify-between rounded-lg border border-dark-700 bg-dark-800 p-4',
        className
      )}
    >
      <div className="flex items-center gap-3">
        <div
          className={cn(
            'flex h-10 w-10 items-center justify-center rounded-lg',
            isOccupied ? 'bg-warning-500/10 text-warning-500' : 'bg-success-500/10 text-success-500'
          )}
        >
          {isOccupied ? <Ship className="h-5 w-5" /> : <Anchor className="h-5 w-5" />}
        </div>
        <div>
          <p className="font-medium text-dark-100">{berth.code}</p>
          <p className="text-xs text-dark-400">{berth.name}</p>
        </div>
      </div>
      <BerthStatusIndicator status={berth.status} size="sm" />
    </div>
  );
}
