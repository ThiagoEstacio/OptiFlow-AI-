import React from 'react';
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { Box, Typography, Paper } from '@mui/material';

interface ParetoItem {
  rank: number;
  failure_type: string;
  count: number;
  percentage: number;
  cumulative_percentage: number;
  is_vital_few: boolean;
}

interface ParetoChartProps {
  data: ParetoItem[];
  title?: string;
  showVitalFewLine?: boolean;
}

const ParetoChart: React.FC<ParetoChartProps> = ({
  data,
  title = 'Análise de Pareto',
  showVitalFewLine = true,
}) => {
  // Colors for bars
  const VITAL_FEW_COLOR = '#ff6b6b'; // Red for vital few (top 20% causing 80% problems)
  const USEFUL_MANY_COLOR = '#4ecdc4'; // Teal for useful many

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <Paper
          sx={{
            p: 2,
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            border: '1px solid #ccc',
          }}
        >
          <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
            {data.failure_type}
          </Typography>
          <Typography variant="body2">
            Rank: #{data.rank}
          </Typography>
          <Typography variant="body2">
            Ocorrências: {data.count}
          </Typography>
          <Typography variant="body2">
            Percentual: {data.percentage.toFixed(1)}%
          </Typography>
          <Typography variant="body2" sx={{ fontWeight: 'bold', mt: 1 }}>
            Acumulado: {data.cumulative_percentage.toFixed(1)}%
          </Typography>
          {data.is_vital_few && (
            <Typography
              variant="caption"
              sx={{
                display: 'block',
                mt: 1,
                color: VITAL_FEW_COLOR,
                fontWeight: 'bold',
              }}
            >
              🎯 VITAL FEW (80/20)
            </Typography>
          )}
        </Paper>
      );
    }
    return null;
  };

  // Custom label for bars
  const renderCustomBarLabel = (props: any) => {
    const { x, y, width, value } = props;
    return (
      <text
        x={x + width / 2}
        y={y - 5}
        fill="#666"
        textAnchor="middle"
        fontSize={11}
      >
        {value}
      </text>
    );
  };

  return (
    <Box>
      {title && (
        <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold' }}>
          {title}
        </Typography>
      )}

      <ResponsiveContainer width="100%" height={400}>
        <ComposedChart
          data={data}
          margin={{ top: 20, right: 30, left: 20, bottom: 80 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />

          <XAxis
            dataKey="failure_type"
            angle={-45}
            textAnchor="end"
            height={100}
            interval={0}
            tick={{ fontSize: 11 }}
          />

          <YAxis
            yAxisId="left"
            label={{
              value: 'Número de Ocorrências',
              angle: -90,
              position: 'insideLeft',
              style: { fontSize: 12 },
            }}
            tick={{ fontSize: 11 }}
          />

          <YAxis
            yAxisId="right"
            orientation="right"
            domain={[0, 100]}
            label={{
              value: 'Percentual Acumulado (%)',
              angle: 90,
              position: 'insideRight',
              style: { fontSize: 12 },
            }}
            tick={{ fontSize: 11 }}
          />

          <Tooltip content={<CustomTooltip />} />

          <Legend
            verticalAlign="top"
            height={36}
            iconType="square"
            wrapperStyle={{ fontSize: 12 }}
          />

          {/* Bar chart for frequency */}
          <Bar
            yAxisId="left"
            dataKey="count"
            name="Ocorrências"
            label={renderCustomBarLabel}
          >
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.is_vital_few ? VITAL_FEW_COLOR : USEFUL_MANY_COLOR}
              />
            ))}
          </Bar>

          {/* Line chart for cumulative percentage */}
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="cumulative_percentage"
            name="% Acumulado"
            stroke="#2196f3"
            strokeWidth={3}
            dot={{ fill: '#2196f3', r: 4 }}
            activeDot={{ r: 6 }}
          />

          {/* 80% reference line */}
          {showVitalFewLine && (
            <Line
              yAxisId="right"
              type="monotone"
              dataKey={() => 80}
              name="Linha 80% (Vital Few)"
              stroke="#ff9800"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={false}
            />
          )}
        </ComposedChart>
      </ResponsiveContainer>

      {/* Legend explanation */}
      <Box sx={{ mt: 2, display: 'flex', gap: 3, justifyContent: 'center', flexWrap: 'wrap' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box
            sx={{
              width: 16,
              height: 16,
              backgroundColor: VITAL_FEW_COLOR,
              borderRadius: 1,
            }}
          />
          <Typography variant="caption">
            Vital Few (causam 80% dos problemas)
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box
            sx={{
              width: 16,
              height: 16,
              backgroundColor: USEFUL_MANY_COLOR,
              borderRadius: 1,
            }}
          />
          <Typography variant="caption">
            Useful Many (causam 20% dos problemas)
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box
            sx={{
              width: 24,
              height: 2,
              backgroundColor: '#ff9800',
              borderRadius: 1,
            }}
          />
          <Typography variant="caption">
            Linha 80/20 (Princípio de Pareto)
          </Typography>
        </Box>
      </Box>

      {/* Summary statistics */}
      {data.length > 0 && (
        <Box sx={{ mt: 3, p: 2, backgroundColor: '#f5f5f5', borderRadius: 1 }}>
          <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
            📊 Estatísticas:
          </Typography>
          <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
            <Typography variant="body2">
              Total de tipos de falha: <strong>{data.length}</strong>
            </Typography>
            <Typography variant="body2">
              Vital Few:{' '}
              <strong style={{ color: VITAL_FEW_COLOR }}>
                {data.filter((d) => d.is_vital_few).length}
              </strong>
            </Typography>
            <Typography variant="body2">
              Ocorrências totais:{' '}
              <strong>{data.reduce((sum, d) => sum + d.count, 0)}</strong>
            </Typography>
            <Typography variant="body2">
              Impacto Vital Few:{' '}
              <strong style={{ color: VITAL_FEW_COLOR }}>
                {data.find((d) => !d.is_vital_few)?.cumulative_percentage.toFixed(1) || '0'}%
              </strong>
            </Typography>
          </Box>
        </Box>
      )}
    </Box>
  );
};

export default ParetoChart;
