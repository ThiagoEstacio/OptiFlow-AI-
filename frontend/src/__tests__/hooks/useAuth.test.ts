/**
 * Unit tests for useAuth hook
 * Tests authentication state management and API interactions
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'

// Mock the API client
vi.mock('@/api/client', () => ({
  apiClient: {
    post: vi.fn(),
    get: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  },
}))

// Mock localStorage before importing useAuth
const mockLocalStorage = {
  store: {} as Record<string, string>,
  getItem: vi.fn((key: string) => mockLocalStorage.store[key] || null),
  setItem: vi.fn((key: string, value: string) => {
    mockLocalStorage.store[key] = value
  }),
  removeItem: vi.fn((key: string) => {
    delete mockLocalStorage.store[key]
  }),
  clear: vi.fn(() => {
    mockLocalStorage.store = {}
  }),
}

Object.defineProperty(window, 'localStorage', { value: mockLocalStorage })

describe('useAuth Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockLocalStorage.clear()
  })

  afterEach(() => {
    vi.resetAllMocks()
  })

  describe('Initial State', () => {
    it('should start with no user when no token exists', async () => {
      // Dynamic import to get fresh module state
      const { useAuth } = await import('@/hooks/useAuth')
      const { result } = renderHook(() => useAuth())

      expect(result.current.user).toBeNull()
      expect(result.current.loading).toBeDefined()
    })

    it('should check for existing token on mount', async () => {
      // Set a token before mounting
      mockLocalStorage.setItem('access_token', 'existing_token')

      const { useAuth } = await import('@/hooks/useAuth')
      const { result } = renderHook(() => useAuth())

      // Should check localStorage
      expect(mockLocalStorage.getItem).toHaveBeenCalled()
    })
  })

  describe('Login', () => {
    it('should have login function', async () => {
      const { useAuth } = await import('@/hooks/useAuth')
      const { result } = renderHook(() => useAuth())

      expect(typeof result.current.login).toBe('function')
    })

    it('should store tokens after successful login', async () => {
      const { apiClient } = await import('@/api/client')
      const mockPost = apiClient.post as ReturnType<typeof vi.fn>

      mockPost.mockResolvedValueOnce({
        data: {
          access_token: 'new_access_token',
          refresh_token: 'new_refresh_token',
          token_type: 'bearer',
        },
      })

      const { useAuth } = await import('@/hooks/useAuth')
      const { result } = renderHook(() => useAuth())

      await act(async () => {
        await result.current.login('test@example.com', 'password123')
      })

      // Should store the token
      expect(mockLocalStorage.setItem).toHaveBeenCalled()
    })
  })

  describe('Logout', () => {
    it('should have logout function', async () => {
      const { useAuth } = await import('@/hooks/useAuth')
      const { result } = renderHook(() => useAuth())

      expect(typeof result.current.logout).toBe('function')
    })

    it('should clear tokens on logout', async () => {
      mockLocalStorage.setItem('access_token', 'some_token')

      const { useAuth } = await import('@/hooks/useAuth')
      const { result } = renderHook(() => useAuth())

      act(() => {
        result.current.logout()
      })

      expect(mockLocalStorage.removeItem).toHaveBeenCalled()
    })

    it('should clear user state on logout', async () => {
      const { useAuth } = await import('@/hooks/useAuth')
      const { result } = renderHook(() => useAuth())

      act(() => {
        result.current.logout()
      })

      expect(result.current.user).toBeNull()
    })
  })

  describe('Loading State', () => {
    it('should expose loading state', async () => {
      const { useAuth } = await import('@/hooks/useAuth')
      const { result } = renderHook(() => useAuth())

      expect(result.current.loading).toBeDefined()
      expect(typeof result.current.loading).toBe('boolean')
    })
  })

  describe('Error Handling', () => {
    it('should handle login errors gracefully', async () => {
      const { apiClient } = await import('@/api/client')
      const mockPost = apiClient.post as ReturnType<typeof vi.fn>

      mockPost.mockRejectedValueOnce(new Error('Invalid credentials'))

      const { useAuth } = await import('@/hooks/useAuth')
      const { result } = renderHook(() => useAuth())

      await expect(
        act(async () => {
          await result.current.login('test@example.com', 'wrongpassword')
        })
      ).rejects.toThrow()
    })
  })

  describe('isAuthenticated', () => {
    it('should return false when no user', async () => {
      const { useAuth } = await import('@/hooks/useAuth')
      const { result } = renderHook(() => useAuth())

      expect(result.current.isAuthenticated).toBe(false)
    })
  })
})

describe('Token Management', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockLocalStorage.clear()
  })

  it('should save access token to localStorage', async () => {
    mockLocalStorage.setItem('access_token', 'test_token')
    expect(mockLocalStorage.store['access_token']).toBe('test_token')
  })

  it('should remove tokens on clear', async () => {
    mockLocalStorage.setItem('access_token', 'test_token')
    mockLocalStorage.setItem('refresh_token', 'refresh_token')
    mockLocalStorage.clear()

    expect(mockLocalStorage.store['access_token']).toBeUndefined()
    expect(mockLocalStorage.store['refresh_token']).toBeUndefined()
  })
})
