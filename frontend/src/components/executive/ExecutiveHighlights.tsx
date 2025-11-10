import React from 'react';
import { Box, Card, CardContent, Typography, Chip } from '@mui/material';
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
          This Week's Highlights
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mt: 1 }}>
          {highlights.map((highlight, index) => (
            <Box key={index} sx={{ flex: '1 1 calc(33.333% - 11px)', minWidth: '250px', display: 'flex', alignItems: 'flex-start' }}>
              <CheckCircle sx={{ mr: 1, mt: 0.5, fontSize: 20 }} />
              <Typography variant="body2">{highlight}</Typography>
            </Box>
          ))}
        </Box>
      </CardContent>
    </Card>
  );
};

export default ExecutiveHighlights;
