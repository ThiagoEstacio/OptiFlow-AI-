/**
 * Overall Health Score Component
 * Displays the unified terminal health score with visual indicator
 */
import React from 'react';
import { Box, Typography } from '@mui/material';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend } from 'recharts';

interface Props {
  score: number;
  status: string;
  maintenanceComponent: number;
  operationsComponent: number;
}

const OverallHealthScore: React.FC<Props> = ({
  score,
  status,
  maintenanceComponent,
  operationsComponent,
}) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'excellent':
        return '#4caf50';
      case 'good':
        return '#2196f3';
      case 'warning':
        return '#ff9800';
      case 'critical':
        return '#f44336';
      default:
        return '#9e9e9e';
    }
  };

  const data = [
    { name: 'Maintenance', value: maintenanceComponent || 0 },
    { name: 'Operations', value: operationsComponent || 0 },
  ];

  const COLORS = ['rgba(255,255,255,0.8)', 'rgba(255,255,255,0.5)'];

  return (
    <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap', alignItems: 'center' }}>
      <Box sx={{ flex: '1 1 calc(50% - 12px)', minWidth: '300px', textAlign: 'center' }}>
        <Typography variant="h2" fontWeight="bold" sx={{ fontSize: { xs: '3rem', md: '4rem' } }}>
          {score || 0}
          <Typography component="span" variant="h4" sx={{ opacity: 0.8 }}>
            /100
          </Typography>
        </Typography>
        <Typography variant="h5" fontWeight="medium" sx={{ mt: 1, textTransform: 'uppercase' }}>
          {status || 'Unknown'}
        </Typography>
        <Typography variant="body1" sx={{ mt: 2, opacity: 0.9 }}>
          Overall Terminal Health
        </Typography>
      </Box>

      <Box sx={{ flex: '1 1 calc(50% - 12px)', minWidth: '300px', height: 200 }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={80}
              fill="#8884d8"
              paddingAngle={5}
              dataKey="value"
              label={({ name, value }) => `${name}: ${value}`}
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Legend
              verticalAlign="bottom"
              height={36}
              wrapperStyle={{ color: 'white' }}
            />
          </PieChart>
        </ResponsiveContainer>
      </Box>
    </Box>
  );
};

export default OverallHealthScore;
