/**
 * 📊 Dashboards List Page - Tremor Professional
 * ==============================================
 *
 * List, create, and manage user dashboards
 */
import React, { useState, useEffect } from 'react';
import {
  Card,
  Title,
  Text,
  Flex,
  Grid,
  Badge,
  Button,
  TextInput,
  Select,
  SelectItem,
} from '@tremor/react';
import {
  LayoutDashboard,
  Plus,
  Search,
  Eye,
  Pencil,
  Trash2,
  Copy,
  Share2,
  Clock,
  Calendar,
  Filter,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../../api/client';

interface Dashboard {
  id: string;
  name: string;
  description: string;
  module: string;
  is_public: boolean;
  is_template: boolean;
  view_count: number;
  widget_count: number;
  last_viewed_at: string;
  created_at: string;
  updated_at: string;
}

const moduleColors: Record<string, string> = {
  operations: 'blue',
  maintenance: 'orange',
  quality: 'green',
  executive: 'purple',
  energy: 'yellow',
  analytics: 'cyan',
};

const moduleLabels: Record<string, string> = {
  operations: 'Operações',
  maintenance: 'Manutenção',
  quality: 'Qualidade',
  executive: 'Executivo',
  energy: 'Energia',
  analytics: 'Analytics',
};

export const TremorDashboardsList: React.FC = () => {
  const navigate = useNavigate();
  const [dashboards, setDashboards] = useState<Dashboard[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [moduleFilter, setModuleFilter] = useState('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newDashboard, setNewDashboard] = useState({ name: '', description: '', module: 'operations' });

  useEffect(() => {
    fetchDashboards();
  }, []);

  const fetchDashboards = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/api/v1/dashboards');
      setDashboards(response.data || []);
    } catch (error) {
      console.error('Error fetching dashboards:', error);
      // Fallback to empty list
      setDashboards([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateDashboard = async () => {
    try {
      const response = await apiClient.post('/api/v1/dashboards', {
        name: newDashboard.name,
        description: newDashboard.description,
        module: newDashboard.module,
        is_public: false,
        layout: [],
      });
      setDashboards([...dashboards, response.data]);
      setShowCreateModal(false);
      setNewDashboard({ name: '', description: '', module: 'operations' });
    } catch (error) {
      console.error('Error creating dashboard:', error);
    }
  };

  const handleDeleteDashboard = async (id: string) => {
    if (!confirm('Tem certeza que deseja excluir este dashboard?')) return;
    try {
      await apiClient.delete(`/api/v1/dashboards/${id}`);
      setDashboards(dashboards.filter(d => d.id !== id));
    } catch (error) {
      console.error('Error deleting dashboard:', error);
    }
  };

  const handleCloneDashboard = async (id: string) => {
    try {
      const response = await apiClient.post(`/api/v1/dashboards/${id}/clone`);
      setDashboards([...dashboards, response.data]);
    } catch (error) {
      console.error('Error cloning dashboard:', error);
    }
  };

  const filteredDashboards = dashboards.filter(d => {
    const matchesSearch = d.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          d.description?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesModule = moduleFilter === 'all' || d.module === moduleFilter;
    return matchesSearch && matchesModule;
  });

  const formatDate = (dateStr: string) => {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' });
  };

  const formatDateTime = (dateStr: string) => {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <Flex justifyContent="between" alignItems="center">
        <div>
          <Title className="text-2xl font-bold text-gray-800">Meus Dashboards</Title>
          <Text className="text-gray-500">Gerencie seus dashboards personalizados</Text>
        </div>
        <Button
          icon={Plus}
          onClick={() => setShowCreateModal(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white"
        >
          Novo Dashboard
        </Button>
      </Flex>

      {/* Filters */}
      <Card className="p-4">
        <Flex className="gap-4" justifyContent="start">
          <div className="w-64">
            <TextInput
              icon={Search}
              placeholder="Buscar dashboards..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <div className="w-48">
            <Select
              value={moduleFilter}
              onValueChange={setModuleFilter}
              icon={Filter}
            >
              <SelectItem value="all">Todos os módulos</SelectItem>
              <SelectItem value="operations">Operações</SelectItem>
              <SelectItem value="maintenance">Manutenção</SelectItem>
              <SelectItem value="quality">Qualidade</SelectItem>
              <SelectItem value="executive">Executivo</SelectItem>
              <SelectItem value="energy">Energia</SelectItem>
              <SelectItem value="analytics">Analytics</SelectItem>
            </Select>
          </div>
          <Badge color="gray" className="ml-auto">
            {filteredDashboards.length} dashboard(s)
          </Badge>
        </Flex>
      </Card>

      {/* Dashboards Grid */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-600">Carregando dashboards...</span>
        </div>
      ) : filteredDashboards.length === 0 ? (
        <Card className="p-12 text-center">
          <LayoutDashboard className="w-16 h-16 mx-auto text-gray-400 mb-4" />
          <Title className="text-gray-600">Nenhum dashboard encontrado</Title>
          <Text className="text-gray-500 mt-2">
            {searchTerm || moduleFilter !== 'all'
              ? 'Tente ajustar os filtros de busca'
              : 'Crie seu primeiro dashboard clicando no botão acima'}
          </Text>
          {!searchTerm && moduleFilter === 'all' && (
            <Button
              icon={Plus}
              className="mt-4 bg-blue-600 hover:bg-blue-700 text-white"
              onClick={() => setShowCreateModal(true)}
            >
              Criar Dashboard
            </Button>
          )}
        </Card>
      ) : (
        <Grid numItemsMd={2} numItemsLg={3} className="gap-6">
          {filteredDashboards.map((dashboard) => (
            <Card key={dashboard.id} className="p-4 hover:shadow-lg transition-shadow cursor-pointer group">
              <Flex justifyContent="between" alignItems="start">
                <div className="flex-1">
                  <Flex justifyContent="start" className="gap-2 mb-2">
                    <Badge color={moduleColors[dashboard.module] || 'gray'} size="sm">
                      {moduleLabels[dashboard.module] || dashboard.module}
                    </Badge>
                    {dashboard.is_public && (
                      <Badge color="green" size="sm">Público</Badge>
                    )}
                    {dashboard.is_template && (
                      <Badge color="purple" size="sm">Template</Badge>
                    )}
                  </Flex>
                  <Title className="text-lg font-semibold text-gray-800 mb-1">
                    {dashboard.name}
                  </Title>
                  <Text className="text-gray-500 text-sm line-clamp-2">
                    {dashboard.description || 'Sem descrição'}
                  </Text>
                </div>
              </Flex>

              {/* Stats */}
              <Flex className="mt-4 gap-4" justifyContent="start">
                <Flex className="gap-1 text-gray-500 text-xs">
                  <Eye className="w-4 h-4" />
                  <span>{dashboard.view_count} views</span>
                </Flex>
                <Flex className="gap-1 text-gray-500 text-xs">
                  <LayoutDashboard className="w-4 h-4" />
                  <span>{dashboard.widget_count} widgets</span>
                </Flex>
              </Flex>

              {/* Dates */}
              <Flex className="mt-2 gap-4" justifyContent="start">
                <Flex className="gap-1 text-gray-400 text-xs">
                  <Calendar className="w-3 h-3" />
                  <span>Criado: {formatDate(dashboard.created_at)}</span>
                </Flex>
                {dashboard.last_viewed_at && (
                  <Flex className="gap-1 text-gray-400 text-xs">
                    <Clock className="w-3 h-3" />
                    <span>Visto: {formatDateTime(dashboard.last_viewed_at)}</span>
                  </Flex>
                )}
              </Flex>

              {/* Actions */}
              <Flex className="mt-4 gap-2 opacity-0 group-hover:opacity-100 transition-opacity" justifyContent="end">
                <Button
                  size="xs"
                  variant="secondary"
                  icon={Eye}
                  onClick={(e) => {
                    e.stopPropagation();
                    navigate(`/dashboards/${dashboard.id}`);
                  }}
                >
                  Abrir
                </Button>
                <Button
                  size="xs"
                  variant="secondary"
                  icon={Pencil}
                  onClick={(e) => {
                    e.stopPropagation();
                    navigate(`/dashboards/builder?id=${dashboard.id}`);
                  }}
                >
                  Editar
                </Button>
                <Button
                  size="xs"
                  variant="secondary"
                  icon={Copy}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleCloneDashboard(dashboard.id);
                  }}
                />
                <Button
                  size="xs"
                  variant="secondary"
                  color="red"
                  icon={Trash2}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteDashboard(dashboard.id);
                  }}
                />
              </Flex>
            </Card>
          ))}
        </Grid>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md p-6">
            <Title className="mb-4">Novo Dashboard</Title>
            <div className="space-y-4">
              <div>
                <Text className="mb-1 text-sm font-medium">Nome</Text>
                <TextInput
                  placeholder="Nome do dashboard"
                  value={newDashboard.name}
                  onChange={(e) => setNewDashboard({ ...newDashboard, name: e.target.value })}
                />
              </div>
              <div>
                <Text className="mb-1 text-sm font-medium">Descrição</Text>
                <TextInput
                  placeholder="Descrição (opcional)"
                  value={newDashboard.description}
                  onChange={(e) => setNewDashboard({ ...newDashboard, description: e.target.value })}
                />
              </div>
              <div>
                <Text className="mb-1 text-sm font-medium">Módulo</Text>
                <Select
                  value={newDashboard.module}
                  onValueChange={(v) => setNewDashboard({ ...newDashboard, module: v })}
                >
                  <SelectItem value="operations">Operações</SelectItem>
                  <SelectItem value="maintenance">Manutenção</SelectItem>
                  <SelectItem value="quality">Qualidade</SelectItem>
                  <SelectItem value="executive">Executivo</SelectItem>
                  <SelectItem value="energy">Energia</SelectItem>
                  <SelectItem value="analytics">Analytics</SelectItem>
                </Select>
              </div>
            </div>
            <Flex className="mt-6 gap-2" justifyContent="end">
              <Button
                variant="secondary"
                onClick={() => setShowCreateModal(false)}
              >
                Cancelar
              </Button>
              <Button
                className="bg-blue-600 hover:bg-blue-700 text-white"
                onClick={handleCreateDashboard}
                disabled={!newDashboard.name}
              >
                Criar Dashboard
              </Button>
            </Flex>
          </Card>
        </div>
      )}
    </div>
  );
};

export default TremorDashboardsList;
