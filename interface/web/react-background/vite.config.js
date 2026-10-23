import path from 'node:path';
import { fileURLToPath } from 'node:url';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

const projectDir = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig(({ mode }) => ({
  plugins: [react()],
  define: { 'process.env.NODE_ENV': JSON.stringify(mode) },
  resolve: {
    alias: {
      '@': path.resolve(projectDir, 'src'),
    },
  },
  build: {
    outDir: path.resolve(projectDir, '../assets/react-background'),
    emptyOutDir: true,
    lib: {
      entry: path.resolve(projectDir, 'src/bridge.jsx'),
      name: 'LiberoBackground',
      formats: ['iife'],
      fileName: () => 'libero-background.js',
      cssFileName: 'libero-background',
    },
  },
}));
