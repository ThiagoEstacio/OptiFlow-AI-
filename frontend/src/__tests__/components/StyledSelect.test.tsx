/**
 * Tests for StyledSelect component
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { StyledSelect, TimeRangeSelect } from '../../components/common/StyledSelect'

describe('StyledSelect', () => {
  const defaultOptions = [
    { value: 'opt1', label: 'Option 1' },
    { value: 'opt2', label: 'Option 2' },
    { value: 'opt3', label: 'Option 3' },
  ]

  it('renders with options', () => {
    render(
      <StyledSelect
        value="opt1"
        onChange={() => {}}
        options={defaultOptions}
      />
    )

    expect(screen.getByRole('combobox')).toBeInTheDocument()
    expect(screen.getAllByRole('option')).toHaveLength(3)
  })

  it('calls onChange when selection changes', () => {
    const handleChange = vi.fn()
    render(
      <StyledSelect
        value="opt1"
        onChange={handleChange}
        options={defaultOptions}
      />
    )

    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'opt2' } })
    expect(handleChange).toHaveBeenCalledWith('opt2')
  })

  it('renders with placeholder when provided', () => {
    render(
      <StyledSelect
        value=""
        onChange={() => {}}
        options={defaultOptions}
        placeholder="Select an option"
      />
    )

    expect(screen.getByRole('option', { name: 'Select an option' })).toBeInTheDocument()
    expect(screen.getAllByRole('option')).toHaveLength(4) // placeholder + 3 options
  })

  it('renders with label when provided', () => {
    render(
      <StyledSelect
        value="opt1"
        onChange={() => {}}
        options={defaultOptions}
        label="Select Option"
      />
    )

    expect(screen.getByText('Select Option')).toBeInTheDocument()
  })

  it('applies correct size classes', () => {
    const { container, rerender } = render(
      <StyledSelect
        value="opt1"
        onChange={() => {}}
        options={defaultOptions}
        size="sm"
      />
    )

    const select = container.querySelector('select')
    expect(select).toHaveClass('text-sm')

    rerender(
      <StyledSelect
        value="opt1"
        onChange={() => {}}
        options={defaultOptions}
        size="lg"
      />
    )

    expect(container.querySelector('select')).toHaveClass('text-base')
  })
})

describe('TimeRangeSelect', () => {
  it('renders with default time options', () => {
    render(
      <TimeRangeSelect
        value="24h"
        onChange={() => {}}
      />
    )

    expect(screen.getByRole('combobox')).toBeInTheDocument()
    expect(screen.getByRole('option', { name: '1 hora' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: '24 horas' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: '7 dias' })).toBeInTheDocument()
  })

  it('uses custom options when provided', () => {
    const customOptions = [
      { value: '1m', label: '1 mês' },
      { value: '3m', label: '3 meses' },
    ]

    render(
      <TimeRangeSelect
        value="1m"
        onChange={() => {}}
        options={customOptions}
      />
    )

    expect(screen.getByRole('option', { name: '1 mês' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: '3 meses' })).toBeInTheDocument()
    expect(screen.queryByRole('option', { name: '24 horas' })).not.toBeInTheDocument()
  })
})
