/**
 * 🎯 Simplified Layout - No MUI Version (v2.0)
 * =============================================
 *
 * Layout using pure Tailwind CSS (no MUI/Emotion)
 * Improvements:
 * - Better overflow handling
 * - Consistent color scheme (slate palette)
 * - Improved responsiveness
 * - Smooth transitions
 */
import React from 'react';
import { Outlet } from 'react-router-dom';
import { SimplifiedSidebar } from './SimplifiedSidebar';
import { TopBarSimple } from './TopBarSimple';
import { Breadcrumbs } from '../Breadcrumbs';
import { useAppSelector } from '../../store';

export const SimplifiedLayoutNoMui: React.FC = () => {
  const sidebarOpen = useAppSelector((state) => state.ui.sidebarOpen);

  return (
    <div className="flex min-h-screen bg-slate-50">
      {/* Simplified Sidebar */}
      <SimplifiedSidebar />

      {/* Main Content */}
      <div
        className="flex-1 flex flex-col min-w-0 transition-all duration-300 ease-out"
        style={{ marginLeft: sidebarOpen ? '256px' : '80px' }}
      >
        {/* Top Bar */}
        <TopBarSimple />

        {/* Page Content */}
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-slate-50">
          {/* Breadcrumbs */}
          <Breadcrumbs />

          {/* Page Content with proper padding and max-width */}
          <div className="p-4 md:p-6 pb-24">
            <div className="max-w-[1920px] mx-auto">
              <Outlet />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};
