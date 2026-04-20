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
    // Plotly.js is heavy; split it into its own chunk to keep the main bundle lean.
    rollupOptions: {
      output: {
        manualChunks: (id: string) => {
          if (id.includes("plotly.js") || id.includes("react-plotly.js")) {
            return "plotly";
          }
          return undefined;
        },
      },
    },
  },
});
