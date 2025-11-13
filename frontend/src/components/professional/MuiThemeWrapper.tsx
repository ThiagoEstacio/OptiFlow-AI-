/**
 * MUI Theme Wrapper - Integrates ThemeContext with MUI ThemeProvider
 */
import React, { ReactNode } from 'react';
import { ThemeProvider as MuiThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { useTheme } from '../../contexts/ThemeContext';
import { lightTheme, darkTheme } from '../../theme/professionalTheme';

interface MuiThemeWrapperProps {
  children: ReactNode;
}

export const MuiThemeWrapper: React.FC<MuiThemeWrapperProps> = ({ children }) => {
  const { effectiveTheme } = useTheme();
  const theme = effectiveTheme === 'dark' ? darkTheme : lightTheme;

  return (
    <MuiThemeProvider theme={theme}>
      <CssBaseline />
      {children}
    </MuiThemeProvider>
  );
};
