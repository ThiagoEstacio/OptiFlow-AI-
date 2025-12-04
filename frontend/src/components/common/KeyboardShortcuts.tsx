/**
 * Keyboard Shortcuts Component
 * ============================
 *
 * Global keyboard shortcuts handler with visual help modal.
 * Improves UX for power users and accessibility.
 */
import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { X, Command, Search, Home, Activity, Bell, Settings, BarChart2, Zap, FileText, HelpCircle } from 'lucide-react';

export interface ShortcutDefinition {
  key: string;
  ctrl?: boolean;
  alt?: boolean;
  shift?: boolean;
  description: string;
  category: string;
  action: () => void;
}

interface KeyboardShortcutsProps {
  customShortcuts?: ShortcutDefinition[];
  enabled?: boolean;
}

// Default shortcuts configuration
const createDefaultShortcuts = (navigate: ReturnType<typeof useNavigate>): ShortcutDefinition[] => [
  // Navigation
  {
    key: 'h',
    alt: true,
    description: 'Ir para Dashboard Principal',
    category: 'Navegação',
    action: () => navigate('/'),
  },
  {
    key: 'r',
    alt: true,
    description: 'Ir para Tempo Real',
    category: 'Navegação',
    action: () => navigate('/realtime'),
  },
  {
    key: 'a',
    alt: true,
    description: 'Ir para Alarmes',
    category: 'Navegação',
    action: () => navigate('/alarms'),
  },
  {
    key: 'e',
    alt: true,
    description: 'Ir para Executivo',
    category: 'Navegação',
    action: () => navigate('/executive'),
  },
  {
    key: 'm',
    alt: true,
    description: 'Ir para Manutenção',
    category: 'Navegação',
    action: () => navigate('/maintenance'),
  },
  {
    key: 'q',
    alt: true,
    description: 'Ir para Qualidade',
    category: 'Navegação',
    action: () => navigate('/quality'),
  },
  {
    key: 'n',
    alt: true,
    description: 'Ir para Energia',
    category: 'Navegação',
    action: () => navigate('/executive/energy'),
  },
  {
    key: 's',
    alt: true,
    description: 'Ir para Configurações',
    category: 'Navegação',
    action: () => navigate('/settings'),
  },
  // Actions
  {
    key: 'k',
    ctrl: true,
    description: 'Abrir busca rápida',
    category: 'Ações',
    action: () => {
      // Trigger search modal (emit custom event)
      window.dispatchEvent(new CustomEvent('optiflow:openSearch'));
    },
  },
  {
    key: '/',
    description: 'Focar na busca',
    category: 'Ações',
    action: () => {
      const searchInput = document.querySelector('[data-search-input]') as HTMLInputElement;
      searchInput?.focus();
    },
  },
  {
    key: 'Escape',
    description: 'Fechar modal/popup',
    category: 'Ações',
    action: () => {
      window.dispatchEvent(new CustomEvent('optiflow:closeModals'));
    },
  },
  {
    key: '?',
    shift: true,
    description: 'Mostrar atalhos de teclado',
    category: 'Ajuda',
    action: () => {
      window.dispatchEvent(new CustomEvent('optiflow:showShortcuts'));
    },
  },
];

