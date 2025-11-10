import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { BarChart3, Zap, FileText, Settings } from 'lucide-react';

const EngineeringHub: React.FC = () => {
  const navigate = useNavigate();

  const engineeringModules = [
    {
      id: 'analytics',
      title: 'Analytics Hub',
      description: 'Advanced analytics, AI insights, and performance analysis',
      icon: BarChart3,
      path: '/analytics-hub',
      color: 'bg-indigo-500',
      status: 'active'
    },
    {
      id: 'optimization',
      title: 'Process Optimization',
      description: 'Process optimization tools and energy efficiency analysis',
      icon: Zap,
      path: '/engineering/optimization',
      color: 'bg-yellow-500',
      status: 'planned'
    },
    {
      id: 'reports',
      title: 'Technical Reports',
      description: 'Generate technical reports and performance documentation',
      icon: FileText,
      path: '/engineering/reports',
      color: 'bg-green-500',
      status: 'planned'
    },
    {
      id: 'kpi-config',
      title: 'KPI Configuration',
      description: 'Configure and manage key performance indicators',
      icon: Settings,
      path: '/engineering/kpi-config',
      color: 'bg-purple-500',
      status: 'planned'
    }
  ];

  return (
    <div className="container mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Engineering</h1>
        <p className="text-gray-600">
          Analytics, optimization, and technical configuration
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {engineeringModules.map((module) => {
          const Icon = module.icon;
          const isActive = module.status === 'active';

          return (
            <Card
              key={module.id}
              className={`cursor-pointer transition-all hover:shadow-lg ${
                isActive ? 'hover:border-indigo-500' : 'opacity-60'
              }`}
              onClick={() => isActive && navigate(module.path)}
            >
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className={`${module.color} p-3 rounded-lg`}>
                    <Icon className="h-6 w-6 text-white" />
                  </div>
                  <div className="flex-1">
                    <CardTitle className="text-lg">{module.title}</CardTitle>
                    {!isActive && (
                      <span className="text-xs text-gray-500 font-normal">
                        Coming Soon
                      </span>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600">{module.description}</p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="mt-8 bg-indigo-50 border border-indigo-200 rounded-lg p-4">
        <h3 className="font-semibold text-indigo-900 mb-2">About Engineering Module</h3>
        <p className="text-sm text-indigo-800">
          The Engineering module provides advanced tools for process engineers to analyze
          performance, optimize operations, and configure system parameters. Includes AI-powered
          insights and comprehensive reporting capabilities.
        </p>
      </div>
    </div>
  );
};

export default EngineeringHub;
