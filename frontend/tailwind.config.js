/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // SmartPort Brand Colors (Dark Mode Principal)
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',  // Primary blue
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
          950: '#172554',
        },
        // Success (Verde tecnológico)
        success: {
          300: '#6ee7b7',
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
        },
        // Warning (Laranja para alertas)
        warning: {
          300: '#fcd34d',
          400: '#fbbf24',
          500: '#f59e0b',
          600: '#d97706',
          700: '#b45309',
        },
        // Danger (Vermelho para crítico)
        danger: {
          300: '#fca5a5',
          400: '#f87171',
          500: '#ef4444',
          600: '#dc2626',
          700: '#b91c1c',
        },
        // Info (Ciano para informação)
        info: {
          400: '#22d3ee',
          500: '#06b6d4',
          600: '#0891b2',
        },
        // Dark theme (Background colors)
        dark: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',  // Cards
          800: '#1e293b',  // Background dark
          900: '#0f172a',  // Background darker
          950: '#020617',  // Deepest dark
        },
        // Status colors (Operacional)
        status: {
          operating: '#22c55e',    // Verde - operando
          idle: '#94a3b8',         // Cinza - parado
          warning: '#f59e0b',      // Laranja - atenção
          error: '#ef4444',        // Vermelho - erro
          maintenance: '#8b5cf6',  // Roxo - manutenção
          offline: '#64748b',      // Cinza escuro - offline
        },
        // Vessel status
        vessel: {
          loading: '#22c55e',
          unloading: '#06b6d4',
          berthed: '#3b82f6',
          anchored: '#f59e0b',
          scheduled: '#94a3b8',
          departed: '#64748b',
        },
        // Berth status
        berth: {
          available: '#22c55e',
          occupied: '#f59e0b',
          maintenance: '#8b5cf6',
          reserved: '#3b82f6',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'bounce-slow': 'bounce 2s infinite',
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
      backdropBlur: {
        xs: '2px',
      },
      boxShadow: {
        'glow-sm': '0 0 10px rgba(59, 130, 246, 0.3)',
        'glow-md': '0 0 20px rgba(59, 130, 246, 0.4)',
        'glow-lg': '0 0 30px rgba(59, 130, 246, 0.5)',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}
