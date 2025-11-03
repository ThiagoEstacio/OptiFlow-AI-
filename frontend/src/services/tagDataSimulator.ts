/**
 * Tag Data Simulator - Bridge between real simulator and tag system
 *
 * This module wraps the professional GrainTerminalSimulator and provides
 * the legacy interface for backwards compatibility
 */

import { grainTerminalSimulator, GrainTerminalSimulator } from './grainTerminalSimulator';
import { PORT_GRAIN_TERMINAL_TAGS, Tag, getTagById } from '../data/portGrainTerminalTags';

export interface TagValue {
  tagId: string;
  value: number;
  timestamp: Date;
  quality: 'good' | 'uncertain' | 'bad';
}

export interface AlarmCondition {
  tagId: string;
  tagName: string;
  value: number;
  condition: 'high' | 'low';
  threshold: number;
  severity: 'warning' | 'alarm';
  timestamp: Date;
}

class TagDataSimulator {
  private simulator: GrainTerminalSimulator;
  private updateInterval: NodeJS.Timeout | null = null;
  private running: boolean = false;
  private simulationSpeed: number = 1.0;
  private alarmsEnabled: boolean = true;

  constructor() {
    this.simulator = grainTerminalSimulator;
  }

  /**
   * Start the simulation
   */
  public start(): void {
    if (this.running) return;

    console.log('🚀 Starting Grain Terminal Simulator');
    this.simulator.start();
    this.running = true;

    // Update at 1Hz (or faster based on speed)
    const interval_ms = 1000 / this.simulationSpeed;
    this.updateInterval = setInterval(() => {
      this.simulator.step();
    }, interval_ms);
  }

  /**
   * Stop the simulation
   */
  public stop(): void {
    if (!this.running) return;

    console.log('⏹️ Stopping Grain Terminal Simulator');
    this.simulator.stop();
    this.running = false;

    if (this.updateInterval) {
      clearInterval(this.updateInterval);
      this.updateInterval = null;
    }
  }

  /**
   * Emergency stop
   */
  public emergencyStop(): void {
    this.simulator.emergencyStop();
    this.stop();
  }

  /**
   * Reset simulation
   */
  public reset(): void {
    this.simulator.reset();
  }

  /**
   * Get current value for a tag
   */
  public getTagValue(tagId: string): number | null {
    const value = this.simulator.getTagValue(tagId);
    return value !== null && typeof value === 'number' ? value : null;
  }

  /**
   * Update simulation values (legacy - now handled by internal step)
   */
  public updateValues(): void {
    // No-op - values updated by internal step loop
  }

  /**
   * Set simulation speed
   */
  public setSimulationSpeed(speed: number): void {
    this.simulationSpeed = Math.max(0.1, Math.min(10, speed));

    // Restart interval with new speed
    if (this.running) {
      this.stop();
      this.start();
    }
  }

  /**
   * Get simulation speed
   */
  public getSimulationSpeed(): number {
    return this.simulationSpeed;
  }

  /**
   * Set shiploader setpoint
   */
  public setShipLoadingActive(active: boolean): void {
    if (active) {
      this.simulator.setShipLoaderSetpoint(1500);
    } else {
      this.simulator.setShipLoaderSetpoint(0);
    }
  }

  /**
   * Set gate manual control
   */
  public setGatePosition(gateId: number, open_pct: number): void {
    this.simulator.setGateManual(gateId, open_pct);
  }

  /**
   * Enable/disable truck receiving (legacy)
   */
  public setTruckReceivingActive(active: boolean): void {
    // Gates are now controlled by PI controller
    // This is kept for backwards compatibility
  }

  /**
   * Enable/disable alarms
   */
  public setAlarmsEnabled(enabled: boolean): void {
    this.alarmsEnabled = enabled;
  }

  /**
   * Trigger high temperature alarm (for testing)
   */
  public triggerHighTemperatureAlarm(): void {
    // Temperature will naturally rise with load
    console.log('⚠️ Monitoring thermal conditions...');
  }

  /**
   * Trigger conveyor jam (for testing)
   */
  public triggerConveyorJam(): void {
    console.log('⚠️ Conveyor jam simulation not yet implemented');
  }

  /**
   * Get active alarms
   */
  public getActiveAlarms(): AlarmCondition[] {
    if (!this.alarmsEnabled) return [];

    const state = this.simulator.getState();
    const alarmConditions: AlarmCondition[] = [];

    // Convert simulator alarms to AlarmCondition format
    state.alarms.forEach(alarm => {
      if (alarm.active) {
        alarmConditions.push({
          tagId: alarm.tag,
          tagName: alarm.tag,
          value: 0,
          condition: 'high',
          threshold: 0,
          severity: alarm.latched ? 'alarm' : 'warning',
          timestamp: new Date(alarm.timestamp * 1000)
        });
      }
    });

    state.trips.forEach(trip => {
      if (trip.active) {
        alarmConditions.push({
          tagId: trip.tag,
          tagName: trip.tag,
          value: 0,
          condition: 'high',
          threshold: 0,
          severity: 'alarm',
          timestamp: new Date(trip.timestamp * 1000)
        });
      }
    });

    return alarmConditions;
  }

  /**
   * Get simulation state (for debugging/display)
   */
  public getSimulatorState() {
    return this.simulator.getState();
  }

  /**
   * Check if simulation is running
   */
  public isRunning(): boolean {
    return this.running;
  }
}

// Singleton instance
export const tagDataSimulator = new TagDataSimulator();
