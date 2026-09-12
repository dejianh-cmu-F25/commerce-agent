import path from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Dev server proxies the API to the FastAPI backend; the production build is
// emitted into web/static/app and served by FastAPI as the SPA.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(import.meta.dirname, "./src"),
    },
  },
  build: {
    outDir: "../web/static/app",
    emptyOutDir: true,
  },
  server: {
    proxy: {
      "/chat": "http://127.0.0.1:8000",
      "/healthz": "http://127.0.0.1:8000",
      "/readyz": "http://127.0.0.1:8000",
      "/budget": "http://127.0.0.1:8000",
    },
  },
});
