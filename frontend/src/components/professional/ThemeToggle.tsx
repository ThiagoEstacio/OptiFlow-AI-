/**
 * Professional Theme Toggle - Animated Switch
 * Smooth transition between light and dark modes
 */
import React from 'react';
import {
  IconButton,
  Tooltip,
  Box,
  useTheme as useMuiTheme,
  alpha
} from '@mui/material';
import {
  LightMode,
  DarkMode,
  Brightness4
} from '@mui/icons-material';
import { useTheme } from '../../contexts/ThemeContext';

export const ThemeToggle: React.FC = () => {
  const { theme, effectiveTheme, toggleTheme } = useTheme();
  const muiTheme = useMuiTheme();

  const getIcon = () => {
    if (effectiveTheme === 'dark') {
      return <DarkMode />;
    }
    return <LightMode />;
  };

  const getTooltip = () => {
    return effectiveTheme === 'dark'
      ? 'Switch to light mode'
      : 'Switch to dark mode';
  };

  return (
    <Tooltip title={getTooltip()} arrow>
      <IconButton
        onClick={toggleTheme}
        sx={{
          width: 40,
          height: 40,
          position: 'relative',
          overflow: 'hidden',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          backgroundColor: alpha(muiTheme.palette.primary.main, 0.08),
          '&:hover': {
            backgroundColor: alpha(muiTheme.palette.primary.main, 0.12),
            transform: 'rotate(180deg)',
          },
          '& .MuiSvgIcon-root': {
            fontSize: '1.25rem',
            color: muiTheme.palette.primary.main,
            transition: 'all 0.3s',
          },
        }}
      >
        {getIcon()}
      </IconButton>
    </Tooltip>
  );
};
