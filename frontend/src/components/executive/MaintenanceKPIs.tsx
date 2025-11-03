import React from 'react';
import { Card, CardContent, Typography, Grid, Box, LinearProgress, Chip } from '@mui/material';
import { Build, Warning, TrendingUp, TrendingDown, Remove } from '@mui/icons-material';

interface Props {
  data: any;
  detailed?: boolean;
}

const MaintenanceKPIs: React.FC<Props> = ({ data, detailed = false }) => {
  if (!data) return null;

  const getTrendIcon = (trend: string) => {
    if (trend === 'improving') return <TrendingUp color="success" />;
    if (trend === 'declining') return <TrendingDown color="error" />;
    return <Remove />;
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" fontWeight="bold" gutterBottom>
          Maintenance & Asset Health
        </Typography>

        <Grid container spacing={2} mt={1}>
          <Grid item xs={12} sm={6}>
            <Box>
              <Typography variant="body2" color="text.secondary">Average Health Score</Typography>
              <Typography variant="h4" fontWeight="bold">{data.average_health_score || 0}</Typography>
              <LinearProgress
                variant="determinate"
                value={data.average_health_score || 0}
                sx={{ mt: 1, height: 8, borderRadius: 1 }}
              />
            </Box>
          </Grid>

          <Grid item xs={12} sm={6}>
            <Box>
              <Typography variant="body2" color="text.secondary">Health Trend</Typography>
              <Box display="flex" alignItems="center" mt={1}>
                {getTrendIcon(data.health_trend)}
                <Typography variant="h6" ml={1} textTransform="capitalize">
                  {data.health_trend || 'Stable'}
                </Typography>
              </Box>
            </Box>
          </Grid>

          <Grid item xs={12}>
            <Typography variant="body2" color="text.secondary" gutterBottom>Assets by Health</Typography>
            <Grid container spacing={1}>
              <Grid item>
                <Chip label={`Healthy: ${data.assets_by_health?.healthy || 0}`} color="success" size="small" />
              </Grid>
              <Grid item>
                <Chip label={`Warning: ${data.assets_by_health?.warning || 0}`} color="warning" size="small" />
              </Grid>
              <Grid item>
                <Chip label={`Critical: ${data.assets_by_health?.critical || 0}`} color="error" size="small" />
              </Grid>
            </Grid>
          </Grid>

          {detailed && (
            <>
              <Grid item xs={12} sm={6}>
                <Typography variant="body2" color="text.secondary">Total Alarms</Typography>
                <Typography variant="h5">{data.alarms?.total || 0}</Typography>
                <Typography variant="caption">Avg: {data.alarms?.avg_per_day || 0}/day</Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="body2" color="text.secondary">Critical Alarms</Typography>
                <Typography variant="h5" color="error.main">{data.alarms?.critical || 0}</Typography>
              </Grid>
            </>
          )}
        </Grid>
      </CardContent>
    </Card>
  );
};

export default MaintenanceKPIs;
