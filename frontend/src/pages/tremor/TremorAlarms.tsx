/**
 * 🚨 Professional Alarms Page with Tremor
 * ========================================
 *
 * Alarm management and event history
 */
import React, { useState } from 'react';
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
import { AlertTriangle, AlertCircle, Info, CheckCircle, Bell, Clock } from 'lucide-react';
import { ProfessionalDonutChart, ProfessionalBarChart } from '../../components/charts/ProfessionalCharts';

interface Alarm {
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
}

// Mock alarms data
const generateAlarms = (): Alarm[] => {
  const severities: Alarm['severity'][] = ['critical', 'high', 'medium', 'low'];
  const statuses: Alarm['status'][] = ['active', 'acknowledged', 'resolved'];
  const messages = [
    'Alta temperatura detectada',
    'Pressão acima do limite',
    'Vibração excessiva',
    'Nível crítico atingido',
    'Falha de comunicação',
    'Vazão abaixo do esperado',
    'Tensão fora do range',
    'Corrente anormal',
  ];

  return Array.from({ length: 50 }, (_, i) => {
    const timestamp = new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000);
    const status = statuses[Math.floor(Math.random() * statuses.length)];

    return {
      id: `ALM_${String(i + 1).padStart(4, '0')}`,
      tagId: `TAG_${String(Math.floor(Math.random() * 100)).padStart(3, '0')}`,
      tagName: `Equipamento ${Math.floor(Math.random() * 20) + 1}`,
      message: messages[Math.floor(Math.random() * messages.length)],
      severity: severities[Math.floor(Math.random() * severities.length)],
      status,
      timestamp,
      acknowledgedAt: status !== 'active' ? new Date(timestamp.getTime() + Math.random() * 60 * 60 * 1000) : undefined,
      resolvedAt: status === 'resolved' ? new Date(timestamp.getTime() + Math.random() * 2 * 60 * 60 * 1000) : undefined,
      acknowledgedBy: status !== 'active' ? 'Operador' : undefined,
    };
  }).sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
};

export const TremorAlarms: React.FC = () => {
  const [alarms] = useState<Alarm[]>(generateAlarms());
  const [dateRange, setDateRange] = useState<DateRangePickerValue>({
    from: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
    to: new Date(),
  });
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');

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

  // Chart data
  const severityDistribution = [
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Title>Central de Alarmes</Title>
          <Text>Gerenciamento de alarmes e histórico de eventos</Text>
        </div>
        <div className="flex items-center gap-2">
          <Bell className="w-5 h-5 text-rose-500 animate-pulse" />
          <Badge color="rose" size="xl">{activeAlarms.length} ativos</Badge>
        </div>
      </div>

      {/* Status Cards */}
      <Grid numItemsSm={2} numItemsLg={4} className="gap-6">
        <Card decoration="top" decorationColor="rose">
          <Flex justifyContent="between" alignItems="center">
            <div>
              <Text>Ativos</Text>
              <Metric>{activeAlarms.length}</Metric>
            </div>
            <AlertCircle className="w-10 h-10 text-rose-500" />
          </Flex>
          <Text className="mt-2 text-sm text-gray-500">
            {activeAlarms.filter(a => a.severity === 'critical').length} críticos
          </Text>
        </Card>

        <Card decoration="top" decorationColor="amber">
          <Flex justifyContent="between" alignItems="center">
            <div>
              <Text>Reconhecidos</Text>
              <Metric>{acknowledgedAlarms.length}</Metric>
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
              <Metric>23 min</Metric>
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
            <Tab>Histórico</Tab>
          </TabList>
          <TabPanels>
            <TabPanel>
              <Table className="mt-4">
                <TableHead>
                  <TableRow>
                    <TableHeaderCell>ID</TableHeaderCell>
                    <TableHeaderCell>Tag</TableHeaderCell>
                    <TableHeaderCell>Mensagem</TableHeaderCell>
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
                        <Text className="font-mono">{alarm.id}</Text>
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
                            <Button size="xs" variant="secondary">
                              Reconhecer
                            </Button>
                          )}
                          {alarm.status === 'acknowledged' && (
                            <Button size="xs" color="emerald">
                              Resolver
                            </Button>
                          )}
                        </Flex>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TabPanel>
            <TabPanel>
              <Text className="mt-4 text-center text-gray-500">
                Visualização de alarmes ativos
              </Text>
            </TabPanel>
            <TabPanel>
              <Text className="mt-4 text-center text-gray-500">
                Histórico completo de alarmes
              </Text>
            </TabPanel>
          </TabPanels>
        </TabGroup>
      </Card>
    </div>
  );
};

export default TremorAlarms;
