import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => ({
  plugins: [react()],
  define: { 'process.env.NODE_ENV': JSON.stringify(mode) },
  build: {
    outDir: '../interface/web/assets/react-app',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: './src/main.jsx',
      },
      output: {
        entryFileNames: 'app.js',
        chunkFileNames: 'app-[hash].js',
        assetFileNames: 'app-[hash].[ext]',
      },
    },
  },
  server: { port: 3000, strictPort: true },
}));
