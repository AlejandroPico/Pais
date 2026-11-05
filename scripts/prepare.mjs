import {copyFileSync, mkdirSync} from 'node:fs';
// The editable favicon lives at the repository root; Vite publishes this copy unchanged.
mkdirSync(new URL('../public/',import.meta.url),{recursive:true});
copyFileSync(new URL('../favicon.svg',import.meta.url),new URL('../public/favicon.svg',import.meta.url));
