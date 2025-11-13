/**
 * Professional Theme Configuration - Enterprise Grade
 * Optimized color palettes for light and dark modes
 */
import { createTheme, ThemeOptions, alpha } from '@mui/material/styles';

// Professional Color Palette
const colors = {
  primary: {
    light: '#42a5f5',
    main: '#1976d2',
    dark: '#1565c0',
    contrastText: '#fff',
  },
  secondary: {
    light: '#ba68c8',
    main: '#9c27b0',
    dark: '#7b1fa2',
    contrastText: '#fff',
  },
  success: {
    light: '#66bb6a',
    main: '#2e7d32',
    dark: '#1b5e20',
    contrastText: '#fff',
  },
  error: {
    light: '#ef5350',
    main: '#d32f2f',
    dark: '#c62828',
    contrastText: '#fff',
  },
  warning: {
    light: '#ffa726',
    main: '#ed6c02',
    dark: '#e65100',
    contrastText: '#fff',
  },
  info: {
    light: '#29b6f6',
    main: '#0288d1',
    dark: '#01579b',
    contrastText: '#fff',
  },
};

// Base theme options (shared between light and dark)
const baseThemeOptions: ThemeOptions = {
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontWeight: 700,
      fontSize: '2.5rem',
      lineHeight: 1.2,
      letterSpacing: '-0.02em',
    },
    h2: {
      fontWeight: 700,
      fontSize: '2rem',
      lineHeight: 1.25,
      letterSpacing: '-0.01em',
    },
    h3: {
      fontWeight: 700,
      fontSize: '1.75rem',
      lineHeight: 1.3,
      letterSpacing: '-0.01em',
    },
    h4: {
      fontWeight: 600,
      fontSize: '1.5rem',
      lineHeight: 1.35,
    },
    h5: {
      fontWeight: 600,
      fontSize: '1.25rem',
      lineHeight: 1.4,
    },
    h6: {
      fontWeight: 600,
      fontSize: '1rem',
      lineHeight: 1.5,
    },
    subtitle1: {
      fontSize: '1rem',
      fontWeight: 500,
      lineHeight: 1.5,
    },
    subtitle2: {
      fontSize: '0.875rem',
      fontWeight: 500,
      lineHeight: 1.57,
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.5,
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.57,
    },
    button: {
      textTransform: 'none',
      fontWeight: 600,
    },
    caption: {
      fontSize: '0.75rem',
      lineHeight: 1.66,
    },
    overline: {
      fontSize: '0.75rem',
      fontWeight: 600,
      lineHeight: 2.66,
      textTransform: 'uppercase',
      letterSpacing: '1px',
    },
  },
  shape: {
    borderRadius: 8,
  },
  shadows: [
    'none',
    '0px 2px 1px -1px rgba(0,0,0,0.06),0px 1px 1px 0px rgba(0,0,0,0.042),0px 1px 3px 0px rgba(0,0,0,0.036)',
    '0px 3px 1px -2px rgba(0,0,0,0.06),0px 2px 2px 0px rgba(0,0,0,0.042),0px 1px 5px 0px rgba(0,0,0,0.036)',
    '0px 3px 3px -2px rgba(0,0,0,0.06),0px 3px 4px 0px rgba(0,0,0,0.042),0px 1px 8px 0px rgba(0,0,0,0.036)',
    '0px 2px 4px -1px rgba(0,0,0,0.06),0px 4px 5px 0px rgba(0,0,0,0.042),0px 1px 10px 0px rgba(0,0,0,0.036)',
    '0px 3px 5px -1px rgba(0,0,0,0.06),0px 5px 8px 0px rgba(0,0,0,0.042),0px 1px 14px 0px rgba(0,0,0,0.036)',
    '0px 3px 5px -1px rgba(0,0,0,0.06),0px 6px 10px 0px rgba(0,0,0,0.042),0px 1px 18px 0px rgba(0,0,0,0.036)',
    '0px 4px 5px -2px rgba(0,0,0,0.06),0px 7px 10px 1px rgba(0,0,0,0.042),0px 2px 16px 1px rgba(0,0,0,0.036)',
    '0px 5px 5px -3px rgba(0,0,0,0.06),0px 8px 10px 1px rgba(0,0,0,0.042),0px 3px 14px 2px rgba(0,0,0,0.036)',
    '0px 5px 6px -3px rgba(0,0,0,0.06),0px 9px 12px 1px rgba(0,0,0,0.042),0px 3px 16px 2px rgba(0,0,0,0.036)',
    '0px 6px 6px -3px rgba(0,0,0,0.06),0px 10px 14px 1px rgba(0,0,0,0.042),0px 4px 18px 3px rgba(0,0,0,0.036)',
    '0px 6px 7px -4px rgba(0,0,0,0.06),0px 11px 15px 1px rgba(0,0,0,0.042),0px 4px 20px 3px rgba(0,0,0,0.036)',
    '0px 7px 8px -4px rgba(0,0,0,0.06),0px 12px 17px 2px rgba(0,0,0,0.042),0px 5px 22px 4px rgba(0,0,0,0.036)',
    '0px 7px 8px -4px rgba(0,0,0,0.06),0px 13px 19px 2px rgba(0,0,0,0.042),0px 5px 24px 4px rgba(0,0,0,0.036)',
    '0px 7px 9px -4px rgba(0,0,0,0.06),0px 14px 21px 2px rgba(0,0,0,0.042),0px 5px 26px 4px rgba(0,0,0,0.036)',
    '0px 8px 9px -5px rgba(0,0,0,0.06),0px 15px 22px 2px rgba(0,0,0,0.042),0px 6px 28px 5px rgba(0,0,0,0.036)',
    '0px 8px 10px -5px rgba(0,0,0,0.06),0px 16px 24px 2px rgba(0,0,0,0.042),0px 6px 30px 5px rgba(0,0,0,0.036)',
    '0px 8px 11px -5px rgba(0,0,0,0.06),0px 17px 26px 2px rgba(0,0,0,0.042),0px 6px 32px 5px rgba(0,0,0,0.036)',
    '0px 9px 11px -5px rgba(0,0,0,0.06),0px 18px 28px 2px rgba(0,0,0,0.042),0px 7px 34px 6px rgba(0,0,0,0.036)',
    '0px 9px 12px -6px rgba(0,0,0,0.06),0px 19px 29px 2px rgba(0,0,0,0.042),0px 7px 36px 6px rgba(0,0,0,0.036)',
    '0px 10px 13px -6px rgba(0,0,0,0.06),0px 20px 31px 3px rgba(0,0,0,0.042),0px 8px 38px 7px rgba(0,0,0,0.036)',
    '0px 10px 13px -6px rgba(0,0,0,0.06),0px 21px 33px 3px rgba(0,0,0,0.042),0px 8px 40px 7px rgba(0,0,0,0.036)',
    '0px 10px 14px -6px rgba(0,0,0,0.06),0px 22px 35px 3px rgba(0,0,0,0.042),0px 8px 42px 7px rgba(0,0,0,0.036)',
    '0px 11px 14px -7px rgba(0,0,0,0.06),0px 23px 36px 3px rgba(0,0,0,0.042),0px 9px 44px 8px rgba(0,0,0,0.036)',
    '0px 11px 15px -7px rgba(0,0,0,0.06),0px 24px 38px 3px rgba(0,0,0,0.042),0px 9px 46px 8px rgba(0,0,0,0.036)',
  ],
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: '8px 16px',
          fontSize: '0.875rem',
          fontWeight: 600,
          textTransform: 'none',
          boxShadow: 'none',
          '&:hover': {
            boxShadow: 'none',
          },
        },
        contained: {
          '&:hover': {
            transform: 'translateY(-1px)',
            transition: 'all 0.2s',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0px 2px 4px rgba(0,0,0,0.08)',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
        rounded: {
          borderRadius: 12,
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 6,
          fontWeight: 500,
        },
      },
    },
  },
};

