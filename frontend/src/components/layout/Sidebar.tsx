/**
 * Sidebar - Main navigation sidebar
 */
import { NavLink } from 'react-router-dom';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  Ship,
  Anchor,
  PackageOpen,
  Settings as SettingsIcon,
  BarChart3,
  Cpu,
  AlertTriangle,
  FileText,
  X,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';

export interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

interface NavItem {
  name: string;
  href: string;
  icon: React.ElementType;
  badge?: number;
}

const navigation: NavItem[] = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Vessels', href: '/vessels', icon: Ship },
  { name: 'Berths', href: '/berths', icon: Anchor },
  { name: 'Operations', href: '/operations', icon: PackageOpen },
  { name: 'Equipment', href: '/equipment', icon: Cpu },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  { name: 'Alerts', href: '/alerts', icon: AlertTriangle, badge: 3 },
  { name: 'Reports', href: '/reports', icon: FileText },
  { name: 'Settings', href: '/settings', icon: SettingsIcon },
];

export function Sidebar({ isOpen = true, onClose }: SidebarProps) {
  return (
    <>
      {/* Mobile Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed left-0 top-0 z-50 h-full w-64 border-r border-dark-700 bg-dark-800 transition-transform duration-300 lg:sticky lg:translate-x-0',
          isOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {/* Logo Section */}
        <div className="flex h-16 items-center justify-between border-b border-dark-700 px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-500/10">
              <span className="text-xl font-bold text-primary-500">S</span>
            </div>
            <div>
              <h1 className="text-base font-bold text-dark-100">SmartPort</h1>
              <p className="text-xs text-dark-400">OptiFlow AI</p>
            </div>
          </div>

          {/* Close button (mobile) */}
          <Button
            variant="ghost"
            size="sm"
            icon={<X className="h-5 w-5" />}
            onClick={onClose}
            className="lg:hidden"
          />
        </div>

        {/* Navigation */}
        <nav className="flex flex-col gap-1 p-4">
          {navigation.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary-500/10 text-primary-500'
                    : 'text-dark-300 hover:bg-dark-700 hover:text-dark-100'
                )
              }
              onClick={() => {
                // Close sidebar on mobile after navigation
                if (window.innerWidth < 1024) {
                  onClose?.();
                }
              }}
            >
              <item.icon className="h-5 w-5" />
              <span className="flex-1">{item.name}</span>
              {item.badge && (
                <span className="flex h-5 min-w-[20px] items-center justify-center rounded-full bg-danger-500 px-1.5 text-xs font-semibold text-white">
                  {item.badge}
                </span>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Footer Info */}
        <div className="absolute bottom-0 left-0 right-0 border-t border-dark-700 p-4">
          <div className="rounded-lg bg-dark-700/50 p-3">
            <p className="text-xs font-medium text-dark-300">
              Terminal Santos Grãos
            </p>
            <p className="mt-1 text-xs text-dark-400">Santos, SP - Brasil</p>
          </div>
        </div>
      </aside>
    </>
  );
}
