/**
 * Header - Top navigation bar
 */
import { Bell, Search, Settings, User, Menu } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';

export interface HeaderProps {
  onMenuClick?: () => void;
  showMenuButton?: boolean;
}

export function Header({ onMenuClick, showMenuButton = true }: HeaderProps) {
  return (
    <header className="sticky top-0 z-40 border-b border-dark-700 bg-dark-800/95 backdrop-blur-sm">
      <div className="flex h-16 items-center justify-between px-6">
        {/* Left Section */}
        <div className="flex items-center gap-4">
          {showMenuButton && (
            <Button
              variant="ghost"
              size="sm"
              icon={<Menu className="h-5 w-5" />}
              onClick={onMenuClick}
              className="lg:hidden"
            />
          )}

          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-500/10">
              <span className="text-xl font-bold text-primary-500">S</span>
            </div>
            <div>
              <h1 className="text-lg font-bold text-dark-100">SmartPort</h1>
              <p className="text-xs text-dark-400">OptiFlow AI Platform</p>
            </div>
          </div>
        </div>

        {/* Center Section - Search */}
        <div className="hidden flex-1 max-w-md px-8 md:block">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-dark-400" />
            <input
              type="text"
              placeholder="Search vessels, operations, equipment..."
              className="w-full rounded-lg border border-dark-600 bg-dark-700 py-2 pl-10 pr-4 text-sm text-dark-100 placeholder:text-dark-500 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
            />
          </div>
        </div>

        {/* Right Section */}
        <div className="flex items-center gap-2">
          {/* Notifications */}
          <div className="relative">
            <Button
              variant="ghost"
              size="sm"
              icon={<Bell className="h-5 w-5" />}
            />
            <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-danger-500 ring-2 ring-dark-800" />
          </div>

          {/* Settings */}
          <Button
            variant="ghost"
            size="sm"
            icon={<Settings className="h-5 w-5" />}
          />

          {/* User Profile */}
          <Button
            variant="ghost"
            size="sm"
            icon={<User className="h-5 w-5" />}
          />
        </div>
      </div>
    </header>
  );
}
