/**
 * Simplified Layout - No MUI Version (v3.0)
 * ==========================================
 *
 * Layout using pure Tailwind CSS (no MUI/Emotion)
 * Improvements:
 * - Better overflow handling
 * - Consistent color scheme (slate palette)
 * - Mobile-first responsive design
 * - Smooth transitions
 * - Proper margin handling for collapsed sidebar
 */
import React, { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { SimplifiedSidebar } from './SimplifiedSidebar';
import { TopBarSimple } from './TopBarSimple';
import { Breadcrumbs } from '../Breadcrumbs';
import { useAppSelector } from '../../store';

// Hook for responsive breakpoint detection
const useIsDesktop = () => {
  const [isDesktop, setIsDesktop] = useState(
    typeof window !== 'undefined' ? window.innerWidth >= 768 : true
  );

  useEffect(() => {
    const handleResize = () => {
      setIsDesktop(window.innerWidth >= 768);
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return isDesktop;
};

export const SimplifiedLayoutNoMui: React.FC = () => {
  const sidebarOpen = useAppSelector((state) => state.ui.sidebarOpen);
  const isDesktop = useIsDesktop();

  // Calculate margin based on screen size and sidebar state
  const getMainMargin = () => {
    if (!isDesktop) return '0';
    return sidebarOpen ? '256px' : '80px';
  };

  return (
    <div className="flex min-h-screen bg-slate-50">
      {/* Simplified Sidebar */}
      <SimplifiedSidebar />

      {/* Main Content - Mobile: no margin, Desktop: dynamic margin */}
      <div
        className="flex-1 flex flex-col min-w-0 transition-all duration-300 ease-out"
        style={{ marginLeft: getMainMargin() }}
      >
        {/* Top Bar */}
        <TopBarSimple />

        {/* Page Content */}
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-slate-50">
          {/* Breadcrumbs */}
          <Breadcrumbs />

          {/* Page Content with proper padding and max-width */}
          {/* Mobile: extra top padding for hamburger menu */}
          <div className={`p-4 pb-24 ${isDesktop ? 'md:p-6' : 'pt-16'}`}>
            <div className="max-w-[1920px] mx-auto">
              <Outlet />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};
