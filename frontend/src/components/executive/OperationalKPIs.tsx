import React from 'react';
import { Card, CardContent, Typography, Grid, Box } from '@mui/material';
import { LocalShipping, DirectionsBoat, Scale, Speed } from '@mui/icons-material';

interface Props {
  data: any;
  detailed?: boolean;
}

const OperationalKPIs: React.FC<Props> = ({ data, detailed = false }) => {
  if (!data) return null;

  const kpiCards = [
    {
      icon: <LocalShipping fontSize="large" />,
      label: 'Trucks Processed',
      value: data.trucks?.total || 0,
      subtitle: `${data.trucks?.avg_per_day || 0}/day avg`,
      color: '#2196f3',
    },
    {
      icon: <DirectionsBoat fontSize="large" />,
      label: 'Ships Serviced',
      value: data.ships?.total || 0,
      subtitle: `${data.ships?.completion_rate || 0}% completion`,
      color: '#4caf50',
    },
    {
      icon: <Scale fontSize="large" />,
      label: 'Tonnage Handled',
      value: `${data.tonnage?.total || 0}`,
      subtitle: `${data.tonnage?.avg_per_day || 0}t/day`,
      color: '#ff9800',
    },
    {
      icon: <Speed fontSize="large" />,
      label: 'Efficiency Score',
      value: `${data.efficiency_score || 0}`,
      subtitle: 'out of 100',
      color: '#9c27b0',
    },
  ];

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" fontWeight="bold" gutterBottom>
          Operational Performance
        </Typography>

        <Grid container spacing={2} mt={1}>
          {kpiCards.map((kpi, index) => (
            <Grid item xs={6} sm={3} key={index}>
              <Box textAlign="center">
                <Box sx={{ color: kpi.color, mb: 1 }}>{kpi.icon}</Box>
                <Typography variant="body2" color="text.secondary">{kpi.label}</Typography>
                <Typography variant="h5" fontWeight="bold">{kpi.value}</Typography>
                <Typography variant="caption" color="text.secondary">{kpi.subtitle}</Typography>
              </Box>
            </Grid>
          ))}

          {detailed && (
            <>
              <Grid item xs={12} sm={6}>
                <Typography variant="body2" color="text.secondary">Berth Utilization</Typography>
                <Typography variant="h5">{data.berth_utilization_percent || 0}%</Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="body2" color="text.secondary">Avg Processing Time</Typography>
                <Typography variant="h5">{data.trucks?.avg_processing_time_hours || 0}h</Typography>
              </Grid>
            </>
          )}
        </Grid>
      </CardContent>
    </Card>
  );
};

export default OperationalKPIs;
