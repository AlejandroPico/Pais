import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {gunzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';
import {defaultDimensions,queryCube,seriesCsv,unitFor} from '../src/demography-data.ts';

const read = path => readFileSync(new URL('../' + path, import.meta.url));
const json = path => JSON.parse(read(path));
const base = 'datos/cuidados/imserso/';
const imserso = json(base + 'index.json');

function lookup(id, level, code, period, indicator) {
  const table = imserso.tables.find(item => item.id === id);
  const cube = JSON.parse(gunzipSync(read(base + table.shards[0].file)));
  const query = {
    level,
    territory: table.territories.findIndex(area => area.level === level && area.code === code),
    period: table.periods.findIndex(item => item.id === period),
    dims: [table.dimensions[0].values.indexOf(indicator)]
  };
  assert.ok(query.territory >= 0 && query.period >= 0 && query.dims[0] >= 0);
  const result = queryCube(table, cube, query);
  return {table,query,result,value:result.values.find(item => item.area === query.territory)?.value};
}

test('F05 covers all INE tables from operation 215 plus all five PNC annexes', () => {
  const ine = json('datos/cuidados/ine/index.json');
  const inventory = json('datos/cuidados/ine/inventory.json');
  const available = json('registry/care-products.json').available;
  assert.deepEqual(new Set(ine.tables.map(item => item.id)), new Set(inventory.operations[0].tables.map(item => item.Id)));
  assert.equal(ine.tables.reduce((sum, item) => sum + item.rows, 0), 238792);
  assert.equal(available.length, 101);
  assert.equal(imserso.edition, '2026M10');
  for (const table of imserso.tables) {
    const source = table.sourceTables[0];
    assert.equal(createHash('sha256').update(read(base + source.originalFile)).digest('hex'), source.sha256);
    const decompressed = gunzipSync(read(base + table.shards[0].file));
    assert.equal(createHash('sha256').update(decompressed).digest('hex'), table.shards[0].contentSha256);
    assert.equal(JSON.parse(decompressed).rows.length, table.rows);
  }
});

test('F05 uses published PNC geography, units, periods, states and official CSV links', () => {
  const month = '2026M10';
  const count = 'Total · Número de pensiones';
  assert.equal(lookup(930002, 'province', '04', month, count).value, 6525);
  assert.equal(lookup(930003, 'community', '01', month, count).value, 95555);
  assert.equal(lookup(930002, 'national', '00', month, count).value, 469763);
  const monthly = lookup(930002, 'national', '00', month, 'Total · Importe bruto');
  const cumulative = lookup(930004, 'national', '00', month, 'Total · Importe bruto acumulado');
  assert.equal(monthly.value, 305915097.76);
  assert.equal(cumulative.value, 3330633594.41);
  assert.equal(unitFor(cumulative.table, cumulative.query.dims), '€');
  assert.match(cumulative.table.periods[cumulative.query.period].label, /enero a octubre/);
  assert.ok(seriesCsv(monthly.table, monthly.query, monthly.result.series).includes('teleformacion.imserso.es'));
  const historical = lookup(930005, 'national', '00', '2019', 'Jubilación · Variación interanual publicada');
  assert.equal(historical.value, null);
  assert.equal(historical.result.series[0].status, '0,10%+3,00%');
});

test('F05 preserves every IMV payroll edition and its published coverage notes', () => {
  const folder = 'datos/cuidados/seguridad-social/';
  const {tables:[table]} = json(folder + 'index.json');
  const cube = JSON.parse(gunzipSync(read(folder + table.shards[0].file)));
  assert.equal(table.sourceTables.length, 34);
  assert.equal(cube.rows.length, 66096);
  assert.equal(table.periods[0].id, '2024M01');
  assert.equal(table.periods.at(-1).id, '2026M10');
  assert.equal(new Set(table.territories.map(a => a.id)).size, 72);
  for (const source of table.sourceTables) {
    assert.equal(createHash('sha256').update(read(folder + source.originalFile)).digest('hex'), source.sha256);
  }
  const lookup = (period, indicator, code = '00', level = 'national') => {
    const query = {
      level,
      territory: table.territories.findIndex(area => area.level === level && area.code === code),
      period: table.periods.findIndex(item => item.id === period),
      dims: [table.dimensions[0].values.indexOf(indicator)]
    };
    const result = queryCube(table, cube, query);
    assert.ok(seriesCsv(table, query, result.series).includes('seg-social.es'));
    return result.values.find(row => row.area === query.territory).value;
  };
  assert.equal(lookup('2026M10', 'Número de prestaciones'), 911274);
  assert.equal(lookup('2026M10', 'Número de beneficiarios'), 2781679);
  assert.equal(lookup('2026M10', 'Número de beneficiarios', '04', 'province'), 83428);
  assert.equal(lookup('2024M07', 'Número de prestaciones'), 639968);
  assert.ok(table.sourceTables.find(source => source.edition === '2024M07').originalFile.endsWith('.pdf'));
  assert.ok(table.sourceTables.at(-1).notes.some(note => note.includes('Catalunya')));
});

test('F05 reproduces the official national INE figures for 2025', () => {
  const root = 'datos/cuidados/ine/';
  const {tables} = json(root + 'index.json');
  for (const [id, expected] of [[28217,33373],[28195,9513]]) {
    const table = tables.find(item => item.id === id);
    const part = table.shards.find(item => item.file.endsWith('-main.json.gz'));
    const cube = JSON.parse(gunzipSync(read(root + part.file)));
    const query = {
      territory: table.territories.findIndex(area => area.level === 'national'),
      level: 'national',
      period: table.periods.findIndex(period => period.id === '2025'),
      dims: defaultDimensions(table)
    };
    const match = queryCube(table, cube, query).values.find(item => item.area === query.territory);
    assert.equal(match.value, expected);
    assert.equal(match.status, 'Definitivo');
  }
});
