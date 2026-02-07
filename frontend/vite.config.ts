import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
                            server: {
                              port: 5173,
                              proxy: {
                                // Roteia /api/v1/... para http://localhost:8000/api/v1/...
                                "/api": {
                                  target: "http://localhost:8000",
                            changeOrigin: true,
                            secure: false,
                                },
                                // Roteia /static/... para http://localhost:8000/static/...
                                "/static": {
                                  target: "http://localhost:8000",
                            changeOrigin: true,
                            secure: false,
                                }
                              }
                            }
});
