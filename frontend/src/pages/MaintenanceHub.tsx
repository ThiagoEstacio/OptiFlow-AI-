import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Heart, TrendingUp, Wrench, History } from 'lucide-react';

const MaintenanceHub: React.FC = () => {
  const navigate = useNavigate();

  const maintenanceModules = [
    {
      id: 'asset-health',
      title: 'Asset Health',
      description: 'Real-time asset health monitoring and condition-based maintenance',
      icon: Heart,
      path: '/asset-health-hub',
      color: 'bg-red-500',
      status: 'active'
    },
    {
      id: 'predictive',
      title: 'Predictive Maintenance',
      description: 'ML-powered failure prediction and remaining useful life estimation',
      icon: TrendingUp,
      path: '/maintenance/predictive',
      color: 'bg-purple-500',
      status: 'active'
    },
    {
      id: 'work-orders',
      title: 'Work Orders',
      description: 'Maintenance work order management and scheduling',
      icon: Wrench,
      path: '/maintenance/work-orders',
      color: 'bg-blue-500',
      status: 'planned'
    },
    {
      id: 'history',
      title: 'Maintenance History',
      description: 'Historical maintenance records and intervention tracking',
      icon: History,
      path: '/maintenance/history',
      color: 'bg-green-500',
      status: 'planned'
    }
  ];

  return (
    <div className="container mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Maintenance</h1>
        <p className="text-gray-600">
          Predictive and preventive maintenance management
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {maintenanceModules.map((module) => {
          const Icon = module.icon;
          const isActive = module.status === 'active';

          return (
            <Card
              key={module.id}
              className={`cursor-pointer transition-all hover:shadow-lg ${
                isActive ? 'hover:border-red-500' : 'opacity-60'
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

      <div className="mt-8 bg-red-50 border border-red-200 rounded-lg p-4">
        <h3 className="font-semibold text-red-900 mb-2">About Maintenance Module</h3>
        <p className="text-sm text-red-800">
          The Maintenance module leverages AI and machine learning to predict equipment
          failures, optimize maintenance schedules, and extend asset life. Integrates with
          real-time sensor data and historical maintenance records.
        </p>
      </div>
    </div>
  );
};

export default MaintenanceHub;
