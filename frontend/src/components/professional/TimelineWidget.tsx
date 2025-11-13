/**
 * Professional Timeline Widget - Events and Activities Display
 * Vertical timeline for maintenance, alarms, and system events
 */
import React from 'react';
import {
  Card,
  CardHeader,
  CardContent,
  Typography,
  Box,
  Stack,
  Avatar,
  Chip,
  IconButton,
  alpha,
  useTheme
} from '@mui/material';
import {
  MoreVert,
  CheckCircle,
  Error,
  Warning,
  Info,
  Build,
  Notifications,
  Settings
} from '@mui/icons-material';
import { formatDistanceToNow } from 'date-fns';

export interface TimelineEvent {
  id: string;
  title: string;
  description?: string;
  timestamp: Date;
  type: 'success' | 'error' | 'warning' | 'info' | 'maintenance' | 'alarm' | 'system';
  severity?: 'critical' | 'high' | 'medium' | 'low';
  user?: string;
  tags?: string[];
}

interface TimelineWidgetProps {
  title: string;
  events: TimelineEvent[];
  maxEvents?: number;
  showTime?: boolean;
  onEventClick?: (event: TimelineEvent) => void;
}

export const TimelineWidget: React.FC<TimelineWidgetProps> = ({
  title,
  events,
  maxEvents = 10,
  showTime = true,
  onEventClick
}) => {
  const theme = useTheme();

  const getEventIcon = (type: TimelineEvent['type']) => {
    switch (type) {
      case 'success':
        return <CheckCircle />;
      case 'error':
        return <Error />;
      case 'warning':
        return <Warning />;
      case 'info':
        return <Info />;
      case 'maintenance':
        return <Build />;
      case 'alarm':
        return <Notifications />;
      case 'system':
        return <Settings />;
      default:
        return <Info />;
    }
  };

  const getEventColor = (type: TimelineEvent['type'], severity?: TimelineEvent['severity']) => {
    if (severity === 'critical') return theme.palette.error.main;
    if (severity === 'high') return theme.palette.error.light;
    if (severity === 'medium') return theme.palette.warning.main;
    if (severity === 'low') return theme.palette.info.main;

    switch (type) {
      case 'success':
        return theme.palette.success.main;
      case 'error':
        return theme.palette.error.main;
      case 'warning':
        return theme.palette.warning.main;
      case 'maintenance':
        return theme.palette.info.main;
      case 'alarm':
        return theme.palette.error.main;
      case 'system':
        return theme.palette.primary.main;
      default:
        return theme.palette.info.main;
    }
  };

  const displayEvents = events.slice(0, maxEvents);

  return (
    <Card
      sx={{
        borderRadius: 2,
        height: '100%',
        display: 'flex',
        flexDirection: 'column'
      }}
    >
      <CardHeader
        title={
          <Typography variant="h6" fontWeight={600}>
            {title}
          </Typography>
        }
        action={
          <IconButton size="small">
            <MoreVert />
          </IconButton>
        }
        sx={{ pb: 1 }}
      />

      <CardContent sx={{ flex: 1, overflow: 'auto', pt: 0 }}>
        {displayEvents.length === 0 ? (
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              py: 6,
              color: 'text.secondary'
            }}
          >
            <Info sx={{ fontSize: 48, mb: 2, opacity: 0.3 }} />
            <Typography variant="body2">No events to display</Typography>
          </Box>
        ) : (
          <Box sx={{ position: 'relative' }}>
            {/* Vertical line */}
            <Box
              sx={{
                position: 'absolute',
                left: 20,
                top: 8,
                bottom: 8,
                width: 2,
                bgcolor: theme.palette.divider
              }}
            />

            {/* Events */}
            <Stack spacing={3}>
              {displayEvents.map((event, index) => {
                const eventColor = getEventColor(event.type, event.severity);

                return (
                  <Box
                    key={event.id}
                    sx={{
                      position: 'relative',
                      pl: 6,
                      cursor: onEventClick ? 'pointer' : 'default',
                      transition: 'all 0.2s',
                      '&:hover': onEventClick
                        ? {
                            bgcolor: alpha(theme.palette.action.hover, 0.5),
                            borderRadius: 1,
                            ml: -1,
                            pl: 7,
                            pr: 1,
                            py: 0.5
                          }
                        : {}
                    }}
                    onClick={() => onEventClick?.(event)}
                  >
                    {/* Icon */}
                    <Avatar
                      sx={{
                        position: 'absolute',
                        left: 0,
                        top: 0,
                        width: 40,
                        height: 40,
                        bgcolor: alpha(eventColor, 0.1),
                        color: eventColor,
                        border: `2px solid ${theme.palette.background.paper}`,
                        boxShadow: `0 0 0 2px ${theme.palette.divider}`
                      }}
                    >
                      {getEventIcon(event.type)}
                    </Avatar>

                    {/* Content */}
                    <Box>
                      {/* Header */}
                      <Stack
                        direction="row"
                        justifyContent="space-between"
                        alignItems="flex-start"
                        spacing={1}
                        mb={0.5}
                      >
                        <Typography variant="subtitle2" fontWeight={600}>
                          {event.title}
                        </Typography>

                        {showTime && (
                          <Typography
                            variant="caption"
                            color="text.secondary"
                            sx={{ whiteSpace: 'nowrap', flexShrink: 0 }}
                          >
                            {formatDistanceToNow(event.timestamp, { addSuffix: true })}
                          </Typography>
                        )}
                      </Stack>

                      {/* Description */}
                      {event.description && (
                        <Typography
                          variant="body2"
                          color="text.secondary"
                          sx={{
                            mb: event.tags || event.user ? 1 : 0,
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            display: '-webkit-box',
                            WebkitLineClamp: 2,
                            WebkitBoxOrient: 'vertical'
                          }}
                        >
                          {event.description}
                        </Typography>
                      )}

                      {/* Footer: User and Tags */}
                      <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                        {event.user && (
                          <Typography variant="caption" color="text.secondary">
                            {event.user}
                          </Typography>
                        )}

                        {event.tags && event.tags.length > 0 && (
                          <Stack direction="row" spacing={0.5} flexWrap="wrap">
                            {event.tags.map((tag) => (
                              <Chip
                                key={tag}
                                label={tag}
                                size="small"
                                sx={{
                                  height: 20,
                                  fontSize: '0.65rem',
                                  bgcolor: alpha(eventColor, 0.1),
                                  color: eventColor
                                }}
                              />
                            ))}
                          </Stack>
                        )}
                      </Stack>
                    </Box>
                  </Box>
                );
              })}
            </Stack>
          </Box>
        )}
      </CardContent>

      {/* Footer */}
      {events.length > maxEvents && (
        <Box
          sx={{
            p: 2,
            borderTop: 1,
            borderColor: 'divider',
            textAlign: 'center'
          }}
        >
          <Typography variant="caption" color="text.secondary">
            Showing {maxEvents} of {events.length} events
          </Typography>
        </Box>
      )}
    </Card>
  );
};
