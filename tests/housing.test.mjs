import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {gunzipSync} from 'node:zlib';
import {queryCube,seriesCsv,unitFor} from '../src/demography-data.ts';

const read = path => readFileSync(new URL('../' + path, import.meta.url));
const json = path => JSON.parse(read(path));
const root = 'datos/vivienda/';
const ine = json(root + 'ine/index.json');
const ministry = json(root + 'mivau/index.json');

function query(folder, table, level, code, period, dimensions) {
  const query = {
    level,
    territory: table.territories.findIndex(area => area.level === level && area.code === code),
    period: table.periods.findIndex(item => item.id === period),
    dims: table.dimensions.map(dimension => dimension.values.indexOf(dimensions[dimension.name]))
  };
  assert.ok(query.territory >= 0 && query.period >= 0 && query.dims.every(i => i >= 0));
  const part = level === 'municipal' || level === 'district' ? code.slice(0,2) : 'main';
  const shard = table.shards.find(item => item.id === part);
  const cube = JSON.parse(gunzipSync(read(root + folder + '/' + shard.file)));
  const result = queryCube(table,cube,query);
  return {value:result.values.find(item => item.area === query.territory)?.value,
    unit:unitFor(table,query.dims), csv:seriesCsv(table,query,result.series)};
}

test('F06 covers all inventoried housing INE tables and official SIU layers', () => {
  const inventory = json(root + 'ine/inventory.json');
  const {excluded} = json('registry/housing-tables.json');
  const expected = inventory.operations.flatMap(operation => operation.tables)
      .map(table => table.Id).filter(id => !Object.hasOwn(excluded,id));
  assert.deepEqual(new Set(ine.tables.map(table => table.id)),new Set(expected));
  assert.equal(ine.tables.reduce((n,t) => n+t.rows,0),3779166);
  assert.equal(ministry.tables.length,7);
  assert.equal(ministry.tables.reduce((n,t) => n+t.rawRows,0),717941);
  const siu = json(root + 'siu/layers.json');
  assert.equal(siu.layers.length,17);
  assert.equal(siu.unavailable.length,0);
  for (const layer of siu.layers) {
    assert.match(layer.verifiedMap,/REQUEST=GetMap/);
    assert.match(layer.verifiedInfo,/REQUEST=GetFeatureInfo/);
    assert.ok(layer.provider.queryable);
  }
});

test('F06 maps declared municipal rent and retains the published annual series in euros', () => {
  const table = ministry.tables.find(t => t.id === 940001);
  const {value,unit,csv} = query('mivau',table,'municipal','28079','2024',{
    'Indicador':'Cuantía mensual','Estadístico':'Mediana','Tipo de vivienda':'Colectiva'
  });
  assert.equal(value,868.8);
  assert.equal(unit,'€/mes');
  assert.match(csv,/VDP001_01\.csv/);
  assert.match(csv,/"2011"/);
});

test('F06 reproduces monthly transmission and revised census values with their official units', () => {
  const transmissions = ine.tables.find(t => t.id === 6146);
  assert.equal(query('ine',transmissions,'national','ES','2026M08',
    {'Tipo de dato':'Número','Naturaleza de la finca':'Total fincas'}).value,162007);
  const census = ine.tables.find(t => t.id === 59531);
  assert.equal(query('ine',census,'national','ES','2021',{'Consumo eléctrico':'Viviendas vacías'}).value,3828307);
  assert.equal(query('ine',census,'national','ES','2021',{'Consumo eléctrico':'Mediana consumo anual'}).unit,'kWh');
  assert.ok(census.territories.some(area => area.level === 'unlocated' && area.name.includes('Resto de Almería')));
  const building = ine.tables.find(t => t.id === 79851);
  assert.ok(building.territories.some(area => area.level === 'community'));
  assert.ok(building.territories.every(area => area.level !== 'section'));
});

test('F06 keeps conflicting rehabilitation figures out of the unambiguous series', () => {
  const table = ministry.tables.find(t => t.id === 940007);
  const selections = {'Indicador':'Viviendas','Tipo de actuación':'Protegida','Trámite':'Calificación','Estado de tramitación':'Provisional'};
  const lookup = name => query('mivau',table,'province','23','2009M04',{...selections,'Registro':name});
  assert.equal(lookup('Serie principal').value,null);
  assert.deepEqual(new Set([lookup('Coincidencia 1').value,lookup('Coincidencia 2').value]),new Set([2,80]));
});
