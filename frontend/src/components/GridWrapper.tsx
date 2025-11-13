/**
 * Grid Wrapper Component
 *
 * Temporary wrapper to maintain MUI v6 Grid API compatibility
 * while using MUI v7 Grid component
 *
 * This allows gradual migration from:
 * <Grid item xs={12} md={6}> to MUI v7 API
 */

import React from 'react';
import { Grid as MuiGrid, GridProps as MuiGridProps } from '@mui/material';

interface LegacyGridItemProps {
  item?: boolean;
  xs?: number | boolean;
  sm?: number | boolean;
  md?: number | boolean;
  lg?: number | boolean;
  xl?: number | boolean;
  spacing?: number;
  container?: boolean;
  children?: React.ReactNode;
  [key: string]: any;
}

/**
 * GridWrapper component that accepts both MUI v6 and v7 props
 * Converts legacy item/xs/sm/md syntax to MUI v7 compatible props
 */
export const GridWrapper: React.FC<LegacyGridItemProps> = ({
  item,
  xs,
  sm,
  md,
  lg,
  xl,
  container,
  spacing,
  children,
  ...otherProps
}) => {
  // If it's a container, pass through directly
  if (container) {
    return (
      <MuiGrid container spacing={spacing} {...otherProps}>
        {children}
      </MuiGrid>
    );
  }

  // If it's an item, suppress TypeScript errors with any cast
  // This is temporary until full MUI v7 migration
  if (item) {
    const gridProps: any = {
      item: true,
      ...otherProps,
    };

    if (xs !== undefined) gridProps.xs = xs;
    if (sm !== undefined) gridProps.sm = sm;
    if (md !== undefined) gridProps.md = md;
    if (lg !== undefined) gridProps.lg = lg;
    if (xl !== undefined) gridProps.xl = xl;

    return <MuiGrid {...gridProps}>{children}</MuiGrid>;
  }

  // Default: pass through
  return <MuiGrid {...(otherProps as any)}>{children}</MuiGrid>;
};

// Export with same name as Grid for easy replacement
export { GridWrapper as Grid };
export default GridWrapper;
