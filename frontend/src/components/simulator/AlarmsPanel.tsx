import React from 'react';
import { Box, Paper, Typography, List, ListItem, ListItemText, Chip, Button, Stack, Alert } from '@mui/material';
import { Warning, Error as ErrorIcon } from '@mui/icons-material';

interface Alarm {
  tag: string;
  active: boolean;
  latched: boolean;
  timestamp: number;
  count: number;
}

interface AlarmsPanelProps {
  alarms: Alarm[];
  trips: Alarm[];
  onAcknowledgeAll: () => void;
}

export default function AlarmsPanel({ alarms, trips, onAcknowledgeAll }: AlarmsPanelProps) {
  const activeAlarms = alarms.filter(a => a.active);
  const activeTrips = trips.filter(t => t.active);

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
        <Typography variant="h6">Alarmes e Trips Ativos</Typography>
        <Button variant="outlined" onClick={onAcknowledgeAll}>
          Reconhecer Todos
        </Button>
      </Stack>

      {activeTrips.length === 0 && activeAlarms.length === 0 && (
        <Alert severity="success">Sistema sem alarmes ativos</Alert>
      )}

      {activeTrips.length > 0 && (
        <Paper sx={{ p: 2, mb: 2, bgcolor: '#ffebee' }}>
          <Typography variant="subtitle1" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <ErrorIcon color="error" /> Trips Ativos ({activeTrips.length})
          </Typography>
          <List dense>
            {activeTrips.map((trip, idx) => (
              <ListItem key={idx}>
                <ListItemText
                  primary={trip.tag}
                  secondary={`Contagem: ${trip.count} | Tempo: ${trip.timestamp}s`}
                />
                <Chip label="TRIP" color="error" size="small" />
              </ListItem>
            ))}
          </List>
        </Paper>
      )}

      {activeAlarms.length > 0 && (
        <Paper sx={{ p: 2, bgcolor: '#fff3e0' }}>
          <Typography variant="subtitle1" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Warning color="warning" /> Alarmes Ativos ({activeAlarms.length})
          </Typography>
          <List dense>
            {activeAlarms.map((alarm, idx) => (
              <ListItem key={idx}>
                <ListItemText
                  primary={alarm.tag}
                  secondary={`Contagem: ${alarm.count} | Tempo: ${alarm.timestamp}s`}
                />
                <Chip label="ATIVO" color="warning" size="small" />
              </ListItem>
            ))}
          </List>
        </Paper>
      )}
    </Box>
  );
}
