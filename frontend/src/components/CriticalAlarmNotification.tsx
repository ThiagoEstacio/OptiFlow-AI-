/**
 * PDCA #5: Critical Alarm Notification System
 *
 * Features:
 * - Screen flash (red overlay) for Critical/High alarms
 * - Audio beep (3x 100ms at 880Hz) for attention
 * - Persistent notification until acknowledged
 * - Target MTTR <30 seconds
 */
import React, { useEffect, useState, useCallback, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Stack,
  Fade,
  IconButton,
  Tooltip,
  alpha
} from '@mui/material';
import {
  NotificationsActive,
  VolumeOff,
  VolumeUp,
  Close,
  Warning
} from '@mui/icons-material';

interface CriticalAlarm {
  id: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  message: string;
  tag_name?: string;
  value: number;
  limit: number;
  occurred_at: string;
}

interface CriticalAlarmNotificationProps {
  alarm: CriticalAlarm | null;
  onAcknowledge: (alarmId: string) => void;
  onClose: () => void;
}

/**
 * Audio Beep Generator
 * Generates 880Hz beep (musical note A5) for 100ms, 3 times with 200ms interval
 */
class AudioBeeper {
  private audioContext: AudioContext | null = null;
  private enabled: boolean = true;

  constructor() {
    // Create AudioContext on user interaction (browser requirement)
    if (typeof window !== 'undefined' && 'AudioContext' in window) {
      this.audioContext = new AudioContext();
    }
  }

  setEnabled(enabled: boolean) {
    this.enabled = enabled;
  }

  async beep(frequency: number = 880, duration: number = 100): Promise<void> {
    if (!this.enabled || !this.audioContext) return;

    const oscillator = this.audioContext.createOscillator();
    const gainNode = this.audioContext.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(this.audioContext.destination);

    oscillator.frequency.value = frequency;
    oscillator.type = 'sine';

    // ADSR envelope for smoother sound
    gainNode.gain.setValueAtTime(0, this.audioContext.currentTime);
    gainNode.gain.linearRampToValueAtTime(0.3, this.audioContext.currentTime + 0.01); // Attack
    gainNode.gain.linearRampToValueAtTime(0.2, this.audioContext.currentTime + duration / 1000 - 0.01); // Sustain
    gainNode.gain.linearRampToValueAtTime(0, this.audioContext.currentTime + duration / 1000); // Release

    oscillator.start(this.audioContext.currentTime);
    oscillator.stop(this.audioContext.currentTime + duration / 1000);

    return new Promise(resolve => {
      setTimeout(resolve, duration);
    });
  }

  async playAlertSequence(): Promise<void> {
    if (!this.enabled) return;

    // 3 beeps with 200ms interval
    for (let i = 0; i < 3; i++) {
      await this.beep(880, 100);
      if (i < 2) await new Promise(resolve => setTimeout(resolve, 200));
    }
  }

  destroy() {
    if (this.audioContext) {
      this.audioContext.close();
    }
  }
}

