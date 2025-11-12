/**
 * Simulator Data Sync Service
 * Sends simulated tag data to backend for storage
 */

import { tagDataSimulator } from './tagDataSimulator';
import { apiClient } from '../api/client';
import { PORT_GRAIN_TERMINAL_TAGS } from '../data/portGrainTerminalTags';

class SimulatorDataSync {
  private syncInterval: NodeJS.Timeout | null = null;
  private running: boolean = false;
  private syncIntervalMs: number = 2000; // Sync every 2 seconds

  /**
   * Start syncing simulator data to backend
   */
  public start(): void {
    if (this.running) {
      console.log('⚠️ Simulator data sync already running');
      return;
    }

    console.log('🔄 Starting simulator data sync to backend...');
    this.running = true;

    // Sync immediately
    this.syncData();

    // Then sync periodically
    this.syncInterval = setInterval(() => {
      this.syncData();
    }, this.syncIntervalMs);
  }

  /**
   * Stop syncing
   */
  public stop(): void {
    if (!this.running) return;

    console.log('⏹️ Stopping simulator data sync');
    this.running = false;

    if (this.syncInterval) {
      clearInterval(this.syncInterval);
      this.syncInterval = null;
    }
  }

  /**
   * Sync current simulator values to backend
   */
  private async syncData(): Promise<void> {
    try {
      // Get all tag values from simulator
      const dataPoints: any[] = [];
      const timestamp = new Date().toISOString();

      // Sample key tags (not all to avoid overwhelming the backend)
      const keyTags = PORT_GRAIN_TERMINAL_TAGS.filter(tag => 
        tag.id.includes('_PV') || // Process values
        tag.id.includes('RATE') || // Flow rates
        tag.id.includes('STATUS') || // Status tags
        tag.id.includes('LEVEL') // Levels
      );

      for (const tag of keyTags) {
        const value = tagDataSimulator.getTagValue(tag.id);
        
        if (value !== null) {
          dataPoints.push({
            tag_id: tag.id,
            timestamp,
            value,
            quality: 'good',
          });
        }
      }

      // Send batch to backend (using axios directly since writeBatch doesn't exist)
      if (dataPoints.length > 0) {
        const response = await fetch('/api/v1/timeseries/batch', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ points: dataPoints }),
        }).catch((err) => {
          console.error('❌ Network error syncing data:', err);
          return null;
        });

        if (response && response.ok) {
          console.log(`✅ Synced ${dataPoints.length} data points to backend`);
        } else if (response) {
          const errorText = await response.text().catch(() => 'Unknown error');
          console.warn(`⚠️ Failed to sync data: ${response.status} - ${errorText}`);
        }
      }
    } catch (error) {
      console.error('❌ Error syncing simulator data to backend:', error);
      // Don't stop on error - will retry on next interval
    }
  }

  /**
   * Check if sync is running
   */
  public isRunning(): boolean {
    return this.running;
  }

  /**
   * Set sync interval
   */
  public setSyncInterval(intervalMs: number): void {
    this.syncIntervalMs = Math.max(1000, intervalMs); // Min 1 second

    if (this.running) {
      this.stop();
      this.start();
    }
  }
}

// Singleton instance
export const simulatorDataSync = new SimulatorDataSync();