// Light Theme
export const lightTheme = createTheme({
  ...baseThemeOptions,
  palette: {
    mode: 'light',
    ...colors,
    background: {
      default: '#f5f7fa',
      paper: '#ffffff',
    },
    text: {
      primary: '#1a1a1a',
      secondary: '#666666',
      disabled: '#9e9e9e',
    },
    divider: 'rgba(0, 0, 0, 0.08)',
  },
});

// Dark Theme
export const darkTheme = createTheme({
  ...baseThemeOptions,
  palette: {
    mode: 'dark',
    ...colors,
    primary: {
      light: '#64b5f6',
      main: '#42a5f5',
      dark: '#1976d2',
      contrastText: '#fff',
    },
    background: {
      default: '#0a1929',
      paper: '#132f4c',
    },
    text: {
      primary: '#ffffff',
      secondary: '#b0bec5',
      disabled: '#78909c',
    },
    divider: 'rgba(255, 255, 255, 0.12)',
  },
  shadows: [
    'none',
    '0px 2px 1px -1px rgba(0,0,0,0.2),0px 1px 1px 0px rgba(0,0,0,0.14),0px 1px 3px 0px rgba(0,0,0,0.12)',
    '0px 3px 1px -2px rgba(0,0,0,0.2),0px 2px 2px 0px rgba(0,0,0,0.14),0px 1px 5px 0px rgba(0,0,0,0.12)',
    '0px 3px 3px -2px rgba(0,0,0,0.2),0px 3px 4px 0px rgba(0,0,0,0.14),0px 1px 8px 0px rgba(0,0,0,0.12)',
    '0px 2px 4px -1px rgba(0,0,0,0.2),0px 4px 5px 0px rgba(0,0,0,0.14),0px 1px 10px 0px rgba(0,0,0,0.12)',
    '0px 3px 5px -1px rgba(0,0,0,0.2),0px 5px 8px 0px rgba(0,0,0,0.14),0px 1px 14px 0px rgba(0,0,0,0.12)',
    '0px 3px 5px -1px rgba(0,0,0,0.2),0px 6px 10px 0px rgba(0,0,0,0.14),0px 1px 18px 0px rgba(0,0,0,0.12)',
    '0px 4px 5px -2px rgba(0,0,0,0.2),0px 7px 10px 1px rgba(0,0,0,0.14),0px 2px 16px 1px rgba(0,0,0,0.12)',
    '0px 5px 5px -3px rgba(0,0,0,0.2),0px 8px 10px 1px rgba(0,0,0,0.14),0px 3px 14px 2px rgba(0,0,0,0.12)',
    '0px 5px 6px -3px rgba(0,0,0,0.2),0px 9px 12px 1px rgba(0,0,0,0.14),0px 3px 16px 2px rgba(0,0,0,0.12)',
    '0px 6px 6px -3px rgba(0,0,0,0.2),0px 10px 14px 1px rgba(0,0,0,0.14),0px 4px 18px 3px rgba(0,0,0,0.12)',
    '0px 6px 7px -4px rgba(0,0,0,0.2),0px 11px 15px 1px rgba(0,0,0,0.14),0px 4px 20px 3px rgba(0,0,0,0.12)',
    '0px 7px 8px -4px rgba(0,0,0,0.2),0px 12px 17px 2px rgba(0,0,0,0.14),0px 5px 22px 4px rgba(0,0,0,0.12)',
    '0px 7px 8px -4px rgba(0,0,0,0.2),0px 13px 19px 2px rgba(0,0,0,0.14),0px 5px 24px 4px rgba(0,0,0,0.12)',
    '0px 7px 9px -4px rgba(0,0,0,0.2),0px 14px 21px 2px rgba(0,0,0,0.14),0px 5px 26px 4px rgba(0,0,0,0.12)',
    '0px 8px 9px -5px rgba(0,0,0,0.2),0px 15px 22px 2px rgba(0,0,0,0.14),0px 6px 28px 5px rgba(0,0,0,0.12)',
    '0px 8px 10px -5px rgba(0,0,0,0.2),0px 16px 24px 2px rgba(0,0,0,0.14),0px 6px 30px 5px rgba(0,0,0,0.12)',
    '0px 8px 11px -5px rgba(0,0,0,0.2),0px 17px 26px 2px rgba(0,0,0,0.14),0px 6px 32px 5px rgba(0,0,0,0.12)',
    '0px 9px 11px -5px rgba(0,0,0,0.2),0px 18px 28px 2px rgba(0,0,0,0.14),0px 7px 34px 6px rgba(0,0,0,0.12)',
    '0px 9px 12px -6px rgba(0,0,0,0.2),0px 19px 29px 2px rgba(0,0,0,0.14),0px 7px 36px 6px rgba(0,0,0,0.12)',
    '0px 10px 13px -6px rgba(0,0,0,0.2),0px 20px 31px 3px rgba(0,0,0,0.14),0px 8px 38px 7px rgba(0,0,0,0.12)',
    '0px 10px 13px -6px rgba(0,0,0,0.2),0px 21px 33px 3px rgba(0,0,0,0.14),0px 8px 40px 7px rgba(0,0,0,0.12)',
    '0px 10px 14px -6px rgba(0,0,0,0.2),0px 22px 35px 3px rgba(0,0,0,0.14),0px 8px 42px 7px rgba(0,0,0,0.12)',
    '0px 11px 14px -7px rgba(0,0,0,0.2),0px 23px 36px 3px rgba(0,0,0,0.14),0px 9px 44px 8px rgba(0,0,0,0.12)',
    '0px 11px 15px -7px rgba(0,0,0,0.2),0px 24px 38px 3px rgba(0,0,0,0.14),0px 9px 46px 8px rgba(0,0,0,0.12)',
  ],
});
