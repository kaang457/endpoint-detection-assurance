import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { resolve } from "node:path";

// The build lands inside the Python package so the FastAPI control plane can
// serve it with no second process; `npm run dev` proxies the API instead.
const API = "http://127.0.0.1:8000";
const proxy = Object.fromEntries(
  ["/live", "/catalog", "/report", "/fleet"].map((p) => [p, { target: API, changeOrigin: true }]),
);

export default defineConfig({
  plugins: [react(), tailwindcss()],
  build: {
    outDir: resolve(__dirname, "../src/eda/webui"),
    emptyOutDir: true,
  },
  server: { proxy },
});
