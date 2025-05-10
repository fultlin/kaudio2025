import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
      components: path.resolve(__dirname, "./src/components"),
      axiosurl: path.resolve(__dirname, './src/axios'),
      stores: path.resolve(__dirname, './src/stores'),
      assets: path.resolve(__dirname, './src/assets')
    },
  },
  css: {
    preprocessorOptions: {
      scss: {
        additionalData: `@import "@/variables.scss";`, 
        includePaths: [path.resolve(__dirname, "src")],
      },
    },
  },
});
