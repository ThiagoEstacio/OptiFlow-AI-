/**
 * Real-time Tag Data Simulator for Port Grain Terminal
 *
 * Simulates realistic tag values with:
 * - Correlations between related tags
 * - Normal variations and trends
 * - Occasional alarm conditions
 * - Production cycles (loading/unloading)
 */

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
  private currentValues: Map<string, number> = new Map();
  private lastUpdateTime: Map<string, Date> = new Map();
  private alarms: AlarmCondition[] = [];
  private alarmsEnabled: boolean = true;

  // Simulation state
  private shipLoadingActive: boolean = false;
  private truckReceivingActive: boolean = true;
  private simulationSpeed: number = 1.0; // 1.0 = normal speed

  constructor() {
    this.initializeValues();
  }

  /**
   * Initialize all tags with realistic starting values
   */
  private initializeValues(): void {
    PORT_GRAIN_TERMINAL_TAGS.forEach(tag => {
      let initialValue: number;

      // Set realistic initial values based on tag type
      if (tag.normal_range) {
        // Start within normal range
        const { min, max } = tag.normal_range;
        initialValue = min + (max - min) * 0.5; // Middle of normal range
      } else {
        // Start at 30% of max value for most tags
        initialValue = tag.max_value * 0.3;
      }

      // Special cases for specific tags
      if (tag.name.includes('STATUS')) {
        initialValue = 0; // Start stopped
      } else if (tag.name.includes('PROGRESS')) {
        initialValue = 0; // Start at 0%
      } else if (tag.name.includes('LEVEL') && tag.category === 'Storage') {
        initialValue = 60; // Silos start at 60%
      } else if (tag.name.includes('INVENTORY')) {
        initialValue = 30000; // 30,000 tonnes in storage
      }

      this.currentValues.set(tag.id, initialValue);
      this.lastUpdateTime.set(tag.id, new Date());
    });
  }

  /**
   * Get current value for a tag
   */
  getValue(tagId: string): TagValue | null {
    const value = this.currentValues.get(tagId);
    if (value === undefined) return null;

    return {
      tagId,
      value,
      timestamp: this.lastUpdateTime.get(tagId) || new Date(),
      quality: 'good'
    };
  }

  /**
   * Get all current values
   */
  getAllValues(): TagValue[] {
    return Array.from(this.currentValues.entries()).map(([tagId, value]) => ({
      tagId,
      value,
      timestamp: this.lastUpdateTime.get(tagId) || new Date(),
      quality: 'good'
    }));
  }

  /**
   * Update all tag values (call this periodically)
   */
  updateValues(): void {
    const now = new Date();

    // Update different tag categories with correlations
    this.updateReceptionTags(now);
    this.updateConveyorTags(now);
    this.updateElevatorTags(now);
    this.updateSiloTags(now);
    this.updateShipLoaderTags(now);
    this.updateQualityTags(now);
    this.updateUtilityTags(now);
    this.updateEnvironmentalTags(now);
    this.updateProductionMetrics(now);

    // Check for alarm conditions
    if (this.alarmsEnabled) {
      this.checkAlarms();
    }
  }

  private updateReceptionTags(now: Date): void {
    // Simulate truck arrivals and weighing
    const scale1Status = this.getValue('RCV_SCALE_01_STATUS')?.value || 0;
    const scale2Status = this.getValue('RCV_SCALE_02_STATUS')?.value || 0;

    if (this.truckReceivingActive) {
      // Random truck arrivals
      if (Math.random() < 0.05) { // 5% chance per update
        if (scale1Status === 0) {
          this.currentValues.set('RCV_SCALE_01_STATUS', 1); // Start weighing
          this.currentValues.set('RCV_SCALE_01_WEIGHT', 25000 + Math.random() * 20000);
        }
      }

      if (Math.random() < 0.05) {
        if (scale2Status === 0) {
          this.currentValues.set('RCV_SCALE_02_STATUS', 1);
          this.currentValues.set('RCV_SCALE_02_WEIGHT', 25000 + Math.random() * 20000);
        }
      }

      // Complete weighing after some time
      if (scale1Status === 1 && Math.random() < 0.1) {
        this.currentValues.set('RCV_SCALE_01_STATUS', 2); // Complete
      }
      if (scale2Status === 1 && Math.random() < 0.1) {
        this.currentValues.set('RCV_SCALE_02_STATUS', 2);
      }

      // Reset after completion
      if (scale1Status === 2 && Math.random() < 0.2) {
        this.currentValues.set('RCV_SCALE_01_STATUS', 0);
        this.currentValues.set('RCV_SCALE_01_WEIGHT', 0);
      }
      if (scale2Status === 2 && Math.random() < 0.2) {
        this.currentValues.set('RCV_SCALE_02_STATUS', 0);
        this.currentValues.set('RCV_SCALE_02_WEIGHT', 0);
      }

      // Queue count
      const queueCount = 5 + Math.floor(Math.random() * 15);
      this.currentValues.set('RCV_QUEUE_COUNT', queueCount);

      // Hopper levels
      this.updateWithNoise('RCV_HOPPER_01_LEVEL', 40, 80, 5);
      this.updateWithNoise('RCV_HOPPER_02_LEVEL', 40, 80, 5);

      // Gate openings correlate with hopper levels
      const hopper1Level = this.getValue('RCV_HOPPER_01_LEVEL')?.value || 50;
      this.currentValues.set('RCV_HOPPER_01_GATE', hopper1Level > 70 ? 80 : 40);

      const hopper2Level = this.getValue('RCV_HOPPER_02_LEVEL')?.value || 50;
      this.currentValues.set('RCV_HOPPER_02_GATE', hopper2Level > 70 ? 80 : 40);
    } else {
      // Reception offline
      this.currentValues.set('RCV_QUEUE_COUNT', 0);
      this.updateWithNoise('RCV_HOPPER_01_LEVEL', 0, 20, 2);
      this.updateWithNoise('RCV_HOPPER_02_LEVEL', 0, 20, 2);
    }

    this.lastUpdateTime.set('RCV_SCALE_01_STATUS', now);
    this.lastUpdateTime.set('RCV_SCALE_02_STATUS', now);
  }

  private updateConveyorTags(now: Date): void {
    const isOperating = this.truckReceivingActive || this.shipLoadingActive;

    if (isOperating) {
      // Conveyor speeds correlate with flow
      this.updateWithNoise('CONV_01_SPEED', 2.2, 3.0, 0.1);
      this.updateWithNoise('CONV_02_SPEED', 2.2, 3.0, 0.1);
      this.updateWithNoise('CONV_03_SPEED', 2.8, 3.6, 0.1);

      // Flow rates
      const conv1Speed = this.getValue('CONV_01_SPEED')?.value || 2.5;
      this.currentValues.set('CONV_01_FLOW_RATE', conv1Speed * 200 + Math.random() * 50);

      const conv2Speed = this.getValue('CONV_02_SPEED')?.value || 2.5;
      this.currentValues.set('CONV_02_FLOW_RATE', conv2Speed * 200 + Math.random() * 50);

      const conv3Speed = this.getValue('CONV_03_SPEED')?.value || 3.0;
      this.currentValues.set('CONV_03_FLOW_RATE', conv3Speed * 350 + Math.random() * 100);

      // Motor currents correlate with flow
      const conv1Flow = this.getValue('CONV_01_FLOW_RATE')?.value || 500;
      this.currentValues.set('CONV_01_MOTOR_CURRENT', 150 + conv1Flow * 0.15 + Math.random() * 20);

      const conv2Flow = this.getValue('CONV_02_FLOW_RATE')?.value || 500;
      this.currentValues.set('CONV_02_MOTOR_CURRENT', 150 + conv2Flow * 0.15 + Math.random() * 20);

      const conv3Flow = this.getValue('CONV_03_FLOW_RATE')?.value || 1000;
      this.currentValues.set('CONV_03_MOTOR_CURRENT', 200 + conv3Flow * 0.12 + Math.random() * 30);

      // Motor temperatures correlate with current
      const conv1Current = this.getValue('CONV_01_MOTOR_CURRENT')?.value || 200;
      this.updateWithNoise('CONV_01_MOTOR_TEMP', 45 + conv1Current * 0.08, 70, 2);
    } else {
      // Conveyors stopped
      this.updateWithNoise('CONV_01_SPEED', 0, 0.1, 0.01);
      this.updateWithNoise('CONV_02_SPEED', 0, 0.1, 0.01);
      this.updateWithNoise('CONV_03_SPEED', 0, 0.1, 0.01);
      this.currentValues.set('CONV_01_FLOW_RATE', 0);
      this.currentValues.set('CONV_02_FLOW_RATE', 0);
      this.currentValues.set('CONV_03_FLOW_RATE', 0);
      this.updateWithNoise('CONV_01_MOTOR_CURRENT', 0, 20, 2);
      this.updateWithNoise('CONV_02_MOTOR_CURRENT', 0, 20, 2);
      this.updateWithNoise('CONV_03_MOTOR_CURRENT', 0, 20, 2);
      this.updateWithNoise('CONV_01_MOTOR_TEMP', 30, 40, 1);
    }
  }

  private updateElevatorTags(now: Date): void {
    const isOperating = this.truckReceivingActive || this.shipLoadingActive;

    if (isOperating) {
      this.updateWithNoise('ELEV_01_SPEED', 1.9, 2.2, 0.05);
      this.updateWithNoise('ELEV_02_SPEED', 1.9, 2.2, 0.05);

      // Motor currents
      this.updateWithNoise('ELEV_01_MOTOR_CURRENT', 280, 400, 15);
      this.updateWithNoise('ELEV_02_MOTOR_CURRENT', 280, 400, 15);

      // Temperatures
      const elev1Current = this.getValue('ELEV_01_MOTOR_CURRENT')?.value || 300;
      this.updateWithNoise('ELEV_01_MOTOR_TEMP', 50 + elev1Current * 0.06, 75, 2);

      // Vibration
      this.updateWithNoise('ELEV_01_VIBRATION', 3, 7, 0.5);
    } else {
      this.updateWithNoise('ELEV_01_SPEED', 0, 0.1, 0.01);
      this.updateWithNoise('ELEV_02_SPEED', 0, 0.1, 0.01);
      this.updateWithNoise('ELEV_01_MOTOR_CURRENT', 0, 20, 2);
      this.updateWithNoise('ELEV_02_MOTOR_CURRENT', 0, 20, 2);
      this.updateWithNoise('ELEV_01_MOTOR_TEMP', 35, 45, 1);
      this.updateWithNoise('ELEV_01_VIBRATION', 0, 1, 0.1);
    }
  }

  private updateSiloTags(now: Date): void {
    // Silo levels change slowly
    if (this.truckReceivingActive) {
      // Receiving increases silo levels slightly
      this.updateWithNoise('SILO_01_LEVEL', 55, 75, 0.2);
      this.updateWithNoise('SILO_02_LEVEL', 60, 80, 0.2);
      this.updateWithNoise('SILO_03_LEVEL', 50, 70, 0.2);
    }

    if (this.shipLoadingActive) {
      // Shipping decreases silo levels
      const silo1Level = this.getValue('SILO_01_LEVEL')?.value || 60;
      this.currentValues.set('SILO_01_LEVEL', Math.max(20, silo1Level - 0.1));
    }

    // Weights correlate with levels
    const silo1Level = this.getValue('SILO_01_LEVEL')?.value || 60;
    this.currentValues.set('SILO_01_WEIGHT', silo1Level * 150); // 15,000t at 100%

    const silo2Level = this.getValue('SILO_02_LEVEL')?.value || 60;
    this.currentValues.set('SILO_02_WEIGHT', silo2Level * 150);

    const silo3Level = this.getValue('SILO_03_LEVEL')?.value || 60;
    this.currentValues.set('SILO_03_WEIGHT', silo3Level * 200); // 20,000t at 100%

    // Temperatures influenced by outdoor temp
    const outdoorTemp = this.getValue('ENV_OUTDOOR_TEMP')?.value || 25;
    this.updateWithNoise('SILO_01_TEMP_AVG', outdoorTemp - 5, outdoorTemp + 5, 0.5);
    this.updateWithNoise('SILO_01_TEMP_TOP', outdoorTemp - 3, outdoorTemp + 8, 0.5);
    this.updateWithNoise('SILO_01_TEMP_BOTTOM', outdoorTemp - 8, outdoorTemp + 2, 0.5);
    this.updateWithNoise('SILO_02_TEMP_AVG', outdoorTemp - 5, outdoorTemp + 5, 0.5);
    this.updateWithNoise('SILO_03_TEMP_AVG', outdoorTemp - 5, outdoorTemp + 5, 0.5);

    // Humidity
    this.updateWithNoise('SILO_01_HUMIDITY', 11, 13.5, 0.2);
    this.updateWithNoise('SILO_02_HUMIDITY', 11, 13.5, 0.2);

    // Aeration fans
    const silo1Temp = this.getValue('SILO_01_TEMP_AVG')?.value || 25;
    this.currentValues.set('SILO_01_AERATION_FAN', silo1Temp > 30 ? 1 : 0);
  }

  private updateShipLoaderTags(now: Date): void {
    if (this.shipLoadingActive) {
      // Boom and slew angles
      this.updateWithNoise('SHIP_LOADER_BOOM_ANGLE', 15, 30, 1);
      this.updateWithNoise('SHIP_LOADER_SLEW_ANGLE', -20, 20, 2);

      // Flow rate
      this.updateWithNoise('SHIP_LOADER_FLOW_RATE', 1800, 2600, 50);

      // Motor current correlates with flow
      const flowRate = this.getValue('SHIP_LOADER_FLOW_RATE')?.value || 2000;
      this.currentValues.set('SHIP_LOADER_MOTOR_CURRENT', 250 + flowRate * 0.1 + Math.random() * 30);

      // Vibration
      this.updateWithNoise('SHIP_LOADER_VIBRATION', 3, 8, 0.5);

      // Total loaded increases
      const currentLoaded = this.getValue('SHIP_TOTAL_LOADED')?.value || 0;
      const increment = (flowRate / 3600) * 5; // tonnes per 5 seconds
      this.currentValues.set('SHIP_TOTAL_LOADED', Math.min(75000, currentLoaded + increment));

      // Loading progress
      const totalLoaded = this.getValue('SHIP_TOTAL_LOADED')?.value || 0;
      this.currentValues.set('SHIP_LOADING_PROGRESS', (totalLoaded / 75000) * 100);

      // Draft increases with load
      const draft = 8 + (totalLoaded / 75000) * 8; // 8m to 16m
      this.currentValues.set('SHIP_DRAFT_FORE', draft + Math.random() * 0.3);
      this.currentValues.set('SHIP_DRAFT_AFT', draft + Math.random() * 0.3);

      // Dust suppression
      this.updateWithNoise('SHIP_DUST_SUPPRESSION', 150, 250, 10);
    } else {
      // Shiploader idle
      this.currentValues.set('SHIP_LOADER_FLOW_RATE', 0);
      this.updateWithNoise('SHIP_LOADER_MOTOR_CURRENT', 0, 30, 3);
      this.updateWithNoise('SHIP_LOADER_VIBRATION', 0, 1, 0.1);
      this.currentValues.set('SHIP_DUST_SUPPRESSION', 0);
    }
  }

  private updateQualityTags(now: Date): void {
    // Quality parameters vary slowly
    this.updateWithNoise('QC_MOISTURE_CONTENT', 12.5, 13.5, 0.1);
    this.updateWithNoise('QC_IMPURITIES', 0.5, 1.8, 0.1);
    this.updateWithNoise('QC_BROKEN_GRAINS', 1.5, 3.5, 0.1);
    this.updateWithNoise('QC_PROTEIN_CONTENT', 11.5, 12.5, 0.05);
    this.updateWithNoise('QC_TEST_WEIGHT', 76, 80, 0.2);
  }

  private updateUtilityTags(now: Date): void {
    // Power consumption correlates with motor currents
    const conv1Current = this.getValue('CONV_01_MOTOR_CURRENT')?.value || 0;
    const conv2Current = this.getValue('CONV_02_MOTOR_CURRENT')?.value || 0;
    const elev1Current = this.getValue('ELEV_01_MOTOR_CURRENT')?.value || 0;
    const shipCurrent = this.getValue('SHIP_LOADER_MOTOR_CURRENT')?.value || 0;

    const totalPower = (conv1Current + conv2Current + elev1Current + shipCurrent) * 0.38 * 1.732 / 1000 + 500;
    this.currentValues.set('UTIL_POWER_CONSUMPTION', totalPower + Math.random() * 100);

    // Compressor
    this.updateWithNoise('UTIL_COMPRESSOR_01_PRESSURE', 6.5, 7.8, 0.1);
    this.updateWithNoise('UTIL_COMPRESSOR_01_TEMP', 70, 85, 2);

    // Dust collectors
    this.updateWithNoise('UTIL_DUST_COLLECTOR_01_PRESSURE', 80, 140, 5);
    this.updateWithNoise('UTIL_DUST_COLLECTOR_02_PRESSURE', 80, 140, 5);
  }

  private updateEnvironmentalTags(now: Date): void {
    // Environmental conditions change slowly
    const hour = now.getHours();

    // Temperature follows daily cycle
    const baseTemp = 20 + 10 * Math.sin((hour - 6) * Math.PI / 12);
    this.updateWithNoise('ENV_OUTDOOR_TEMP', baseTemp - 3, baseTemp + 3, 0.5);

    // Humidity inverse to temperature
    const outdoorTemp = this.getValue('ENV_OUTDOOR_TEMP')?.value || 25;
    this.updateWithNoise('ENV_OUTDOOR_HUMIDITY', 90 - outdoorTemp * 2, 100 - outdoorTemp * 2, 2);

    // Wind
    this.updateWithNoise('ENV_WIND_SPEED', 5, 25, 2);
    this.updateWithNoise('ENV_WIND_DIRECTION', 0, 360, 10);

    // Rainfall (occasional)
    if (Math.random() < 0.02) { // 2% chance of rain
      this.updateWithNoise('ENV_RAINFALL', 5, 15, 2);
    } else {
      this.updateWithNoise('ENV_RAINFALL', 0, 0.5, 0.1);
    }
  }

  private updateProductionMetrics(now: Date): void {
    // Production totals
    const scale1Weight = this.getValue('RCV_SCALE_01_WEIGHT')?.value || 0;
    const scale2Weight = this.getValue('RCV_SCALE_02_WEIGHT')?.value || 0;

    if (scale1Weight > 1000 || scale2Weight > 1000) {
      const currentReceived = this.getValue('PROD_TOTAL_RECEIVED_TODAY')?.value || 0;
      this.currentValues.set('PROD_TOTAL_RECEIVED_TODAY', currentReceived + 0.5);
    }

    const shipLoaded = this.getValue('SHIP_TOTAL_LOADED')?.value || 0;
    this.currentValues.set('PROD_TOTAL_SHIPPED_TODAY', shipLoaded);

    // Inventory
    const silo1Weight = this.getValue('SILO_01_WEIGHT')?.value || 0;
    const silo2Weight = this.getValue('SILO_02_WEIGHT')?.value || 0;
    const silo3Weight = this.getValue('SILO_03_WEIGHT')?.value || 0;
    this.currentValues.set('PROD_INVENTORY_TOTAL', silo1Weight + silo2Weight + silo3Weight);

    // OEE (Overall Equipment Efficiency)
    const isRunning = this.truckReceivingActive || this.shipLoadingActive;
    this.updateWithNoise('PROD_EFFICIENCY', isRunning ? 78 : 65, isRunning ? 92 : 75, 1);
  }

  /**
   * Update a value with noise around a target range
   */
  private updateWithNoise(tagId: string, minTarget: number, maxTarget: number, noise: number): void {
    const currentValue = this.currentValues.get(tagId) || ((minTarget + maxTarget) / 2);
    const target = minTarget + Math.random() * (maxTarget - minTarget);

    // Smooth transition towards target
    const newValue = currentValue + (target - currentValue) * 0.1 + (Math.random() - 0.5) * noise;

    // Clamp to tag limits
    const tag = getTagById(tagId);
    if (tag) {
      this.currentValues.set(tagId, Math.max(tag.min_value, Math.min(tag.max_value, newValue)));
    } else {
      this.currentValues.set(tagId, newValue);
    }
  }

  /**
   * Check for alarm conditions
   */
  private checkAlarms(): void {
    this.alarms = [];

    PORT_GRAIN_TERMINAL_TAGS.forEach(tag => {
      const value = this.currentValues.get(tag.id);
      if (value === undefined) return;

      // Check high alarm
      if (tag.alarm_high && value >= tag.alarm_high) {
        this.alarms.push({
          tagId: tag.id,
          tagName: tag.name,
          value,
          condition: 'high',
          threshold: tag.alarm_high,
          severity: 'alarm',
          timestamp: new Date()
        });
      }

      // Check low alarm
      if (tag.alarm_low && value <= tag.alarm_low) {
        this.alarms.push({
          tagId: tag.id,
          tagName: tag.name,
          value,
          condition: 'low',
          threshold: tag.alarm_low,
          severity: 'alarm',
          timestamp: new Date()
        });
      }
    });
  }

  /**
   * Control methods
   */
  setShipLoadingActive(active: boolean): void {
    this.shipLoadingActive = active;
    if (!active) {
      // Reset ship loading counters
      this.currentValues.set('SHIP_TOTAL_LOADED', 0);
      this.currentValues.set('SHIP_LOADING_PROGRESS', 0);
    }
  }

  setTruckReceivingActive(active: boolean): void {
    this.truckReceivingActive = active;
  }

  setAlarmsEnabled(enabled: boolean): void {
    this.alarmsEnabled = enabled;
    if (!enabled) {
      this.alarms = [];
    }
  }

  setSimulationSpeed(speed: number): void {
    this.simulationSpeed = Math.max(0.1, Math.min(10, speed));
  }

  getAlarms(): AlarmCondition[] {
    return [...this.alarms];
  }

  getActiveAlarmCount(): number {
    return this.alarms.length;
  }

  // Trigger specific scenarios for testing
  triggerHighTemperatureAlarm(): void {
    this.currentValues.set('CONV_01_MOTOR_TEMP', 95); // Above alarm threshold
  }

  triggerLowPressureAlarm(): void {
    this.currentValues.set('UTIL_COMPRESSOR_01_PRESSURE', 4); // Below alarm threshold
  }

  triggerHighVibrationAlarm(): void {
    this.currentValues.set('ELEV_01_VIBRATION', 18); // Above alarm threshold
  }

  reset(): void {
    this.initializeValues();
    this.alarms = [];
  }
}

// Export singleton instance
export const tagDataSimulator = new TagDataSimulator();

export default tagDataSimulator;
