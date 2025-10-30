/**
 * Grid Background Component
 * Visual grid for dashboard canvas
 */

import React from 'react';

interface GridBackgroundProps {
  gridSize?: number;
  show?: boolean;
  color?: string;
  opacity?: number;
}

export const GridBackground: React.FC<GridBackgroundProps> = ({
  gridSize = 10,
  show = true,
  color = '#e5e7eb',
  opacity = 0.5,
}) => {
  if (!show) return null;

  return (
    <div
      className="absolute inset-0 pointer-events-none"
      style={{
        backgroundImage: `
          repeating-linear-gradient(
            0deg,
            transparent,
            transparent ${gridSize - 1}px,
            ${color} ${gridSize - 1}px,
            ${color} ${gridSize}px
          ),
          repeating-linear-gradient(
            90deg,
            transparent,
            transparent ${gridSize - 1}px,
            ${color} ${gridSize - 1}px,
            ${color} ${gridSize}px
          )
        `,
        opacity,
      }}
    />
  );
};
