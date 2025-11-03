import React from 'react';
import { Card, CardContent, Typography, List, ListItem, ListItemText, Chip, Box, Alert } from '@mui/material';
import { Link as LinkIcon, AttachMoney } from '@mui/icons-material';

interface Props {
  correlations: any[];
}

const CorrelationAnalysis: React.FC<Props> = ({ correlations }) => {
  if (!correlations || correlations.length === 0) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" fontWeight="bold" gutterBottom>
            Maintenance-Operations Correlation
          </Typography>
          <Alert severity="info">No significant correlations detected in this period</Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" fontWeight="bold" gutterBottom>
          💡 Maintenance-Operations Correlation
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          How maintenance events impacted operations this period:
        </Typography>

        <List>
          {correlations.map((corr, index) => (
            <ListItem key={index} sx={{ flexDirection: 'column', alignItems: 'flex-start', border: '1px solid #eee', borderRadius: 1, mb: 1 }}>
              <Box display="flex" alignItems="center" width="100%" mb={1}>
                <LinkIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="subtitle2" fontWeight="bold">
                  {corr.asset_name} - {corr.asset_type}
                </Typography>
                <Chip
                  label={`${(corr.correlation_confidence * 100).toFixed(0)}% confidence`}
                  size="small"
                  sx={{ ml: 'auto' }}
                />
              </Box>

              <Typography variant="body2" color="text.secondary" gutterBottom>
                {corr.alarm_message}
              </Typography>

              {corr.operational_impact && (
                <Box mt={1} p={1} bgcolor="error.light" borderRadius={1} width="100%">
                  <Typography variant="body2" fontWeight="medium">
                    Impact: {corr.operational_impact.type}
                  </Typography>
                  {corr.operational_impact.estimated_cost && (
                    <Box display="flex" alignItems="center" mt={0.5}>
                      <AttachMoney fontSize="small" />
                      <Typography variant="body2">
                        Estimated Cost: ${corr.operational_impact.estimated_cost.toLocaleString()}
                      </Typography>
                    </Box>
                  )}
                </Box>
              )}
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
};

export default CorrelationAnalysis;
