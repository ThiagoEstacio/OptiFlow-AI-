/**
 * 📊 TremorReports - Professional Reports Page
 * =============================================
 *
 * Industrial reports management with:
 * - Report templates library
 * - Scheduled report generation
 * - Export functionality (PDF, Excel, CSV)
 * - Custom report builder
 * - Historical report archive
 */
import React, { useState } from 'react';
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
  TextInput,
  TabGroup,
  TabList,
  Tab,
  TabPanels,
  TabPanel,
  Grid,
  Metric,
  Flex,
  ProgressBar,
} from '@tremor/react';
import { ProfessionalDonutChart } from '../../components/charts/ProfessionalCharts';
import {
  FileText,
  Download,
  Calendar,
  Clock,
  Mail,
  Plus,
  Search,
  Filter,
  FileSpreadsheet,
  FileType,
  Printer,
  Eye,
  Trash2,
  Edit,
  Share2,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  FolderOpen,
  Star,
  BarChart3,
  PieChart,
  TrendingUp,
  Activity,
  Zap,
  Settings,
} from 'lucide-react';

// Report Templates
const reportTemplates = [
  {
    id: 1,
    name: 'Relatório Diário de Produção',
    description: 'Resumo completo da produção diária com KPIs principais',
    category: 'production',
    icon: BarChart3,
    frequency: 'Diário',
    format: 'PDF',
    starred: true,
  },
  {
    id: 2,
    name: 'Análise de OEE Semanal',
    description: 'Análise detalhada de OEE com breakdown por equipamento',
    category: 'oee',
    icon: PieChart,
    frequency: 'Semanal',
    format: 'Excel',
    starred: true,
  },
  {
    id: 3,
    name: 'Consumo Energético Mensal',
    description: 'Relatório de consumo de energia com análise de custos',
    category: 'energy',
    icon: Zap,
    frequency: 'Mensal',
    format: 'PDF',
    starred: false,
  },
  {
    id: 4,
    name: 'Histórico de Alarmes',
    description: 'Registro completo de alarmes com análise de causas',
    category: 'alarms',
    icon: AlertCircle,
    frequency: 'Sob demanda',
    format: 'Excel',
    starred: false,
  },
  {
    id: 5,
    name: 'Tendências de Processo',
    description: 'Análise de tendências com previsões ML',
    category: 'analytics',
    icon: TrendingUp,
    frequency: 'Semanal',
    format: 'PDF',
    starred: true,
  },
  {
    id: 6,
    name: 'Relatório de Manutenção',
    description: 'Status de manutenção preventiva e corretiva',
    category: 'maintenance',
    icon: Settings,
    frequency: 'Mensal',
    format: 'PDF',
    starred: false,
  },
];

// Generated Reports
const generatedReports = [
  {
    id: 1,
    name: 'Produção_Diária_2024-01-15',
    template: 'Relatório Diário de Produção',
    generatedAt: '2024-01-15 08:00',
    size: '2.4 MB',
    format: 'PDF',
    status: 'completed',
    generatedBy: 'Sistema (Agendado)',
  },
  {
    id: 2,
    name: 'OEE_Semanal_S02_2024',
    template: 'Análise de OEE Semanal',
    generatedAt: '2024-01-14 23:00',
    size: '5.1 MB',
    format: 'Excel',
    status: 'completed',
    generatedBy: 'Sistema (Agendado)',
  },
  {
    id: 3,
    name: 'Energia_Dezembro_2023',
    template: 'Consumo Energético Mensal',
    generatedAt: '2024-01-02 06:00',
    size: '3.8 MB',
    format: 'PDF',
    status: 'completed',
    generatedBy: 'Sistema (Agendado)',
  },
  {
    id: 4,
    name: 'Alarmes_Críticos_Jan2024',
    template: 'Histórico de Alarmes',
    generatedAt: '2024-01-15 10:30',
    size: '1.2 MB',
    format: 'Excel',
    status: 'processing',
    generatedBy: 'João Silva',
  },
  {
    id: 5,
    name: 'Tendências_Q4_2023',
    template: 'Tendências de Processo',
    generatedAt: '2024-01-10 14:00',
    size: '4.5 MB',
    format: 'PDF',
    status: 'completed',
    generatedBy: 'Maria Santos',
  },
];

