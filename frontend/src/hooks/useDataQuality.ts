/**
 * 🏭 useDataQuality - Hook para Monitoramento de Qualidade de Dados
 * ==================================================================
 *
 * Gerencia o estado de qualidade dos dados em tempo real.
 * Detecta automaticamente:
 * - Dados desatualizados (stale)
 * - Falhas de comunicação
 * - Valores fora do range esperado
 */

import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { DataQuality } from '../components/industrial/QualityIndicator';

// ========================================
// Types
// ========================================

export interface TagQualityState {
  tagId: string;
  quality: DataQuality;
  value: number | string | null;
  timestamp: Date | null;
  lastGoodValue: number | string | null;
  lastGoodTimestamp: Date | null;
  isStale: boolean;
  staleDuration: number; // seconds since last update
}

export interface DataQualityConfig {
  staleThreshold?: number; // seconds
  checkInterval?: number; // ms
  minExpectedValue?: number;
  maxExpectedValue?: number;
  autoMarkBad?: boolean; // auto-mark as BAD if no update after threshold
}

export interface UseDataQualityOptions {
  tags: string[];
  config?: DataQualityConfig;
  onQualityChange?: (tagId: string, quality: DataQuality) => void;
  onStaleDetected?: (tagIds: string[]) => void;
}

export interface UseDataQualityReturn {
  qualityStates: Map<string, TagQualityState>;
  updateTagValue: (tagId: string, value: number | string, timestamp?: Date) => void;
  setTagQuality: (tagId: string, quality: DataQuality) => void;
  getTagQuality: (tagId: string) => TagQualityState | undefined;
  staleCount: number;
  badCount: number;
  goodCount: number;
  totalTags: number;
  overallHealth: number; // 0-100 percentage
  forceRefresh: () => void;
  resetTag: (tagId: string) => void;
  resetAll: () => void;
}

// ========================================
// Constants
// ========================================

const DEFAULT_CONFIG: Required<DataQualityConfig> = {
  staleThreshold: 30, // 30 seconds
  checkInterval: 5000, // Check every 5 seconds
  minExpectedValue: Number.MIN_SAFE_INTEGER,
  maxExpectedValue: Number.MAX_SAFE_INTEGER,
  autoMarkBad: false,
};

// ========================================
// Helper Functions
// ========================================

const createInitialState = (tagId: string): TagQualityState => ({
  tagId,
  quality: 'NOT_CONNECTED',
  value: null,
  timestamp: null,
  lastGoodValue: null,
  lastGoodTimestamp: null,
  isStale: false,
  staleDuration: 0,
});

const calculateStaleDuration = (timestamp: Date | null): number => {
  if (!timestamp) return Infinity;
  return Math.floor((Date.now() - timestamp.getTime()) / 1000);
};

const isValueInRange = (
  value: number | string | null,
  min: number,
  max: number
): boolean => {
  if (value === null || typeof value === 'string') return true;
  return value >= min && value <= max;
};

// ========================================
// Hook Implementation
// ========================================

