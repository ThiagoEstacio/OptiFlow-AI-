/**
 * StatusIndicator - SmartPort status display component
 * Maps status values to appropriate badge variants
 */
import { Badge, BadgeProps } from '@/components/ui/Badge';
import type {
  VesselStatus,
  BerthStatus,
  OperationStatus,
  EquipmentStatus,
} from '@/types/port';

type Status = VesselStatus | BerthStatus | OperationStatus | EquipmentStatus | string;

interface StatusIndicatorProps {
  status: Status;
  dot?: boolean;
  size?: BadgeProps['size'];
  className?: string;
}

/**
 * Map status values to badge variants
 */
function getStatusVariant(status: Status): BadgeProps['variant'] {
  const statusLower = status.toLowerCase();

  // Success states (green)
  if (
    statusLower.includes('completed') ||
    statusLower.includes('available') ||
    statusLower.includes('operating') ||
    statusLower.includes('loading') ||
    statusLower.includes('unloading')
  ) {
    return 'success';
  }

  // Warning states (orange/yellow)
  if (
    statusLower.includes('warning') ||
    statusLower.includes('paused') ||
    statusLower.includes('delayed') ||
    statusLower.includes('anchored') ||
    statusLower.includes('occupied') ||
    statusLower.includes('reserved') ||
    statusLower.includes('maintenance')
  ) {
    return 'warning';
  }

  // Danger states (red)
  if (
    statusLower.includes('error') ||
    statusLower.includes('fault') ||
    statusLower.includes('cancelled') ||
    statusLower.includes('offline') ||
    statusLower.includes('unavailable')
  ) {
    return 'danger';
  }

  // Info states (cyan/blue)
  if (
    statusLower.includes('scheduled') ||
    statusLower.includes('planned') ||
    statusLower.includes('ready') ||
    statusLower.includes('berthed') ||
    statusLower.includes('approaching')
  ) {
    return 'info';
  }

  // Purple states
  if (statusLower.includes('in_progress') || statusLower.includes('berthing')) {
    return 'purple';
  }

  // Idle/neutral states
  if (statusLower.includes('idle') || statusLower.includes('departed')) {
    return 'default';
  }

  // Default
  return 'default';
}

/**
 * Format status text for display
 */
function formatStatusText(status: Status): string {
  return status
    .replace(/_/g, ' ')
    .split(' ')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
}

export function StatusIndicator({
  status,
  dot = true,
  size = 'sm',
  className,
}: StatusIndicatorProps) {
  return (
    <Badge
      variant={getStatusVariant(status)}
      size={size}
      dot={dot}
      className={className}
    >
      {formatStatusText(status)}
    </Badge>
  );
}

/**
 * Vessel-specific status indicator
 */
export function VesselStatusIndicator({
  status,
  ...props
}: Omit<StatusIndicatorProps, 'status'> & { status: VesselStatus }) {
  return <StatusIndicator status={status} {...props} />;
}

/**
 * Operation-specific status indicator
 */
export function OperationStatusIndicator({
  status,
  ...props
}: Omit<StatusIndicatorProps, 'status'> & { status: OperationStatus }) {
  return <StatusIndicator status={status} {...props} />;
}

/**
 * Equipment-specific status indicator
 */
export function EquipmentStatusIndicator({
  status,
  ...props
}: Omit<StatusIndicatorProps, 'status'> & { status: EquipmentStatus }) {
  return <StatusIndicator status={status} {...props} />;
}

/**
 * Berth-specific status indicator
 */
export function BerthStatusIndicator({
  status,
  ...props
}: Omit<StatusIndicatorProps, 'status'> & { status: BerthStatus }) {
  return <StatusIndicator status={status} {...props} />;
}
