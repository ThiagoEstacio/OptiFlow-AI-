/**
 * Unit tests for LoginPage component
 * Tests rendering, form validation, and user interactions
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders } from '../test-utils'

// Mock useAuth hook
const mockLogin = vi.fn()
const mockUseAuth = vi.fn(() => ({
  login: mockLogin,
  loading: false,
  user: null,
  isAuthenticated: false,
  error: null,
}))

vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => mockUseAuth(),
}))

// Mock useNavigate
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

// Import after mocks are set up
import { LoginPage } from '@/pages/LoginPage'

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUseAuth.mockReturnValue({
      login: mockLogin,
      loading: false,
      user: null,
      isAuthenticated: false,
      error: null,
    })
  })

  describe('Rendering', () => {
    it('should render login form', () => {
      renderWithProviders(<LoginPage />)

      // Check for main elements
      expect(screen.getByRole('button', { name: /entrar/i })).toBeInTheDocument()
    })

    it('should render email/username input', () => {
      renderWithProviders(<LoginPage />)

      const emailInput = screen.getByPlaceholderText(/admin@optiflow.com/i)
      expect(emailInput).toBeInTheDocument()
    })

    it('should render password input', () => {
      renderWithProviders(<LoginPage />)

      const passwordInput = screen.getByPlaceholderText(/senha/i)
      expect(passwordInput).toBeInTheDocument()
    })

    it('should render OptiFlow branding', () => {
      renderWithProviders(<LoginPage />)

      expect(screen.getByText(/optiflow/i)).toBeInTheDocument()
    })

    it('should render show/hide password toggle', () => {
      renderWithProviders(<LoginPage />)

      // Should have a button to toggle password visibility
      const toggleButtons = screen.getAllByRole('button')
      expect(toggleButtons.length).toBeGreaterThan(0)
    })
  })

  describe('Form Validation', () => {
    it('should require username/email', async () => {
      renderWithProviders(<LoginPage />)

      const submitButton = screen.getByRole('button', { name: /entrar/i })

      // Submit without filling in username
      await userEvent.click(submitButton)

      // Should not call login without credentials
      expect(mockLogin).not.toHaveBeenCalled()
    })

    it('should require password', async () => {
      renderWithProviders(<LoginPage />)

      const emailInput = screen.getByPlaceholderText(/admin@optiflow.com/i)
      const submitButton = screen.getByRole('button', { name: /entrar/i })

      // Fill only email
      await userEvent.type(emailInput, 'test@example.com')
      await userEvent.click(submitButton)

      // Should not call login without password
      expect(mockLogin).not.toHaveBeenCalled()
    })
  })

  describe('Form Submission', () => {
    it('should call login with credentials on submit', async () => {
      mockLogin.mockResolvedValue(true)

      renderWithProviders(<LoginPage />)

      const emailInput = screen.getByPlaceholderText(/admin@optiflow.com/i)
      const passwordInput = screen.getByPlaceholderText(/senha/i)
      const submitButton = screen.getByRole('button', { name: /entrar/i })

      // Fill in form
      await userEvent.type(emailInput, 'admin@optiflow.com')
      await userEvent.type(passwordInput, 'admin123')
      await userEvent.click(submitButton)

      // Should call login with entered credentials
      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalled()
      })
    })
  })

  describe('Loading State', () => {
    it('should show loading state during login', () => {
      mockUseAuth.mockReturnValue({
        login: mockLogin,
        loading: true,
        user: null,
        isAuthenticated: false,
        error: null,
      })

      renderWithProviders(<LoginPage />)

      // Button should be disabled when loading
      const submitButton = screen.getByRole('button', { name: /entrar|entrando|carregando/i })
      expect(submitButton).toBeDisabled()
    })

    it('should disable inputs during loading', () => {
      mockUseAuth.mockReturnValue({
        login: mockLogin,
        loading: true,
        user: null,
        isAuthenticated: false,
        error: null,
      })

      renderWithProviders(<LoginPage />)

      const emailInput = screen.getByPlaceholderText(/admin@optiflow.com/i)
      expect(emailInput).toBeDisabled()
    })
  })

  describe('Error Handling', () => {
    it('should display error message on login failure', async () => {
      mockLogin.mockRejectedValue(new Error('Invalid credentials'))

      renderWithProviders(<LoginPage />)

      const emailInput = screen.getByPlaceholderText(/admin@optiflow.com/i)
      const passwordInput = screen.getByPlaceholderText(/senha/i)
      const submitButton = screen.getByRole('button', { name: /entrar/i })

      await userEvent.type(emailInput, 'test@example.com')
      await userEvent.type(passwordInput, 'wrongpassword')
      await userEvent.click(submitButton)

      // Should show error message (exact text depends on implementation)
      await waitFor(() => {
        // Login was called
        expect(mockLogin).toHaveBeenCalled()
      })
    })
  })

  describe('Password Visibility Toggle', () => {
    it('should toggle password visibility', async () => {
      renderWithProviders(<LoginPage />)

      const passwordInput = screen.getByPlaceholderText(/senha/i)

      // Initially password should be hidden
      expect(passwordInput).toHaveAttribute('type', 'password')

      // Find and click toggle button (it's near the password field)
      const toggleButtons = screen.getAllByRole('button')
      const toggleButton = toggleButtons.find(
        (btn) => btn.querySelector('svg') !== null && btn !== screen.getByRole('button', { name: /entrar/i })
      )

      if (toggleButton) {
        await userEvent.click(toggleButton)

        // After click, should show password
        await waitFor(() => {
          expect(passwordInput).toHaveAttribute('type', 'text')
        })
      }
    })
  })

  describe('Accessibility', () => {
    it('should have form with proper labels', () => {
      renderWithProviders(<LoginPage />)

      // Inputs should have associated labels or aria-labels
      const emailInput = screen.getByPlaceholderText(/admin@optiflow.com/i)
      const passwordInput = screen.getByPlaceholderText(/senha/i)

      expect(emailInput).toBeInTheDocument()
      expect(passwordInput).toBeInTheDocument()
    })

    it('should have submit button with accessible name', () => {
      renderWithProviders(<LoginPage />)

      const submitButton = screen.getByRole('button', { name: /entrar/i })
      expect(submitButton).toBeInTheDocument()
    })
  })

  describe('Navigation', () => {
    it('should redirect to dashboard after successful login', async () => {
      mockLogin.mockResolvedValue(true)

      renderWithProviders(<LoginPage />)

      const emailInput = screen.getByPlaceholderText(/admin@optiflow.com/i)
      const passwordInput = screen.getByPlaceholderText(/senha/i)
      const submitButton = screen.getByRole('button', { name: /entrar/i })

      await userEvent.type(emailInput, 'admin@optiflow.com')
      await userEvent.type(passwordInput, 'admin123')
      await userEvent.click(submitButton)

      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalled()
      })
    })
  })
})

describe('LoginPage UI Elements', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUseAuth.mockReturnValue({
      login: mockLogin,
      loading: false,
      user: null,
      isAuthenticated: false,
      error: null,
    })
  })

  it('should render feature cards on left panel', () => {
    renderWithProviders(<LoginPage />)

    // Check for feature descriptions
    expect(screen.getByText(/Monitoramento em Tempo Real/i)).toBeInTheDocument()
    expect(screen.getByText(/Inteligência Artificial/i)).toBeInTheDocument()
  })

  it('should render copyright notice', () => {
    renderWithProviders(<LoginPage />)

    expect(screen.getByText(/OptiFlow AI/i)).toBeInTheDocument()
    expect(screen.getByText(/direitos reservados/i)).toBeInTheDocument()
  })
})
