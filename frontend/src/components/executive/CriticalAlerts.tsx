import React from 'react';
import { Card, CardContent, Typography, List, ListItem, ListItemText, Chip, Alert } from '@mui/material';
import { Warning, Error } from '@mui/icons-material';

interface Props {
  alerts: any[];
}

const CriticalAlerts: React.FC<Props> = ({ alerts }) => {
  if (!alerts || alerts.length === 0) {
    return (
      <Card>
        <CardContent>
          <Alert severity="success">No critical alerts - All systems operating normally</Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" fontWeight="bold" gutterBottom>
          Critical Alerts ({alerts.length})
        </Typography>
        <List>
          {alerts.slice(0, 10).map((alert, index) => (
            <ListItem key={index}>
              {alert.severity === 'critical' ? <Error color="error" sx={{ mr: 2 }} /> : <Warning color="warning" sx={{ mr: 2 }} />}
              <ListItemText
                primary={alert.message}
                secondary={`${alert.asset_name} - ${alert.duration_hours || 0}h ago`}
              />
              <Chip
                label={alert.severity}
                color={alert.severity === 'critical' ? 'error' : 'warning'}
                size="small"
              />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
};

export default CriticalAlerts;
