/**
 * 🎯 Dashboard Operacional - Visão Geral
 * ======================================
 *
 * Dashboard simplificado com foco em:
 * - Status geral do sistema
 * - Links rápidos para páginas especializadas
 * - Sem duplicação de informações detalhadas
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Title,
  Text,
  Metric,
  Flex,
  Grid,
  Badge,
  Button,
} from '@tremor/react';
import {
  Activity,
  AlertTriangle,
  Clock,
  RefreshCw,
  Factory,
  Zap,
  BarChart3,
  Bell,
  Wrench,
  TrendingUp,
  ArrowRight,
  CheckCircle,
  XCircle,
  AlertCircle,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../../api/client';

interface SystemStatus {
  tags: { total: number; online: number; offline: number };
  alarms: { total: number; critical: number; warning: number };
  equipment: { total: number; running: number; stopped: number; warning: number };
  oee: { current: number; target: number };
  energy: { consumption: number; unit: string };
}

export const TremorDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [currentTime, setCurrentTime] = useState(new Date());
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [status, setStatus] = useState<SystemStatus>({
    tags: { total: 0, online: 0, offline: 0 },
    alarms: { total: 0, critical: 0, warning: 0 },
    equipment: { total: 0, running: 0, stopped: 0, warning: 0 },
    oee: { current: 0, target: 85 },
    energy: { consumption: 0, unit: 'kW' },
  });

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [statsRes, alarmsRes, oeeRes] = await Promise.all([
        apiClient.get('/api/v1/dashboard/stats').catch(() => ({ data: null })),
        apiClient.get('/api/v1/alarms/statistics').catch(() => ({ data: null })),
        apiClient.get('/api/v1/oee/equipment').catch(() => ({ data: null })),
      ]);

      const stats = statsRes.data || {};
      const alarms = alarmsRes.data || {};
      const equipment = oeeRes.data?.equipment || [];

      // Calculate equipment status
      const running = equipment.filter((e: any) => e.status === 'running' || e.oee > 70).length;
      const stopped = equipment.filter((e: any) => e.status === 'stopped' || e.oee === 0).length;
      const warning = equipment.filter((e: any) => e.status === 'warning' || (e.oee > 0 && e.oee < 70)).length;

      setStatus({
        tags: {
          total: stats.total_tags || 0,
          online: stats.active_tags || stats.online_tags || 0,
          offline: (stats.total_tags || 0) - (stats.active_tags || stats.online_tags || 0),
        },
        alarms: {
          total: alarms.active || alarms.total || stats.active_alarms || 0,
          critical: alarms.by_severity?.critical || 0,
          warning: alarms.by_severity?.high || alarms.by_severity?.warning || 0,
        },
        equipment: {
          total: equipment.length || stats.total_devices || 0,
          running,
          stopped,
          warning,
        },
        oee: {
          current: stats.oee_current || equipment.reduce((acc: number, e: any) => acc + (e.oee || 0), 0) / (equipment.length || 1) || 0,
          target: 85,
        },
        energy: {
          consumption: stats.energy_consumption || 0,
          unit: 'kW',
        },
      });

      setLastUpdated(new Date());
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const getHealthStatus = () => {
    if (status.alarms.critical > 0) return { color: 'red', text: 'Crítico', icon: XCircle };
    if (status.alarms.warning > 0 || status.equipment.warning > 0) return { color: 'amber', text: 'Atenção', icon: AlertCircle };
    return { color: 'emerald', text: 'Normal', icon: CheckCircle };
  };

  const health = getHealthStatus();
  const HealthIcon = health.icon;

  if (loading && status.tags.total === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
        <Text className="ml-2">Carregando...</Text>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Title>Dashboard Operacional</Title>
          <Text>Visão geral do sistema</Text>
        </div>
        <div className="flex items-center gap-4">
          <Button size="xs" variant="secondary" icon={RefreshCw} onClick={fetchData} loading={loading}>
            Atualizar
          </Button>
          <div className="flex items-center gap-2 text-gray-500">
            <Clock className="w-4 h-4" />
            <Text>{currentTime.toLocaleString('pt-BR')}</Text>
          </div>
        </div>
      </div>

      {/* System Health Banner */}
      <Card className={`bg-gradient-to-r ${
        health.color === 'red' ? 'from-red-500 to-red-600' :
        health.color === 'amber' ? 'from-amber-500 to-amber-600' :
        'from-emerald-500 to-emerald-600'
      } text-white`}>
        <Flex justifyContent="between" alignItems="center">
          <Flex alignItems="center" className="gap-4">
            <HealthIcon className="w-12 h-12" />
            <div>
              <Text className="text-white/80 text-sm">Status do Sistema</Text>
              <p className="text-2xl font-bold">{health.text}</p>
              <Text className="text-white/70 text-xs">
                Atualizado: {lastUpdated.toLocaleTimeString('pt-BR')}
              </Text>
            </div>
          </Flex>
          <div className="text-right">
            <Text className="text-white/80 text-sm">OEE Geral</Text>
            <p className="text-3xl font-bold">{status.oee.current.toFixed(1)}%</p>
            <Text className="text-white/70 text-xs">Meta: {status.oee.target}%</Text>
          </div>
        </Flex>
      </Card>

      {/* Quick Status Cards */}
      <Grid numItemsSm={2} numItemsLg={4} className="gap-4">
        {/* Tags Status */}
        <Card
          className="cursor-pointer hover:shadow-lg transition-shadow"
          onClick={() => navigate('/monitoring')}
        >
          <Flex justifyContent="between" alignItems="start">
            <div>
              <Text className="text-gray-500">Tags Monitorados</Text>
              <Metric className="mt-1">{status.tags.total}</Metric>
            </div>
            <div className="p-2 bg-blue-100 rounded-lg">
              <Activity className="w-6 h-6 text-blue-600" />
            </div>
          </Flex>
          <Flex className="mt-4 gap-2">
            <Badge color="emerald" size="sm">{status.tags.online} online</Badge>
            {status.tags.offline > 0 && (
              <Badge color="gray" size="sm">{status.tags.offline} offline</Badge>
            )}
          </Flex>
          <Flex className="mt-3 text-blue-600 text-sm" justifyContent="end">
            <span>Ver Monitoramento</span>
            <ArrowRight className="w-4 h-4 ml-1" />
          </Flex>
        </Card>

        {/* Alarms Status */}
        <Card
          className="cursor-pointer hover:shadow-lg transition-shadow"
          onClick={() => navigate('/alarms')}
        >
          <Flex justifyContent="between" alignItems="start">
            <div>
              <Text className="text-gray-500">Alarmes Ativos</Text>
              <Metric className={`mt-1 ${status.alarms.critical > 0 ? 'text-red-600' : ''}`}>
                {status.alarms.total}
              </Metric>
            </div>
            <div className={`p-2 rounded-lg ${status.alarms.critical > 0 ? 'bg-red-100' : 'bg-amber-100'}`}>
              <Bell className={`w-6 h-6 ${status.alarms.critical > 0 ? 'text-red-600' : 'text-amber-600'}`} />
            </div>
          </Flex>
          <Flex className="mt-4 gap-2">
            {status.alarms.critical > 0 && (
              <Badge color="red" size="sm">{status.alarms.critical} críticos</Badge>
            )}
            {status.alarms.warning > 0 && (
              <Badge color="amber" size="sm">{status.alarms.warning} avisos</Badge>
            )}
            {status.alarms.total === 0 && (
              <Badge color="emerald" size="sm">Sem alarmes</Badge>
            )}
          </Flex>
          <Flex className="mt-3 text-blue-600 text-sm" justifyContent="end">
            <span>Ver Alarmes</span>
            <ArrowRight className="w-4 h-4 ml-1" />
          </Flex>
        </Card>

        {/* Equipment Status */}
        <Card
          className="cursor-pointer hover:shadow-lg transition-shadow"
          onClick={() => navigate('/executive/oee')}
        >
          <Flex justifyContent="between" alignItems="start">
            <div>
              <Text className="text-gray-500">Equipamentos</Text>
              <Metric className="mt-1">{status.equipment.total}</Metric>
            </div>
            <div className="p-2 bg-emerald-100 rounded-lg">
              <Factory className="w-6 h-6 text-emerald-600" />
            </div>
          </Flex>
          <Flex className="mt-4 gap-2">
            <Badge color="emerald" size="sm">{status.equipment.running} operando</Badge>
            {status.equipment.warning > 0 && (
              <Badge color="amber" size="sm">{status.equipment.warning} atenção</Badge>
            )}
            {status.equipment.stopped > 0 && (
              <Badge color="gray" size="sm">{status.equipment.stopped} parados</Badge>
            )}
          </Flex>
          <Flex className="mt-3 text-blue-600 text-sm" justifyContent="end">
            <span>Ver OEE</span>
            <ArrowRight className="w-4 h-4 ml-1" />
          </Flex>
        </Card>

        {/* Energy Quick View */}
        <Card
          className="cursor-pointer hover:shadow-lg transition-shadow"
          onClick={() => navigate('/executive/energy')}
        >
          <Flex justifyContent="between" alignItems="start">
            <div>
              <Text className="text-gray-500">Consumo Atual</Text>
              <Metric className="mt-1">
                {status.energy.consumption > 0 ? status.energy.consumption.toFixed(1) : '--'} {status.energy.unit}
              </Metric>
            </div>
            <div className="p-2 bg-yellow-100 rounded-lg">
              <Zap className="w-6 h-6 text-yellow-600" />
            </div>
          </Flex>
          <Text className="mt-4 text-gray-500 text-sm">
            Monitoramento energético
          </Text>
          <Flex className="mt-3 text-blue-600 text-sm" justifyContent="end">
            <span>Ver Energia</span>
            <ArrowRight className="w-4 h-4 ml-1" />
          </Flex>
        </Card>
      </Grid>

      {/* Quick Navigation */}
      <Card>
        <Title>Acesso Rápido</Title>
        <Text className="mb-4">Navegue para as áreas especializadas</Text>
        <Grid numItemsSm={2} numItemsLg={4} className="gap-4">
          <Button
            variant="secondary"
            className="h-20 flex-col gap-2"
            onClick={() => navigate('/monitoring')}
          >
            <Activity className="w-6 h-6" />
            <span>Supervisão</span>
          </Button>
          <Button
            variant="secondary"
            className="h-20 flex-col gap-2"
            onClick={() => navigate('/monitoring/history')}
          >
            <TrendingUp className="w-6 h-6" />
            <span>Histórico</span>
          </Button>
          <Button
            variant="secondary"
            className="h-20 flex-col gap-2"
            onClick={() => navigate('/executive/oee')}
          >
            <BarChart3 className="w-6 h-6" />
            <span>OEE</span>
          </Button>
          <Button
            variant="secondary"
            className="h-20 flex-col gap-2"
            onClick={() => navigate('/maintenance')}
          >
            <Wrench className="w-6 h-6" />
            <span>Manutenção</span>
          </Button>
        </Grid>
      </Card>

      {/* Critical Alerts Section - Only show if there are critical alarms */}
      {status.alarms.critical > 0 && (
        <Card decoration="left" decorationColor="red">
          <Flex justifyContent="between" alignItems="center">
            <Flex alignItems="center" className="gap-3">
              <AlertTriangle className="w-8 h-8 text-red-500" />
              <div>
                <Title className="text-red-700">Atenção Requerida</Title>
                <Text>{status.alarms.critical} alarme(s) crítico(s) ativo(s)</Text>
              </div>
            </Flex>
            <Button color="red" onClick={() => navigate('/alarms')}>
              Ver Alarmes
            </Button>
          </Flex>
        </Card>
      )}
    </div>
  );
};

export default TremorDashboard;
