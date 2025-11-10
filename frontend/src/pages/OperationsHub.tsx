import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Activity, Gauge, Play, FileText } from 'lucide-react';

const OperationsHub: React.FC = () => {
  const navigate = useNavigate();

  const operationsModules = [
    {
      id: 'scada',
      title: 'SCADA Monitor',
      description: 'Real-time process monitoring with live equipment status and KPIs',
      icon: Activity,
      path: '/operations/scada',
      color: 'bg-blue-500',
      status: 'active'
    },
    {
      id: 'overview',
      title: 'Process Overview',
      description: 'General process dashboard with key performance indicators',
      icon: Gauge,
      path: '/operations/overview',
      color: 'bg-green-500',
      status: 'active'
    },
    {
      id: 'control',
      title: 'Manual Control',
      description: 'Manual control interface for equipment and process variables',
      icon: Play,
      path: '/operations/control',
      color: 'bg-purple-500',
      status: 'planned'
    },
    {
      id: 'shift-log',
      title: 'Shift Log',
      description: 'Operator shift logs and event recording',
      icon: FileText,
      path: '/operations/shift-log',
      color: 'bg-orange-500',
      status: 'planned'
    }
  ];

  return (
    <div className="container mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Operations</h1>
        <p className="text-gray-600">
          Real-time monitoring and control of industrial processes
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {operationsModules.map((module) => {
          const Icon = module.icon;
          const isActive = module.status === 'active';

          return (
            <Card
              key={module.id}
              className={`cursor-pointer transition-all hover:shadow-lg ${
                isActive ? 'hover:border-blue-500' : 'opacity-60'
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

      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-2">About Operations Module</h3>
        <p className="text-sm text-blue-800">
          The Operations module provides real-time visibility into plant operations,
          enabling operators to monitor process variables, control equipment, and respond
          to operational events. All data is streamed in real-time via Kafka and InfluxDB.
        </p>
      </div>
    </div>
  );
};

export default OperationsHub;
