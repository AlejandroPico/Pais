import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {gunzipSync} from 'node:zlib';
import {allProvinces, queryCube, seriesCsv, statisticalParts, unitFor} from '../src/demography-data.ts';

const ROOT = new URL('../datos/hacienda/', import.meta.url);
function read(folder, file = 'index.json') {
  const raw = readFileSync(new URL(`${folder}/${file}`, ROOT));
  return JSON.parse(file.endsWith('.gz') ? gunzipSync(raw) : raw);
}

function select(folder, id, place, date, measure) {
  const table = read(folder).tables.find(t => t.id === id);
  const territory = table.territories.findIndex(a => a.id === place);
  const period = table.periods.findIndex(p => p.id === date);
  const dims = [measure === undefined ? 0 : table.dimensions[0].values.indexOf(measure)];
  assert.ok(period >= 0 && territory >= 0 && dims[0] >= 0);
  const {level, provinceCode} = table.territories[territory];
  const selection = {territory, period, dims, level};
  const shard = table.shards.find(s => s.id === (provinceCode ?? 'main'));
  const {series} = queryCube(table, read(folder, shard.file), selection);
  const result = series.find(s => s.period === period);
  assert.ok(result);
  return {table, selection, series, result, unit: unitFor(table, dims)};
}

test('municipal debt preserves all 18 editions, geographic parts and per-edition provenance', () => {
  const madrid = select('deuda-local', 961001, 'municipal:28079', '2025');
  assert.equal(madrid.series.length, 18);
  assert.equal(madrid.result.value, 1_560_729.60704);
  assert.equal(madrid.unit, 'Miles de euros');
  assert.equal(statisticalParts(madrid.table, madrid.selection, allProvinces).length, 52);
  assert.match(seriesCsv(madrid.table, madrid.selection, madrid.series), /deuda-viva-ayuntamientos-202512\.xlsx/);
  const abla = select('deuda-local', 961001, 'municipal:04001', '2008', 'Población publicada con la edición de 2008');
  assert.equal(abla.result.value, 1503);
  assert.equal(abla.unit, 'Personas');
});

test('IGAE percentages agree with the SEC B.9 balance and the published GDP denominator', () => {
  const label = 'Empleos · B.9 · CAPACIDAD (+) O NECESIDAD (-) DE FINANCIACIÓN';
  const amount = select('igae',963091,'community:01','2025',label);
  const ratio = select('igae',963092,'community:01','2025',label);
  const reference = select('igae',963092,'community:01','2025','PIB utilizado');
  assert.equal(amount.result.value,358);
  assert.equal(ratio.result.status,'Provisional');
  assert.equal(ratio.result.value,100*amount.result.value/reference.result.value);
  assert.equal(ratio.unit,'Porcentaje del PIB');
  assert.equal(reference.unit,'Millones de euros');
});

test('CONPREL, AEAT and BdE preserve fiscal phase, currency scale and territorial meaning', () => {
  const abla = select('conprel',965010,'municipal:04001','2026','Previsión Inicial · Impuestos directos');
  assert.equal(abla.result.value,537_500);
  assert.equal(abla.result.status,'Avance · C');
  assert.equal(abla.unit,'Euros');
  const debt = select('bde',795061593,'community:13','2026T2');
  assert.equal(debt.result.value,42_296_265);
  assert.equal(debt.unit,'Miles de euros');
  const tax = select('aeat',964001,'national:ES','2026M09');
  assert.equal(tax.result.value,18_048_952);
  assert.ok(tax.table.territories.some(a=>a.id==='unlocated:servicios centrales'));
});
