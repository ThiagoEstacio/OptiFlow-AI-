import React from 'react';
import { Grid, Card, CardContent, Typography, List, ListItem, ListItemText, Chip, Box } from '@mui/material';
import { Warning, Lightbulb } from '@mui/icons-material';

interface Props {
  risks: any[];
  opportunities: any[];
}

const RisksOpportunities: React.FC<Props> = ({ risks, opportunities }) => {
  return (
    <Grid container spacing={3}>
      {/* Risks */}
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Box display="flex" alignItems="center" mb={2}>
              <Warning color="error" sx={{ mr: 1 }} />
              <Typography variant="h6" fontWeight="bold">
                Risks ({risks?.length || 0})
              </Typography>
            </Box>

            {risks && risks.length > 0 ? (
              <List>
                {risks.slice(0, 5).map((risk, index) => (
                  <ListItem key={index} sx={{ flexDirection: 'column', alignItems: 'flex-start', border: '1px solid #ffebee', borderRadius: 1, mb: 1 }}>
                    <Box display="flex" justifyContent="space-between" width="100%" mb={1}>
                      <Typography variant="subtitle2" fontWeight="bold">
                        {risk.description}
                      </Typography>
                      <Chip
                        label={risk.severity}
                        color={risk.severity === 'critical' ? 'error' : risk.severity === 'high' ? 'warning' : 'default'}
                        size="small"
                      />
                    </Box>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      {risk.potential_impact}
                    </Typography>
                    <Typography variant="caption" color="success.main" fontWeight="medium">
                      ✓ Mitigation: {risk.mitigation}
                    </Typography>
                  </ListItem>
                ))}
              </List>
            ) : (
              <Typography variant="body2" color="text.secondary">No significant risks identified</Typography>
            )}
          </CardContent>
        </Card>
      </Grid>

      {/* Opportunities */}
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Box display="flex" alignItems="center" mb={2}>
              <Lightbulb color="success" sx={{ mr: 1 }} />
              <Typography variant="h6" fontWeight="bold">
                Opportunities ({opportunities?.length || 0})
              </Typography>
            </Box>

            {opportunities && opportunities.length > 0 ? (
              <List>
                {opportunities.slice(0, 5).map((opp, index) => (
                  <ListItem key={index} sx={{ flexDirection: 'column', alignItems: 'flex-start', border: '1px solid #e8f5e9', borderRadius: 1, mb: 1 }}>
                    <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                      {opp.description}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      {opp.benefit}
                    </Typography>
                    {opp.recommendation && (
                      <Typography variant="caption" color="primary.main" fontWeight="medium">
                        → {opp.recommendation}
                      </Typography>
                    )}
                  </ListItem>
                ))}
              </List>
            ) : (
              <Typography variant="body2" color="text.secondary">No opportunities identified</Typography>
            )}
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};

export default RisksOpportunities;
