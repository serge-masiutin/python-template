import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { fileURLToPath } from "node:url";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  base: "/static/",
  resolve: {
    alias: { "@": fileURLToPath(new URL("./web/src", import.meta.url)) },
  },
  publicDir: "web/public",
  server: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
    cors: { origin: "http://127.0.0.1:8000" },
  },
  build: {
    outDir: "web/build",
    emptyOutDir: true,
    manifest: "manifest.json",
    rollupOptions: { input: "web/src/app.tsx" },
  },
});
