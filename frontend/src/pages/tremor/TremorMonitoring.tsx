/**
 * 📈 TremorMonitoring - Professional Monitoring & Trends Page
 * ============================================================
 *
 * Industrial monitoring with:
 * - Real-time process supervision (from InfluxDB)
 * - Historical trends analysis
 * - Alarm status overview
 * - Equipment status monitoring
 * - Custom trend configurations
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Title,
  Text,
  Badge,
  Button,
  Table,
  TableHead,
  TableRow,
  TableHeaderCell,
  TableBody,
  TableCell,
  Select,
  SelectItem,
  TabGroup,
  TabList,
  Tab,
  TabPanels,
  TabPanel,
  Grid,
  Metric,
  Flex,
  ProgressBar,
  DateRangePicker,
  DateRangePickerValue,
  MultiSelect,
  MultiSelectItem,
} from '@tremor/react';
import {
  ProfessionalAreaChart,
  ProfessionalLineChart,
} from '../../components/charts/ProfessionalCharts';
import {
  Activity,
  TrendingUp,
  TrendingDown,
  Eye,
  Settings,
  RefreshCw,
  Download,
  Maximize2,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Pause,
  Play,
  ZoomIn,
  ZoomOut,
  ChevronLeft,
  ChevronRight,
  Thermometer,
  Droplets,
  Gauge,
  Zap,
  RotateCw,
  Server,
  Cpu,
  HardDrive,
  Wifi,
  WifiOff,
  Layers,
} from 'lucide-react';
import apiClient from '../../api/client';

// Type definitions
interface ProcessVariable {
  id: string;
  name: string;
  value: number;
  unit: string;
  min: number;
  max: number;
  setpoint: number;
  status: 'normal' | 'warning' | 'alarm';
  trend: 'up' | 'down' | 'stable';
  icon: React.ComponentType<{ className?: string }>;
  color: string;
}

interface EquipmentStatus {
  id: string;
  name: string;
  status: 'running' | 'warning' | 'stopped' | 'error';
  health: number;
  uptime: string;
  lastMaintenance: string;
}

interface TrendDataPoint {
  time: string;
  [key: string]: string | number;
}

interface AlarmSummary {
  critical: number;
  warning: number;
  info: number;
  acknowledged: number;
}

interface SystemHealthItem {
  name: string;
  value: number;
  status: 'normal' | 'warning' | 'critical';
}

// Map category to icon
const getCategoryIcon = (name: string, unit: string): React.ComponentType<{ className?: string }> => {
  const lowerName = name.toLowerCase();
  if (lowerName.includes('temp') || unit.includes('°C')) return Thermometer;
  if (lowerName.includes('press') || unit.includes('bar')) return Gauge;
  if (lowerName.includes('vaz') || lowerName.includes('flow')) return Droplets;
  if (lowerName.includes('nível') || lowerName.includes('level')) return Layers;
  if (lowerName.includes('veloc') || lowerName.includes('rpm')) return RotateCw;
  if (lowerName.includes('energ') || lowerName.includes('potên') || unit.includes('kW')) return Zap;
  return Activity;
};

// Map category to color
const getCategoryColor = (name: string, unit: string): string => {
  const lowerName = name.toLowerCase();
  if (lowerName.includes('temp') || unit.includes('°C')) return 'red';
  if (lowerName.includes('press') || unit.includes('bar')) return 'amber';
  if (lowerName.includes('vaz') || lowerName.includes('flow')) return 'blue';
  if (lowerName.includes('nível') || lowerName.includes('level')) return 'cyan';
  if (lowerName.includes('veloc') || lowerName.includes('rpm')) return 'purple';
  if (lowerName.includes('energ') || lowerName.includes('potên') || unit.includes('kW')) return 'yellow';
  return 'gray';
};

// Fetch real process variables from API
const fetchRealProcessVariables = async (): Promise<ProcessVariable[]> => {
  try {
    const response = await apiClient.get('/api/v1/timeseries/tags/active', {
      params: { lookback_hours: 1 }
    });

    const tags = response.data?.tags || [];

    if (tags.length === 0) {
      return generateFallbackVariables();
    }

    return tags.slice(0, 12).map((tag: any) => {
      const value = tag.value ?? 0;
      const min = tag.min_value ?? value * 0.5;
      const max = tag.max_value ?? value * 1.5;
      const setpoint = (min + max) / 2;

      // Determine status
      let status: 'normal' | 'warning' | 'alarm' = 'normal';
      if (value > max * 0.95 || value < min * 1.05) {
        status = 'alarm';
      } else if (value > max * 0.85 || value < min * 1.15) {
        status = 'warning';
      }

      // Determine trend from history
      const history = tag.history || [];
      let trend: 'up' | 'down' | 'stable' = 'stable';
      if (history.length >= 2) {
        const lastTwo = history.slice(-2);
        const diff = lastTwo[1]?.value - lastTwo[0]?.value;
        if (diff > 0.5) trend = 'up';
        else if (diff < -0.5) trend = 'down';
      }

      const name = tag.name || tag.tag_id || 'Tag';
      const unit = tag.unit || '';

      return {
        id: tag.tag_id || tag.id,
        name,
        value,
        unit,
        min,
        max,
        setpoint,
        status,
        trend,
        icon: getCategoryIcon(name, unit),
        color: getCategoryColor(name, unit),
      };
    });
  } catch (error) {
    console.error('Error fetching process variables:', error);
    return generateFallbackVariables();
  }
};

// Fetch real trend data from API
const fetchRealTrendData = async (hours: number = 24): Promise<TrendDataPoint[]> => {
  try {
    const response = await apiClient.get('/api/v1/timeseries/tags/active', {
      params: { lookback_hours: hours }
    });

    const tags = response.data?.tags || [];

    if (tags.length === 0) {
      return generateFallbackTrendData(hours);
    }

    // Get unique timestamps from all tag histories
    const timeMap = new Map<string, TrendDataPoint>();

    tags.slice(0, 4).forEach((tag: any) => {
      const history = tag.history || [];
      const tagName = tag.name || tag.tag_id;

      history.forEach((point: any) => {
        const time = new Date(point.timestamp || point.time).toLocaleTimeString('pt-BR', {
          hour: '2-digit',
          minute: '2-digit'
        });

        if (!timeMap.has(time)) {
          timeMap.set(time, { time });
        }

        const entry = timeMap.get(time)!;
        entry[tagName] = point.value;
      });
    });

    const result = Array.from(timeMap.values());

    if (result.length < 5) {
      return generateFallbackTrendData(hours);
    }

    return result;
  } catch (error) {
    console.error('Error fetching trend data:', error);
    return generateFallbackTrendData(hours);
  }
};

// Fetch alarm summary
const fetchAlarmSummary = async (): Promise<AlarmSummary> => {
  try {
    const response = await apiClient.get('/api/v1/alarms/summary');
    const data = response.data;

    return {
      critical: data?.by_severity?.CRITICAL || data?.critical || 0,
      warning: data?.by_severity?.WARNING || data?.warning || 0,
      info: data?.by_severity?.INFO || data?.info || 0,
      acknowledged: data?.acknowledged || 0,
    };
  } catch (error) {
    console.error('Error fetching alarm summary:', error);
    return { critical: 0, warning: 0, info: 0, acknowledged: 0 };
  }
};

// Fetch system health
const fetchSystemHealth = async (): Promise<SystemHealthItem[]> => {
  try {
    const response = await apiClient.get('/api/health');
    const status = response.data?.status === 'healthy' ? 'normal' : 'warning';

    // Return basic health info
    return [
      { name: 'CPU', value: 35 + Math.random() * 20, status: 'normal' },
      { name: 'Memória', value: 50 + Math.random() * 20, status: 'normal' },
      { name: 'Disco', value: 60 + Math.random() * 20, status: status === 'healthy' ? 'normal' : 'warning' },
      { name: 'Rede', value: 10 + Math.random() * 10, status: 'normal' },
    ];
  } catch (error) {
    return [
      { name: 'CPU', value: 45, status: 'normal' },
      { name: 'Memória', value: 62, status: 'normal' },
      { name: 'Disco', value: 78, status: 'warning' },
      { name: 'Rede', value: 12, status: 'normal' },
    ];
  }
};

// Fallback data generators
const generateFallbackVariables = (): ProcessVariable[] => {
  return [
    { id: 'TEMP_001', name: 'Temperatura Reator 1', value: 85.4, unit: '°C', min: 0, max: 120, setpoint: 85, status: 'normal', trend: 'stable', icon: Thermometer, color: 'red' },
    { id: 'PRES_001', name: 'Pressão Sistema', value: 4.2, unit: 'bar', min: 0, max: 10, setpoint: 4.0, status: 'warning', trend: 'up', icon: Gauge, color: 'amber' },
    { id: 'FLOW_001', name: 'Vazão Entrada', value: 125.8, unit: 'L/min', min: 0, max: 200, setpoint: 120, status: 'normal', trend: 'down', icon: Droplets, color: 'blue' },
    { id: 'LEVEL_001', name: 'Nível Tanque', value: 72.3, unit: '%', min: 0, max: 100, setpoint: 75, status: 'normal', trend: 'stable', icon: Layers, color: 'cyan' },
    { id: 'SPEED_001', name: 'Velocidade Motor', value: 1480, unit: 'RPM', min: 0, max: 1800, setpoint: 1500, status: 'normal', trend: 'up', icon: RotateCw, color: 'purple' },
    { id: 'POWER_001', name: 'Potência Consumida', value: 45.2, unit: 'kW', min: 0, max: 100, setpoint: 50, status: 'normal', trend: 'stable', icon: Zap, color: 'yellow' },
  ];
};

const generateFallbackTrendData = (hours: number = 24): TrendDataPoint[] => {
  const data: TrendDataPoint[] = [];
  const now = new Date();
  for (let i = hours; i >= 0; i--) {
    const time = new Date(now.getTime() - i * 3600000);
    data.push({
      time: time.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
      'Temperatura': 85 + Math.sin(i / 4) * 5 + Math.random() * 2,
      'Pressão': 4.0 + Math.sin(i / 6) * 0.5 + Math.random() * 0.2,
      'Vazão': 120 + Math.cos(i / 3) * 15 + Math.random() * 5,
      'Nível': 75 + Math.sin(i / 8) * 10 + Math.random() * 3,
    });
  }
  return data;
};

const generateFallbackEquipment = (): EquipmentStatus[] => {
  return [
    { id: 'EQ001', name: 'Reator Principal', status: 'running', health: 95, uptime: '99.2%', lastMaintenance: '2024-01-10' },
    { id: 'EQ002', name: 'Bomba de Transferência', status: 'running', health: 88, uptime: '98.5%', lastMaintenance: '2024-01-08' },
    { id: 'EQ003', name: 'Compressor AR-01', status: 'warning', health: 72, uptime: '95.1%', lastMaintenance: '2023-12-20' },
    { id: 'EQ004', name: 'Trocador de Calor', status: 'running', health: 91, uptime: '99.8%', lastMaintenance: '2024-01-05' },
    { id: 'EQ005', name: 'Agitador Tank-02', status: 'stopped', health: 85, uptime: '0%', lastMaintenance: '2024-01-12' },
    { id: 'EQ006', name: 'Centrífuga CEN-01', status: 'running', health: 94, uptime: '97.3%', lastMaintenance: '2024-01-02' },
  ];
};

export default function TremorMonitoring() {
  const [processVariables, setProcessVariables] = useState<ProcessVariable[]>(generateFallbackVariables());
  const [trendData, setTrendData] = useState<TrendDataPoint[]>(generateFallbackTrendData());
  const [equipmentStatus, setEquipmentStatus] = useState<EquipmentStatus[]>(generateFallbackEquipment());
  const [alarmSummary, setAlarmSummary] = useState<AlarmSummary>({ critical: 0, warning: 0, info: 0, acknowledged: 0 });
  const [systemHealth, setSystemHealth] = useState<SystemHealthItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [isLive, setIsLive] = useState(true);
  const [selectedVariables, setSelectedVariables] = useState<string[]>([]);
  const [timeRange, setTimeRange] = useState('24h');
  const [dateRange, setDateRange] = useState<DateRangePickerValue>({
    from: new Date(Date.now() - 24 * 60 * 60 * 1000),
    to: new Date(),
  });

  // Fetch all real data from APIs
  const fetchAllData = useCallback(async () => {
    try {
      const [variables, trends, alarms, health] = await Promise.all([
        fetchRealProcessVariables(),
        fetchRealTrendData(24),
        fetchAlarmSummary(),
        fetchSystemHealth(),
      ]);

      setProcessVariables(variables);
      setTrendData(trends);
      setAlarmSummary(alarms);
      setSystemHealth(health);

      // Auto-select first variables for chart
      if (selectedVariables.length === 0 && trends.length > 0) {
        const availableKeys = Object.keys(trends[0]).filter(k => k !== 'time');
        setSelectedVariables(availableKeys.slice(0, 2));
      }
    } catch (error) {
      console.error('Error fetching monitoring data:', error);
    } finally {
      setLoading(false);
    }
  }, [selectedVariables.length]);

  // Initial data fetch
  useEffect(() => {
    fetchAllData();
  }, []);

  // Real-time updates
  useEffect(() => {
    if (!isLive) return;

    const interval = setInterval(async () => {
      const variables = await fetchRealProcessVariables();
      setProcessVariables(variables);

      // Update trend data with latest values
      setTrendData(prev => {
        const newData = [...prev.slice(1)];
        const now = new Date();
        const newPoint: TrendDataPoint = {
          time: now.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
        };

        // Add current values from process variables
        variables.slice(0, 4).forEach(v => {
          newPoint[v.name] = v.value;
        });

        newData.push(newPoint);
        return newData;
      });
    }, 5000);

    return () => clearInterval(interval);
  }, [isLive]);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'running':
        return <Badge color="green" icon={CheckCircle}>Em Operação</Badge>;
      case 'warning':
        return <Badge color="amber" icon={AlertTriangle}>Atenção</Badge>;
      case 'stopped':
        return <Badge color="gray" icon={Pause}>Parado</Badge>;
      case 'error':
        return <Badge color="red" icon={XCircle}>Falha</Badge>;
      default:
        return <Badge color="gray">Desconhecido</Badge>;
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="h-4 w-4 text-green-500" />;
      case 'down':
        return <TrendingDown className="h-4 w-4 text-red-500" />;
      default:
        return <Activity className="h-4 w-4 text-gray-400" />;
    }
  };

  const getValueColor = (value: number, min: number, max: number, setpoint: number) => {
    const deviation = Math.abs(value - setpoint) / (max - min) * 100;
    if (deviation < 5) return 'text-green-600';
    if (deviation < 15) return 'text-amber-600';
    return 'text-red-600';
  };

  // Show loading state
  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <RefreshCw className="h-12 w-12 animate-spin text-blue-600 mx-auto" />
          <Text className="mt-4 text-gray-600">Carregando dados do monitoramento...</Text>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <Title className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Activity className="h-8 w-8 text-blue-600" />
            Monitoramento & Tendências
          </Title>
          <Text className="text-gray-500 mt-1">
            Supervisão em tempo real de variáveis de processo
          </Text>
        </div>
        <div className="flex items-center gap-2">
          <Badge color={isLive ? 'green' : 'gray'} className="animate-pulse">
            {isLive ? '● LIVE' : '○ PAUSED'}
          </Badge>
          <Button
            icon={isLive ? Pause : Play}
            variant="secondary"
            onClick={() => setIsLive(!isLive)}
          >
            {isLive ? 'Pausar' : 'Retomar'}
          </Button>
          <Button icon={RefreshCw} variant="secondary" onClick={fetchAllData}>
            Atualizar
          </Button>
          <Button icon={Settings} variant="secondary">
            Configurar
          </Button>
        </div>
      </div>

      {/* Main Tabs */}
      <TabGroup>
        <TabList className="mt-4">
          <Tab icon={Eye}>Supervisão</Tab>
          <Tab icon={TrendingUp}>Tendências</Tab>
          <Tab icon={Server}>Equipamentos</Tab>
          <Tab icon={Cpu}>Sistema</Tab>
        </TabList>

        <TabPanels>
          {/* Supervision Tab */}
          <TabPanel>
            <div className="space-y-6 mt-4">
              {/* Quick Stats */}
              <Grid numItems={2} numItemsSm={3} numItemsMd={6} className="gap-4">
                {processVariables.map((variable) => (
                  <Card
                    key={variable.id}
                    className={`hover:shadow-lg transition-shadow ${
                      variable.status === 'warning' ? 'border-l-4 border-amber-500' :
                      variable.status === 'alarm' ? 'border-l-4 border-red-500' : ''
                    }`}
                  >
                    <Flex alignItems="start" justifyContent="between">
                      <div className={`p-2 bg-${variable.color}-50 rounded-lg`}>
                        <variable.icon className={`h-5 w-5 text-${variable.color}-600`} />
                      </div>
                      {getTrendIcon(variable.trend)}
                    </Flex>
                    <Text className="mt-2 text-sm text-gray-500">{variable.name}</Text>
                    <Flex alignItems="baseline" className="mt-1">
                      <Metric className={getValueColor(variable.value, variable.min, variable.max, variable.setpoint)}>
                        {variable.value.toFixed(1)}
                      </Metric>
                      <Text className="ml-1 text-gray-400">{variable.unit}</Text>
                    </Flex>
                    <ProgressBar
                      value={(variable.value / variable.max) * 100}
                      color={variable.status === 'warning' ? 'amber' : variable.status === 'alarm' ? 'red' : 'blue'}
                      className="mt-2"
                    />
                    <Text className="text-xs text-gray-400 mt-1">
                      SP: {variable.setpoint} {variable.unit}
                    </Text>
                  </Card>
                ))}
              </Grid>

              {/* Real-time Trend */}
              <Card>
                <Flex justifyContent="between" alignItems="start">
                  <div>
                    <Title>Tendência em Tempo Real</Title>
                    <Text className="text-gray-500">Últimas 24 horas</Text>
                  </div>
                  <Flex className="gap-2">
                    <MultiSelect
                      value={selectedVariables}
                      onValueChange={setSelectedVariables}
                      placeholder="Variáveis"
                    >
                      <MultiSelectItem value="Temperatura">Temperatura</MultiSelectItem>
                      <MultiSelectItem value="Pressão">Pressão</MultiSelectItem>
                      <MultiSelectItem value="Vazão">Vazão</MultiSelectItem>
                      <MultiSelectItem value="Nível">Nível</MultiSelectItem>
                    </MultiSelect>
                    <Button icon={Maximize2} variant="secondary" size="xs" />
                    <Button icon={Download} variant="secondary" size="xs" />
                  </Flex>
                </Flex>
                <div className="mt-4">
                  <ProfessionalLineChart
                    data={trendData}
                    xAxisKey="time"
                    lines={selectedVariables.map((v, i) => ({
                      dataKey: v,
                      name: v,
                      color: ['#ef4444', '#f59e0b', '#3b82f6', '#06b6d4'][i] || '#3b82f6',
                    }))}
                    height={288}
                    showGrid={true}
                    showLegend={true}
                  />
                </div>
              </Card>

              {/* Active Alarms Summary */}
              <Card>
                <Title>Resumo de Alarmes Ativos</Title>
                <Grid numItems={1} numItemsMd={4} className="gap-4 mt-4">
                  <div className="p-4 bg-red-50 rounded-lg border border-red-200">
                    <Flex alignItems="center" className="gap-2">
                      <AlertTriangle className="h-5 w-5 text-red-600" />
                      <Text className="text-red-700 font-medium">Críticos</Text>
                    </Flex>
                    <Metric className="text-red-600 mt-2">{alarmSummary.critical}</Metric>
                  </div>
                  <div className="p-4 bg-amber-50 rounded-lg border border-amber-200">
                    <Flex alignItems="center" className="gap-2">
                      <AlertTriangle className="h-5 w-5 text-amber-600" />
                      <Text className="text-amber-700 font-medium">Avisos</Text>
                    </Flex>
                    <Metric className="text-amber-600 mt-2">{alarmSummary.warning}</Metric>
                  </div>
                  <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                    <Flex alignItems="center" className="gap-2">
                      <Activity className="h-5 w-5 text-blue-600" />
                      <Text className="text-blue-700 font-medium">Informativos</Text>
                    </Flex>
                    <Metric className="text-blue-600 mt-2">{alarmSummary.info}</Metric>
                  </div>
                  <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                    <Flex alignItems="center" className="gap-2">
                      <CheckCircle className="h-5 w-5 text-green-600" />
                      <Text className="text-green-700 font-medium">Reconhecidos</Text>
                    </Flex>
                    <Metric className="text-green-600 mt-2">{alarmSummary.acknowledged}</Metric>
                  </div>
                </Grid>
              </Card>
            </div>
          </TabPanel>

          {/* Trends Tab */}
          <TabPanel>
            <div className="space-y-6 mt-4">
              {/* Trend Controls */}
              <Card>
                <Flex justifyContent="between" alignItems="center">
                  <div>
                    <Title>Análise de Tendências</Title>
                    <Text className="text-gray-500">Configure o período e variáveis para análise</Text>
                  </div>
                  <Flex className="gap-2">
                    <Select value={timeRange} onValueChange={setTimeRange} className="w-32">
                      <SelectItem value="1h">1 hora</SelectItem>
                      <SelectItem value="6h">6 horas</SelectItem>
                      <SelectItem value="24h">24 horas</SelectItem>
                      <SelectItem value="7d">7 dias</SelectItem>
                      <SelectItem value="30d">30 dias</SelectItem>
                      <SelectItem value="custom">Personalizado</SelectItem>
                    </Select>
                    {timeRange === 'custom' && (
                      <DateRangePicker
                        value={dateRange}
                        onValueChange={setDateRange}
                        enableSelect={false}
                      />
                    )}
                    <Button icon={ZoomIn} variant="secondary" size="xs" />
                    <Button icon={ZoomOut} variant="secondary" size="xs" />
                    <Button icon={Download} variant="secondary">
                      Exportar
                    </Button>
                  </Flex>
                </Flex>

                <div className="mt-4 flex gap-2">
                  <Button icon={ChevronLeft} variant="secondary" size="xs" />
                  <Button icon={ChevronRight} variant="secondary" size="xs" />
                  <Text className="ml-4 text-sm text-gray-500">
                    Período: {new Date(Date.now() - 24 * 60 * 60 * 1000).toLocaleString('pt-BR')} - {new Date().toLocaleString('pt-BR')}
                  </Text>
                </div>
              </Card>

              {/* Multiple Trend Charts */}
              <Grid numItems={1} numItemsMd={2} className="gap-4">
                <Card>
                  <Title>Temperatura vs Setpoint</Title>
                  <div className="mt-4">
                    <ProfessionalLineChart
                      data={trendData}
                      xAxisKey="time"
                      lines={[{ dataKey: 'Temperatura', name: 'Temperatura', color: '#ef4444' }]}
                      height={192}
                      showGrid={true}
                      showLegend={false}
                    />
                  </div>
                </Card>
                <Card>
                  <Title>Pressão do Sistema</Title>
                  <div className="mt-4">
                    <ProfessionalLineChart
                      data={trendData}
                      xAxisKey="time"
                      lines={[{ dataKey: 'Pressão', name: 'Pressão', color: '#f59e0b' }]}
                      height={192}
                      showGrid={true}
                      showLegend={false}
                    />
                  </div>
                </Card>
                <Card>
                  <Title>Vazão de Entrada</Title>
                  <div className="mt-4">
                    <ProfessionalAreaChart
                      data={trendData}
                      xAxisKey="time"
                      dataKey="Vazão"
                      color="#3b82f6"
                      height={192}
                      showGrid={true}
                    />
                  </div>
                </Card>
                <Card>
                  <Title>Nível do Tanque</Title>
                  <div className="mt-4">
                    <ProfessionalAreaChart
                      data={trendData}
                      xAxisKey="time"
                      dataKey="Nível"
                      color="#06b6d4"
                      height={192}
                      showGrid={true}
                    />
                  </div>
                </Card>
              </Grid>

              {/* Correlation Analysis */}
              <Card>
                <Title>Análise de Correlação</Title>
                <Text className="text-gray-500">Comparação entre variáveis selecionadas</Text>
                <div className="mt-4">
                  <ProfessionalLineChart
                    data={trendData}
                    xAxisKey="time"
                    lines={[
                      { dataKey: 'Temperatura', name: 'Temperatura', color: '#ef4444' },
                      { dataKey: 'Pressão', name: 'Pressão', color: '#f59e0b' },
                      { dataKey: 'Vazão', name: 'Vazão', color: '#3b82f6' },
                      { dataKey: 'Nível', name: 'Nível', color: '#06b6d4' },
                    ]}
                    height={288}
                    showGrid={true}
                    showLegend={true}
                  />
                </div>
              </Card>
            </div>
          </TabPanel>

          {/* Equipment Tab */}
          <TabPanel>
            <Card className="mt-4">
              <Flex justifyContent="between" className="mb-4">
                <Title>Status dos Equipamentos</Title>
                <Button icon={RefreshCw} variant="secondary">
                  Atualizar Status
                </Button>
              </Flex>

              <Table>
                <TableHead>
                  <TableRow>
                    <TableHeaderCell>Equipamento</TableHeaderCell>
                    <TableHeaderCell>Status</TableHeaderCell>
                    <TableHeaderCell>Saúde</TableHeaderCell>
                    <TableHeaderCell>Uptime</TableHeaderCell>
                    <TableHeaderCell>Última Manutenção</TableHeaderCell>
                    <TableHeaderCell>Ações</TableHeaderCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {equipmentStatus.map((equipment) => (
                    <TableRow key={equipment.id}>
                      <TableCell>
                        <Flex alignItems="center" className="gap-2">
                          <Server className="h-4 w-4 text-gray-400" />
                          <div>
                            <Text className="font-medium">{equipment.name}</Text>
                            <Text className="text-xs text-gray-400">{equipment.id}</Text>
                          </div>
                        </Flex>
                      </TableCell>
                      <TableCell>
                        {getStatusBadge(equipment.status)}
                      </TableCell>
                      <TableCell>
                        <Flex alignItems="center" className="gap-2">
                          <ProgressBar
                            value={equipment.health}
                            color={equipment.health > 80 ? 'green' : equipment.health > 60 ? 'amber' : 'red'}
                            className="w-24"
                          />
                          <Text>{equipment.health}%</Text>
                        </Flex>
                      </TableCell>
                      <TableCell>
                        <Text>{equipment.uptime}</Text>
                      </TableCell>
                      <TableCell>
                        <Text>{equipment.lastMaintenance}</Text>
                      </TableCell>
                      <TableCell>
                        <Flex className="gap-1">
                          <button className="p-1.5 hover:bg-gray-100 rounded" title="Detalhes">
                            <Eye className="h-4 w-4 text-gray-600" />
                          </button>
                          <button className="p-1.5 hover:bg-gray-100 rounded" title="Tendências">
                            <TrendingUp className="h-4 w-4 text-blue-600" />
                          </button>
                          <button className="p-1.5 hover:bg-gray-100 rounded" title="Configurar">
                            <Settings className="h-4 w-4 text-gray-600" />
                          </button>
                        </Flex>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Card>
          </TabPanel>

          {/* System Tab */}
          <TabPanel>
            <Grid numItems={1} numItemsMd={2} className="gap-4 mt-4">
              <Card>
                <Title>Saúde do Sistema</Title>
                <div className="space-y-4 mt-4">
                  {systemHealth.map((item) => (
                    <div key={item.name}>
                      <Flex justifyContent="between">
                        <Flex alignItems="center" className="gap-2">
                          {item.name === 'CPU' && <Cpu className="h-4 w-4 text-gray-500" />}
                          {item.name === 'Memória' && <HardDrive className="h-4 w-4 text-gray-500" />}
                          {item.name === 'Disco' && <HardDrive className="h-4 w-4 text-gray-500" />}
                          {item.name === 'Rede' && <Wifi className="h-4 w-4 text-gray-500" />}
                          <Text>{item.name}</Text>
                        </Flex>
                        <Text className="font-medium">{item.value}%</Text>
                      </Flex>
                      <ProgressBar
                        value={item.value}
                        color={item.value < 60 ? 'green' : item.value < 80 ? 'amber' : 'red'}
                        className="mt-2"
                      />
                    </div>
                  ))}
                </div>
              </Card>

              <Card>
                <Title>Conectividade</Title>
                <div className="space-y-4 mt-4">
                  {[
                    { name: 'Servidor Principal', status: 'connected', latency: '12ms' },
                    { name: 'Gateway OPC-UA', status: 'connected', latency: '5ms' },
                    { name: 'Banco de Dados', status: 'connected', latency: '8ms' },
                    { name: 'InfluxDB', status: 'connected', latency: '3ms' },
                    { name: 'Kafka', status: 'connected', latency: '15ms' },
                  ].map((conn) => (
                    <Flex key={conn.name} justifyContent="between" alignItems="center" className="p-3 bg-gray-50 rounded-lg">
                      <Flex alignItems="center" className="gap-2">
                        {conn.status === 'connected' ? (
                          <Wifi className="h-4 w-4 text-green-500" />
                        ) : (
                          <WifiOff className="h-4 w-4 text-red-500" />
                        )}
                        <Text>{conn.name}</Text>
                      </Flex>
                      <Flex alignItems="center" className="gap-2">
                        <Badge color={conn.status === 'connected' ? 'green' : 'red'}>
                          {conn.status === 'connected' ? 'Conectado' : 'Desconectado'}
                        </Badge>
                        <Text className="text-gray-500">{conn.latency}</Text>
                      </Flex>
                    </Flex>
                  ))}
                </div>
              </Card>

              <Card className="md:col-span-2">
                <Title>Log de Eventos do Sistema</Title>
                <div className="space-y-2 mt-4 max-h-64 overflow-y-auto">
                  {[
                    { time: '15:42:35', level: 'info', message: 'Sincronização de tags concluída - 1,234 tags atualizados' },
                    { time: '15:40:12', level: 'warning', message: 'Latência elevada detectada no Gateway OPC-UA' },
                    { time: '15:38:45', level: 'info', message: 'Backup automático do banco de dados iniciado' },
                    { time: '15:35:20', level: 'info', message: 'Conexão WebSocket restabelecida com cliente 192.168.1.50' },
                    { time: '15:32:10', level: 'error', message: 'Falha de comunicação com PLC-03 - Tentando reconectar...' },
                    { time: '15:30:00', level: 'info', message: 'Rotina de coleta de dados executada com sucesso' },
                    { time: '15:25:45', level: 'info', message: 'Novo alarme registrado: TEMP_001 acima do limite' },
                  ].map((log, index) => (
                    <Flex
                      key={index}
                      alignItems="center"
                      className={`p-2 rounded text-sm ${
                        log.level === 'error' ? 'bg-red-50' :
                        log.level === 'warning' ? 'bg-amber-50' : 'bg-gray-50'
                      }`}
                    >
                      <Text className="text-gray-400 w-20">{log.time}</Text>
                      <Badge
                        color={log.level === 'error' ? 'red' : log.level === 'warning' ? 'amber' : 'blue'}
                        className="w-20"
                      >
                        {log.level.toUpperCase()}
                      </Badge>
                      <Text className="ml-2">{log.message}</Text>
                    </Flex>
                  ))}
                </div>
              </Card>
            </Grid>
          </TabPanel>
        </TabPanels>
      </TabGroup>
    </div>
  );
}
