/**
 * Extended Tags Management Page
 *
 * Main page for managing extended tags with PI Asset Framework features
 */

import React, { useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Alert,
  Snackbar
} from '@mui/material';
import { ExtendedTagsList } from '../components/ExtendedTags/ExtendedTagsList';
import { ExtendedTagEditor } from '../components/ExtendedTags/ExtendedTagEditor';
import {
  GatewayTagExtended,
  GatewayTagExtendedCreate,
  GatewayTagExtendedUpdate
} from '../types/extendedTags';
import { extendedTagsApi } from '../api/extendedTags';

export const ExtendedTagsPage: React.FC = () => {
  const [editorOpen, setEditorOpen] = useState(false);
  const [selectedTag, setSelectedTag] = useState<GatewayTagExtended | null>(null);
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'info';
  }>({
    open: false,
    message: '',
    severity: 'info'
  });
  const [refreshKey, setRefreshKey] = useState(0);

  const handleCreate = () => {
    setSelectedTag(null);
    setEditorOpen(true);
  };

  const handleEdit = (tag: GatewayTagExtended) => {
    setSelectedTag(tag);
    setEditorOpen(true);
  };

  const handleSave = async (tagData: GatewayTagExtendedCreate | GatewayTagExtendedUpdate) => {
    try {
      if (selectedTag) {
        // Update existing tag
        await extendedTagsApi.update(selectedTag.id, tagData as GatewayTagExtendedUpdate);
        showSnackbar('Tag atualizado com sucesso!', 'success');
      } else {
        // Create new tag
        await extendedTagsApi.create(tagData as GatewayTagExtendedCreate);
        showSnackbar('Tag criado com sucesso!', 'success');
      }

      setEditorOpen(false);
      setSelectedTag(null);
      setRefreshKey(prev => prev + 1); // Trigger refresh
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Erro ao salvar tag';
      showSnackbar(message, 'error');
      throw error; // Re-throw to let editor handle it
    }
  };

  const handleDelete = async (tagId: number) => {
    if (!window.confirm('Tem certeza que deseja excluir este tag?')) {
      return;
    }

    try {
      await extendedTagsApi.delete(tagId);
      showSnackbar('Tag excluído com sucesso!', 'success');
      setRefreshKey(prev => prev + 1); // Trigger refresh
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Erro ao excluir tag';
      showSnackbar(message, 'error');
    }
  };

  const showSnackbar = (message: string, severity: 'success' | 'error' | 'info') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleCloseSnackbar = () => {
    setSnackbar(prev => ({ ...prev, open: false }));
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Tags Estendidos - PI Asset Framework
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Gerencie tags com recursos avançados: fórmulas, arquivamento histórico, alarmes e hierarquia.
        </Typography>
      </Box>

      <Alert severity="info" sx={{ mb: 3 }}>
        <strong>Funcionalidades disponíveis:</strong> Tags físicos (PLC), calculados (fórmulas),
        lógicos (condições), arquivamento PI-style, alarmes configuráveis e integração com hierarquia de assets.
      </Alert>

      <ExtendedTagsList
        key={refreshKey}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onCreate={handleCreate}
      />

      <ExtendedTagEditor
        open={editorOpen}
        onClose={() => {
          setEditorOpen(false);
          setSelectedTag(null);
        }}
        onSave={handleSave}
        tag={selectedTag}
      />

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default ExtendedTagsPage;
