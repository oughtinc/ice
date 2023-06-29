import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig({
  base: "./",
  build: {
    chunkSizeWarningLimit: 4000,
    emptyOutDir: true,
    outDir: "../ice/routes/ui/",
  },
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://localhost:8935",
    },
  },
});
