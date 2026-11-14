import {cpSync} from 'node:fs';
import {basename, resolve} from 'node:path';
import {defineConfig} from 'vite';

export default defineConfig({
  base: './',
  server: {watch: {ignored: ['**/.cache/**']}},
  build: {rollupOptions: {output: {manualChunks: {maplibre: ['maplibre-gl']}}}},
  plugins: [{
    name: 'atlas-data',
    apply: 'build',
    writeBundle({dir}) {
      cpSync(resolve('datos'), resolve(dir!, 'datos'), {
        recursive: true,
        filter: source => !basename(source).startsWith('.'),
      });
    },
  }],
});
