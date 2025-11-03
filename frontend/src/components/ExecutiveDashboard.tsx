/**
 * Executive Dashboard - Sales Demo
 * ================================
 * 
 * Dashboard executivo para apresentação comercial do Smartport
 * Mostra KPIs operacionais, eventos, navios e condições em tempo real
 */

import React, { useEffect, useState } from 'react';
import { 
  Ship, 
  TrendingUp, 
  Clock, 
  DollarSign, 
  AlertCircle, 
  Cloud, 
  CloudRain, 
  CloudLightning,
  Package,
  Activity
} from 'lucide-react';

interface Ship {
  name: string;
  dwt: number;
  product: string;
  target_t: number;
  loaded_t: number;
  progress: number;
  status: string;
  priority: number;
}

interface OperationalEvent {
  type: string;
  description: string;
  timestamp: string;
}

interface OperationalData {
  weather: {
    current: string;
    flow_impact: number;
  };
  ships: {
    waiting: number;
    loading: number;
    total_served: number;
    total_loaded_t: number;
    queue: Ship[];
  };
  product: {
    current: string;
  };
  downtime: {
    weather_s: number;
    maintenance_s: number;
  };
  recent_events: OperationalEvent[];
}

const getWeatherIcon = (weather: string) => {
  switch (weather) {
    case 'clear':
      return <Cloud className="w-6 h-6 text-yellow-400" />;
    case 'cloudy':
      return <Cloud className="w-6 h-6 text-gray-400" />;
    case 'light_rain':
      return <CloudRain className="w-6 h-6 text-blue-400" />;
    case 'heavy_rain':
      return <CloudRain className="w-6 h-6 text-blue-600" />;
    case 'strong_wind':
      return <CloudLightning className="w-6 h-6 text-gray-600" />;
    default:
      return <Cloud className="w-6 h-6 text-gray-400" />;
  }
};

const getWeatherLabel = (weather: string): string => {
  const labels: Record<string, string> = {
    clear: 'Céu Limpo',
    cloudy: 'Nublado',
    light_rain: 'Chuva Leve',
    heavy_rain: 'Chuva Forte',
    strong_wind: 'Vento Forte'
  };
  return labels[weather] || weather;
};

const getPriorityColor = (priority: number): string => {
  switch (priority) {
    case 3: return 'text-red-600 font-bold';
    case 2: return 'text-orange-600 font-semibold';
    default: return 'text-gray-600';
  }
};

const getPriorityBadge = (priority: number): string => {
  switch (priority) {
    case 3: return 'URGENTE';
    case 2: return 'ALTA';
    default: return 'NORMAL';
  }
};

