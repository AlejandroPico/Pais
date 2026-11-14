import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {gunzipSync} from 'node:zlib';
import {defaultDimensions,queryCube,seriesCsv} from '../src/demography-data.ts';

const root = new URL('../datos/trabajo/ine/', import.meta.url);
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

test('SEPE downloads preserve monthly values, suppressions and per-edition provenance', () => {
  const {tables}=JSON.parse(readFileSync(new URL('../datos/trabajo/sepe/sepe.json',import.meta.url),'utf8'));
  assert.equal(tables.length,3);
  for(const table of tables){
    assert.equal(table.publisher,'SEPE');
    assert.equal(table.periods[0].id,'2006M01');
    assert.equal(table.periods.at(-1).id,'2026M10');
    assert.equal(table.periods.length,table.id===900003?249:250);
    const part=table.shards.find(shard=>shard.id==='04');
    const cube=JSON.parse(gunzipSync(readFileSync(new URL('../datos/trabajo/sepe/'+part.file,import.meta.url))));
    const territory=table.territories.findIndex(area=>area.code==='04001');
    const period=table.periods.findIndex(entry=>entry.id==='2022M01');
    const query={level:'municipal',territory,period,dims:[0]};
    const {series}=queryCube(table,cube,query);
    assert.equal(series.find(entry=>entry.period===period).value,({900001:91,900002:25,900003:166})[table.id]);
    const protectedCell=queryCube(table,cube,{...query,dims:[1]}).series.find(entry=>entry.period===period);
    assert.equal(protectedCell.value,null);
    assert.equal(protectedCell.status,'<5');
    const exported=seriesCsv(table,query,series);
    assert.match(exported,/sede\.sepe\.gob\.es/);
    const december=series.find(entry=>table.periods[entry.period].id==='2020M12');
    if(table.id===900003){
      assert.equal(december,undefined);
    }else{
      assert.equal(december.value,table.id===900001?88:18);
      assert.match(exported,/www\.sepe\.es.*ESTADISTICA_MUNICIPIOS\.xls/);
    }
    if(table.id!==900003) assert.match(exported,/segundo_semestre_2013_xls\.xls/);
  }
});
