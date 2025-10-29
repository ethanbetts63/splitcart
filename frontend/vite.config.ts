import path from "path"
import tailwindcss from "@tailwindcss/vite"
import react from "@vitejs/plugin-react"
import { defineConfig, loadEnv } from "vite"

// https://vite.dev/config/
export default ({ mode }) => {
  const env = loadEnv(mode, '../', '');
  return defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    proxy: {
      '/api': {
          target: env.API_SERVER_URL || 'http://127.0.0.1:8000',
          changeOrigin: true,
        },
    },
  },
})
}
