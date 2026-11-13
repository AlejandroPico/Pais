import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {gunzipSync} from 'node:zlib';
import {defaultDimensions,queryCube,seriesCsv} from '../src/demography-data.ts';

const root = new URL('../public/data/labor/', import.meta.url);
const index = JSON.parse(readFileSync(new URL('index.json', root), 'utf8'));

function checkObservation(id, periodId, indicator, expected) {
  const table = index.tables.find(table => table.id === id);
  const dims = defaultDimensions(table);
  if (indicator) {
    const axis = table.dimensions.findIndex(dim => dim.values.includes(indicator));
    assert.ok(axis >= 0, indicator);
    dims[axis] = table.dimensions[axis].values.indexOf(indicator);
  }
  const query = {
    level: 'national',
    territory: table.territories.findIndex(area => area.id === 'national:ES'),
    period: table.periods.findIndex(period => period.id === periodId),
    dims,
  };
  assert.ok(query.period >= 0);
  const cube = JSON.parse(gunzipSync(readFileSync(new URL(table.shards[0].file, root))));
  const {series} = queryCube(table, cube, query);
  assert.equal(series.find(row => row.period === query.period).value, expected);
  assert.match(seriesCsv(table, query, series), new RegExp('DATOS_TABLA/' + id));
}

test('labor queries retain official quarterly EPA and ETCL observations and annual salary units', () => {
  checkObservation(65334, '2026T3', null, 10.18);
  checkObservation(65345, '2026T3', 'Ocupados', 22852.6);
  checkObservation(28191, '2024', 'Media', 29540.26);
  checkObservation(79662, '2026T2', 'Coste laboral total', 3388.15);
});
