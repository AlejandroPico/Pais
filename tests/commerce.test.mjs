import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {gunzipSync} from 'node:zlib';
import {queryCube, selectedSeriesMetadata, seriesCsv, unitFor} from '../src/demography-data.ts';

const base = new URL('../datos/comercio/', import.meta.url);
function read(folder, filename = 'index.json') {
  const data = readFileSync(new URL(`${folder}/${filename}`, base));
  return JSON.parse(filename.endsWith('.gz') ? gunzipSync(data) : data);
}

function query(folder, id, geography, date, selections = {}) {
  const table = read(folder).tables.find(item => item.id === id);
  const territory = table.territories.findIndex(item => item.id === geography);
  const period = table.periods.findIndex(item => item.id === date);
  const dims = table.dimensions.map(d => selections[d.name] === undefined ? 0 : d.values.indexOf(selections[d.name]));
  assert.ok(territory >= 0 && period >= 0 && dims.every(i => i >= 0));
  const selection = {territory, period, dims, level: table.territories[territory].level};
  const data = read(folder, table.shards.find(shard => shard.id === 'main').file);
  const {series} = queryCube(table, data, selection);
  const result = series.find(item => item.period === period);
  assert.ok(result);
  return {table, selection, result, series, unit: unitFor(table, dims)};
}

test('F08 preserves IPC measures and the official October 2026 results', () => {
  const index = read('ine');
  assert.equal(index.tables[0].id, 76141);
  assert.equal(new Set(index.tables.map(t => t.id)).size, index.tables.length);
  const spain = query('ine', 76143, 'national:ES', '2026M10', {'Índices y Tasas':'Variación anual'});
  assert.equal(spain.result.value, 4.9);
  assert.equal(spain.result.status, 'Definitivo');
  const madrid = query('ine', 76141, 'province:28', '2026M10');
  assert.equal(madrid.result.value, 106.385);
  assert.equal(madrid.unit, 'Índice');
});

test('F08 preserves BdE geography, codes and series dimensions', () => {
  const madrid = query('bde', 250866080, 'province:28', '2026T2');
  assert.equal(madrid.result.value, 391_552_667);
  assert.equal(madrid.unit, 'Miles de euros');
  assert.equal(madrid.table.territories.filter(a => a.level === 'province').length, 52);
  assert.ok(madrid.table.territories.some(a => a.id === 'unlocated:banca electronica'));
  const metadata = selectedSeriesMetadata(madrid.table, madrid.selection);
  assert.ok(metadata.code.startsWith('D_'));
  const csv = seriesCsv(madrid.table, madrid.selection, madrid.series);
  assert.match(csv, /"codigo_serie";"publicador_original"/);
  assert.ok(csv.includes(metadata.code));
});

test('F08 keeps reporting scopes and units distinct in DataComex and DGOJ', () => {
  const trade = read('datacomex');
  assert.equal(trade.tables.length, 14);
  const annual = query('datacomex', 950090, 'national:ES', '2025');
  assert.equal(annual.result.value, 387091.6168667604);
  assert.equal(annual.result.status, 'Provisional');
  assert.equal(annual.unit, 'Millones de euros');
  const together = trade.tables.find(t => t.id === 950051);
  assert.equal(together.periods[0].id, '2026M08');
  assert.match(together.sourceTables[0].notes[0], /H=Acum\. 24, I=Acum\. 23/);
  const gambling = query('dgoj', 951002, 'national:ES', '2026M06');
  assert.equal(gambling.result.value, 554_785_249);
  assert.equal(gambling.unit, 'Euros');
  assert.equal(read('dgoj').tables.length, 4);
});
