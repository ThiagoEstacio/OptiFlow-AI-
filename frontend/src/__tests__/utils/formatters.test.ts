/**
 * Tests for utility formatters
 */
import { describe, it, expect } from 'vitest'

// Common utility functions that should be tested
describe('Number Formatters', () => {
  const formatNumber = (value: number, decimals: number = 2): string => {
    return value.toLocaleString('pt-BR', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    })
  }

  const formatPercentage = (value: number, decimals: number = 1): string => {
    return `${value.toFixed(decimals)}%`
  }

  const formatCurrency = (value: number): string => {
    return value.toLocaleString('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    })
  }

  it('should format numbers with Brazilian locale', () => {
    expect(formatNumber(1234.56)).toBe('1.234,56')
    expect(formatNumber(0.123, 3)).toBe('0,123')
    expect(formatNumber(1000000)).toBe('1.000.000,00')
  })

  it('should format percentages correctly', () => {
    expect(formatPercentage(85.5)).toBe('85.5%')
    expect(formatPercentage(100)).toBe('100.0%')
    expect(formatPercentage(0.5, 2)).toBe('0.50%')
  })

  it('should format currency in BRL', () => {
    expect(formatCurrency(1234.56)).toContain('R$')
    expect(formatCurrency(1234.56)).toContain('1.234,56')
  })
})

describe('Date Formatters', () => {
  const formatDateTime = (date: Date | string): string => {
    const d = new Date(date)
    return d.toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const formatDateOnly = (date: Date | string): string => {
    const d = new Date(date)
    return d.toLocaleDateString('pt-BR')
  }

  const formatTimeOnly = (date: Date | string): string => {
    const d = new Date(date)
    return d.toLocaleTimeString('pt-BR', {
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  it('should format date and time correctly', () => {
    // Use explicit timezone to avoid test flakiness
    const date = new Date(2024, 0, 15, 14, 30, 0) // January 15, 2024 14:30
    const formatted = formatDateTime(date)
    expect(formatted).toContain('15/01/2024')
    expect(formatted).toContain('14:30')
  })

  it('should format date only', () => {
    // Use Date constructor with year, month, day to avoid timezone issues
    const date = new Date(2024, 11, 25) // December 25, 2024
    expect(formatDateOnly(date)).toBe('25/12/2024')
  })

  it('should format time only', () => {
    const date = new Date(2024, 0, 1, 9, 5, 0) // 09:05
    expect(formatTimeOnly(date)).toBe('09:05')
  })
})

describe('String Formatters', () => {
  const truncate = (str: string, maxLength: number): string => {
    if (str.length <= maxLength) return str
    return str.substring(0, maxLength - 3) + '...'
  }

  const capitalize = (str: string): string => {
    return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase()
  }

  const slugify = (str: string): string => {
    return str
      .toLowerCase()
      .trim()
      .replace(/[^\w\s-]/g, '')
      .replace(/[\s_-]+/g, '-')
      .replace(/^-+|-+$/g, '')
  }

  it('should truncate long strings', () => {
    expect(truncate('Hello World', 20)).toBe('Hello World')
    expect(truncate('This is a very long string', 10)).toBe('This is...')
  })

  it('should capitalize strings', () => {
    expect(capitalize('hello')).toBe('Hello')
    expect(capitalize('WORLD')).toBe('World')
    expect(capitalize('hELLO wORLD')).toBe('Hello world')
  })

  it('should slugify strings', () => {
    expect(slugify('Hello World')).toBe('hello-world')
    expect(slugify('  Multiple   Spaces  ')).toBe('multiple-spaces')
    expect(slugify('Special!@#Characters')).toBe('specialcharacters')
  })
})

describe('Value Status Helpers', () => {
  const getStatusColor = (value: number, threshold: number, inverse: boolean = false): string => {
    if (inverse) {
      // Lower is better (e.g., errors, defects)
      if (value <= threshold * 0.5) return 'green'
      if (value <= threshold) return 'yellow'
      return 'red'
    } else {
      // Higher is better (e.g., OEE, availability)
      if (value >= threshold) return 'green'
      if (value >= threshold * 0.8) return 'yellow'
      return 'red'
    }
  }

  const getPercentageStatus = (value: number): 'success' | 'warning' | 'error' => {
    if (value >= 90) return 'success'
    if (value >= 70) return 'warning'
    return 'error'
  }

  it('should return correct status colors for normal metrics', () => {
    expect(getStatusColor(95, 90)).toBe('green')
    expect(getStatusColor(80, 90)).toBe('yellow')
    expect(getStatusColor(60, 90)).toBe('red')
  })

  it('should return correct status colors for inverse metrics', () => {
    expect(getStatusColor(2, 10, true)).toBe('green')
    expect(getStatusColor(8, 10, true)).toBe('yellow')
    expect(getStatusColor(15, 10, true)).toBe('red')
  })

  it('should return correct percentage status', () => {
    expect(getPercentageStatus(95)).toBe('success')
    expect(getPercentageStatus(75)).toBe('warning')
    expect(getPercentageStatus(50)).toBe('error')
  })
})
