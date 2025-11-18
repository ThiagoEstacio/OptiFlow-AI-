/**
 * Circuit Breaker Pattern for Frontend
 * Prevents cascade failures when backend is unavailable
 */

type CircuitState = 'CLOSED' | 'OPEN' | 'HALF_OPEN';

interface CircuitBreakerOptions {
  failureThreshold?: number;      // Number of failures before opening
  resetTimeout?: number;          // Time in ms to wait before half-open
  halfOpenMaxCalls?: number;      // Max calls allowed in half-open state
  onStateChange?: (newState: CircuitState, oldState: CircuitState) => void;
}

interface CircuitMetrics {
  totalCalls: number;
  successfulCalls: number;
  failedCalls: number;
  rejectedCalls: number;
  lastFailureTime: number | null;
  consecutiveFailures: number;
}

export class CircuitBreaker {
  private state: CircuitState = 'CLOSED';
  private failureCount: number = 0;
  private lastFailureTime: number = 0;
  private halfOpenCalls: number = 0;
  private metrics: CircuitMetrics;

  private readonly failureThreshold: number;
  private readonly resetTimeout: number;
  private readonly halfOpenMaxCalls: number;
  private readonly onStateChange?: (newState: CircuitState, oldState: CircuitState) => void;

  constructor(options: CircuitBreakerOptions = {}) {
    this.failureThreshold = options.failureThreshold ?? 5;
    this.resetTimeout = options.resetTimeout ?? 30000; // 30 seconds
    this.halfOpenMaxCalls = options.halfOpenMaxCalls ?? 3;
    this.onStateChange = options.onStateChange;

    this.metrics = {
      totalCalls: 0,
      successfulCalls: 0,
      failedCalls: 0,
      rejectedCalls: 0,
      lastFailureTime: null,
      consecutiveFailures: 0,
    };
  }

  /**
   * Execute a function with circuit breaker protection
   */
  async execute<T>(fn: () => Promise<T>): Promise<T> {
    this.metrics.totalCalls++;

    // Check if circuit should transition from OPEN to HALF_OPEN
    if (this.state === 'OPEN') {
      if (Date.now() - this.lastFailureTime >= this.resetTimeout) {
        this.transitionTo('HALF_OPEN');
      } else {
        this.metrics.rejectedCalls++;
        throw new CircuitBreakerError('Circuit breaker is OPEN');
      }
    }

    // Check half-open state limits
    if (this.state === 'HALF_OPEN') {
      if (this.halfOpenCalls >= this.halfOpenMaxCalls) {
        this.metrics.rejectedCalls++;
        throw new CircuitBreakerError('Circuit breaker is HALF_OPEN and max calls reached');
      }
      this.halfOpenCalls++;
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  /**
   * Check if circuit allows requests
   */
  canExecute(): boolean {
    if (this.state === 'CLOSED') {
      return true;
    }

    if (this.state === 'OPEN') {
      if (Date.now() - this.lastFailureTime >= this.resetTimeout) {
        this.transitionTo('HALF_OPEN');
        return true;
      }
      return false;
    }

    // HALF_OPEN
    return this.halfOpenCalls < this.halfOpenMaxCalls;
  }

  /**
   * Get current circuit state
   */
  getState(): CircuitState {
    return this.state;
  }

  /**
   * Get circuit metrics
   */
  getMetrics(): CircuitMetrics {
    return { ...this.metrics };
  }

  /**
   * Manually reset circuit to CLOSED
   */
  reset(): void {
    this.transitionTo('CLOSED');
    this.failureCount = 0;
    this.halfOpenCalls = 0;
    this.metrics.consecutiveFailures = 0;
  }

  private onSuccess(): void {
    this.metrics.successfulCalls++;
    this.metrics.consecutiveFailures = 0;

    if (this.state === 'HALF_OPEN') {
      // Reset to closed after successful call in half-open
      this.transitionTo('CLOSED');
      this.failureCount = 0;
      this.halfOpenCalls = 0;
    } else if (this.state === 'CLOSED') {
      // Reset failure count on success
      this.failureCount = 0;
    }
  }

  private onFailure(): void {
    this.metrics.failedCalls++;
    this.metrics.consecutiveFailures++;
    this.metrics.lastFailureTime = Date.now();
    this.failureCount++;
    this.lastFailureTime = Date.now();

    if (this.state === 'HALF_OPEN') {
      // Immediately open on failure in half-open
      this.transitionTo('OPEN');
      this.halfOpenCalls = 0;
    } else if (this.state === 'CLOSED' && this.failureCount >= this.failureThreshold) {
      // Open circuit when threshold reached
      this.transitionTo('OPEN');
    }
  }

  private transitionTo(newState: CircuitState): void {
    if (this.state !== newState) {
      const oldState = this.state;
      this.state = newState;

      console.log(`Circuit breaker: ${oldState} -> ${newState}`);

      if (this.onStateChange) {
        this.onStateChange(newState, oldState);
      }
    }
  }
}

/**
 * Custom error for circuit breaker rejections
 */
export class CircuitBreakerError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'CircuitBreakerError';
  }
}

/**
 * Global circuit breaker instances for different services
 */
const circuitBreakers: Map<string, CircuitBreaker> = new Map();

/**
 * Get or create a circuit breaker for a service
 */
export const getCircuitBreaker = (serviceName: string, options?: CircuitBreakerOptions): CircuitBreaker => {
  if (!circuitBreakers.has(serviceName)) {
    circuitBreakers.set(serviceName, new CircuitBreaker(options));
  }
  return circuitBreakers.get(serviceName)!;
};

/**
 * Reset all circuit breakers
 */
export const resetAllCircuitBreakers = (): void => {
  circuitBreakers.forEach(cb => cb.reset());
};

/**
 * Get status of all circuit breakers
 */
export const getAllCircuitBreakerStatus = (): Record<string, { state: CircuitState; metrics: CircuitMetrics }> => {
  const status: Record<string, { state: CircuitState; metrics: CircuitMetrics }> = {};
  circuitBreakers.forEach((cb, name) => {
    status[name] = {
      state: cb.getState(),
      metrics: cb.getMetrics(),
    };
  });
  return status;
};

export default CircuitBreaker;