// Hook for keyboard shortcuts
export function useKeyboardShortcuts(shortcuts: ShortcutDefinition[], enabled: boolean = true) {
  useEffect(() => {
    if (!enabled) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      // Don't trigger shortcuts when typing in inputs
      const target = event.target as HTMLElement;
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable
      ) {
        // Allow Escape in inputs
        if (event.key !== 'Escape') return;
      }

      for (const shortcut of shortcuts) {
        const keyMatch = event.key.toLowerCase() === shortcut.key.toLowerCase() ||
                        event.key === shortcut.key;
        const ctrlMatch = shortcut.ctrl ? (event.ctrlKey || event.metaKey) : !event.ctrlKey && !event.metaKey;
        const altMatch = shortcut.alt ? event.altKey : !event.altKey;
        const shiftMatch = shortcut.shift ? event.shiftKey : !event.shiftKey;

        if (keyMatch && ctrlMatch && altMatch && shiftMatch) {
          event.preventDefault();
          shortcut.action();
          return;
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [shortcuts, enabled]);
}

// Visual component for shortcuts help
export const KeyboardShortcuts: React.FC<KeyboardShortcutsProps> = ({
  customShortcuts = [],
  enabled = true,
}) => {
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);

  const defaultShortcuts = createDefaultShortcuts(navigate);
  const allShortcuts = [...defaultShortcuts, ...customShortcuts];

  // Group shortcuts by category
  const groupedShortcuts = allShortcuts.reduce((acc, shortcut) => {
    if (!acc[shortcut.category]) {
      acc[shortcut.category] = [];
    }
    acc[shortcut.category].push(shortcut);
    return acc;
  }, {} as Record<string, ShortcutDefinition[]>);

  // Listen for show shortcuts event
  useEffect(() => {
    const handleShowShortcuts = () => setIsOpen(true);
    const handleCloseModals = () => setIsOpen(false);

    window.addEventListener('optiflow:showShortcuts', handleShowShortcuts);
    window.addEventListener('optiflow:closeModals', handleCloseModals);

    return () => {
      window.removeEventListener('optiflow:showShortcuts', handleShowShortcuts);
      window.removeEventListener('optiflow:closeModals', handleCloseModals);
    };
  }, []);

  // Register shortcuts
  useKeyboardShortcuts(allShortcuts, enabled);

  // Format key display
  const formatKey = (shortcut: ShortcutDefinition) => {
    const keys: string[] = [];
    if (shortcut.ctrl) keys.push(navigator.platform.includes('Mac') ? '⌘' : 'Ctrl');
    if (shortcut.alt) keys.push(navigator.platform.includes('Mac') ? '⌥' : 'Alt');
    if (shortcut.shift) keys.push('⇧');
    keys.push(shortcut.key.toUpperCase());
    return keys;
  };

  // Category icons
  const categoryIcons: Record<string, React.ReactNode> = {
    'Navegação': <Home className="w-4 h-4" />,
    'Ações': <Command className="w-4 h-4" />,
    'Ajuda': <HelpCircle className="w-4 h-4" />,
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-slate-50">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Command className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-slate-800">Atalhos de Teclado</h2>
              <p className="text-sm text-slate-500">Navegue rapidamente pelo OptiFlow</p>
            </div>
          </div>
          <button
            onClick={() => setIsOpen(false)}
            className="p-2 rounded-lg hover:bg-slate-200 text-slate-400 hover:text-slate-600 transition-colors"
            aria-label="Fechar"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          <div className="grid gap-6">
            {Object.entries(groupedShortcuts).map(([category, shortcuts]) => (
              <div key={category}>
                <div className="flex items-center gap-2 mb-3">
                  {categoryIcons[category] || <Command className="w-4 h-4" />}
                  <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wide">
                    {category}
                  </h3>
                </div>
                <div className="space-y-2">
                  {shortcuts.map((shortcut, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-slate-50"
                    >
                      <span className="text-sm text-slate-600">{shortcut.description}</span>
                      <div className="flex items-center gap-1">
                        {formatKey(shortcut).map((key, keyIdx) => (
                          <React.Fragment key={keyIdx}>
                            <kbd className="px-2 py-1 text-xs font-medium text-slate-700 bg-slate-100 border border-slate-300 rounded shadow-sm">
                              {key}
                            </kbd>
                            {keyIdx < formatKey(shortcut).length - 1 && (
                              <span className="text-slate-400">+</span>
                            )}
                          </React.Fragment>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-200 bg-slate-50">
          <p className="text-xs text-slate-500 text-center">
            Pressione <kbd className="px-1.5 py-0.5 text-xs bg-slate-200 rounded">Shift</kbd> + <kbd className="px-1.5 py-0.5 text-xs bg-slate-200 rounded">?</kbd> a qualquer momento para ver esta ajuda
          </p>
        </div>
      </div>
    </div>
  );
};

export default KeyboardShortcuts;