export const ExecutiveDashboard: React.FC = () => {
  const [data, setData] = useState<OperationalData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('/api/v1/simulator/status');
        const status = await response.json();
        
        if (status.operational_events) {
          setData(status.operational_events);
        }
        setLoading(false);
      } catch (error) {
        console.error('Erro ao buscar dados operacionais:', error);
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 2000); // Atualiza a cada 2s

    return () => clearInterval(interval);
  }, []);

  if (loading || !data) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <Activity className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Carregando dados operacionais...</p>
        </div>
      </div>
    );
  }

  // Calcular KPIs
  const totalDowntimeHours = (data.downtime.weather_s + data.downtime.maintenance_s) / 3600;
  const avgLoadPerShip = data.ships.total_served > 0 
    ? data.ships.total_loaded_t / data.ships.total_served 
    : 0;

  // Estimativa de custo (R$ 0.50/kWh, assumindo 1000 kW médio)
  const estimatedCostBRL = (data.ships.total_loaded_t / 1000) * 0.5 * 100; // Simplificado

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-4xl font-bold text-gray-800 mb-2">
          Terminal de Grãos - Dashboard Executivo
        </h1>
        <p className="text-gray-600">
          Monitoramento em tempo real | Smartport AI-Powered Terminal
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        {/* Throughput Total */}
        <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-blue-500">
          <div className="flex items-center justify-between mb-2">
            <TrendingUp className="w-8 h-8 text-blue-500" />
            <span className="text-sm font-medium text-gray-500">THROUGHPUT</span>
          </div>
          <div className="text-3xl font-bold text-gray-800">
            {(data.ships.total_loaded_t / 1000).toFixed(1)}k
          </div>
          <div className="text-sm text-gray-600 mt-1">toneladas movimentadas</div>
        </div>

        {/* Navios Atendidos */}
        <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-green-500">
          <div className="flex items-center justify-between mb-2">
            <Ship className="w-8 h-8 text-green-500" />
            <span className="text-sm font-medium text-gray-500">NAVIOS</span>
          </div>
          <div className="text-3xl font-bold text-gray-800">
            {data.ships.total_served}
          </div>
          <div className="text-sm text-gray-600 mt-1">
            {data.ships.waiting + data.ships.loading} na fila/carregando
          </div>
        </div>

        {/* Downtime */}
        <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-orange-500">
          <div className="flex items-center justify-between mb-2">
            <Clock className="w-8 h-8 text-orange-500" />
            <span className="text-sm font-medium text-gray-500">DOWNTIME</span>
          </div>
          <div className="text-3xl font-bold text-gray-800">
            {totalDowntimeHours.toFixed(1)}h
          </div>
          <div className="text-sm text-gray-600 mt-1">
            clima + manutenção
          </div>
        </div>

        {/* Custo Estimado */}
        <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-purple-500">
          <div className="flex items-center justify-between mb-2">
            <DollarSign className="w-8 h-8 text-purple-500" />
            <span className="text-sm font-medium text-gray-500">CUSTO</span>
          </div>
          <div className="text-3xl font-bold text-gray-800">
            R$ {(estimatedCostBRL / 1000).toFixed(1)}k
          </div>
          <div className="text-sm text-gray-600 mt-1">energia estimada</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* Condições Operacionais */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
            <Activity className="w-6 h-6 mr-2 text-blue-600" />
            Condições Atuais
          </h3>
          
          {/* Clima */}
          <div className="flex items-center justify-between mb-4 p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center">
              {getWeatherIcon(data.weather.current)}
              <div className="ml-3">
                <div className="font-semibold text-gray-800">
                  {getWeatherLabel(data.weather.current)}
                </div>
                <div className="text-sm text-gray-600">
                  Impacto no fluxo: {((1 - data.weather.flow_impact) * 100).toFixed(0)}%
                </div>
              </div>
            </div>
          </div>

          {/* Produto */}
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center">
              <Package className="w-6 h-6 text-amber-600" />
              <div className="ml-3">
                <div className="font-semibold text-gray-800">
                  Produto: {data.product.current.toUpperCase()}
                </div>
                <div className="text-sm text-gray-600">
                  Média {avgLoadPerShip.toFixed(0)}t/navio
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Fila de Navios */}
        <div className="bg-white rounded-xl shadow-lg p-6 lg:col-span-2">
          <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
            <Ship className="w-6 h-6 mr-2 text-blue-600" />
            Fila de Navios ({data.ships.queue.length})
          </h3>
          
          <div className="space-y-3 max-h-80 overflow-y-auto">
            {data.ships.queue.length === 0 ? (
              <p className="text-gray-500 text-center py-4">Nenhum navio na fila</p>
            ) : (
              data.ships.queue.map((ship, idx) => (
                <div 
                  key={idx} 
                  className={`p-4 rounded-lg border-2 ${
                    ship.status === 'loading' 
                      ? 'border-green-500 bg-green-50' 
                      : 'border-gray-200 bg-gray-50'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center">
                      <Ship className={`w-5 h-5 mr-2 ${
                        ship.status === 'loading' ? 'text-green-600' : 'text-gray-600'
                      }`} />
                      <span className="font-bold text-gray-800">{ship.name}</span>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded ${getPriorityColor(ship.priority)}`}>
                      {getPriorityBadge(ship.priority)}
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-3 gap-2 text-sm text-gray-600 mb-2">
                    <div>
                      <span className="font-semibold">DWT:</span> {ship.dwt.toLocaleString()}t
                    </div>
                    <div>
                      <span className="font-semibold">Produto:</span> {ship.product}
                    </div>
                    <div>
                      <span className="font-semibold">Meta:</span> {ship.target_t.toLocaleString('pt-BR', { maximumFractionDigits: 0 })}t
                    </div>
                  </div>
                  
                  {ship.status === 'loading' && (
                    <div className="mt-2">
                      <div className="flex justify-between text-xs text-gray-600 mb-1">
                        <span>Carregado: {ship.loaded_t.toLocaleString('pt-BR', { maximumFractionDigits: 0 })}t</span>
                        <span>{ship.progress.toFixed(1)}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-green-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${Math.min(100, ship.progress)}%` }}
                        />
                      </div>
                    </div>
                  )}
                  
                  <div className="mt-2 text-xs">
                    <span className={`px-2 py-1 rounded ${
                      ship.status === 'loading' 
                        ? 'bg-green-200 text-green-800' 
                        : 'bg-yellow-200 text-yellow-800'
                    }`}>
                      {ship.status === 'loading' ? '🚢 CARREGANDO' : '⏳ AGUARDANDO'}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Eventos Recentes */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
          <AlertCircle className="w-6 h-6 mr-2 text-blue-600" />
          Eventos Operacionais Recentes
        </h3>
        
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {data.recent_events.length === 0 ? (
            <p className="text-gray-500 text-center py-4">Nenhum evento recente</p>
          ) : (
            data.recent_events.slice().reverse().map((event, idx) => (
              <div 
                key={idx} 
                className="flex items-start p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition"
              >
                <AlertCircle className="w-4 h-4 text-blue-600 mt-1 mr-3 flex-shrink-0" />
                <div className="flex-1">
                  <div className="font-semibold text-gray-800">{event.description}</div>
                  <div className="text-xs text-gray-500 mt-1">
                    {new Date(event.timestamp).toLocaleString('pt-BR')}
                  </div>
                </div>
                <span className="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded ml-2">
                  {event.type}
                </span>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="mt-6 text-center text-sm text-gray-500">
        <p>
          Smartport AI-Powered Terminal Management System | 
          Atualização automática a cada 2 segundos | 
          Dados em tempo real via DEM Physics & InfluxDB
        </p>
      </div>
    </div>
  );
};
