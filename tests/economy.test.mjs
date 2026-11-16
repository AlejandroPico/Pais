import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {gunzipSync} from 'node:zlib';
import {queryCube, seriesCsv, unitFor} from '../src/demography-data.ts';

const base = new URL('../datos/economia/', import.meta.url);
const read = (folder, file = 'index.json') => {
  const bytes = readFileSync(new URL(`${folder}/${file}`, base));
  return JSON.parse(file.endsWith('.gz') ? gunzipSync(bytes) : bytes);
};
const sections = ['ine', 'dae-historica', 'cna', 'miteco'];

function lookup(folder, id, areaId, periodId, filters = {}) {
  const table = read(folder).tables.find(t => t.id === id);
  const territory = table.territories.findIndex(a => a.id === areaId);
  const period = table.periods.findIndex(p => p.id === periodId);
  const dims = table.dimensions.map(d => filters[d.name] === undefined ? 0 : d.values.indexOf(filters[d.name]));
  assert.ok(territory >= 0 && period >= 0 && dims.every(i => i >= 0));
  const query = {territory, period, dims, level: table.territories[territory].level};
  const cube = read(folder, table.shards.find(s => s.id === 'main').file);
  const {series} = queryCube(table, cube, query);
  const point = series.find(row => row.period === period);
  assert.ok(point);
  return {table, query, series, point, unit: unitFor(table, dims)};
}

test('F07 has distinct products, all 17 DAE editions and a documented empty INE distribution', () => {
  const tables = sections.flatMap(folder => read(folder).tables);
  assert.equal(tables.length, 454);
  assert.equal(new Set(tables.map(t => t.id)).size, 454);
  assert.equal(tables.reduce((n, t) => n + t.rows, 0), 6_296_184);
  const dae = tables.filter(t => t.family === 'Demografía armonizada de empresas');
  const editions = new Map();
  for (const table of dae) {
    const year = Number(table.label.match(/ · (\d{4})$/)[1]);
    editions.set(year, (editions.get(year) ?? 0) + 1);
  }
  assert.deepEqual([...editions].sort((a, b) => a[0] - b[0]),
    Array.from({length: 17}, (_, i) => [2008 + i, i < 6 ? 10 : 11]));
  const products = JSON.parse(readFileSync(new URL('../registry/economy-products.json', import.meta.url)));
  const empty = products.inventory.find(p => p.id === 'economy-inventory:82225');
  assert.equal(empty.status, 'bloqueado');
  assert.equal(empty.mapAction, undefined);
});

test('F07 matches regional accounts, company demography and each data source’s units', () => {
  const madrid = lookup('ine', 82284, 'community:13', '2025');
  assert.equal(madrid.point.value, 337_216_162);
  assert.equal(madrid.point.status, 'Avance');
  assert.equal(madrid.unit, 'Miles · Euros');
  const spain = lookup('ine', 82286, 'national:ES', '2025');
  assert.equal(spain.point.value, 2.6);
  assert.equal(spain.unit, 'Porcentaje');
  assert.equal(lookup('ine', 82463, 'national:ES', '2024').point.value, 3_552_872);
  assert.equal(lookup('dae-historica', 943001, 'national:ES', '2008').point.value, 3_711_835);
  assert.equal(lookup('ine', 79486, 'national:ES', '2023').point.value, 54_424);

  const annual = lookup('cna', 941001, 'national:ES', '2025', {Indicador: 'PIB per cápita (Euros) · PIB per cápita (*)'});
  assert.equal(annual.unit, 'Euros por habitante');
  assert.equal(annual.point.status, 'Avance');
  const mining = lookup('miteco', 942001, 'province:17', '2018');
  assert.equal(mining.point.value, 6_672);
  assert.equal(mining.unit, 'Unidad sin especificar en el CSV');
  const csv = seriesCsv(mining.table, mining.query, mining.series);
  assert.match(csv, /^\uFEFF"distribución"/);
  assert.match(csv, /descargaCSVProduccion\.aspx/);
});
