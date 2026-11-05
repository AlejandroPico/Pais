import fs from 'node:fs';
import clipping from 'polygon-clipping';
const path = new URL('../public/data/', import.meta.url);
const communities = JSON.parse(fs.readFileSync(new URL('communities.geojson', path), 'utf8'));
const spain = clipping.union(...communities.features.map(f => f.geometry.coordinates));
const surroundings = clipping.difference([[[[-30,20],[15,20],[15,55],[-30,55],[-30,20]]]], spain);
fs.writeFileSync(new URL('context-mask.geojson', path), JSON.stringify({type:'Feature',properties:{source:'Máscara calculada a partir de límites IGN actuales · CC BY 4.0'},geometry:{type:'MultiPolygon',coordinates:surroundings}}));
console.log('Spain context mask prepared');
