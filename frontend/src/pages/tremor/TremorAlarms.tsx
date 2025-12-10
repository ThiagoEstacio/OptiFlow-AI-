/**
 * 🚨 Professional Alarms Page with Tremor
 * ========================================
 *
 * Real-time alarm management with backend integration
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
  Table,
  TableHead,
  TableRow,
  TableHeaderCell,
  TableBody,
  TableCell,
  TabGroup,
  TabList,
  Tab,
  TabPanels,
  TabPanel,
  DateRangePicker,
  DateRangePickerValue,
  SearchSelect,
  SearchSelectItem,
  Button,
} from '@tremor/react';
import { AlertTriangle, AlertCircle, Info, CheckCircle, Bell, Clock, RefreshCw } from 'lucide-react';
import { ProfessionalDonutChart, ProfessionalBarChart } from '../../components/charts/ProfessionalCharts';
import { alarmsApi, AlarmEvent, AlarmStatistics, formatDuration } from '../../services/alarms.api';

interface DisplayAlarm {
  id: string;
  tagId: string;
  tagName: string;
  message: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  status: 'active' | 'acknowledged' | 'resolved';
  timestamp: Date;
  acknowledgedAt?: Date;
  resolvedAt?: Date;
  acknowledgedBy?: string;
  triggerValue?: number;
}

// Convert API alarm to display format
const mapAlarmToDisplay = (alarm: AlarmEvent): DisplayAlarm => ({
  id: alarm.id,
  tagId: alarm.tag_id,
  tagName: alarm.alarm_name || alarm.tag_id,
  message: alarm.message || alarm.description || 'Alarme',
  severity: (alarm.severity?.toLowerCase() || 'medium') as DisplayAlarm['severity'],
  status: alarm.state === 'cleared' ? 'resolved' : alarm.state as DisplayAlarm['status'],
  timestamp: new Date(alarm.trigger_timestamp),
  acknowledgedAt: alarm.acknowledged_at ? new Date(alarm.acknowledged_at) : undefined,
  resolvedAt: alarm.cleared_at ? new Date(alarm.cleared_at) : undefined,
  acknowledgedBy: alarm.acknowledged_by,
  triggerValue: alarm.trigger_value,
});

export const TremorAlarms: React.FC = () => {
  const [alarms, setAlarms] = useState<DisplayAlarm[]>([]);
  const [statistics, setStatistics] = useState<AlarmStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [dateRange, setDateRange] = useState<DateRangePickerValue>({
    from: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
    to: new Date(),
  });
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  // Fetch alarms from API
  const fetchAlarms = useCallback(async () => {
    try {
      const [activeAlarms, historyAlarms, stats] = await Promise.all([
        alarmsApi.getActiveAlarms({ limit: 100 }),
        alarmsApi.getHistory({
          start_date: dateRange.from?.toISOString(),
          end_date: dateRange.to?.toISOString(),
          limit: 200,
        }),
        alarmsApi.getStatistics(),
      ]);

      // Combine active and history, removing duplicates
      const allAlarms = [...activeAlarms, ...historyAlarms];
      const uniqueAlarms = allAlarms.reduce((acc, alarm) => {
        if (!acc.find(a => a.id === alarm.id)) {
          acc.push(alarm);
        }
        return acc;
      }, [] as AlarmEvent[]);

      const displayAlarms = uniqueAlarms
        .map(mapAlarmToDisplay)
        .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());

      setAlarms(displayAlarms);
      setStatistics(stats);
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Error fetching alarms:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [dateRange]);

  // Initial fetch and auto-refresh
  useEffect(() => {
    fetchAlarms();
    const interval = setInterval(fetchAlarms, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, [fetchAlarms]);

  // Manual refresh
  const handleRefresh = () => {
    setRefreshing(true);
    fetchAlarms();
  };

  // Acknowledge alarm
  const handleAcknowledge = async (alarmId: string) => {
    try {
      await alarmsApi.acknowledgeAlarm(alarmId);
      fetchAlarms();
    } catch (error) {
      console.error('Error acknowledging alarm:', error);
    }
  };

  // Clear alarm
  const handleClear = async (alarmId: string) => {
    try {
      await alarmsApi.clearAlarm(alarmId);
      fetchAlarms();
    } catch (error) {
      console.error('Error clearing alarm:', error);
    }
  };

  const activeAlarms = alarms.filter(a => a.status === 'active');
  const acknowledgedAlarms = alarms.filter(a => a.status === 'acknowledged');
  const resolvedAlarms = alarms.filter(a => a.status === 'resolved');

  const filteredAlarms = alarms.filter(alarm => {
    const matchesSeverity = severityFilter === 'all' || alarm.severity === severityFilter;
    const matchesStatus = statusFilter === 'all' || alarm.status === statusFilter;
    const matchesDate = (!dateRange.from || alarm.timestamp >= dateRange.from) &&
                       (!dateRange.to || alarm.timestamp <= dateRange.to);
    return matchesSeverity && matchesStatus && matchesDate;
  });

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'rose';
      case 'high': return 'orange';
      case 'medium': return 'amber';
      default: return 'blue';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical': return <AlertCircle className="w-4 h-4" />;
      case 'high': return <AlertTriangle className="w-4 h-4" />;
      case 'medium': return <Info className="w-4 h-4" />;
      default: return <Info className="w-4 h-4" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'rose';
      case 'acknowledged': return 'amber';
      default: return 'emerald';
    }
  };

  // Chart data from statistics or calculated from alarms
  const severityDistribution = statistics ? [
    { name: 'Crítico', value: statistics.by_severity.critical },
    { name: 'Alto', value: statistics.by_severity.high },
    { name: 'Médio', value: statistics.by_severity.medium },
    { name: 'Baixo', value: statistics.by_severity.low },
  ] : [
    { name: 'Crítico', value: alarms.filter(a => a.severity === 'critical').length },
    { name: 'Alto', value: alarms.filter(a => a.severity === 'high').length },
    { name: 'Médio', value: alarms.filter(a => a.severity === 'medium').length },
    { name: 'Baixo', value: alarms.filter(a => a.severity === 'low').length },
  ];

  const alarmsPerDay = Array.from({ length: 7 }, (_, i) => {
    const date = new Date(Date.now() - (6 - i) * 24 * 60 * 60 * 1000);
    const dayAlarms = alarms.filter(a =>
      a.timestamp.toDateString() === date.toDateString()
    );
    return {
      date: date.toLocaleDateString('pt-BR', { weekday: 'short', day: '2-digit' }),
      Crítico: dayAlarms.filter(a => a.severity === 'critical').length,
      Alto: dayAlarms.filter(a => a.severity === 'high').length,
      Médio: dayAlarms.filter(a => a.severity === 'medium').length,
      Baixo: dayAlarms.filter(a => a.severity === 'low').length,
    };
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
        <Text className="ml-2">Carregando alarmes...</Text>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Title>Central de Alarmes</Title>
          <Text>Gerenciamento de alarmes e histórico de eventos</Text>
          <Text className="text-xs text-gray-400 mt-1">
            Atualizado: {lastUpdated.toLocaleTimeString('pt-BR')}
          </Text>
        </div>
        <div className="flex items-center gap-3">
          <Button
            icon={RefreshCw}
            variant="secondary"
            size="xs"
            onClick={handleRefresh}
            loading={refreshing}
          >
            Atualizar
          </Button>
          <div className="flex items-center gap-2">
            <Bell className="w-5 h-5 text-rose-500 animate-pulse" />
            <Badge color="rose" size="xl">{activeAlarms.length} ativos</Badge>
          </div>
        </div>
      </div>

      {/* Status Cards */}
      <Grid numItemsSm={2} numItemsLg={4} className="gap-6">
        <Card decoration="top" decorationColor="rose">
          <Flex justifyContent="between" alignItems="center">
            <div>
              <Text>Ativos</Text>
              <Metric>{statistics?.active ?? activeAlarms.length}</Metric>
            </div>
            <AlertCircle className="w-10 h-10 text-rose-500" />
          </Flex>
          <Text className="mt-2 text-sm text-gray-500">
            {statistics?.by_severity.critical ?? activeAlarms.filter(a => a.severity === 'critical').length} críticos
          </Text>
        </Card>

        <Card decoration="top" decorationColor="amber">
          <Flex justifyContent="between" alignItems="center">
            <div>
              <Text>Reconhecidos</Text>
              <Metric>{statistics?.acknowledged ?? acknowledgedAlarms.length}</Metric>
            </div>
            <Bell className="w-10 h-10 text-amber-500" />
          </Flex>
          <Text className="mt-2 text-sm text-gray-500">
            Aguardando resolução
          </Text>
        </Card>

        <Card decoration="top" decorationColor="emerald">
          <Flex justifyContent="between" alignItems="center">
            <div>
              <Text>Resolvidos (24h)</Text>
              <Metric>
                {resolvedAlarms.filter(a =>
                  a.resolvedAt && a.resolvedAt > new Date(Date.now() - 24 * 60 * 60 * 1000)
                ).length}
              </Metric>
            </div>
            <CheckCircle className="w-10 h-10 text-emerald-500" />
          </Flex>
          <Text className="mt-2 text-sm text-gray-500">
            Tratados com sucesso
          </Text>
        </Card>

        <Card decoration="top" decorationColor="blue">
          <Flex justifyContent="between" alignItems="center">
            <div>
              <Text>MTTR Médio</Text>
              <Metric>
                {statistics?.average_duration_minutes
                  ? formatDuration(statistics.average_duration_minutes * 60)
                  : '-- min'}
              </Metric>
            </div>
            <Clock className="w-10 h-10 text-blue-500" />
          </Flex>
          <Text className="mt-2 text-sm text-gray-500">
            Tempo médio de resolução
          </Text>
        </Card>
      </Grid>

      {/* Charts - Professional Components */}
      <Grid numItemsSm={1} numItemsLg={2} className="gap-6">
        <Card>
          <Title>Distribuição por Severidade</Title>
          <div className="mt-4">
            <ProfessionalDonutChart
              data={severityDistribution}
              colors={['#f43f5e', '#f97316', '#f59e0b', '#3b82f6']}
              height={200}
              showLegend={true}
            />
          </div>
        </Card>

        <Card>
          <Title>Alarmes por Dia</Title>
          <div className="mt-4">
            <ProfessionalBarChart
              data={alarmsPerDay}
              xAxisKey="date"
              categories={['Crítico', 'Alto', 'Médio', 'Baixo']}
              colors={['#f43f5e', '#f97316', '#f59e0b', '#3b82f6']}
              height={200}
              stacked={true}
              showLegend={true}
            />
          </div>
        </Card>
      </Grid>

      {/* Filters */}
      <Card>
        <Flex justifyContent="start" className="gap-4 flex-wrap">
          <DateRangePicker
            value={dateRange}
            onValueChange={setDateRange}
            selectPlaceholder="Período"
            className="max-w-xs"
          />
          <SearchSelect
            value={severityFilter}
            onValueChange={setSeverityFilter}
            placeholder="Severidade"
            className="max-w-xs"
          >
            <SearchSelectItem value="all">Todas</SearchSelectItem>
            <SearchSelectItem value="critical">Crítico</SearchSelectItem>
            <SearchSelectItem value="high">Alto</SearchSelectItem>
            <SearchSelectItem value="medium">Médio</SearchSelectItem>
            <SearchSelectItem value="low">Baixo</SearchSelectItem>
          </SearchSelect>
          <SearchSelect
            value={statusFilter}
            onValueChange={setStatusFilter}
            placeholder="Status"
            className="max-w-xs"
          >
            <SearchSelectItem value="all">Todos</SearchSelectItem>
            <SearchSelectItem value="active">Ativos</SearchSelectItem>
            <SearchSelectItem value="acknowledged">Reconhecidos</SearchSelectItem>
            <SearchSelectItem value="resolved">Resolvidos</SearchSelectItem>
          </SearchSelect>
        </Flex>
      </Card>

      {/* Alarms Table */}
      <Card>
        <TabGroup>
          <TabList>
            <Tab>Todos ({filteredAlarms.length})</Tab>
            <Tab>Ativos ({activeAlarms.length})</Tab>
            <Tab>Histórico ({resolvedAlarms.length})</Tab>
          </TabList>
          <TabPanels>
            {/* All Alarms */}
            <TabPanel>
              <Table className="mt-4">
                <TableHead>
                  <TableRow>
                    <TableHeaderCell>ID</TableHeaderCell>
                    <TableHeaderCell>Tag</TableHeaderCell>
                    <TableHeaderCell>Mensagem</TableHeaderCell>
                    <TableHeaderCell>Valor</TableHeaderCell>
                    <TableHeaderCell>Severidade</TableHeaderCell>
                    <TableHeaderCell>Status</TableHeaderCell>
                    <TableHeaderCell>Data/Hora</TableHeaderCell>
                    <TableHeaderCell>Ações</TableHeaderCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredAlarms.slice(0, 20).map((alarm) => (
                    <TableRow key={alarm.id} className="hover:bg-gray-50">
                      <TableCell>
                        <Text className="font-mono text-xs">{alarm.id.slice(0, 8)}</Text>
                      </TableCell>
                      <TableCell>
                        <div>
                          <Text className="font-medium">{alarm.tagId}</Text>
                          <Text className="text-xs text-gray-500">{alarm.tagName}</Text>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Text>{alarm.message}</Text>
                      </TableCell>
                      <TableCell>
                        <Text className="font-mono">
                          {alarm.triggerValue?.toFixed(2) ?? '-'}
                        </Text>
                      </TableCell>
                      <TableCell>
                        <Badge color={getSeverityColor(alarm.severity)} icon={() => getSeverityIcon(alarm.severity)}>
                          {alarm.severity === 'critical' ? 'Crítico' :
                           alarm.severity === 'high' ? 'Alto' :
                           alarm.severity === 'medium' ? 'Médio' : 'Baixo'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge color={getStatusColor(alarm.status)}>
                          {alarm.status === 'active' ? 'Ativo' :
                           alarm.status === 'acknowledged' ? 'Reconhecido' : 'Resolvido'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Text className="text-sm">
                          {alarm.timestamp.toLocaleDateString('pt-BR')} {alarm.timestamp.toLocaleTimeString('pt-BR')}
                        </Text>
                      </TableCell>
                      <TableCell>
                        <Flex justifyContent="start" className="gap-2">
                          {alarm.status === 'active' && (
                            <Button size="xs" variant="secondary" onClick={() => handleAcknowledge(alarm.id)}>
                              Reconhecer
                            </Button>
                          )}
                          {alarm.status === 'acknowledged' && (
                            <Button size="xs" color="emerald" onClick={() => handleClear(alarm.id)}>
                              Resolver
                            </Button>
                          )}
                        </Flex>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              {filteredAlarms.length === 0 && (
                <Text className="text-center text-gray-500 py-8">
                  Nenhum alarme encontrado com os filtros selecionados
                </Text>
              )}
            </TabPanel>

            {/* Active Alarms */}
            <TabPanel>
              <Table className="mt-4">
                <TableHead>
                  <TableRow>
                    <TableHeaderCell>Tag</TableHeaderCell>
                    <TableHeaderCell>Mensagem</TableHeaderCell>
                    <TableHeaderCell>Valor</TableHeaderCell>
                    <TableHeaderCell>Severidade</TableHeaderCell>
                    <TableHeaderCell>Desde</TableHeaderCell>
                    <TableHeaderCell>Ação</TableHeaderCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {activeAlarms.map((alarm) => (
                    <TableRow key={alarm.id} className="hover:bg-gray-50">
                      <TableCell>
                        <div>
                          <Text className="font-medium">{alarm.tagId}</Text>
                          <Text className="text-xs text-gray-500">{alarm.tagName}</Text>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Text>{alarm.message}</Text>
                      </TableCell>
                      <TableCell>
                        <Text className="font-mono text-rose-600 font-bold">
                          {alarm.triggerValue?.toFixed(2) ?? '-'}
                        </Text>
                      </TableCell>
                      <TableCell>
                        <Badge color={getSeverityColor(alarm.severity)} icon={() => getSeverityIcon(alarm.severity)}>
                          {alarm.severity === 'critical' ? 'Crítico' :
                           alarm.severity === 'high' ? 'Alto' :
                           alarm.severity === 'medium' ? 'Médio' : 'Baixo'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Text className="text-sm">
                          {alarm.timestamp.toLocaleTimeString('pt-BR')}
                        </Text>
                      </TableCell>
                      <TableCell>
                        <Button size="xs" variant="secondary" onClick={() => handleAcknowledge(alarm.id)}>
                          Reconhecer
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              {activeAlarms.length === 0 && (
                <div className="text-center py-12">
                  <CheckCircle className="w-12 h-12 text-emerald-500 mx-auto mb-4" />
                  <Text className="text-gray-500">Nenhum alarme ativo</Text>
                </div>
              )}
            </TabPanel>

            {/* History */}
            <TabPanel>
              <Table className="mt-4">
                <TableHead>
                  <TableRow>
                    <TableHeaderCell>Tag</TableHeaderCell>
                    <TableHeaderCell>Mensagem</TableHeaderCell>
                    <TableHeaderCell>Severidade</TableHeaderCell>
                    <TableHeaderCell>Início</TableHeaderCell>
                    <TableHeaderCell>Resolução</TableHeaderCell>
                    <TableHeaderCell>Duração</TableHeaderCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {resolvedAlarms.slice(0, 20).map((alarm) => {
                    const duration = alarm.resolvedAt
                      ? Math.round((alarm.resolvedAt.getTime() - alarm.timestamp.getTime()) / 1000)
                      : null;
                    return (
                      <TableRow key={alarm.id} className="hover:bg-gray-50">
                        <TableCell>
                          <div>
                            <Text className="font-medium">{alarm.tagId}</Text>
                            <Text className="text-xs text-gray-500">{alarm.tagName}</Text>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Text>{alarm.message}</Text>
                        </TableCell>
                        <TableCell>
                          <Badge color={getSeverityColor(alarm.severity)}>
                            {alarm.severity === 'critical' ? 'Crítico' :
                             alarm.severity === 'high' ? 'Alto' :
                             alarm.severity === 'medium' ? 'Médio' : 'Baixo'}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Text className="text-sm">
                            {alarm.timestamp.toLocaleDateString('pt-BR')} {alarm.timestamp.toLocaleTimeString('pt-BR')}
                          </Text>
                        </TableCell>
                        <TableCell>
                          <Text className="text-sm">
                            {alarm.resolvedAt?.toLocaleTimeString('pt-BR') ?? '-'}
                          </Text>
                        </TableCell>
                        <TableCell>
                          <Text className="text-sm text-emerald-600">
                            {duration ? formatDuration(duration) : '-'}
                          </Text>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
              {resolvedAlarms.length === 0 && (
                <Text className="text-center text-gray-500 py-8">
                  Nenhum alarme resolvido no período selecionado
                </Text>
              )}
            </TabPanel>
          </TabPanels>
        </TabGroup>
      </Card>
    </div>
  );
};

export default TremorAlarms;
