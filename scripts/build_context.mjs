import fs from 'node:fs';
import crypto from 'node:crypto';
import clipping from 'polygon-clipping';

// Natural Earth is used only for neighbouring land, clipped to Spain's context.
// Spain's coast remains the detailed IGN geometry already in the repository.
const input = new URL('../.cache/natural-earth-countries.geojson', import.meta.url);
const raw = fs.readFileSync(input);
const countries = JSON.parse(raw);
const provinces = JSON.parse(fs.readFileSync(new URL('../public/data/provinces.geojson',import.meta.url)));
const rectangle = [[[-21,24],[8,24],[8,48],[-21,48],[-21,24]]];
const spain = clipping.union(...provinces.features.map(f=>f.geometry.coordinates));
const nearby = countries.features.filter(f => ['PRT','FRA','MAR','DZA','AND','GIB','TUN'].includes(f.properties.ADM0_A3));
if (nearby.length < 5) throw new Error('Missing neighbouring countries');
const land = clipping.union(...nearby.map(f=>f.geometry.type==='Polygon'?[f.geometry.coordinates]:f.geometry.coordinates));
const neighbors = clipping.difference(clipping.intersection(land,rectangle),spain);
const sea = clipping.difference(rectangle,clipping.union(neighbors,spain));
for(const [name,coordinates] of [['neighbor-land',neighbors],['sea',sea]]) {
  fs.writeFileSync(new URL(`../public/data/${name}.geojson`,import.meta.url),JSON.stringify({type:'Feature',properties:{source:'IGN + Natural Earth',scope:'Contexto de España; sin valor de delimitación marítima'},geometry:{type:'MultiPolygon',coordinates}}));
}
fs.writeFileSync(new URL('../public/data/context-provenance.json',import.meta.url),JSON.stringify({source:'https://github.com/nvkelso/natural-earth-vector/blob/master/geojson/ne_10m_admin_0_countries.geojson',license:'Natural Earth · public domain',sha256:crypto.createHash('sha256').update(raw).digest('hex'),spain:'Límites IGN preservados; CC BY 4.0',bounds:[-21,24,8,48]},null,2));

// A compact, recognisable peninsular silhouette for the favicon.
const mainland=spain.flatMap(p=>[p[0]]).filter(r=>r.some(([x,y])=>x>-10&&x<4&&y>36&&y<44)).sort((a,b)=>b.length-a.length)[0];
const sample=mainland.filter((_,i)=>i%Math.max(1,Math.floor(mainland.length/100))===0);
const path=sample.map(([x,y],i)=>`${i?'L':'M'}${(10+(x+9.4)*3.8).toFixed(1)},${(10+(43.85-y)*5.5).toFixed(1)}`).join(' ')+'Z';
fs.writeFileSync(new URL('../favicon.svg',import.meta.url),`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="#15231e"/><path d="${path}" fill="#d7eaa1" stroke="#d7eaa1" stroke-width="1" stroke-linejoin="round"/></svg>\n`);
console.log('Coastal context and Spain favicon generated.');
