/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class', // Enable dark mode with class strategy
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
          950: '#172554',
        },
        // Industrial color scheme
        industrial: {
          orange: '#FF6B35',
          blue: '#004E89',
          gray: '#1A1A2E',
          lightGray: '#E8E8E8',
        },
        // Status colors
        status: {
          running: '#10B981',
          stopped: '#EF4444',
          idle: '#F59E0B',
          warning: '#F59E0B',
          error: '#EF4444',
          maintenance: '#8B5CF6',
        },
        // Alarm severity
        alarm: {
          critical: '#DC2626',
          high: '#F59E0B',
          medium: '#3B82F6',
          low: '#10B981',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [],
}