// Scheduled Reports
const scheduledReports = [
  {
    id: 1,
    template: 'Relatório Diário de Produção',
    schedule: 'Diário às 08:00',
    nextRun: '2024-01-16 08:00',
    recipients: ['gerencia@empresa.com', 'producao@empresa.com'],
    enabled: true,
  },
  {
    id: 2,
    template: 'Análise de OEE Semanal',
    schedule: 'Domingos às 23:00',
    nextRun: '2024-01-21 23:00',
    recipients: ['diretoria@empresa.com'],
    enabled: true,
  },
  {
    id: 3,
    template: 'Consumo Energético Mensal',
    schedule: 'Dia 1 de cada mês às 06:00',
    nextRun: '2024-02-01 06:00',
    recipients: ['financeiro@empresa.com', 'engenharia@empresa.com'],
    enabled: true,
  },
  {
    id: 4,
    template: 'Relatório de Manutenção',
    schedule: 'Dia 15 de cada mês às 07:00',
    nextRun: '2024-02-15 07:00',
    recipients: ['manutencao@empresa.com'],
    enabled: false,
  },
];

// Report categories for donut chart
const reportCategories = [
  { name: 'Produção', value: 45 },
  { name: 'OEE', value: 25 },
  { name: 'Energia', value: 15 },
  { name: 'Manutenção', value: 10 },
  { name: 'Outros', value: 5 },
];

