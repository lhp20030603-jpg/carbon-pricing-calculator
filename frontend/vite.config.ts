import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";

// Dev proxy forwards /api/* to the uvicorn backend so the frontend fetches
// a relative path in both dev and prod (Vercel rewrites do the same in prod).
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    sourcemap: true,
    // Strip `<link rel="modulepreload">` for the lazy Plotly chunk so the
    // ~1.4 MB gzipped bundle is fetched only when the chart actually renders.
    modulePreload: {
      resolveDependencies: (_url, deps) =>
        deps.filter((dep) => !dep.includes("plotly")),
    },
  },
});
