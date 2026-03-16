import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
// API_TARGET env var lets docker-compose point to the backend service name.
// Falls back to localhost:9000 for non-Docker local dev.
const apiTarget = process.env.API_TARGET ?? 'http://localhost:9000';

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    allowedHosts: ['localhost', '2c2d17fef2ff.ngrok-free.app'],
    hmr: {
      // Browser connects to HMR websocket via the host machine, not the container
      host: 'localhost',
      port: 5173,
    },
    proxy: {
      '/api': {
        target: apiTarget,
        changeOrigin: true,
        secure: false,
      }
    }
  },
})