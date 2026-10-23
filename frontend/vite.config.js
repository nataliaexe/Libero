import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => ({
  plugins: [react()],
  define: { 'process.env.NODE_ENV': JSON.stringify(mode) },
  build: {
    outDir: '../interface/web/assets/libero-avatar',
    emptyOutDir: true,
    lib: {
      entry: 'src/avatarBridge.jsx',
      name: 'LiberoAvatar',
      formats: ['iife'],
      fileName: () => 'libero-avatar.js',
      cssFileName: 'libero-avatar',
    },
  },
  server: { port: 3000, strictPort: true },
}));
