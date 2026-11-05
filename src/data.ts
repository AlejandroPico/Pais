export type Metric = 'population' | 'density' | 'women' | 'change';
export type Observation = Record<string, number>;
export type Territory = { name: string; series: Record<string, Observation> };
export type Population = { source: string; sourceUrl: string; license: string; note: string; data: { province: Record<string, Territory>; community: Record<string, Territory> } };
export type Properties = { code: string; name: string; communityCode: string; areaKm2: number };
export const labels: Record<Metric, string> = {population:'Población', density:'Densidad de población', women:'Proporción de mujeres', change:'Cambio desde 1996'};
export const units: Record<Metric, string> = {population:'habitantes',density:'hab./km² · aprox.',women:'% de la población',change:'% respecto a 1996'};
export const normalize = (text: string) => text.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
export function valueFor(territory: Territory | undefined, year: number, metric: Metric, area: number): number | null {
  const row = territory?.series[String(year)];
  if (!row || !Number.isFinite(row['0'])) return null;
  const total = row['0'];
  if (metric === 'population') return total;
  if (metric === 'density') return area > 0 ? total / area : null;
  if (metric === 'women') return total > 0 && Number.isFinite(row['2']) ? row['2'] / total * 100 : null;
  const base = territory?.series['1996']?.['0'];
  return base && base > 0 ? (total / base - 1) * 100 : null;
}
export function formatValue(value: number | null, metric: Metric) {
  return value === null ? 'Sin datos' : new Intl.NumberFormat('es-ES', {maximumFractionDigits:metric === 'population' ? 0 : 1}).format(value);
}
export const scales: Record<Metric, {stops: number[]; colors: string[]}> = {
  population:{stops:[0,100000,300000,700000,1500000,4000000,7000000],colors:['#edf1d5','#c9dea7','#a0c68a','#70a87b','#43866a','#266153','#123f38']},
  density:{stops:[0,10,25,50,100,300,1000],colors:['#edf1d5','#c9dea7','#a0c68a','#70a87b','#43866a','#266153','#123f38']},
  women:{stops:[48,49,50,51,52,53,54],colors:['#f1dec3','#dfc39c','#c8bc94','#a1b391','#78a18a','#4b8172','#235b56']},
  change:{stops:[-30,-15,0,15,30,50,80],colors:['#aa624b','#cd9674','#eee3c8','#bad0a0','#7fa788','#498276','#24594f']}
};
export function safeUrl(value: string | undefined, fallback: string) {
  if (!value) return fallback;
  try {const u = new URL(value, 'https://www.ine.es'); return u.protocol === 'https:' ? u.href : fallback;} catch {return fallback;}
}
