import React from 'react';
import { Box, Typography, Button, Paper } from '@mui/material';
import {
  Inbox as InboxIcon,
  CloudOff as CloudOffIcon,
  ErrorOutline as ErrorIcon,
  Search as SearchIcon,
  Add as AddIcon,
} from '@mui/icons-material';

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  variant?: 'default' | 'error' | 'search' | 'offline';
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  actionLabel,
  onAction,
  variant = 'default',
}) => {
  const getDefaultIcon = () => {
    switch (variant) {
      case 'error':
        return <ErrorIcon sx={{ fontSize: 80, color: 'error.main' }} />;
      case 'search':
        return <SearchIcon sx={{ fontSize: 80, color: 'text.disabled' }} />;
      case 'offline':
        return <CloudOffIcon sx={{ fontSize: 80, color: 'text.disabled' }} />;
      default:
        return <InboxIcon sx={{ fontSize: 80, color: 'text.disabled' }} />;
    }
  };

  return (
    <Paper
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        py: 8,
        px: 4,
        textAlign: 'center',
        bgcolor: 'grey.50',
      }}
      elevation={0}
    >
      <Box sx={{ mb: 3 }}>{icon || getDefaultIcon()}</Box>

      <Typography variant="h6" gutterBottom fontWeight="bold" color="text.primary">
        {title}
      </Typography>

      {description && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3, maxWidth: 400 }}>
          {description}
        </Typography>
      )}

      {actionLabel && onAction && (
        <Button variant="contained" onClick={onAction} startIcon={<AddIcon />}>
          {actionLabel}
        </Button>
      )}
    </Paper>
  );
};

interface NoDataProps {
  message?: string;
  showAction?: boolean;
  actionLabel?: string;
  onAction?: () => void;
}

export const NoData: React.FC<NoDataProps> = ({
  message = 'Nenhum dado encontrado',
  showAction = false,
  actionLabel = 'Adicionar',
  onAction,
}) => {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        py: 6,
        textAlign: 'center',
      }}
    >
      <InboxIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
      <Typography variant="body1" color="text.secondary" gutterBottom>
        {message}
      </Typography>
      {showAction && onAction && (
        <Button variant="outlined" onClick={onAction} sx={{ mt: 2 }} startIcon={<AddIcon />}>
          {actionLabel}
        </Button>
      )}
    </Box>
  );
};

export const ErrorState: React.FC<{ message: string; onRetry?: () => void }> = ({
  message,
  onRetry,
}) => {
  return (
    <EmptyState
      variant="error"
      title="Erro ao Carregar Dados"
      description={message}
      actionLabel={onRetry ? 'Tentar Novamente' : undefined}
      onAction={onRetry}
    />
  );
};
