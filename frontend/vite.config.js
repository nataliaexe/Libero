import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
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
});