export const CriticalAlarmNotification: React.FC<CriticalAlarmNotificationProps> = ({
  alarm,
  onAcknowledge,
  onClose
}) => {
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [flashVisible, setFlashVisible] = useState(false);
  const [hasPlayed, setHasPlayed] = useState(false);
  const beeperRef = useRef<AudioBeeper | null>(null);

  // Initialize audio beeper
  useEffect(() => {
    beeperRef.current = new AudioBeeper();
    return () => {
      beeperRef.current?.destroy();
    };
  }, []);

  // Handle alarm display and audio
  useEffect(() => {
    if (!alarm || hasPlayed) return;

    const isCritical = alarm.severity === 'CRITICAL' || alarm.severity === 'HIGH';
    if (!isCritical) return;

    // Screen flash effect
    setFlashVisible(true);
    const flashTimer = setInterval(() => {
      setFlashVisible(prev => !prev);
    }, 500); // Flash every 500ms

    // Audio alert
    if (soundEnabled && beeperRef.current) {
      beeperRef.current.playAlertSequence();
      setHasPlayed(true);
    }

    return () => {
      clearInterval(flashTimer);
    };
  }, [alarm, soundEnabled, hasPlayed]);

  // Update sound enabled state
  useEffect(() => {
    if (beeperRef.current) {
      beeperRef.current.setEnabled(soundEnabled);
    }
  }, [soundEnabled]);

  const handleAcknowledge = useCallback(() => {
    if (alarm) {
      onAcknowledge(alarm.id);
      setFlashVisible(false);
      setHasPlayed(false);
    }
  }, [alarm, onAcknowledge]);

  const handleClose = useCallback(() => {
    setFlashVisible(false);
    setHasPlayed(false);
    onClose();
  }, [onClose]);

  const toggleSound = useCallback(() => {
    setSoundEnabled(prev => !prev);
  }, []);

  if (!alarm) return null;

  const isCritical = alarm.severity === 'CRITICAL' || alarm.severity === 'HIGH';
  const severityColor = alarm.severity === 'CRITICAL' ? '#dc2626' : '#f59e0b';

  return (
    <>
      {/* Screen Flash Overlay */}
      {isCritical && flashVisible && (
        <Box
          sx={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: alpha(severityColor, 0.15),
            pointerEvents: 'none',
            zIndex: 9998,
            animation: 'pulse 0.5s ease-in-out infinite'
          }}
        />
      )}

      {/* Notification Card */}
      <Fade in={true}>
        <Paper
          elevation={24}
          sx={{
            position: 'fixed',
            top: 20,
            right: 20,
            maxWidth: 400,
            zIndex: 9999,
            backgroundColor: alpha(severityColor, 0.95),
            color: 'white',
            backdropFilter: 'blur(10px)',
            border: `2px solid ${severityColor}`,
            boxShadow: `0 0 20px ${alpha(severityColor, 0.5)}`,
            animation: isCritical ? 'shake 0.5s ease-in-out infinite' : 'none'
          }}
        >
          <Box sx={{ p: 2.5 }}>
            <Stack spacing={2}>
              {/* Header */}
              <Stack direction="row" alignItems="center" justifyContent="space-between">
                <Stack direction="row" alignItems="center" spacing={1}>
                  <NotificationsActive
                    sx={{
                      fontSize: 28,
                      animation: 'ring 1s ease-in-out infinite'
                    }}
                  />
                  <Typography variant="h6" fontWeight="bold">
                    {alarm.severity} ALARM
                  </Typography>
                </Stack>
                <Stack direction="row" spacing={0.5}>
                  <Tooltip title={soundEnabled ? 'Mute sound' : 'Enable sound'}>
                    <IconButton
                      size="small"
                      onClick={toggleSound}
                      sx={{ color: 'white' }}
                    >
                      {soundEnabled ? <VolumeUp /> : <VolumeOff />}
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Close">
                    <IconButton
                      size="small"
                      onClick={handleClose}
                      sx={{ color: 'white' }}
                    >
                      <Close />
                    </IconButton>
                  </Tooltip>
                </Stack>
              </Stack>

              {/* Tag Name */}
              {alarm.tag_name && (
                <Stack direction="row" spacing={1} alignItems="center">
                  <Warning />
                  <Typography variant="subtitle1" fontWeight="600">
                    {alarm.tag_name}
                  </Typography>
                </Stack>
              )}

              {/* Message */}
              <Typography variant="body1" sx={{ fontWeight: 500 }}>
                {alarm.message}
              </Typography>

              {/* Value Details */}
              <Box
                sx={{
                  p: 1.5,
                  backgroundColor: alpha('#000', 0.2),
                  borderRadius: 1
                }}
              >
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="body2">Current Value:</Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {alarm.value.toFixed(2)}
                  </Typography>
                </Stack>
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="body2">Limit:</Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {alarm.limit.toFixed(2)}
                  </Typography>
                </Stack>
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="body2">Time:</Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {new Date(alarm.occurred_at).toLocaleTimeString()}
                  </Typography>
                </Stack>
              </Box>

              {/* Acknowledge Button */}
              <Button
                variant="contained"
                fullWidth
                onClick={handleAcknowledge}
                sx={{
                  backgroundColor: 'white',
                  color: severityColor,
                  fontWeight: 'bold',
                  fontSize: '1rem',
                  py: 1.5,
                  '&:hover': {
                    backgroundColor: alpha('#fff', 0.9)
                  }
                }}
              >
                ACKNOWLEDGE ALARM
              </Button>
            </Stack>
          </Box>
        </Paper>
      </Fade>

      {/* CSS Animations */}
      <style>
        {`
          @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-5px); }
            75% { transform: translateX(5px); }
          }

          @keyframes ring {
            0%, 100% { transform: rotate(-15deg); }
            50% { transform: rotate(15deg); }
          }

          @keyframes pulse {
            0%, 100% { opacity: 0.15; }
            50% { opacity: 0.3; }
          }
        `}
      </style>
    </>
  );
};
