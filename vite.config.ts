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
      const sourceRoot = resolve('datos');
      const offlineIndexes = new Set(['poblacion', 'renta', 'vivienda'].map(topic => resolve(sourceRoot, topic, 'ine', 'index.json')));
      offlineIndexes.add(resolve(sourceRoot, 'catalogo', 'investigacion'));
      cpSync(sourceRoot, resolve(dir!, 'datos'), {
        recursive: true,
        filter: source => !basename(source).startsWith('.') && !offlineIndexes.has(source),
      });
    },
  }],
});
