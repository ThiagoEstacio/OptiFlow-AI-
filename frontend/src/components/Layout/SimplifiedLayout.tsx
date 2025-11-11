/**
 * 🎯 Simplified Layout - Clean and Focused
 * ========================================
 * 
 * Layout using the new SimplifiedSidebar
 */
import React from 'react';
import { Outlet } from 'react-router-dom';
import { SimplifiedSidebar } from './SimplifiedSidebar';
import { TopBar } from './TopBar';
import { Breadcrumbs } from '../Breadcrumbs';
import { useAppSelector } from '../../store';
import { Box } from '@mui/material';

export const SimplifiedLayout: React.FC = () => {
  const sidebarOpen = useAppSelector((state) => state.ui.sidebarOpen);

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: 'grey.100' }}>
      {/* Simplified Sidebar */}
      <SimplifiedSidebar />

      {/* Main Content */}
      <Box
        sx={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          ml: sidebarOpen ? '256px' : '80px', // Adjusted for sidebar widths (w-64 / w-20)
          transition: 'margin-left 0.3s ease',
        }}
      >
        {/* Top Bar */}
        <TopBar />

        {/* Page Content */}
        <Box
          component="main"
          sx={{
            flex: 1,
            overflow: 'auto',
            bgcolor: 'grey.100',
          }}
        >
          {/* Breadcrumbs */}
          <Breadcrumbs />

          {/* Page Content with padding */}
          <Box sx={{ p: 3 }}>
            <Outlet />
          </Box>
        </Box>
      </Box>
    </Box>
  );
};
