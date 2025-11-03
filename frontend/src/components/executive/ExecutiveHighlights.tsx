import React from 'react';
import { Box, Card, CardContent, Typography, Grid, Chip } from '@mui/material';
import { TrendingUp, CheckCircle, Build, LocalShipping } from '@mui/icons-material';

interface Props {
  highlights: string[];
  roiData: any;
}

const ExecutiveHighlights: React.FC<Props> = ({ highlights, roiData }) => {
  if (!highlights || highlights.length === 0) return null;

  return (
    <Card sx={{ mb: 3, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
      <CardContent>
        <Typography variant="h6" fontWeight="bold" gutterBottom>
          🎯 This Week's Highlights
        </Typography>
        <Grid container spacing={2} mt={1}>
          {highlights.map((highlight, index) => (
            <Grid item xs={12} sm={6} md={4} key={index}>
              <Box display="flex" alignItems="flex-start">
                <CheckCircle sx={{ mr: 1, mt: 0.5, fontSize: 20 }} />
                <Typography variant="body2">{highlight}</Typography>
              </Box>
            </Grid>
          ))}
        </Grid>
      </CardContent>
    </Card>
  );
};

export default ExecutiveHighlights;