export function useDataQuality(options: UseDataQualityOptions): UseDataQualityReturn {
  const { tags, config: userConfig, onQualityChange, onStaleDetected } = options;
  const config = useMemo(() => ({ ...DEFAULT_CONFIG, ...userConfig }), [userConfig]);

  // State
  const [qualityStates, setQualityStates] = useState<Map<string, TagQualityState>>(
    () => new Map(tags.map((tagId) => [tagId, createInitialState(tagId)]))
  );

  // Refs for callbacks
  const onQualityChangeRef = useRef(onQualityChange);
  const onStaleDetectedRef = useRef(onStaleDetected);

  useEffect(() => {
    onQualityChangeRef.current = onQualityChange;
    onStaleDetectedRef.current = onStaleDetected;
  }, [onQualityChange, onStaleDetected]);

  // Initialize new tags
  useEffect(() => {
    setQualityStates((prev) => {
      const newMap = new Map(prev);
      tags.forEach((tagId) => {
        if (!newMap.has(tagId)) {
          newMap.set(tagId, createInitialState(tagId));
        }
      });
      // Remove tags that are no longer in the list
      newMap.forEach((_, tagId) => {
        if (!tags.includes(tagId)) {
          newMap.delete(tagId);
        }
      });
      return newMap;
    });
  }, [tags]);

  // Periodic stale check
  useEffect(() => {
    const interval = setInterval(() => {
      setQualityStates((prev) => {
        const newMap = new Map(prev);
        const staleTagIds: string[] = [];

        newMap.forEach((state, tagId) => {
          const staleDuration = calculateStaleDuration(state.timestamp);
          const wasStale = state.isStale;
          const isNowStale = staleDuration > config.staleThreshold;

          // Update state
          const newState = {
            ...state,
            staleDuration,
            isStale: isNowStale,
          };

          // Auto-mark as BAD if configured
          if (isNowStale && config.autoMarkBad && state.quality === 'GOOD') {
            newState.quality = 'BAD';
          } else if (isNowStale && state.quality === 'GOOD') {
            newState.quality = 'STALE';
          }

          newMap.set(tagId, newState);

          // Track newly stale tags
          if (isNowStale && !wasStale) {
            staleTagIds.push(tagId);
          }

          // Fire quality change callback
          if (newState.quality !== state.quality && onQualityChangeRef.current) {
            onQualityChangeRef.current(tagId, newState.quality);
          }
        });

        // Fire stale detected callback
        if (staleTagIds.length > 0 && onStaleDetectedRef.current) {
          onStaleDetectedRef.current(staleTagIds);
        }

        return newMap;
      });
    }, config.checkInterval);

    return () => clearInterval(interval);
  }, [config.staleThreshold, config.checkInterval, config.autoMarkBad]);

  // Update tag value
  const updateTagValue = useCallback(
    (tagId: string, value: number | string, timestamp: Date = new Date()) => {
      setQualityStates((prev) => {
        const newMap = new Map(prev);
        const currentState = newMap.get(tagId) || createInitialState(tagId);

        // Determine quality based on value
        let newQuality: DataQuality = 'GOOD';
        if (!isValueInRange(value, config.minExpectedValue, config.maxExpectedValue)) {
          newQuality = 'UNCERTAIN';
        }

        const newState: TagQualityState = {
          ...currentState,
          value,
          timestamp,
          quality: newQuality,
          isStale: false,
          staleDuration: 0,
          lastGoodValue: newQuality === 'GOOD' ? value : currentState.lastGoodValue,
          lastGoodTimestamp: newQuality === 'GOOD' ? timestamp : currentState.lastGoodTimestamp,
        };

        newMap.set(tagId, newState);

        // Fire quality change callback
        if (newState.quality !== currentState.quality && onQualityChangeRef.current) {
          onQualityChangeRef.current(tagId, newState.quality);
        }

        return newMap;
      });
    },
    [config.minExpectedValue, config.maxExpectedValue]
  );

  // Set tag quality manually
  const setTagQuality = useCallback((tagId: string, quality: DataQuality) => {
    setQualityStates((prev) => {
      const newMap = new Map(prev);
      const currentState = newMap.get(tagId);
      if (currentState) {
        newMap.set(tagId, { ...currentState, quality });
      }
      return newMap;
    });
  }, []);

  // Get tag quality
  const getTagQuality = useCallback(
    (tagId: string): TagQualityState | undefined => {
      return qualityStates.get(tagId);
    },
    [qualityStates]
  );

  // Force refresh
  const forceRefresh = useCallback(() => {
    // This would typically trigger a re-fetch from the server
    // For now, just update timestamps to mark as checking
    setQualityStates((prev) => {
      const newMap = new Map(prev);
      newMap.forEach((state, tagId) => {
        newMap.set(tagId, {
          ...state,
          staleDuration: calculateStaleDuration(state.timestamp),
        });
      });
      return newMap;
    });
  }, []);

  // Reset single tag
  const resetTag = useCallback((tagId: string) => {
    setQualityStates((prev) => {
      const newMap = new Map(prev);
      newMap.set(tagId, createInitialState(tagId));
      return newMap;
    });
  }, []);

  // Reset all
  const resetAll = useCallback(() => {
    setQualityStates(new Map(tags.map((tagId) => [tagId, createInitialState(tagId)])));
  }, [tags]);

  // Computed values
  const stats = useMemo(() => {
    let staleCount = 0;
    let badCount = 0;
    let goodCount = 0;

    qualityStates.forEach((state) => {
      switch (state.quality) {
        case 'GOOD':
          goodCount++;
          break;
        case 'STALE':
          staleCount++;
          break;
        case 'BAD':
        case 'NOT_CONNECTED':
          badCount++;
          break;
      }
    });

    const totalTags = qualityStates.size;
    const overallHealth = totalTags > 0 ? (goodCount / totalTags) * 100 : 0;

    return { staleCount, badCount, goodCount, totalTags, overallHealth };
  }, [qualityStates]);

  return {
    qualityStates,
    updateTagValue,
    setTagQuality,
    getTagQuality,
    forceRefresh,
    resetTag,
    resetAll,
    ...stats,
  };
}

export default useDataQuality;
