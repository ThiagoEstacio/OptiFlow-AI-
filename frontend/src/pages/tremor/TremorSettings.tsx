/**
 * ⚙️ Professional Settings Page with Tremor
 * ==========================================
 *
 * User preferences and system configuration
 */
import React, { useState } from 'react';
import {
  Card,
  Title,
  Text,
  Flex,
  Grid,
  Badge,
  TabGroup,
  TabList,
  Tab,
  TabPanels,
  TabPanel,
  TextInput,
  NumberInput,
  Switch,
  Button,
  Divider,
  List,
  ListItem,
} from '@tremor/react';
import { User, Bell, Shield, Database, Palette, Globe, Save, RefreshCw } from 'lucide-react';

export const TremorSettings: React.FC = () => {
  const [notifications, setNotifications] = useState({
    email: true,
    push: true,
    critical: true,
    reports: false,
  });

  const [refreshInterval, setRefreshInterval] = useState(30);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <Title>Configurações</Title>
        <Text>Personalize sua experiência e configure o sistema</Text>
      </div>

      <TabGroup>
        <TabList>
          <Tab icon={User}>Perfil</Tab>
          <Tab icon={Bell}>Notificações</Tab>
          <Tab icon={Palette}>Aparência</Tab>
          <Tab icon={Database}>Sistema</Tab>
        </TabList>

        <TabPanels>
          {/* Profile Tab */}
          <TabPanel>
            <Grid numItemsSm={1} numItemsLg={2} className="gap-6 mt-6">
              <Card>
                <Title>Informações do Usuário</Title>
                <div className="mt-4 space-y-4">
                  <div>
                    <Text className="mb-2">Nome</Text>
                    <TextInput placeholder="Seu nome" defaultValue="Administrador" />
                  </div>
                  <div>
                    <Text className="mb-2">Email</Text>
                    <TextInput placeholder="seu@email.com" defaultValue="admin@optiflow.com" />
                  </div>
                  <div>
                    <Text className="mb-2">Cargo</Text>
                    <TextInput placeholder="Seu cargo" defaultValue="Engenheiro de Automação" />
                  </div>
                  <div>
                    <Text className="mb-2">Departamento</Text>
                    <TextInput placeholder="Departamento" defaultValue="Operações" />
                  </div>
                  <Button className="mt-4" icon={Save}>
                    Salvar Alterações
                  </Button>
                </div>
              </Card>

              <Card>
                <Title>Segurança</Title>
                <div className="mt-4 space-y-4">
                  <div>
                    <Text className="mb-2">Senha Atual</Text>
                    <TextInput type="password" placeholder="••••••••" />
                  </div>
                  <div>
                    <Text className="mb-2">Nova Senha</Text>
                    <TextInput type="password" placeholder="••••••••" />
                  </div>
                  <div>
                    <Text className="mb-2">Confirmar Nova Senha</Text>
                    <TextInput type="password" placeholder="••••••••" />
                  </div>
                  <Divider />
                  <Flex justifyContent="between" alignItems="center">
                    <div>
                      <Text className="font-medium">Autenticação em 2 Fatores</Text>
                      <Text className="text-sm text-gray-500">Adicione uma camada extra de segurança</Text>
                    </div>
                    <Badge color="emerald">Ativado</Badge>
                  </Flex>
                  <Button variant="secondary" icon={Shield}>
                    Alterar Senha
                  </Button>
                </div>
              </Card>
            </Grid>
          </TabPanel>

          {/* Notifications Tab */}
          <TabPanel>
            <Card className="mt-6">
              <Title>Preferências de Notificação</Title>
              <Text>Configure como você deseja receber alertas e atualizações</Text>

              <div className="mt-6 space-y-6">
                <Flex justifyContent="between" alignItems="center">
                  <div>
                    <Text className="font-medium">Notificações por Email</Text>
                    <Text className="text-sm text-gray-500">Receba alertas importantes no seu email</Text>
                  </div>
                  <Switch
                    checked={notifications.email}
                    onChange={() => setNotifications(n => ({ ...n, email: !n.email }))}
                  />
                </Flex>

                <Divider />

                <Flex justifyContent="between" alignItems="center">
                  <div>
                    <Text className="font-medium">Notificações Push</Text>
                    <Text className="text-sm text-gray-500">Alertas em tempo real no navegador</Text>
                  </div>
                  <Switch
                    checked={notifications.push}
                    onChange={() => setNotifications(n => ({ ...n, push: !n.push }))}
                  />
                </Flex>

                <Divider />

                <Flex justifyContent="between" alignItems="center">
                  <div>
                    <Text className="font-medium">Alarmes Críticos</Text>
                    <Text className="text-sm text-gray-500">Sempre notificar para alarmes de alta prioridade</Text>
                  </div>
                  <Switch
                    checked={notifications.critical}
                    onChange={() => setNotifications(n => ({ ...n, critical: !n.critical }))}
                  />
                </Flex>

                <Divider />

                <Flex justifyContent="between" alignItems="center">
                  <div>
                    <Text className="font-medium">Relatórios Semanais</Text>
                    <Text className="text-sm text-gray-500">Receba resumos semanais de performance</Text>
                  </div>
                  <Switch
                    checked={notifications.reports}
                    onChange={() => setNotifications(n => ({ ...n, reports: !n.reports }))}
                  />
                </Flex>
              </div>
            </Card>
          </TabPanel>

          {/* Appearance Tab */}
          <TabPanel>
            <Grid numItemsSm={1} numItemsLg={2} className="gap-6 mt-6">
              <Card>
                <Title>Tema</Title>
                <div className="mt-4 space-y-4">
                  <Flex justifyContent="between" alignItems="center" className="p-4 border rounded-lg cursor-pointer hover:bg-gray-50">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-white border rounded-lg" />
                      <div>
                        <Text className="font-medium">Claro</Text>
                        <Text className="text-sm text-gray-500">Tema padrão com fundo branco</Text>
                      </div>
                    </div>
                    <Badge color="blue">Ativo</Badge>
                  </Flex>

                  <Flex justifyContent="between" alignItems="center" className="p-4 border rounded-lg cursor-pointer hover:bg-gray-50">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-gray-900 rounded-lg" />
                      <div>
                        <Text className="font-medium">Escuro</Text>
                        <Text className="text-sm text-gray-500">Tema escuro para ambientes com pouca luz</Text>
                      </div>
                    </div>
                  </Flex>

                  <Flex justifyContent="between" alignItems="center" className="p-4 border rounded-lg cursor-pointer hover:bg-gray-50">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-gradient-to-r from-gray-100 to-gray-900 rounded-lg" />
                      <div>
                        <Text className="font-medium">Automático</Text>
                        <Text className="text-sm text-gray-500">Segue as preferências do sistema</Text>
                      </div>
                    </div>
                  </Flex>
                </div>
              </Card>

              <Card>
                <Title>Idioma e Região</Title>
                <div className="mt-4 space-y-4">
                  <div>
                    <Text className="mb-2">Idioma</Text>
                    <TextInput defaultValue="Português (Brasil)" disabled />
                  </div>
                  <div>
                    <Text className="mb-2">Fuso Horário</Text>
                    <TextInput defaultValue="America/Sao_Paulo (GMT-3)" disabled />
                  </div>
                  <div>
                    <Text className="mb-2">Formato de Data</Text>
                    <TextInput defaultValue="DD/MM/YYYY" disabled />
                  </div>
                </div>
              </Card>
            </Grid>
          </TabPanel>

          {/* System Tab */}
          <TabPanel>
            <Grid numItemsSm={1} numItemsLg={2} className="gap-6 mt-6">
              <Card>
                <Title>Atualização de Dados</Title>
                <div className="mt-4 space-y-4">
                  <div>
                    <Text className="mb-2">Intervalo de Atualização (segundos)</Text>
                    <NumberInput
                      value={refreshInterval}
                      onValueChange={setRefreshInterval}
                      min={5}
                      max={300}
                    />
                    <Text className="text-sm text-gray-500 mt-1">
                      Define a frequência de atualização dos dados em tempo real
                    </Text>
                  </div>

                  <Divider />

                  <Flex justifyContent="between" alignItems="center">
                    <div>
                      <Text className="font-medium">Cache de Dados</Text>
                      <Text className="text-sm text-gray-500">Otimiza performance com cache local</Text>
                    </div>
                    <Switch defaultChecked />
                  </Flex>

                  <Flex justifyContent="between" alignItems="center">
                    <div>
                      <Text className="font-medium">Compressão de Dados</Text>
                      <Text className="text-sm text-gray-500">Reduz uso de bandwidth</Text>
                    </div>
                    <Switch defaultChecked />
                  </Flex>
                </div>
              </Card>

              <Card>
                <Title>Informações do Sistema</Title>
                <List className="mt-4">
                  <ListItem>
                    <Flex justifyContent="between" className="w-full">
                      <Text>Versão do Frontend</Text>
                      <Badge color="blue">v3.0.0</Badge>
                    </Flex>
                  </ListItem>
                  <ListItem>
                    <Flex justifyContent="between" className="w-full">
                      <Text>Versão do Backend</Text>
                      <Badge color="blue">v2.5.0</Badge>
                    </Flex>
                  </ListItem>
                  <ListItem>
                    <Flex justifyContent="between" className="w-full">
                      <Text>Status do Servidor</Text>
                      <Badge color="emerald">Online</Badge>
                    </Flex>
                  </ListItem>
                  <ListItem>
                    <Flex justifyContent="between" className="w-full">
                      <Text>Último Deploy</Text>
                      <Text className="text-gray-500">03/12/2025 10:30</Text>
                    </Flex>
                  </ListItem>
                  <ListItem>
                    <Flex justifyContent="between" className="w-full">
                      <Text>Uptime</Text>
                      <Text className="text-gray-500">15 dias, 7 horas</Text>
                    </Flex>
                  </ListItem>
                </List>

                <Button variant="secondary" className="mt-4 w-full" icon={RefreshCw}>
                  Verificar Atualizações
                </Button>
              </Card>
            </Grid>
          </TabPanel>
        </TabPanels>
      </TabGroup>
    </div>
  );
};

export default TremorSettings;
