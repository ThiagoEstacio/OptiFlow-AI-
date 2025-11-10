import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Database, Tag, Bell, Users, Cpu, Shield } from 'lucide-react';

const ConfigurationHub: React.FC = () => {
  const navigate = useNavigate();

  const configModules = [
    {
      id: 'simulator',
      title: 'Simulator Control',
      description: 'Control and configure the grain terminal simulator (virtual PLC)',
      icon: Cpu,
      path: '/config/simulator',
      color: 'bg-cyan-500',
      status: 'active'
    },
    {
      id: 'data-sources',
      title: 'Data Sources',
      description: 'Manage gateways, OPC-UA connections, and protocol adapters',
      icon: Database,
      path: '/config/data-sources',
      color: 'bg-blue-500',
      status: 'active'
    },
    {
      id: 'tags',
      title: 'Tag Management',
      description: 'Configure process tags, scaling, and data mapping',
      icon: Tag,
      path: '/config/tags',
      color: 'bg-green-500',
      status: 'active'
    },
    {
      id: 'alarms',
      title: 'Alarm Configuration',
      description: 'Set up alarm limits, notifications, and escalation rules',
      icon: Bell,
      path: '/config/alarms',
      color: 'bg-yellow-500',
      status: 'active'
    },
    {
      id: 'users',
      title: 'User Management',
      description: 'Manage users, roles, and access permissions',
      icon: Users,
      path: '/config/users',
      color: 'bg-purple-500',
      status: 'active'
    },
    {
      id: 'admin',
      title: 'System Admin',
      description: 'Advanced system configuration and maintenance',
      icon: Shield,
      path: '/admin',
      color: 'bg-red-500',
      status: 'active'
    }
  ];

  return (
    <div className="container mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Configuration</h1>
        <p className="text-gray-600">
          System configuration, data sources, and user management
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {configModules.map((module) => {
          const Icon = module.icon;
          const isActive = module.status === 'active';

          return (
            <Card
              key={module.id}
              className={`cursor-pointer transition-all hover:shadow-lg ${
                isActive ? 'hover:border-gray-500' : 'opacity-60'
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

      <div className="mt-8 bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h3 className="font-semibold text-gray-900 mb-2">About Configuration Module</h3>
        <p className="text-sm text-gray-800">
          The Configuration module provides centralized management of system settings,
          data sources, user permissions, and integration parameters. Essential for
          system administrators and engineers.
        </p>
      </div>
    </div>
  );
};

export default ConfigurationHub;
