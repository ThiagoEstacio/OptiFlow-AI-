/**
 * PDCA #5: Critical Alarm Notification System (No MUI Version)
 *
 * Features:
 * - Screen flash (red overlay) for Critical/High alarms
 * - Audio beep (3x 100ms at 880Hz) for attention
 * - Persistent notification until acknowledged
 * - Target MTTR <30 seconds
 */
import React, { useEffect, useState, useCallback, useRef } from 'react';
import { AlertTriangle, Bell, Volume2, VolumeX, X } from 'lucide-react';

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
  const bgColor = alarm.severity === 'CRITICAL' ? 'bg-red-600' : 'bg-amber-500';
  const borderColor = alarm.severity === 'CRITICAL' ? 'border-red-700' : 'border-amber-600';

  return (
    <>
      {/* Screen Flash Overlay */}
      {isCritical && flashVisible && (
        <div
          className="fixed inset-0 pointer-events-none z-[9998] animate-pulse"
          style={{
            backgroundColor: alarm.severity === 'CRITICAL'
              ? 'rgba(220, 38, 38, 0.15)'
              : 'rgba(245, 158, 11, 0.15)'
          }}
        />
      )}

      {/* Notification Card */}
      <div
        className={`fixed top-5 right-5 max-w-md z-[9999] ${bgColor} text-white rounded-lg shadow-2xl border-2 ${borderColor} backdrop-blur-sm ${isCritical ? 'animate-shake' : ''}`}
        style={{
          boxShadow: alarm.severity === 'CRITICAL'
            ? '0 0 20px rgba(220, 38, 38, 0.5)'
            : '0 0 20px rgba(245, 158, 11, 0.5)'
        }}
      >
        <div className="p-4">
          {/* Header */}
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Bell className="w-7 h-7 animate-ring" />
              <span className="text-lg font-bold">{alarm.severity} ALARM</span>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={toggleSound}
                className="p-1.5 rounded hover:bg-white/20 transition-colors"
                title={soundEnabled ? 'Mute sound' : 'Enable sound'}
              >
                {soundEnabled ? <Volume2 className="w-5 h-5" /> : <VolumeX className="w-5 h-5" />}
              </button>
              <button
                onClick={handleClose}
                className="p-1.5 rounded hover:bg-white/20 transition-colors"
                title="Close"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Tag Name */}
          {alarm.tag_name && (
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="w-5 h-5" />
              <span className="font-semibold">{alarm.tag_name}</span>
            </div>
          )}

          {/* Message */}
          <p className="font-medium mb-3">{alarm.message}</p>

          {/* Value Details */}
          <div className="bg-black/20 rounded p-3 mb-4 space-y-1">
            <div className="flex justify-between text-sm">
              <span>Current Value:</span>
              <span className="font-bold">{alarm.value.toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span>Limit:</span>
              <span className="font-bold">{alarm.limit.toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span>Time:</span>
              <span className="font-bold">{new Date(alarm.occurred_at).toLocaleTimeString()}</span>
            </div>
          </div>

          {/* Acknowledge Button */}
          <button
            onClick={handleAcknowledge}
            className={`w-full py-3 rounded font-bold text-base transition-colors ${
              alarm.severity === 'CRITICAL'
                ? 'bg-white text-red-600 hover:bg-red-50'
                : 'bg-white text-amber-600 hover:bg-amber-50'
            }`}
          >
            ACKNOWLEDGE ALARM
          </button>
        </div>
      </div>

      {/* CSS Animations */}
      <style>
        {`
          @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-5px); }
            75% { transform: translateX(5px); }
          }
          .animate-shake {
            animation: shake 0.5s ease-in-out infinite;
          }

          @keyframes ring {
            0%, 100% { transform: rotate(-15deg); }
            50% { transform: rotate(15deg); }
          }
          .animate-ring {
            animation: ring 1s ease-in-out infinite;
          }
        `}
      </style>
    </>
  );
};
