import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@pages': path.resolve(__dirname, './src/pages'),
      '@api': path.resolve(__dirname, './src/api'),
      '@store': path.resolve(__dirname, './src/store'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@utils': path.resolve(__dirname, './src/utils'),
      '@types': path.resolve(__dirname, './src/types'),
      // Polyfills for Node.js modules in browser
      'buffer': 'buffer',
      'stream': 'stream-browserify',
      'assert': 'assert',
    },
  },
  define: {
    // Fix for buffer polyfill
    'global': 'globalThis',
  },
  server: {
    port: 3000,
    host: true,
    watch: {
      usePolling: false,
      interval: 100,
    },
    hmr: {
      overlay: true,
    },
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: process.env.VITE_WS_URL || 'ws://127.0.0.1:8000',
        ws: true,
      },
    },
  },
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      'react-is',
      'prop-types',
      '@mui/material',
      '@mui/system',
      '@mui/x-tree-view',
      '@emotion/react',
      '@emotion/styled',
      '@reduxjs/toolkit',
      'react-redux',
      'axios',
      'date-fns',
      'buffer',
      'stream-browserify',
      'assert'
    ],
    exclude: ['@mui/icons-material'],
    esbuildOptions: {
      loader: {
        '.js': 'jsx',
      },
      define: {
        global: 'globalThis'
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    chunkSizeWarningLimit: 1000, // Increase warning limit to 1MB
    rollupOptions: {
      output: {
        manualChunks: (id) => {
          // React core - always needed
          if (id.includes('node_modules/react/') ||
              id.includes('node_modules/react-dom/') ||
              id.includes('node_modules/react-router')) {
            return 'react-vendor';
          }

          // Redux - often needed for state
          if (id.includes('node_modules/@reduxjs/') ||
              id.includes('node_modules/react-redux/')) {
            return 'redux-vendor';
          }

          // MUI - UI framework (large but commonly used)
          if (id.includes('node_modules/@mui/') ||
              id.includes('node_modules/@emotion/')) {
            return 'mui-vendor';
          }

          // Plotly - HEAVY (~4MB) - lazy load only when needed
          // This chunk will only load when Visualization components are used
          if (id.includes('node_modules/plotly') ||
              id.includes('node_modules/react-plotly')) {
            return 'plotly-vendor';
          }

          // D3 - used by Recharts and some visualizations
          if (id.includes('node_modules/d3')) {
            return 'd3-vendor';
          }

          // Recharts - lightweight charting (main charts)
          if (id.includes('node_modules/recharts')) {
            return 'recharts-vendor';
          }

          // Other utilities
          if (id.includes('node_modules/axios') ||
              id.includes('node_modules/date-fns') ||
              id.includes('node_modules/zod')) {
            return 'utils-vendor';
          }

          // Framer Motion - animations
          if (id.includes('node_modules/framer-motion')) {
            return 'animation-vendor';
          }

          // Grid/DnD libraries
          if (id.includes('node_modules/react-grid-layout') ||
              id.includes('node_modules/react-dnd') ||
              id.includes('node_modules/react-draggable') ||
              id.includes('node_modules/react-resizable')) {
            return 'grid-vendor';
          }
        },
      },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    css: true,
  },
})
