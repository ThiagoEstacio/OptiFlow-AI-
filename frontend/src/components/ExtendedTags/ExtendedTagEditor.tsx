/**
 * Extended Tag Editor - PI Asset Framework style
 *
 * Multi-tab editor for creating/editing tags with:
 * - General configuration
 * - Historical archiving
 * - Formulas and calculations
 * - Alarms and limits
 */

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Tabs,
  Tab,
  Box,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  FormControlLabel,
  Switch,
  Typography,
  Alert
} from '@mui/material';
import {
  GatewayTagExtended,
  GatewayTagExtendedCreate,
  GatewayTagExtendedUpdate,
  TagType,
  ArchiveType,
  AlarmConfig
} from '../../types/extendedTags';

interface ExtendedTagEditorProps {
  open: boolean;
  onClose: () => void;
  onSave: (tagData: GatewayTagExtendedCreate | GatewayTagExtendedUpdate) => Promise<void>;
  tag?: GatewayTagExtended | null;
  gatewayId?: number;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tag-editor-tabpanel-${index}`}
      aria-labelledby={`tag-editor-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export const ExtendedTagEditor: React.FC<ExtendedTagEditorProps> = ({
  open,
  onClose,
  onSave,
  tag,
  gatewayId
}) => {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [formData, setFormData] = useState<GatewayTagExtendedCreate>({
    gateway_id: gatewayId,
    tag_name: '',
    enabled: true,
    tag_type: TagType.PHYSICAL,
    data_type: 'float',
    scale_factor: 1.0,
    tag_offset: 0.0,
    archive_enabled: true,
    archive_type: ArchiveType.ON_CHANGE,
    quality_enabled: true,
    alarm_enabled: false
  });

  // Initialize form with existing tag data
  useEffect(() => {
    if (tag) {
      setFormData({
        gateway_id: tag.gateway_id,
        tag_name: tag.tag_name,
        enabled: tag.enabled,
        asset_id: tag.asset_id,
        tag_group: tag.tag_group,
        tag_type: tag.tag_type,
        address_config: tag.address_config,
        data_type: tag.data_type,
        scale_factor: tag.scale_factor,
        tag_offset: tag.tag_offset,
        formula: tag.formula,
        formula_tags: tag.formula_tags,
        condition: tag.condition,
        unit: tag.unit,
        min_value: tag.min_value,
        max_value: tag.max_value,
        archive_enabled: tag.archive_enabled,
        archive_type: tag.archive_type,
        archive_deadband: tag.archive_deadband,
        archive_interval_seconds: tag.archive_interval_seconds,
        compression_deviation: tag.compression_deviation,
        quality_enabled: tag.quality_enabled,
        alarm_enabled: tag.alarm_enabled,
        alarm_config: tag.alarm_config,
        description: tag.description,
        category: tag.category,
        properties: tag.properties
      });
    } else {
      // Reset for new tag
      setFormData({
        gateway_id: gatewayId,
        tag_name: '',
        enabled: true,
        tag_type: TagType.PHYSICAL,
        data_type: 'float',
        scale_factor: 1.0,
        tag_offset: 0.0,
        archive_enabled: true,
        archive_type: ArchiveType.ON_CHANGE,
        quality_enabled: true,
        alarm_enabled: false
      });
    }
    setActiveTab(0);
    setError(null);
  }, [tag, gatewayId, open]);

  const handleChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleAlarmConfigChange = (field: keyof AlarmConfig, value: any) => {
    setFormData(prev => ({
      ...prev,
      alarm_config: {
        ...prev.alarm_config,
        [field]: value
      }
    }));
  };

  const handleSave = async () => {
    setLoading(true);
    setError(null);

    try {
      // Validation
      if (!formData.tag_name?.trim()) {
        throw new Error('Nome do tag é obrigatório');
      }

      if (formData.tag_type === TagType.CALCULATED || formData.tag_type === TagType.LOGICAL) {
        if (!formData.formula && !formData.condition) {
          throw new Error('Tags calculados/lógicos devem ter fórmula ou condição');
        }
      }

      if (formData.tag_type === TagType.PHYSICAL && !formData.address_config) {
        throw new Error('Tags físicos devem ter configuração de endereço');
      }

      await onSave(formData);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Erro ao salvar tag');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        {tag ? `Editar Tag: ${tag.tag_name}` : 'Criar Novo Tag'}
      </DialogTitle>

      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)}>
          <Tab label="Geral" />
          <Tab label="Histórico" />
          <Tab label="Fórmula" />
          <Tab label="Alarmes" />
        </Tabs>

        {/* Tab 1: General Configuration */}
        <TabPanel value={activeTab} index={0}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Box>
              <TextField
                fullWidth
                label="Nome do Tag"
                value={formData.tag_name}
                onChange={(e) => handleChange('tag_name', e.target.value)}
                required
              />
            </Box>

            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: 250 }}>
                <FormControl fullWidth>
                  <InputLabel>Tipo de Tag</InputLabel>
                  <Select
                    value={formData.tag_type}
                    onChange={(e) => handleChange('tag_type', e.target.value)}
                    label="Tipo de Tag"
                  >
                    <MenuItem value={TagType.PHYSICAL}>Físico (PLC)</MenuItem>
                    <MenuItem value={TagType.CALCULATED}>Calculado (Fórmula)</MenuItem>
                    <MenuItem value={TagType.LOGICAL}>Lógico (Condição)</MenuItem>
                    <MenuItem value={TagType.AGGREGATED}>Agregado (Estatística)</MenuItem>
                  </Select>
                </FormControl>
              </Box>

              <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: 250 }}>
                <FormControl fullWidth>
                  <InputLabel>Tipo de Dado</InputLabel>
                  <Select
                    value={formData.data_type}
                    onChange={(e) => handleChange('data_type', e.target.value)}
                    label="Tipo de Dado"
                  >
                    <MenuItem value="float">Float</MenuItem>
                    <MenuItem value="int">Integer</MenuItem>
                    <MenuItem value="bool">Boolean</MenuItem>
                    <MenuItem value="string">String</MenuItem>
                  </Select>
                </FormControl>
              </Box>
            </Box>

            <Box>
              <TextField
                fullWidth
                label="Descrição"
                value={formData.description || ''}
                onChange={(e) => handleChange('description', e.target.value)}
                multiline
                rows={2}
              />
            </Box>

            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: 250 }}>
                <TextField
                  fullWidth
                  label="Unidade de Engenharia"
                  value={formData.unit || ''}
                  onChange={(e) => handleChange('unit', e.target.value)}
                  placeholder="Ex: °C, bar, RPM"
                />
              </Box>

              <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: 250 }}>
                <TextField
                  fullWidth
                  label="Categoria"
                  value={formData.category || ''}
                  onChange={(e) => handleChange('category', e.target.value)}
                  placeholder="Ex: Process, Control, Status"
                />
              </Box>
            </Box>

            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: 250 }}>
                <TextField
                  fullWidth
                  type="number"
                  label="Fator de Escala"
                  value={formData.scale_factor}
                  onChange={(e) => handleChange('scale_factor', parseFloat(e.target.value))}
                  inputProps={{ step: 0.1 }}
                />
              </Box>

              <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: 250 }}>
                <TextField
                  fullWidth
                  type="number"
                  label="Offset"
                  value={formData.tag_offset}
                  onChange={(e) => handleChange('tag_offset', parseFloat(e.target.value))}
                  inputProps={{ step: 0.1 }}
                />
              </Box>
            </Box>

            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <Box sx={{ flex: '1 1 calc(33.33% - 16px)', minWidth: 200 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.enabled}
                      onChange={(e) => handleChange('enabled', e.target.checked)}
                    />
                  }
                  label="Habilitado"
                />
              </Box>

              <Box sx={{ flex: '1 1 calc(33.33% - 16px)', minWidth: 200 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.quality_enabled}
                      onChange={(e) => handleChange('quality_enabled', e.target.checked)}
                    />
                  }
                  label="Controle de Qualidade"
                />
              </Box>
            </Box>
          </Box>
        </TabPanel>

        {/* Tab 2: Historical Configuration */}
        <TabPanel value={activeTab} index={1}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Box>
              <Typography variant="h6" gutterBottom>
                Configuração de Arquivamento (PI Data Archive style)
              </Typography>
            </Box>

            <Box>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.archive_enabled}
                    onChange={(e) => handleChange('archive_enabled', e.target.checked)}
                  />
                }
                label="Habilitar Historização"
              />
            </Box>

            {formData.archive_enabled && (
              <>
                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                  <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: 250 }}>
                    <FormControl fullWidth>
                      <InputLabel>Tipo de Arquivamento</InputLabel>
                      <Select
                        value={formData.archive_type}
                        onChange={(e) => handleChange('archive_type', e.target.value)}
                        label="Tipo de Arquivamento"
                      >
                        <MenuItem value={ArchiveType.ON_CHANGE}>On Change (Mudança)</MenuItem>
                        <MenuItem value={ArchiveType.PERIODIC}>Periodic (Periódico)</MenuItem>
                        <MenuItem value={ArchiveType.COMPRESSED}>Compressed (Comprimido)</MenuItem>
                      </Select>
                    </FormControl>
                  </Box>

                  <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: 250 }}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Deadband (Mudança mínima)"
                      value={formData.archive_deadband || ''}
                      onChange={(e) => handleChange('archive_deadband', parseFloat(e.target.value))}
                      helperText="Mudança mínima para arquivar (absoluta ou %)"
                      inputProps={{ step: 0.01 }}
                    />
                  </Box>
                </Box>

                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                  <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: 250 }}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Intervalo (segundos)"
                      value={formData.archive_interval_seconds || ''}
                      onChange={(e) => handleChange('archive_interval_seconds', parseInt(e.target.value))}
                      helperText="Para arquivamento periódico"
                      inputProps={{ min: 1 }}
                    />
                  </Box>

                  <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: 250 }}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Desvio de Compressão"
                      value={formData.compression_deviation || ''}
                      onChange={(e) => handleChange('compression_deviation', parseFloat(e.target.value))}
                      helperText="Para arquivamento comprimido"
                      inputProps={{ step: 0.01 }}
                    />
                  </Box>
                </Box>

                <Box>
                  <Alert severity="info">
                    <strong>Dica:</strong> Use "On Change" com deadband para processos variáveis,
                    "Periodic" para logs regulares, "Compressed" para otimizar espaço.
                  </Alert>
                </Box>
              </>
            )}
          </Box>
        </TabPanel>

        {/* Tab 3: Formula Configuration */}
        <TabPanel value={activeTab} index={2}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Box>
              <Typography variant="h6" gutterBottom>
                Fórmulas e Expressões
              </Typography>
            </Box>

            {(formData.tag_type === TagType.CALCULATED || formData.tag_type === TagType.LOGICAL) && (
              <>
                <Box>
                  <TextField
                    fullWidth
                    label="Fórmula"
                    value={formData.formula || ''}
                    onChange={(e) => handleChange('formula', e.target.value)}
                    multiline
                    rows={4}
                    placeholder="Ex: {TAG1} * 1.5 + {TAG2}"
                    helperText="Use {TAG_NAME} para referenciar outros tags"
                  />
                </Box>

                <Box>
                  <TextField
                    fullWidth
                    label="Condição Lógica"
                    value={formData.condition || ''}
                    onChange={(e) => handleChange('condition', e.target.value)}
                    multiline
                    rows={3}
                    placeholder="Ex: if {TAG1} > 100 then 1 else 0"
                    helperText="Para tags lógicos com condições"
                  />
                </Box>

                <Box>
                  <Alert severity="warning">
                    <strong>Importante:</strong> Tags calculados/lógicos devem ter pelo menos
                    uma fórmula ou condição definida.
                  </Alert>
                </Box>
              </>
            )}

            {formData.tag_type === TagType.PHYSICAL && (
              <Box>
                <Alert severity="info">
                  Fórmulas e condições são apenas para tags Calculados, Lógicos ou Agregados.
                  Tags físicos leem valores diretamente do PLC/Gateway.
                </Alert>
              </Box>
            )}
          </Box>
        </TabPanel>

        {/* Tab 4: Alarms Configuration */}
        <TabPanel value={activeTab} index={3}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Box>
              <Typography variant="h6" gutterBottom>
                Configuração de Alarmes
              </Typography>
            </Box>

            <Box>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.alarm_enabled}
                    onChange={(e) => handleChange('alarm_enabled', e.target.checked)}
                  />
                }
                label="Habilitar Alarmes"
              />
            </Box>

            {formData.alarm_enabled && (
              <>
                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                  <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: 250 }}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Limite Mínimo"
                      value={formData.min_value || ''}
                      onChange={(e) => handleChange('min_value', parseFloat(e.target.value))}
                      inputProps={{ step: 0.1 }}
                    />
                  </Box>

                  <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: 250 }}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Limite Máximo"
                      value={formData.max_value || ''}
                      onChange={(e) => handleChange('max_value', parseFloat(e.target.value))}
                      inputProps={{ step: 0.1 }}
                    />
                  </Box>
                </Box>

                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                  <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: 250 }}>
                    <TextField
                      fullWidth
                      type="number"
                      label="High High (HH)"
                      value={formData.alarm_config?.high_high || ''}
                      onChange={(e) => handleAlarmConfigChange('high_high', parseFloat(e.target.value))}
                      helperText="Alarme crítico superior"
                      inputProps={{ step: 0.1 }}
                    />
                  </Box>

                  <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: 250 }}>
                    <TextField
                      fullWidth
                      type="number"
                      label="High (H)"
                      value={formData.alarm_config?.high || ''}
                      onChange={(e) => handleAlarmConfigChange('high', parseFloat(e.target.value))}
                      helperText="Alarme alto"
                      inputProps={{ step: 0.1 }}
                    />
                  </Box>
                </Box>

                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                  <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: 250 }}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Low (L)"
                      value={formData.alarm_config?.low || ''}
                      onChange={(e) => handleAlarmConfigChange('low', parseFloat(e.target.value))}
                      helperText="Alarme baixo"
                      inputProps={{ step: 0.1 }}
                    />
                  </Box>

                  <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: 250 }}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Low Low (LL)"
                      value={formData.alarm_config?.low_low || ''}
                      onChange={(e) => handleAlarmConfigChange('low_low', parseFloat(e.target.value))}
                      helperText="Alarme crítico inferior"
                      inputProps={{ step: 0.1 }}
                    />
                  </Box>
                </Box>

                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                  <Box sx={{ flex: '1 1 calc(50% - 8px)', minWidth: 250 }}>
                    <FormControl fullWidth>
                      <InputLabel>Prioridade</InputLabel>
                      <Select
                        value={formData.alarm_config?.priority || 'medium'}
                        onChange={(e) => handleAlarmConfigChange('priority', e.target.value)}
                        label="Prioridade"
                      >
                        <MenuItem value="low">Baixa</MenuItem>
                        <MenuItem value="medium">Média</MenuItem>
                        <MenuItem value="high">Alta</MenuItem>
                        <MenuItem value="critical">Crítica</MenuItem>
                      </Select>
                    </FormControl>
                  </Box>
                </Box>

                <Box>
                  <TextField
                    fullWidth
                    label="Mensagem de Alarme"
                    value={formData.alarm_config?.message || ''}
                    onChange={(e) => handleAlarmConfigChange('message', e.target.value)}
                    placeholder="Mensagem personalizada quando alarme disparar"
                  />
                </Box>
              </>
            )}
          </Box>
        </TabPanel>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose} disabled={loading}>
          Cancelar
        </Button>
        <Button onClick={handleSave} variant="contained" disabled={loading}>
          {loading ? 'Salvando...' : 'Salvar'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ExtendedTagEditor;
