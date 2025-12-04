/**
 * Vitest Setup File
 *
 * This file is run before each test file.
 * Used to setup global mocks and test utilities.
 */
import '@testing-library/jest-dom'
import { vi } from 'vitest'

// Mock matchMedia for components that use it
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// Mock scrollTo
Element.prototype.scrollTo = vi.fn()
window.scrollTo = vi.fn()

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
Object.defineProperty(window, 'localStorage', { value: localStorageMock })

// Mock fetch
global.fetch = vi.fn()

// Suppress console errors during tests (optional, can be removed for debugging)
// const originalError = console.error
// console.error = (...args: any[]) => {
//   if (
//     typeof args[0] === 'string' &&
//     args[0].includes('Warning: ReactDOM.render is no longer supported')
//   ) {
//     return
//   }
//   originalError.call(console, ...args)
// }
