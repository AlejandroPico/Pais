import fs from 'node:fs';
import clipping from 'polygon-clipping';
import {projectFeature,ATLAS_REGIONS} from '../src/atlas-coordinates.ts';
const root=new URL('../',import.meta.url);
const read=p=>JSON.parse(fs.readFileSync(new URL(p,root),'utf8'));
const provinces=read('datos/territorio/provinces.geojson');
// IGN code 54 includes other administrative situations; it is not an assertion
// that every polygon is Spanish territory. Render the reviewed island/peñon groups.
const selected=provinces.features.map(f=>f.properties.code==='54'?{...f,geometry:{...f.geometry,coordinates:f.geometry.coordinates.filter(poly=>poly[0].every(p=>p[1]<35.3))}}:f);
const country=clipping.union(...selected.map(f=>f.geometry.coordinates));
const feature=coordinates=>({type:'Feature',properties:{name:'España',source:'IGN · CC BY 4.0'},geometry:{type:'MultiPolygon',coordinates}});
const displayed=projectFeature(feature(country));
const world=[[[[-180,-85],[180,-85],[180,85],[-180,85],[-180,-85]]]];
const sea=feature(clipping.difference(world,displayed.geometry.coordinates));
sea.properties={name:'Máscara de presentación: solo España',visualization:'Composición cartográfica con escalas distintas. No reutilizar como delimitación geográfica.'};
fs.writeFileSync(new URL('datos/territorio/country.geojson',root),JSON.stringify(feature(country)));
fs.writeFileSync(new URL('datos/territorio/country-atlas.geojson',root),JSON.stringify({...displayed,properties:{name:'España',source:'IGN · CC BY 4.0',geographicCoordinates:false,canonicalSource:'country.geojson',visualization:'Canarias, Ceuta, Melilla y grupos insulares en marcos de atlas; ampliaciones rotuladas'}}));
fs.writeFileSync(new URL('datos/territorio/sea-atlas.geojson',root),JSON.stringify(sea));
const small=selected.flatMap(f=>f.geometry.coordinates.filter(poly=>poly[0].every(p=>ATLAS_REGIONS.slice(3).some(r=>p[0]>=r.original[0]&&p[0]<=r.original[2]&&p[1]>=r.original[1]&&p[1]<=r.original[3]))));
fs.writeFileSync(new URL('datos/territorio/islets-atlas.geojson',root),JSON.stringify(projectFeature(feature(small))));
console.log('Atlas layout: Spain only; four anchored frames; original source geometries retained.');
