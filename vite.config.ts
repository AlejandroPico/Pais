import {cpSync} from 'node:fs';
import {basename, resolve, sep} from 'node:path';
import {defineConfig} from 'vite';
import pagesArchives from './registry/pages-archives.json';

export default defineConfig({
  base: './',
  server: {watch: {ignored: ['**/.cache/**']}},
  build: {rollupOptions: {output: {manualChunks: {maplibre: ['maplibre-gl']}}}},
  plugins: [{
    name: 'atlas-data',
    apply: 'build',
    writeBundle({dir}) {
      const sourceRoot = resolve('datos');
      const offlineIndexes = new Set(['poblacion', 'renta', 'vivienda', 'economia', 'comercio'].map(topic => resolve(sourceRoot, topic, 'ine', 'index.json')));
      offlineIndexes.add(resolve(sourceRoot, 'catalogo', 'investigacion'));
      for(const file of pagesArchives.files)offlineIndexes.add(resolve(sourceRoot,'territorio',file));
      const education=resolve(sourceRoot,'educacion');
      const science=resolve(sourceRoot,'ciencia');
      cpSync(sourceRoot, resolve(dir!, 'datos'), {
        recursive: true,
        filter: source => !basename(source).startsWith('.') && !offlineIndexes.has(source)
          && !(source.startsWith(education+sep)&&['index.json', '-main.json.gz'].some(suffix=>source.endsWith(suffix)))
          && !(source.startsWith(science+sep)&&resolve(science,'viewer.json.gz')!==source
            && (source.endsWith('index.json')||source.endsWith('.gz'))),
      });
    },
  }],
});