export default function TremorReports() {
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [selectedTab, setSelectedTab] = useState(0);

  const filteredTemplates = reportTemplates.filter((template) => {
    const matchesSearch = template.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      template.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = categoryFilter === 'all' || template.category === categoryFilter;
    return matchesSearch && matchesCategory;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge color="green" icon={CheckCircle}>Concluído</Badge>;
      case 'processing':
        return <Badge color="yellow" icon={RefreshCw}>Processando</Badge>;
      case 'failed':
        return <Badge color="red" icon={AlertCircle}>Falhou</Badge>;
      default:
        return <Badge color="gray">Desconhecido</Badge>;
    }
  };

  const getFormatIcon = (format: string) => {
    switch (format) {
      case 'PDF':
        return <FileType className="h-4 w-4 text-red-500" />;
      case 'Excel':
        return <FileSpreadsheet className="h-4 w-4 text-green-500" />;
      default:
        return <FileText className="h-4 w-4 text-gray-500" />;
    }
  };

  return (
    <div className="p-6 space-y-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <Title className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <FileText className="h-8 w-8 text-blue-600" />
            Central de Relatórios
          </Title>
          <Text className="text-gray-500 mt-1">
            Geração, agendamento e gerenciamento de relatórios industriais
          </Text>
        </div>
        <div className="flex gap-2">
          <Button icon={Plus} color="blue">
            Novo Relatório
          </Button>
          <Button icon={Calendar} variant="secondary">
            Agendar
          </Button>
        </div>
      </div>

      {/* Quick Stats */}
      <Grid numItems={1} numItemsSm={2} numItemsMd={4} className="gap-4">
        <Card decoration="top" decorationColor="blue">
          <Flex alignItems="start">
            <div>
              <Text>Relatórios Gerados</Text>
              <Metric>1,234</Metric>
              <Text className="text-green-600 text-sm mt-1">+12% este mês</Text>
            </div>
            <FileText className="h-10 w-10 text-blue-600" />
          </Flex>
        </Card>

        <Card decoration="top" decorationColor="green">
          <Flex alignItems="start">
            <div>
              <Text>Agendados Ativos</Text>
              <Metric>8</Metric>
              <Text className="text-gray-500 text-sm mt-1">Próximo: 08:00</Text>
            </div>
            <Clock className="h-10 w-10 text-green-600" />
          </Flex>
        </Card>

        <Card decoration="top" decorationColor="amber">
          <Flex alignItems="start">
            <div>
              <Text>Downloads Hoje</Text>
              <Metric>47</Metric>
              <Text className="text-gray-500 text-sm mt-1">5 usuários únicos</Text>
            </div>
            <Download className="h-10 w-10 text-amber-600" />
          </Flex>
        </Card>

        <Card decoration="top" decorationColor="purple">
          <Flex alignItems="start">
            <div>
              <Text>Espaço Utilizado</Text>
              <Metric>2.4 GB</Metric>
              <ProgressBar value={48} color="purple" className="mt-2" />
            </div>
            <FolderOpen className="h-10 w-10 text-purple-600" />
          </Flex>
        </Card>
      </Grid>

      {/* Main Content */}
      <TabGroup index={selectedTab} onIndexChange={setSelectedTab}>
        <TabList className="mt-4">
          <Tab icon={FileText}>Templates</Tab>
          <Tab icon={FolderOpen}>Relatórios Gerados</Tab>
          <Tab icon={Calendar}>Agendamentos</Tab>
          <Tab icon={BarChart3}>Estatísticas</Tab>
        </TabList>

        <TabPanels>
          {/* Templates Tab */}
          <TabPanel>
            <Card className="mt-4">
              <div className="flex flex-col md:flex-row gap-4 mb-6">
                <div className="flex-1">
                  <TextInput
                    icon={Search}
                    placeholder="Buscar templates..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </div>
                <Select
                  value={categoryFilter}
                  onValueChange={setCategoryFilter}
                  className="w-48"
                >
                  <SelectItem value="all">Todas Categorias</SelectItem>
                  <SelectItem value="production">Produção</SelectItem>
                  <SelectItem value="oee">OEE</SelectItem>
                  <SelectItem value="energy">Energia</SelectItem>
                  <SelectItem value="alarms">Alarmes</SelectItem>
                  <SelectItem value="analytics">Analytics</SelectItem>
                  <SelectItem value="maintenance">Manutenção</SelectItem>
                </Select>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredTemplates.map((template) => (
                  <Card
                    key={template.id}
                    className="hover:shadow-lg transition-shadow cursor-pointer border border-gray-200"
                  >
                    <Flex alignItems="start" className="gap-3">
                      <div className="p-3 bg-blue-50 rounded-lg">
                        <template.icon className="h-6 w-6 text-blue-600" />
                      </div>
                      <div className="flex-1">
                        <Flex justifyContent="between" alignItems="start">
                          <Title className="text-base">{template.name}</Title>
                          {template.starred && <Star className="h-4 w-4 text-yellow-500 fill-current" />}
                        </Flex>
                        <Text className="text-sm text-gray-500 mt-1 line-clamp-2">
                          {template.description}
                        </Text>
                        <Flex className="mt-3 gap-2">
                          <Badge color="gray">{template.frequency}</Badge>
                          <Badge color="blue">{template.format}</Badge>
                        </Flex>
                        <Flex className="mt-3 gap-2">
                          <Button size="xs" icon={Eye}>
                            Visualizar
                          </Button>
                          <Button size="xs" variant="secondary" icon={Download}>
                            Gerar
                          </Button>
                        </Flex>
                      </div>
                    </Flex>
                  </Card>
                ))}
              </div>
            </Card>
          </TabPanel>

          {/* Generated Reports Tab */}
          <TabPanel>
            <Card className="mt-4">
              <Flex justifyContent="between" className="mb-4">
                <Title>Relatórios Gerados</Title>
                <div className="flex gap-2">
                  <TextInput
                    icon={Search}
                    placeholder="Buscar..."
                    className="w-64"
                  />
                  <Button icon={Filter} variant="secondary">
                    Filtrar
                  </Button>
                </div>
              </Flex>

              <Table>
                <TableHead>
                  <TableRow>
                    <TableHeaderCell>Nome</TableHeaderCell>
                    <TableHeaderCell>Template</TableHeaderCell>
                    <TableHeaderCell>Gerado em</TableHeaderCell>
                    <TableHeaderCell>Tamanho</TableHeaderCell>
                    <TableHeaderCell>Formato</TableHeaderCell>
                    <TableHeaderCell>Status</TableHeaderCell>
                    <TableHeaderCell>Ações</TableHeaderCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {generatedReports.map((report) => (
                    <TableRow key={report.id}>
                      <TableCell>
                        <Flex alignItems="center" className="gap-2">
                          {getFormatIcon(report.format)}
                          <Text className="font-medium">{report.name}</Text>
                        </Flex>
                      </TableCell>
                      <TableCell>
                        <Text className="text-gray-500">{report.template}</Text>
                      </TableCell>
                      <TableCell>
                        <Text>{report.generatedAt}</Text>
                        <Text className="text-xs text-gray-400">{report.generatedBy}</Text>
                      </TableCell>
                      <TableCell>
                        <Text>{report.size}</Text>
                      </TableCell>
                      <TableCell>
                        <Badge color={report.format === 'PDF' ? 'red' : 'green'}>
                          {report.format}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {getStatusBadge(report.status)}
                      </TableCell>
                      <TableCell>
                        <Flex className="gap-1">
                          <button className="p-1.5 hover:bg-gray-100 rounded" title="Download">
                            <Download className="h-4 w-4 text-gray-600" />
                          </button>
                          <button className="p-1.5 hover:bg-gray-100 rounded" title="Visualizar">
                            <Eye className="h-4 w-4 text-gray-600" />
                          </button>
                          <button className="p-1.5 hover:bg-gray-100 rounded" title="Compartilhar">
                            <Share2 className="h-4 w-4 text-gray-600" />
                          </button>
                          <button className="p-1.5 hover:bg-gray-100 rounded" title="Imprimir">
                            <Printer className="h-4 w-4 text-gray-600" />
                          </button>
                          <button className="p-1.5 hover:bg-gray-100 rounded" title="Excluir">
                            <Trash2 className="h-4 w-4 text-red-500" />
                          </button>
                        </Flex>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Card>
          </TabPanel>

          {/* Scheduled Reports Tab */}
          <TabPanel>
            <Card className="mt-4">
              <Flex justifyContent="between" className="mb-4">
                <Title>Relatórios Agendados</Title>
                <Button icon={Plus} color="blue">
                  Novo Agendamento
                </Button>
              </Flex>

              <Table>
                <TableHead>
                  <TableRow>
                    <TableHeaderCell>Template</TableHeaderCell>
                    <TableHeaderCell>Agendamento</TableHeaderCell>
                    <TableHeaderCell>Próxima Execução</TableHeaderCell>
                    <TableHeaderCell>Destinatários</TableHeaderCell>
                    <TableHeaderCell>Status</TableHeaderCell>
                    <TableHeaderCell>Ações</TableHeaderCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {scheduledReports.map((schedule) => (
                    <TableRow key={schedule.id}>
                      <TableCell>
                        <Flex alignItems="center" className="gap-2">
                          <Calendar className="h-4 w-4 text-blue-600" />
                          <Text className="font-medium">{schedule.template}</Text>
                        </Flex>
                      </TableCell>
                      <TableCell>
                        <Text>{schedule.schedule}</Text>
                      </TableCell>
                      <TableCell>
                        <Flex alignItems="center" className="gap-1">
                          <Clock className="h-4 w-4 text-gray-400" />
                          <Text>{schedule.nextRun}</Text>
                        </Flex>
                      </TableCell>
                      <TableCell>
                        <Flex alignItems="center" className="gap-1">
                          <Mail className="h-4 w-4 text-gray-400" />
                          <Text className="text-sm">{schedule.recipients.length} destinatário(s)</Text>
                        </Flex>
                      </TableCell>
                      <TableCell>
                        <Badge color={schedule.enabled ? 'green' : 'gray'}>
                          {schedule.enabled ? 'Ativo' : 'Inativo'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Flex className="gap-1">
                          <button className="p-1.5 hover:bg-gray-100 rounded" title="Editar">
                            <Edit className="h-4 w-4 text-gray-600" />
                          </button>
                          <button className="p-1.5 hover:bg-gray-100 rounded" title="Executar Agora">
                            <RefreshCw className="h-4 w-4 text-blue-600" />
                          </button>
                          <button className="p-1.5 hover:bg-gray-100 rounded" title="Excluir">
                            <Trash2 className="h-4 w-4 text-red-500" />
                          </button>
                        </Flex>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Card>
          </TabPanel>

          {/* Statistics Tab */}
          <TabPanel>
            <Grid numItems={1} numItemsMd={2} className="gap-4 mt-4">
              <Card>
                <Title>Relatórios por Categoria</Title>
                <Text className="text-gray-500">Distribuição de relatórios gerados</Text>
                <div className="mt-4">
                  <ProfessionalDonutChart
                    data={reportCategories}
                    colors={['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#94a3b8']}
                    height={256}
                    showLegend={true}
                  />
                </div>
              </Card>

              <Card>
                <Title>Métricas de Uso</Title>
                <div className="space-y-4 mt-4">
                  <div>
                    <Flex justifyContent="between">
                      <Text>Relatórios PDF</Text>
                      <Text className="font-medium">756</Text>
                    </Flex>
                    <ProgressBar value={62} color="red" className="mt-2" />
                  </div>
                  <div>
                    <Flex justifyContent="between">
                      <Text>Relatórios Excel</Text>
                      <Text className="font-medium">398</Text>
                    </Flex>
                    <ProgressBar value={32} color="green" className="mt-2" />
                  </div>
                  <div>
                    <Flex justifyContent="between">
                      <Text>Relatórios CSV</Text>
                      <Text className="font-medium">80</Text>
                    </Flex>
                    <ProgressBar value={6} color="blue" className="mt-2" />
                  </div>
                  <div className="pt-4 border-t">
                    <Flex justifyContent="between">
                      <Text>Taxa de Sucesso</Text>
                      <Text className="font-medium text-green-600">99.2%</Text>
                    </Flex>
                    <ProgressBar value={99.2} color="green" className="mt-2" />
                  </div>
                  <div>
                    <Flex justifyContent="between">
                      <Text>Tempo Médio de Geração</Text>
                      <Text className="font-medium">12.4 segundos</Text>
                    </Flex>
                  </div>
                </div>
              </Card>

              <Card className="md:col-span-2">
                <Title>Atividade Recente</Title>
                <div className="space-y-3 mt-4">
                  {[
                    { action: 'Relatório gerado', report: 'Produção_Diária_2024-01-15', user: 'Sistema', time: '5 min atrás', color: 'green' },
                    { action: 'Download realizado', report: 'OEE_Semanal_S02_2024', user: 'João Silva', time: '15 min atrás', color: 'blue' },
                    { action: 'Agendamento criado', report: 'Análise de Custos', user: 'Maria Santos', time: '1h atrás', color: 'purple' },
                    { action: 'Relatório compartilhado', report: 'Energia_Dezembro_2023', user: 'Carlos Lima', time: '2h atrás', color: 'amber' },
                    { action: 'Template modificado', report: 'Histórico de Alarmes', user: 'Admin', time: '3h atrás', color: 'gray' },
                  ].map((activity, index) => (
                    <Flex key={index} alignItems="center" className="p-3 bg-gray-50 rounded-lg">
                      <div className={`w-2 h-2 rounded-full mr-3 bg-${activity.color}-500`} />
                      <div className="flex-1">
                        <Text className="font-medium">{activity.action}</Text>
                        <Text className="text-sm text-gray-500">{activity.report}</Text>
                      </div>
                      <div className="text-right">
                        <Text className="text-sm text-gray-600">{activity.user}</Text>
                        <Text className="text-xs text-gray-400">{activity.time}</Text>
                      </div>
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
