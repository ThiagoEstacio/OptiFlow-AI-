/**
 * Breadcrumbs Component - Navegação Contextual
 * =============================================
 *
 * Componente de breadcrumbs para drill-down entre páginas.
 * Suporta navegação hierárquica e estado persistente.
 */
import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';

export interface BreadcrumbItem {
  label: string;
  path?: string;
  icon?: React.ReactNode;
}

interface BreadcrumbsProps {
  items?: BreadcrumbItem[];
  showHome?: boolean;
  className?: string;
}

// Mapeamento de rotas para labels amigáveis
const routeLabels: Record<string, string> = {
  dashboard: 'Dashboard',
  executive: 'Executivo',
  realtime: 'Tempo Real',
  alarms: 'Alarmes',
  analytics: 'Analytics',
  settings: 'Configurações',
  reports: 'Relatórios',
  monitoring: 'Monitoramento',
  history: 'Histórico',
  quality: 'Qualidade',
  maintenance: 'Manutenção',
  pcm: 'PCM',
  kpis: 'KPIs',
  backlog: 'Backlog',
  analysis: 'Análise',
  oee: 'OEE',
  energy: 'Energia',
  trends: 'Tendências',
  supervision: 'Supervisão',
  overview: 'Visão Geral',
};

// Gera breadcrumbs automaticamente a partir da URL
function generateBreadcrumbs(pathname: string): BreadcrumbItem[] {
  const segments = pathname.split('/').filter(Boolean);
  const breadcrumbs: BreadcrumbItem[] = [];

  let currentPath = '';
  segments.forEach((segment, index) => {
    currentPath += `/${segment}`;
    const label = routeLabels[segment] || segment.charAt(0).toUpperCase() + segment.slice(1);

    breadcrumbs.push({
      label,
      path: index < segments.length - 1 ? currentPath : undefined, // Último item não é clicável
    });
  });

  return breadcrumbs;
}

export const Breadcrumbs: React.FC<BreadcrumbsProps> = ({
  items,
  showHome = true,
  className = '',
}) => {
  const location = useLocation();
  const breadcrumbs = items || generateBreadcrumbs(location.pathname);

  if (breadcrumbs.length === 0 && !showHome) {
    return null;
  }

  return (
    <nav
      aria-label="Breadcrumb"
      className={`flex items-center space-x-1 text-sm ${className}`}
    >
      {showHome && (
        <>
          <Link
            to="/"
            className="flex items-center text-gray-500 hover:text-blue-600 transition-colors"
            title="Página Inicial"
          >
            <Home className="w-4 h-4" />
          </Link>
          {breadcrumbs.length > 0 && (
            <ChevronRight className="w-4 h-4 text-gray-400" />
          )}
        </>
      )}

      {breadcrumbs.map((item, index) => (
        <React.Fragment key={index}>
          {index > 0 && (
            <ChevronRight className="w-4 h-4 text-gray-400" />
          )}

          {item.path ? (
            <Link
              to={item.path}
              className="flex items-center gap-1 text-gray-500 hover:text-blue-600 transition-colors"
            >
              {item.icon}
              <span>{item.label}</span>
            </Link>
          ) : (
            <span className="flex items-center gap-1 text-gray-900 dark:text-white font-medium">
              {item.icon}
              <span>{item.label}</span>
            </span>
          )}
        </React.Fragment>
      ))}
    </nav>
  );
};

// Hook para gerenciar estado de navegação entre páginas
export function useNavigationState<T>() {
  const location = useLocation();

  const getState = (): T | null => {
    return location.state as T | null;
  };

  const createLinkWithState = (path: string, state: T) => {
    return { pathname: path, state };
  };

  return { getState, createLinkWithState };
}

export default Breadcrumbs;
