/**
 * Tests for ProfessionalCharts components
 *
 * Note: Recharts components may not render SVG elements in jsdom,
 * so we test that components render without throwing errors.
 */
import { describe, it, expect, vi } from 'vitest'
import { render } from '@testing-library/react'
import React from 'react'

// Mock recharts ResponsiveContainer before importing components
vi.mock('recharts', async () => {
  const actual = await vi.importActual<typeof import('recharts')>('recharts')
  return {
    ...actual,
    ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
      <div data-testid="responsive-container" style={{ width: 500, height: 300 }}>
        {children}
      </div>
    ),
  }
})

// Import components after mock
import {
  ProfessionalAreaChart,
  ProfessionalLineChart,
  ProfessionalBarChart,
  ProfessionalDonutChart,
} from '../../components/charts/ProfessionalCharts'

// Sample data for tests
const timeSeriesData = [
  { timestamp: '2024-01-01', value: 10 },
  { timestamp: '2024-01-02', value: 20 },
  { timestamp: '2024-01-03', value: 15 },
]

const categoryData = [
  { name: 'Category A', value: 30 },
  { name: 'Category B', value: 50 },
  { name: 'Category C', value: 20 },
]

const barChartData = [
  { category: 'A', value: 30 },
  { category: 'B', value: 50 },
  { category: 'C', value: 20 },
]

describe('ProfessionalAreaChart', () => {
  it('renders without crashing', () => {
    const { container } = render(
      <ProfessionalAreaChart
        data={timeSeriesData}
        xAxisKey="timestamp"
        dataKey="value"
        height={300}
      />
    )

    // Just verify it rendered something
    expect(container.firstChild).not.toBeNull()
  })

  it('renders with empty data', () => {
    const { container } = render(
      <ProfessionalAreaChart
        data={[]}
        xAxisKey="timestamp"
        dataKey="value"
        height={300}
      />
    )

    expect(container.firstChild).not.toBeNull()
  })
})

describe('ProfessionalLineChart', () => {
  it('renders without crashing', () => {
    const { container } = render(
      <ProfessionalLineChart
        data={timeSeriesData}
        xAxisKey="timestamp"
        lines={[{ dataKey: 'value', name: 'Value', color: '#3b82f6' }]}
        height={300}
      />
    )

    expect(container.firstChild).not.toBeNull()
  })

  it('renders with multiple lines', () => {
    const multiData = timeSeriesData.map((d, i) => ({
      ...d,
      value2: d.value + i * 5,
    }))

    const { container } = render(
      <ProfessionalLineChart
        data={multiData}
        xAxisKey="timestamp"
        lines={[
          { dataKey: 'value', name: 'Value 1', color: '#3b82f6' },
          { dataKey: 'value2', name: 'Value 2', color: '#ef4444' },
        ]}
        height={300}
      />
    )

    expect(container.firstChild).not.toBeNull()
  })
})

describe('ProfessionalBarChart', () => {
  it('renders without crashing', () => {
    const { container } = render(
      <ProfessionalBarChart
        data={barChartData}
        xAxisKey="category"
        categories={['value']}
        colors={['#3b82f6']}
        height={300}
      />
    )

    expect(container.firstChild).not.toBeNull()
  })

  it('renders with empty data', () => {
    const { container } = render(
      <ProfessionalBarChart
        data={[]}
        xAxisKey="category"
        categories={['value']}
        colors={['#3b82f6']}
        height={300}
      />
    )

    expect(container.firstChild).not.toBeNull()
  })
})

describe('ProfessionalDonutChart', () => {
  it('renders without crashing', () => {
    const { container } = render(
      <ProfessionalDonutChart
        data={categoryData}
        height={300}
      />
    )

    expect(container.firstChild).not.toBeNull()
  })

  it('renders with custom colors', () => {
    const { container } = render(
      <ProfessionalDonutChart
        data={categoryData}
        height={300}
        colors={['#ef4444', '#3b82f6', '#10b981']}
      />
    )

    expect(container.firstChild).not.toBeNull()
  })
})
