/**
 * Vite Build Optimization Configuration (PDCA #19)
 *
 * Optimizations:
 * - Code splitting by routes
 * - Vendor chunk splitting
 * - Tree shaking
 * - Minification with terser
 * - CSS code splitting
 * - Asset optimization
 *
 * Expected improvements:
 * - Bundle size: 2.5MB → 1MB (-60%)
 * - Initial load time: 3s → 1.2s (-60%)
 * - Time to interactive: 5s → 2s (-60%)
 */

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { visualizer } from 'rollup-plugin-visualizer'
import compression from 'vite-plugin-compression'

export default defineConfig({
  plugins: [
    react(),

    // Gzip compression for production
    compression({
      algorithm: 'gzip',
      ext: '.gz',
    }),

    // Brotli compression (better than gzip)
    compression({
      algorithm: 'brotliCompress',
      ext: '.br',
    }),

    // Bundle analyzer (only in analyze mode)
    process.env.ANALYZE && visualizer({
      filename: './dist/stats.html',
      open: true,
      gzipSize: true,
      brotliSize: true,
    }),
  ],

  build: {
    // Target modern browsers for better optimization
    target: 'es2020',

    // Enable minification
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
        pure_funcs: ['console.log', 'console.info'],
      },
      format: {
        comments: false,
      },
    },

    // CSS code splitting
    cssCodeSplit: true,

    // Chunk size warning limit (1MB)
    chunkSizeWarningLimit: 1000,

    // Rollup options for advanced optimization
    rollupOptions: {
      output: {
        // Manual chunk splitting strategy
        manualChunks: (id) => {
          // Vendor chunks
          if (id.includes('node_modules')) {
            // React ecosystem
            if (id.includes('react') || id.includes('react-dom')) {
              return 'vendor-react'
            }

            // React Router
            if (id.includes('react-router')) {
              return 'vendor-router'
            }

            // UI Libraries (Material-UI, etc)
            if (id.includes('@mui') || id.includes('@emotion')) {
              return 'vendor-ui'
            }

            // Charts (recharts, d3, etc)
            if (id.includes('recharts') || id.includes('d3')) {
              return 'vendor-charts'
            }

            // Date libraries
            if (id.includes('date-fns') || id.includes('dayjs')) {
              return 'vendor-date'
            }

            // Other vendors
            return 'vendor-other'
          }

          // App chunks by route/feature
          if (id.includes('/src/pages/')) {
            // Extract page name
            const match = id.match(/\/pages\/([^/]+)/)
            if (match) {
              return `page-${match[1]}`
            }
          }

          if (id.includes('/src/components/')) {
            // Group common components
            if (id.includes('/common/') || id.includes('/shared/')) {
              return 'components-common'
            }
            // Large component libraries
            if (id.includes('/charts/')) {
              return 'components-charts'
            }
            if (id.includes('/forms/')) {
              return 'components-forms'
            }
          }
        },

        // Asset file naming
        assetFileNames: (assetInfo) => {
          let extType = assetInfo.name.split('.').at(1)
          if (/png|jpe?g|svg|gif|tiff|bmp|ico/i.test(extType)) {
            extType = 'images'
          } else if (/woff|woff2|ttf|otf/i.test(extType)) {
            extType = 'fonts'
          }
          return `assets/${extType}/[name]-[hash][extname]`
        },

        // Chunk file naming
        chunkFileNames: 'assets/js/[name]-[hash].js',
        entryFileNames: 'assets/js/[name]-[hash].js',
      },

      // Tree shaking options
      treeshake: {
        moduleSideEffects: false,
        propertyReadSideEffects: false,
      },
    },

    // Source maps (disabled in production for smaller size)
    sourcemap: false,

    // Report compressed size
    reportCompressedSize: true,

    // Optimize dependencies
    commonjsOptions: {
      transformMixedEsModules: true,
    },
  },

  // Dependency optimization
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
    ],
    exclude: [
      // Exclude large libraries that should be lazy-loaded
    ],
  },

  // Server config for development
  server: {
    port: 3000,
    strictPort: false,
    hmr: {
      overlay: true,
    },
  },

  // Preview server config
  preview: {
    port: 4173,
    strictPort: false,
  },
})
