import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

// Tauri 期望固定端口；不能在 dev 时清屏，否则 Rust 日志会被吞。
// 注意：Windows 保留段 1337-1436，所以不用 1420，改 5173。
export default defineConfig({
  plugins: [vue()],
  clearScreen: false,
  server: {
    port: 5173,
    strictPort: true,
    host: "127.0.0.1",
    watch: { ignored: ["**/src-tauri/**"] }
  },
  build: {
    target: "chrome110",
    minify: "esbuild",
    sourcemap: false
  }
});
