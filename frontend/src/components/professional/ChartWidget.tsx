/**
 * Professional Chart Widget - Enterprise Data Visualization
 * Supports multiple chart types with professional styling
 */
import React from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Typography,
  Box,
  IconButton,
  Menu,
  MenuItem,
  Chip,
  Stack,
  alpha,
  useTheme,
  Avatar
} from '@mui/material';
import {
  MoreVert,
  Download,
  Fullscreen,
  Refresh,
  TrendingUp,
  TrendingDown,
  Remove
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

interface ChartWidgetProps {
  title: string;
  subtitle?: string;
  data: any[];
  type?: 'line' | 'area' | 'bar';
  dataKey: string;
  xAxisKey: string;
  color?: 'primary' | 'secondary' | 'success' | 'error' | 'warning' | 'info';
  height?: number;
  showGrid?: boolean;
  showLegend?: boolean;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  onRefresh?: () => void;
  onDownload?: () => void;
  onFullscreen?: () => void;
  loading?: boolean;
  actions?: React.ReactNode;
}

export const ChartWidget: React.FC<ChartWidgetProps> = ({
  title,
  subtitle,
  data,
  type = 'line',
  dataKey,
  xAxisKey,
  color = 'primary',
  height = 300,
  showGrid = true,
  showLegend = false,
  trend,
  trendValue,
  onRefresh,
  onDownload,
  onFullscreen,
  loading = false,
  actions
}) => {
  const theme = useTheme();
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const chartColor = theme.palette[color].main;
  const gradientId = `gradient-${color}-${dataKey}`;

  const getTrendIcon = () => {
    if (trend === 'up') return <TrendingUp fontSize="small" />;
    if (trend === 'down') return <TrendingDown fontSize="small" />;
    return <Remove fontSize="small" />;
  };

  const getTrendColor = () => {
    if (trend === 'up') return theme.palette.success.main;
    if (trend === 'down') return theme.palette.error.main;
    return theme.palette.text.secondary;
  };

  const renderChart = () => {
    const commonProps = {
      data,
      margin: { top: 10, right: 10, left: 0, bottom: 0 }
    };

    switch (type) {
      case 'area':
        return (
          <AreaChart {...commonProps}>
            <defs>
              <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={chartColor} stopOpacity={0.3} />
                <stop offset="95%" stopColor={chartColor} stopOpacity={0} />
              </linearGradient>
            </defs>
            {showGrid && (
              <CartesianGrid
                strokeDasharray="3 3"
                stroke={alpha(theme.palette.divider, 0.5)}
                vertical={false}
              />
            )}
            <XAxis
              dataKey={xAxisKey}
              tick={{ fontSize: 12, fill: theme.palette.text.secondary }}
              stroke={theme.palette.divider}
            />
            <YAxis
              tick={{ fontSize: 12, fill: theme.palette.text.secondary }}
              stroke={theme.palette.divider}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: theme.palette.background.paper,
                border: `1px solid ${theme.palette.divider}`,
                borderRadius: 8,
                boxShadow: theme.shadows[4]
              }}
            />
            {showLegend && <Legend />}
            <Area
              type="monotone"
              dataKey={dataKey}
              stroke={chartColor}
              strokeWidth={2}
              fill={`url(#${gradientId})`}
              animationDuration={1000}
            />
          </AreaChart>
        );

      case 'bar':
        return (
          <BarChart {...commonProps}>
            {showGrid && (
              <CartesianGrid
                strokeDasharray="3 3"
                stroke={alpha(theme.palette.divider, 0.5)}
                vertical={false}
              />
            )}
            <XAxis
              dataKey={xAxisKey}
              tick={{ fontSize: 12, fill: theme.palette.text.secondary }}
              stroke={theme.palette.divider}
            />
            <YAxis
              tick={{ fontSize: 12, fill: theme.palette.text.secondary }}
              stroke={theme.palette.divider}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: theme.palette.background.paper,
                border: `1px solid ${theme.palette.divider}`,
                borderRadius: 8,
                boxShadow: theme.shadows[4]
              }}
            />
            {showLegend && <Legend />}
            <Bar
              dataKey={dataKey}
              fill={chartColor}
              radius={[8, 8, 0, 0]}
              animationDuration={1000}
            />
          </BarChart>
        );

      default: // line
        return (
          <LineChart {...commonProps}>
            {showGrid && (
              <CartesianGrid
                strokeDasharray="3 3"
                stroke={alpha(theme.palette.divider, 0.5)}
                vertical={false}
              />
            )}
            <XAxis
              dataKey={xAxisKey}
              tick={{ fontSize: 12, fill: theme.palette.text.secondary }}
              stroke={theme.palette.divider}
            />
            <YAxis
              tick={{ fontSize: 12, fill: theme.palette.text.secondary }}
              stroke={theme.palette.divider}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: theme.palette.background.paper,
                border: `1px solid ${theme.palette.divider}`,
                borderRadius: 8,
                boxShadow: theme.shadows[4]
              }}
            />
            {showLegend && <Legend />}
            <Line
              type="monotone"
              dataKey={dataKey}
              stroke={chartColor}
              strokeWidth={2}
              dot={false}
              animationDuration={1000}
            />
          </LineChart>
        );
    }
  };

  return (
    <Card
      sx={{
        borderRadius: 2,
        boxShadow: theme.shadows[2],
        transition: 'box-shadow 0.3s',
        '&:hover': {
          boxShadow: theme.shadows[4]
        }
      }}
    >
      <CardHeader
        avatar={
          trend && (
            <Avatar
              sx={{
                bgcolor: alpha(getTrendColor(), 0.1),
                color: getTrendColor(),
                width: 40,
                height: 40
              }}
            >
              {getTrendIcon()}
            </Avatar>
          )
        }
        title={
          <Typography variant="h6" fontWeight={600}>
            {title}
          </Typography>
        }
        subheader={
          <Stack direction="row" spacing={1} alignItems="center" mt={0.5}>
            {subtitle && (
              <Typography variant="body2" color="text.secondary">
                {subtitle}
              </Typography>
            )}
            {trendValue && (
              <Chip
                label={trendValue}
                size="small"
                sx={{
                  bgcolor: alpha(getTrendColor(), 0.1),
                  color: getTrendColor(),
                  fontWeight: 600,
                  height: 20,
                  fontSize: '0.7rem'
                }}
              />
            )}
          </Stack>
        }
        action={
          <Stack direction="row" spacing={0.5}>
            {actions}
            <IconButton size="small" onClick={handleMenuClick}>
              <MoreVert />
            </IconButton>
          </Stack>
        }
        sx={{ pb: 1 }}
      />

      <CardContent sx={{ pt: 0 }}>
        <Box sx={{ width: '100%', height }}>
          {loading ? (
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%',
                color: 'text.secondary'
              }}
            >
              <Typography>Loading chart...</Typography>
            </Box>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              {renderChart()}
            </ResponsiveContainer>
          )}
        </Box>
      </CardContent>

      <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleMenuClose}>
        {onRefresh && (
          <MenuItem
            onClick={() => {
              onRefresh();
              handleMenuClose();
            }}
          >
            <Refresh fontSize="small" sx={{ mr: 1 }} />
            Refresh
          </MenuItem>
        )}
        {onDownload && (
          <MenuItem
            onClick={() => {
              onDownload();
              handleMenuClose();
            }}
          >
            <Download fontSize="small" sx={{ mr: 1 }} />
            Download
          </MenuItem>
        )}
        {onFullscreen && (
          <MenuItem
            onClick={() => {
              onFullscreen();
              handleMenuClose();
            }}
          >
            <Fullscreen fontSize="small" sx={{ mr: 1 }} />
            Fullscreen
          </MenuItem>
        )}
      </Menu>
    </Card>
  );
};
