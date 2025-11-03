import React from 'react';
import { Card, CardContent, Typography, List, ListItem, ListItemText, Chip, Box } from '@mui/material';

interface Props {
  data: any;
  detailed?: boolean;
}

const AssetHealthSummary: React.FC<Props> = ({ data, detailed = false }) => {
  if (!data) return null;

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" fontWeight="bold" gutterBottom>
          Asset Health Summary
        </Typography>

        {data.by_type && (
          <Box mt={2}>
            <Typography variant="body2" color="text.secondary" gutterBottom>By Asset Type</Typography>
            {Object.entries(data.by_type).map(([type, info]: [string, any]) => (
              <Box key={type} display="flex" justifyContent="space-between" py={1}>
                <Typography variant="body2">{type}</Typography>
                <Chip label={`${info.count} assets - ${info.avg_health} health`} size="small" />
              </Box>
            ))}
          </Box>
        )}

        {detailed && data.worst_performing && (
          <Box mt={2}>
            <Typography variant="body2" color="text.secondary" gutterBottom>Worst Performing Assets</Typography>
            <List dense>
              {data.worst_performing.map((asset: any, index: number) => (
                <ListItem key={index}>
                  <ListItemText
                    primary={asset.name}
                    secondary={`Health: ${asset.health_score} - ${asset.type}`}
                  />
                  <Chip
                    label={asset.priority}
                    color={asset.priority === 'critical' ? 'error' : 'warning'}
                    size="small"
                  />
                </ListItem>
              ))}
            </List>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default AssetHealthSummary;
