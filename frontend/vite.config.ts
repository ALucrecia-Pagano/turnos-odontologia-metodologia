/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// El .env vive en la raíz del repo (envDir: ".."); en Docker, Compose pasa VITE_API_URL.
// usePolling: Docker Desktop en Windows no propaga los eventos del bind mount (HMR).
export default defineConfig({
  plugins: [react()],
  envDir: "..",
  server: {
    port: 5173,
    strictPort: true,
    watch: {
      usePolling: true,
      interval: 300,
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/test/setup.ts",
    css: { modules: { classNameStrategy: "non-scoped" } },
  },
});
