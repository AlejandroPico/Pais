import { defineConfig } from 'vite';
export default defineConfig({base: './',server:{watch:{ignored:['**/.cache/**']}}, build: {rollupOptions:{output:{manualChunks:{maplibre:['maplibre-gl']}}}}});
