/**
 * Breadcrumbs Component
 * Displays hierarchical navigation breadcrumbs
 */

import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';

export const Breadcrumbs: React.FC = () => {
  const location = useLocation();
  const pathnames = location.pathname.split('/').filter((x) => x);

  // Map route segments to friendly labels
  const routeLabels: Record<string, string> = {
    operations: 'Operações',
    scada: 'SCADA Monitor',
    overview: 'Visão Geral',
    maintenance: 'Manutenção',
    predictive: 'Asset Health',
    engineering: 'Engenharia',
    analytics: 'Analytics',
    executive: 'Executivo',
    config: 'Configuração',
    simulator: 'Simulador',
    tags: 'Tags',
    alarms: 'Alarmes',
    users: 'Usuários',
    'data-sources': 'Fontes de Dados',
    admin: 'Administração',
    gbm: 'GBM Insights',
    historical: 'Tendências Históricas',
    chat: 'Chat IA',
    dashboard: 'Dashboard',
    'asset-health-hub': 'Asset Health',
    gateways: 'Gateways',
  };

  // Don't show breadcrumbs on home page
  if (pathnames.length === 0) return null;

  return (
    <nav className="flex items-center gap-2 text-sm text-gray-600 mb-4 px-6 py-3 bg-gray-50 border-b">
      <Link
        to="/"
        className="flex items-center gap-1 hover:text-purple-600 transition-colors"
        title="Ir para Home"
      >
        <Home size={16} />
        <span>Home</span>
      </Link>

      {pathnames.map((value, index) => {
        const to = `/${pathnames.slice(0, index + 1).join('/')}`;
        const isLast = index === pathnames.length - 1;
        const label = routeLabels[value] || value.charAt(0).toUpperCase() + value.slice(1);

        return (
          <React.Fragment key={to}>
            <ChevronRight size={16} className="text-gray-400" />
            {isLast ? (
              <span className="font-semibold text-gray-900">{label}</span>
            ) : (
              <Link
                to={to}
                className="hover:text-purple-600 transition-colors"
                title={`Ir para ${label}`}
              >
                {label}
              </Link>
            )}
          </React.Fragment>
        );
      })}
    </nav>
  );
};

export default Breadcrumbs;
