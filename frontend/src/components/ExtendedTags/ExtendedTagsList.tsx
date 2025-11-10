/**
 * Extended Tags List Component
 *
 * Displays list of extended tags with:
 * - Filtering by gateway, asset, type
 * - Search functionality
 * - Bulk operations
 * - Tag status indicators
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Checkbox,
  IconButton,
  Chip,
  Tooltip,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Button,
  Menu,
  ListItemIcon,
  ListItemText,
  Typography
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  MoreVert as MoreVertIcon,
  FilterList as FilterIcon,
  Add as AddIcon,
  CheckCircle as EnabledIcon,
  Cancel as DisabledIcon,
  Functions as FormulaIcon,
  Storage as ArchiveIcon,
  Storage as StorageIcon,
  Warning as AlarmIcon
} from '@mui/icons-material';
import { GatewayTagExtended, TagType, ExtendedTagFilters } from '../../types/extendedTags';
import { extendedTagsApi } from '../../api/extendedTags';

interface ExtendedTagsListProps {
  onEdit: (tag: GatewayTagExtended) => void;
  onDelete: (tagId: number) => void;
  onCreate: () => void;
  gatewayId?: number;
}

export const ExtendedTagsList: React.FC<ExtendedTagsListProps> = ({
  onEdit,
  onDelete,
  onCreate,
  gatewayId
}) => {
  const [tags, setTags] = useState<GatewayTagExtended[]>([]);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState<number[]>([]);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [currentTag, setCurrentTag] = useState<GatewayTagExtended | null>(null);

  // Filters
  const [filters, setFilters] = useState<ExtendedTagFilters>({
    gateway_id: gatewayId,
    enabled_only: false,
    skip: 0,
    limit: 25
  });
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadTags();
  }, [filters]);

  const loadTags = async () => {
    setLoading(true);
    try {
      const data = await extendedTagsApi.list(filters);
      setTags(data);
    } catch (error) {
      console.error('Error loading tags:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (field: keyof ExtendedTagFilters, value: any) => {
    setFilters(prev => ({
      ...prev,
      [field]: value,
      skip: 0 // Reset pagination
    }));
    setPage(0);
  };

  const handleSearch = () => {
    handleFilterChange('search', searchTerm);
  };

  const handleSelectAll = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.checked) {
      setSelected(tags.map(tag => tag.id));
    } else {
      setSelected([]);
    }
  };

  const handleSelectOne = (tagId: number) => {
    setSelected(prev =>
      prev.includes(tagId)
        ? prev.filter(id => id !== tagId)
        : [...prev, tagId]
    );
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, tag: GatewayTagExtended) => {
    setAnchorEl(event.currentTarget);
    setCurrentTag(tag);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setCurrentTag(null);
  };

  const handleEdit = () => {
    if (currentTag) {
      onEdit(currentTag);
      handleMenuClose();
    }
  };

  const handleDelete = () => {
    if (currentTag) {
      onDelete(currentTag.id);
      handleMenuClose();
    }
  };

  const getTagTypeChip = (tagType: TagType) => {
    const config = {
      [TagType.PHYSICAL]: { label: 'Físico', color: 'primary' as const, icon: <StorageIcon /> },
      [TagType.CALCULATED]: { label: 'Calculado', color: 'secondary' as const, icon: <FormulaIcon /> },
      [TagType.LOGICAL]: { label: 'Lógico', color: 'info' as const, icon: <FormulaIcon /> },
      [TagType.AGGREGATED]: { label: 'Agregado', color: 'warning' as const, icon: <FormulaIcon /> }
    };
    const c = config[tagType];
    return <Chip size="small" label={c.label} color={c.color} icon={c.icon} />;
  };

  return (
    <Box>
      {/* Filters and Actions */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
          <Box sx={{ flex: '1 1 calc(33.33% - 16px)', minWidth: 250 }}>
            <TextField
              fullWidth
              size="small"
              label="Buscar"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Nome ou descrição"
            />
          </Box>

          <Box sx={{ flex: '1 1 calc(16.66% - 16px)', minWidth: 150 }}>
            <FormControl fullWidth size="small">
              <InputLabel>Tipo</InputLabel>
              <Select
                value={filters.tag_type || ''}
                onChange={(e) => handleFilterChange('tag_type', e.target.value || undefined)}
                label="Tipo"
              >
                <MenuItem value="">Todos</MenuItem>
                <MenuItem value={TagType.PHYSICAL}>Físico</MenuItem>
                <MenuItem value={TagType.CALCULATED}>Calculado</MenuItem>
                <MenuItem value={TagType.LOGICAL}>Lógico</MenuItem>
                <MenuItem value={TagType.AGGREGATED}>Agregado</MenuItem>
              </Select>
            </FormControl>
          </Box>

          <Box sx={{ flex: '1 1 calc(16.66% - 16px)', minWidth: 150 }}>
            <FormControl fullWidth size="small">
              <InputLabel>Status</InputLabel>
              <Select
                value={filters.enabled_only ? 'enabled' : 'all'}
                onChange={(e) => handleFilterChange('enabled_only', e.target.value === 'enabled')}
                label="Status"
              >
                <MenuItem value="all">Todos</MenuItem>
                <MenuItem value="enabled">Habilitados</MenuItem>
              </Select>
            </FormControl>
          </Box>

          <Box sx={{ flex: '1 1 calc(16.66% - 16px)', minWidth: 120 }}>
            <Button
              fullWidth
              variant="outlined"
              startIcon={<FilterIcon />}
              onClick={handleSearch}
            >
              Filtrar
            </Button>
          </Box>

          <Box sx={{ flex: '1 1 calc(16.66% - 16px)', minWidth: 140 }}>
            <Button
              fullWidth
              variant="contained"
              startIcon={<AddIcon />}
              onClick={onCreate}
            >
              Novo Tag
            </Button>
          </Box>
        </Box>

        {selected.length > 0 && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" color="text.secondary">
              {selected.length} tag(s) selecionado(s)
            </Typography>
          </Box>
        )}
      </Paper>

      {/* Tags Table */}
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell padding="checkbox">
                <Checkbox
                  indeterminate={selected.length > 0 && selected.length < tags.length}
                  checked={tags.length > 0 && selected.length === tags.length}
                  onChange={handleSelectAll}
                />
              </TableCell>
              <TableCell>Nome</TableCell>
              <TableCell>Tipo</TableCell>
              <TableCell>Unidade</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Arquivo</TableCell>
              <TableCell>Alarme</TableCell>
              <TableCell>Descrição</TableCell>
              <TableCell align="right">Ações</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={9} align="center">
                  Carregando...
                </TableCell>
              </TableRow>
            ) : tags.length === 0 ? (
              <TableRow>
                <TableCell colSpan={9} align="center">
                  Nenhum tag encontrado. Clique em "Novo Tag" para criar.
                </TableCell>
              </TableRow>
            ) : (
              tags.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage).map((tag) => (
                <TableRow key={tag.id} hover>
                  <TableCell padding="checkbox">
                    <Checkbox
                      checked={selected.includes(tag.id)}
                      onChange={() => handleSelectOne(tag.id)}
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium">
                      {tag.tag_name}
                    </Typography>
                  </TableCell>
                  <TableCell>{getTagTypeChip(tag.tag_type)}</TableCell>
                  <TableCell>{tag.unit || '-'}</TableCell>
                  <TableCell>
                    {tag.enabled ? (
                      <Tooltip title="Habilitado">
                        <EnabledIcon color="success" fontSize="small" />
                      </Tooltip>
                    ) : (
                      <Tooltip title="Desabilitado">
                        <DisabledIcon color="disabled" fontSize="small" />
                      </Tooltip>
                    )}
                  </TableCell>
                  <TableCell>
                    {tag.archive_enabled ? (
                      <Tooltip title={`${tag.archive_type} - Deadband: ${tag.archive_deadband || 'N/A'}`}>
                        <ArchiveIcon color="primary" fontSize="small" />
                      </Tooltip>
                    ) : (
                      <Tooltip title="Sem histórico">
                        <ArchiveIcon color="disabled" fontSize="small" />
                      </Tooltip>
                    )}
                  </TableCell>
                  <TableCell>
                    {tag.alarm_enabled ? (
                      <Tooltip title="Alarmes configurados">
                        <AlarmIcon color="warning" fontSize="small" />
                      </Tooltip>
                    ) : (
                      <AlarmIcon color="disabled" fontSize="small" />
                    )}
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                      {tag.description || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    <IconButton
                      size="small"
                      onClick={(e) => handleMenuOpen(e, tag)}
                    >
                      <MoreVertIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>

        <TablePagination
          component="div"
          count={tags.length}
          page={page}
          onPageChange={(_, newPage) => setPage(newPage)}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={(e) => {
            setRowsPerPage(parseInt(e.target.value, 10));
            setPage(0);
          }}
          labelRowsPerPage="Tags por página:"
        />
      </TableContainer>

      {/* Context Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleEdit}>
          <ListItemIcon>
            <EditIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Editar</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleDelete}>
          <ListItemIcon>
            <DeleteIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Excluir</ListItemText>
        </MenuItem>
      </Menu>
    </Box>
  );
};

export default ExtendedTagsList;
