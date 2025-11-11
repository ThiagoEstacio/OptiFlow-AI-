/**
 * OptiFlow AI - Real-Time Data Visualization Dashboard
 * 
 * Visualiza dados em tempo real de todos os dispositivos IoT
 * com gráficos interativos e métricas ao vivo
 */
import React, { useState, useEffect } from 'react';
import { 
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar
} from 'recharts';
import { Activity, Database, Cpu, HardDrive, Zap, TrendingUp, AlertCircle, CheckCircle } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  change?: string;
  changeType?: 'positive' | 'negative' | 'neutral';
  icon: React.ReactNode;
  color: string;
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, change, changeType, icon, color }) => {
  const changeColor = {
    positive: 'text-green-600',
    negative: 'text-red-600',
    neutral: 'text-gray-600'
  }[changeType || 'neutral'];

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-600 mb-1">{title}</p>
          <p className="text-3xl font-bold text-gray-900">{value}</p>
          {change && (
            <p className={`text-sm mt-2 ${changeColor}`}>
              {change}
            </p>
          )}
        </div>
        <div className={`p-4 rounded-full ${color}`}>
          {icon}
        </div>
      </div>
    </div>
  );
};

export const RealTimeVisualizationDashboard: React.FC = () => {
  const [timeSeriesData, setTimeSeriesData] = useState<any[]>([]);
  const [systemMetrics, setSystemMetrics] = useState({
    dataPoints: 0,
    devicesOnline: 0,
    avgLatency: 0,
    throughput: 0
  });

  // Simular dados em tempo real
  useEffect(() => {
    const generateData = () => {
      const now = new Date();
      const newData = Array.from({ length: 20 }, (_, i) => {
        const time = new Date(now.getTime() - (19 - i) * 5000);
        return {
          time: time.toLocaleTimeString(),
          temperature: 20 + Math.random() * 10,
          pressure: 100 + Math.random() * 20,
          flow: 50 + Math.random() * 30,
          power: 70 + Math.random() * 25
        };
      });
      setTimeSeriesData(newData);
      
      // Atualizar métricas
      setSystemMetrics({
        dataPoints: Math.floor(24500 + Math.random() * 1000),
        devicesOnline: Math.floor(45 + Math.random() * 5),
        avgLatency: Math.floor(25 + Math.random() * 10),
        throughput: Math.floor(1200 + Math.random() * 300)
      });
    };

    generateData();
    const interval = setInterval(generateData, 5000);
    return () => clearInterval(interval);
  }, []);

  // Dados para gráfico de pizza (distribuição de dispositivos)
  const deviceDistribution = [
    { name: 'Sensores', value: 25, color: '#3b82f6' },
    { name: 'PLCs', value: 12, color: '#10b981' },
    { name: 'RTUs', value: 8, color: '#f59e0b' },
    { name: 'Gateways', value: 5, color: '#8b5cf6' }
  ];

  // Dados para gráfico radar (saúde dos sistemas)
  const systemHealth = [
    { subject: 'CPU', value: 85, fullMark: 100 },
    { subject: 'Memória', value: 72, fullMark: 100 },
    { subject: 'Rede', value: 95, fullMark: 100 },
    { subject: 'Disco', value: 68, fullMark: 100 },
    { subject: 'Latência', value: 90, fullMark: 100 }
  ];

  // Dados de performance por hora
  const hourlyPerformance = [
    { hour: '00:00', requests: 450, errors: 5 },
    { hour: '04:00', requests: 320, errors: 2 },
    { hour: '08:00', requests: 890, errors: 12 },
    { hour: '12:00', requests: 1240, errors: 8 },
    { hour: '16:00', requests: 1350, errors: 15 },
    { hour: '20:00', requests: 980, errors: 6 }
  ];

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">
          🎯 Visualização de Dados em Tempo Real
        </h1>
        <p className="text-gray-600">
          Monitoramento ao vivo de todos os sensores e dispositivos IoT
        </p>
      </div>

      {/* Métricas Principais */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <MetricCard
          title="Pontos de Dados (Hoje)"
          value={systemMetrics.dataPoints.toLocaleString()}
          change="+12.5% vs ontem"
          changeType="positive"
          icon={<Database className="w-8 h-8 text-white" />}
          color="bg-blue-500"
        />
        <MetricCard
          title="Dispositivos Online"
          value={`${systemMetrics.devicesOnline}/50`}
          change="98% uptime"
          changeType="positive"
          icon={<Activity className="w-8 h-8 text-white" />}
          color="bg-green-500"
        />
        <MetricCard
          title="Latência Média"
          value={`${systemMetrics.avgLatency}ms`}
          change="-8% vs média"
          changeType="positive"
          icon={<Zap className="w-8 h-8 text-white" />}
          color="bg-yellow-500"
        />
        <MetricCard
          title="Throughput"
          value={`${systemMetrics.throughput}/s`}
          change="+15% vs hora anterior"
          changeType="positive"
          icon={<TrendingUp className="w-8 h-8 text-white" />}
          color="bg-purple-500"
        />
      </div>

      {/* Gráficos Principais - Linha Superior */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Gráfico de Linha - Time Series */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">
            📈 Tendências em Tempo Real
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={timeSeriesData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis 
                dataKey="time" 
                tick={{ fontSize: 12 }}
                stroke="#6b7280"
              />
              <YAxis tick={{ fontSize: 12 }} stroke="#6b7280" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1f2937', 
                  border: 'none', 
                  borderRadius: '8px',
                  color: '#fff'
                }}
              />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="temperature" 
                stroke="#3b82f6" 
                strokeWidth={2}
                dot={false}
                name="Temperatura (°C)"
              />
              <Line 
                type="monotone" 
                dataKey="pressure" 
                stroke="#10b981" 
                strokeWidth={2}
                dot={false}
                name="Pressão (bar)"
              />
              <Line 
                type="monotone" 
                dataKey="flow" 
                stroke="#f59e0b" 
                strokeWidth={2}
                dot={false}
                name="Vazão (m³/h)"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Gráfico de Área - Power Consumption */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">
            ⚡ Consumo de Energia
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={timeSeriesData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis 
                dataKey="time" 
                tick={{ fontSize: 12 }}
                stroke="#6b7280"
              />
              <YAxis tick={{ fontSize: 12 }} stroke="#6b7280" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1f2937', 
                  border: 'none', 
                  borderRadius: '8px',
                  color: '#fff'
                }}
              />
              <Legend />
              <Area 
                type="monotone" 
                dataKey="power" 
                stroke="#8b5cf6" 
                fill="#8b5cf6"
                fillOpacity={0.6}
                name="Potência (kW)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Gráficos Secundários - Linha Inferior */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Gráfico de Pizza - Distribuição */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">
            🔌 Distribuição de Dispositivos
          </h2>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={deviceDistribution}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {deviceDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Gráfico Radar - Saúde do Sistema */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">
            🎯 Saúde do Sistema
          </h2>
          <ResponsiveContainer width="100%" height={250}>
            <RadarChart cx="50%" cy="50%" outerRadius="80%" data={systemHealth}>
              <PolarGrid stroke="#e5e7eb" />
              <PolarAngleAxis dataKey="subject" tick={{ fontSize: 12 }} />
              <PolarRadiusAxis angle={90} domain={[0, 100]} />
              <Radar 
                name="Performance" 
                dataKey="value" 
                stroke="#3b82f6" 
                fill="#3b82f6" 
                fillOpacity={0.6} 
              />
              <Tooltip />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* Gráfico de Barras - Performance */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">
            📊 Performance por Hora
          </h2>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={hourlyPerformance}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="hour" tick={{ fontSize: 12 }} stroke="#6b7280" />
              <YAxis tick={{ fontSize: 12 }} stroke="#6b7280" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1f2937', 
                  border: 'none', 
                  borderRadius: '8px',
                  color: '#fff'
                }}
              />
              <Legend />
              <Bar dataKey="requests" fill="#10b981" name="Requisições" />
              <Bar dataKey="errors" fill="#ef4444" name="Erros" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Status dos Serviços */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-6">
          🖥️ Status dos Serviços
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { name: 'PostgreSQL', status: 'online', latency: '12ms', cpu: '45%' },
            { name: 'InfluxDB', status: 'online', latency: '18ms', cpu: '62%' },
            { name: 'Redis', status: 'online', latency: '3ms', cpu: '28%' },
            { name: 'Backend API', status: 'online', latency: '25ms', cpu: '38%' },
            { name: 'Gateway', status: 'online', latency: '15ms', cpu: '52%' },
            { name: 'Ollama (AI)', status: 'online', latency: '120ms', cpu: '78%' },
            { name: 'Prometheus', status: 'online', latency: '8ms', cpu: '22%' },
            { name: 'Grafana', status: 'online', latency: '35ms', cpu: '18%' }
          ].map((service, index) => (
            <div key={index} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-gray-900">{service.name}</h3>
                {service.status === 'online' ? (
                  <CheckCircle className="w-5 h-5 text-green-500" />
                ) : (
                  <AlertCircle className="w-5 h-5 text-red-500" />
                )}
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Latência:</span>
                  <span className="font-medium text-gray-900">{service.latency}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">CPU:</span>
                  <span className="font-medium text-gray-900">{service.cpu}</span>
                </div>
                <div className="mt-2">
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-green-500 h-2 rounded-full" 
                      style={{ width: service.cpu }}
                    />
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Footer com informações adicionais */}
      <div className="mt-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg shadow-lg p-6 text-white">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 text-center">
          <div>
            <p className="text-3xl font-bold">99.8%</p>
            <p className="text-blue-100 mt-1">Uptime</p>
          </div>
          <div>
            <p className="text-3xl font-bold">1.2M</p>
            <p className="text-blue-100 mt-1">Dados Processados (Hoje)</p>
          </div>
          <div>
            <p className="text-3xl font-bold">45ms</p>
            <p className="text-blue-100 mt-1">Tempo de Resposta P95</p>
          </div>
          <div>
            <p className="text-3xl font-bold">0</p>
            <p className="text-blue-100 mt-1">Alertas Críticos</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RealTimeVisualizationDashboard;
