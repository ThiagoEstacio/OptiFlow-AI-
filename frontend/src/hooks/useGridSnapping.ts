/**
 * Grid Snapping Hook
 * Provides grid snapping functionality for dashboard widgets
 */

import { useState, useCallback } from 'react';

interface Position {
  x: number;
  y: number;
}

interface Size {
  width: number;
  height: number;
}

interface UseGridSnappingOptions {
  gridSize?: number;
  enabled?: boolean;
}

export const useGridSnapping = (options: UseGridSnappingOptions = {}) => {
  const { gridSize = 10, enabled = true } = options;

  const [isSnapping, setIsSnapping] = useState(enabled);

  // Snap a value to the grid
  const snapToGrid = useCallback(
    (value: number): number => {
      if (!isSnapping) return value;
      return Math.round(value / gridSize) * gridSize;
    },
    [gridSize, isSnapping]
  );

  // Snap a position to the grid
  const snapPosition = useCallback(
    (position: Position): Position => {
      if (!isSnapping) return position;
      return {
        x: snapToGrid(position.x),
        y: snapToGrid(position.y),
      };
    },
    [snapToGrid, isSnapping]
  );

  // Snap a size to the grid
  const snapSize = useCallback(
    (size: Size): Size => {
      if (!isSnapping) return size;
      return {
        width: snapToGrid(size.width),
        height: snapToGrid(size.height),
      };
    },
    [snapToGrid, isSnapping]
  );

  // Toggle snapping on/off
  const toggleSnapping = useCallback(() => {
    setIsSnapping(prev => !prev);
  }, []);

  return {
    isSnapping,
    gridSize,
    snapToGrid,
    snapPosition,
    snapSize,
    toggleSnapping,
    setIsSnapping,
  };
};
