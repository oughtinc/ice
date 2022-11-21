import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig({
  build: {
    outDir: "../ice/routes/ui/",
  },
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://localhost:8935",
    },
  },
});
