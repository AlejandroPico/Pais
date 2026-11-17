export type DemographicArea={id:string;level:string;code:string;name:string;provinceCode?:string;municipalityCode?:string;sourceTableIds?:number[];publicationTableId?:number};
export type SeriesMetadata={code:string;publisher?:string;description?:string;note?:string;frequency?:string;alias?:string};
export type DemographicTable={snapshotFile?:string;snapshotLabel?:string;seriesMetadata?:Record<string,Record<string,SeriesMetadata>>;id:number;compactColumns?:boolean;dataFolder?:string;partitionDimension?:string;publisher?:string;label:string;title:string;family:string;unit:string;unitsByConditions?:{when:Record<string,string>;unit:string}[];sourceTables?:{id:number;url:string;year?:number;notes?:string[]}[];unitsByCategory?:{dimension:string;values:Record<string,string>};note:string;sourceUrl:string;downloadUrl:string;license:string;rows:number;dimensions:{name:string;values:string[]}[];periods:{id:string;label:string}[];territories:DemographicArea[];shards:{id:string;file:string;rows:number;bytes:number;sha256:string;contentSha256:string}[];missingTokens:Record<string,number>};
export type DemographicIndex={revision:string;tables:DemographicTable[];inventoryTables:number;operations:number};
export type DemographicQuery={period:number;dims:number[];level:string;territory:number};
type Cells=(number|string|null)[];
export type Cube={rows:Cells[]}|{axes:number[];cells:Cells;flags?:Record<number,string>};
export function cubeSize(cube:Cube){return 'rows' in cube?cube.rows.length:cube.cells.length;}
export type DemographicResult={values:{area:number;value:number|null;status:string}[];domain:{area:number;period:number;value:number}[];series:{period:number;value:number|null;status:string;sourceTableId?:number}[];pyramid:{age:string;men:number|null;women:number|null}[]};
export const allProvinces = 'all';
export const detailedLevels = ['municipal','district','section'];
const spanishNames = new Intl.Collator('es', {sensitivity:'base',numeric:true});

export function territoryLabel(name:string){return name.replace(/^\d+\s+(?:[-–]\s*)?/, '');}
export function compareTerritoryNames(a:string,b:string){return spanishNames.compare(territoryLabel(a),territoryLabel(b));}

export function provinceCodesForLevel(table:DemographicTable,level:string){
  return new Set(table.territories.filter(a=>a.level===level&&a.provinceCode).map(a=>a.provinceCode!));
}

export function statisticalParts(table:DemographicTable,query:DemographicQuery,province:string){
  const dimension=table.dimensions.findIndex(d=>d.name===table.partitionDimension);
  const suffix=dimension<0?'':'-d'+query.dims[dimension];
  if(!detailedLevels.includes(query.level))return ['main'+suffix];
  if(province!==allProvinces)return [province+suffix];
  const codes=provinceCodesForLevel(table,query.level);
  return table.shards.map(shard=>shard.id).filter(id=>id.endsWith(suffix)&&codes.has(suffix?id.slice(0,-suffix.length):id));
}

export function appendCubeResult(target:DemographicResult,result:DemographicResult){
  for(const entry of result.domain)target.domain.push(entry);
  for(const entry of result.values)target.values.push(entry);
  for(const entry of result.series)target.series.push(entry);
  for(const entry of result.pyramid)target.pyramid.push(entry);
}

export function totalIndex(values:string[]){const i=values.findIndex(v=>/^(total|ambos sexos|todas las edades|todos|total nacional|dato base)$/i.test(v));return i<0?0:i;}
export function defaultDimensions(table:DemographicTable){return table.dimensions.map(d=>totalIndex(d.values));}
export function unitFor(table:DemographicTable,dims:number[]){const condition=table.unitsByConditions?.find(r=>Object.entries(r.when).every(([name,value])=>{const i=table.dimensions.findIndex(d=>d.name===name);return i>=0&&table.dimensions[i].values[dims[i]]===value;}));if(condition)return condition.unit;const rule=table.unitsByCategory,i=table.dimensions.findIndex(d=>d.name===rule?.dimension);return i>=0?rule!.values[table.dimensions[i].values[dims[i]]]||table.unit:table.unit;}
function queryGrid(table:DemographicTable,cube:Extract<Cube,{axes:number[]}>,q:DemographicQuery):DemographicResult{
  const strides=new Map<number,number>();
  const result:DemographicResult={values:[],domain:[],series:[],pyramid:[]};
  let size=1;
  for(const axis of [...cube.axes].reverse()){
    strides.set(axis,size);
    size*=axis===-2?table.territories.length:axis===-1?table.periods.length:table.dimensions[axis].values.length;
  }
  if(size!==cube.cells.length||!strides.has(-2)||!strides.has(-1))throw new Error('La cuadrícula tiene dimensiones incorrectas.');
  const selected=q.dims.reduce((offset,category,axis)=>offset+category*strides.get(axis)!,0);
  const areaStride=strides.get(-2)!,periodStride=strides.get(-1)!;
  const periods=periodOrder(table);
  for(const [area,territory] of table.territories.entries()){
    if(territory.level!==q.level&&area!==q.territory)continue;
    for(const period of periods){
      const index=selected+area*areaStride+period*periodStride;
      const cell=cube.cells[index];
      const value=typeof cell==='number'?cell:null;
      const status=cube.flags?.[index]||(typeof cell==='string'?cell:'');
      if(territory.level===q.level){
        if(period===q.period)result.values.push({area,value,status});
        if(value!==null)result.domain.push({area,period,value});
      }
      if(area===q.territory)result.series.push({period,value,status,sourceTableId:table.id});
    }
  }
  return result;
}
export function queryCube(table:DemographicTable,cube:Cube,q:DemographicQuery):DemographicResult{
  if('axes' in cube)return queryGrid(table,cube,q);
  const n=table.dimensions.length,vi=2+n,values:DemographicResult['values']=[],series:DemographicResult['series']=[],domain:DemographicResult['domain']=[];
  const age=table.dimensions.findIndex(d=>/^(edad|edad simple|grupo quinquenal de edad)$/i.test(d.name)),sex=table.dimensions.findIndex(d=>/^sexo$/i.test(d.name));
  const pyramid=new Map<number,{age:string;men:number|null;women:number|null}>();
  for(const row of cube.rows){
    if(table.compactColumns){
      const area=Number(row[0]),period=Number(row[1]),cell=row[3+q.dims[0]];
      const value=typeof cell==='number'?cell:null,status=typeof cell==='string'?cell:'';
      if(table.territories[area].level===q.level){
        if(period===q.period)values.push({area,value,status});
        if(value!==null)domain.push({area,period,value});
      }
      if(area===q.territory)series.push({period,value,status,sourceTableId:Number(row[2])});
      continue;
    }
    const area=Number(row[0]),period=Number(row[1]);let match=true,other=true;
    for(let i=0;i<n;i++)if(row[i+2]!==q.dims[i]){match=false;if(i!==age&&i!==sex)other=false;}
    const value=typeof row[vi]==='number'?row[vi] as number:null,status=String(row[vi+1]||'');
    if(match){if(table.territories[area].level===q.level){if(period===q.period)values.push({area,value,status});if(value!==null)domain.push({area,period,value});}if(area===q.territory)series.push({period,value,status,...(typeof row[vi+2]==='number'?{sourceTableId:row[vi+2] as number}:{})});}
    if(age>=0&&sex>=0&&other&&area===q.territory&&period===q.period){
      const a=Number(row[age+2]),s=table.dimensions[sex].values[Number(row[sex+2])];
      if(a!==totalIndex(table.dimensions[age].values)&&/^(hombres|mujeres)$/i.test(s)){
        const item=pyramid.get(a)||{age:table.dimensions[age].values[a],men:null,women:null};
        if(/^hombres$/i.test(s))item.men=value;else item.women=value;pyramid.set(a,item);
      }
    }
  }
  series.sort((a,b)=>table.periods[a.period].id.localeCompare(table.periods[b.period].id));
  return {values,domain,series,pyramid:[...pyramid.values()].sort((a,b)=>(Number(a.age.match(/\d+/)?.[0])||0)-(Number(b.age.match(/\d+/)?.[0])||0))};
}
export function periodOrder(table:DemographicTable){return table.periods.map((_,i)=>i).sort((a,b)=>table.periods[a].id.localeCompare(table.periods[b].id));}
export function periodTimestamp(id:string){
  const week=id.match(/^(\d{4})SM(\d{2})$/);
  if(week){
    const januaryFourth=new Date(Date.UTC(Number(week[1]),0,4));
    const daysToMonday=(januaryFourth.getUTCDay()+6)%7;
    return Date.UTC(Number(week[1]),0,4-daysToMonday+(Number(week[2])-1)*7);
  }
  const m=id.match(/^(\d{4})(?:-(\d{2})-(\d{2})|M(\d{2})|T([1-4])|R\d{2})?$/);
  if(!m)throw new Error('Periodo desconocido');
  return Date.UTC(Number(m[1]),m[2]?Number(m[2])-1:m[4]?Number(m[4])-1:m[5]?(Number(m[5])-1)*3:0,Number(m[3]||1));
}
export function relativeChange(value:number|null,baseline:number|undefined){return value!==null&&baseline!==undefined&&baseline>0?(value/baseline-1)*100:null;}
export function csvCell(value:unknown){return '"'+String(value??'').replace(/"/g,'""')+'"';}
export function selectedSeriesMetadata(table:DemographicTable,q:DemographicQuery){
  const dimension=table.dimensions.findIndex(d=>d.name==='Serie');
  if(!table.seriesMetadata||dimension<0)return undefined;
  const measure=table.dimensions[dimension].values[q.dims[dimension]];
  return table.seriesMetadata[measure]?.[table.territories[q.territory].id];
}
export function seriesCsv(table:DemographicTable,q:DemographicQuery,series:DemographicResult['series']){
  const a=table.territories[q.territory];
  const officialEdition=table.publisher&&table.publisher!=='INE';
  const hasEditionYear=officialEdition&&table.sourceTables?.some(source=>source.year!==undefined);
  const distributionId=table.dataFolder==='economia/cna'||table.dataFolder==='economia/dae-historica'?'identificador_atlas':'tabla_ine';
  const metadata=selectedSeriesMetadata(table,q);
  const heading=[officialEdition?(hasEditionYear?'año_edición':'distribución'):distributionId,'territorio','codigo','nivel','periodo',
    ...table.dimensions.map(d=>d.name),'valor','estado','unidad','fuente'];
  if(metadata)heading.push('codigo_serie','publicador_original');
  const units=unitFor(table,q.dims);
  const categories=table.dimensions.map((d,i)=>d.values[q.dims[i]]);
  const rows=series.map(r=>{
    const edition=table.sourceTables?.find(source=>source.id===r.sourceTableId);
    const id=hasEditionYear?edition?.year:r.sourceTableId||table.id;
    let url=edition?.url||table.sourceUrl;
    if(!officialEdition&&r.sourceTableId&&!edition) url='https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/'+r.sourceTableId+'?tip=AM';
    return [id,a.name,a.code,a.level,table.periods[r.period].label,...categories,r.value,r.status,units,url,
      ...(metadata?[metadata.code,metadata.publisher||table.publisher]:[])];
  });
  return '\uFEFF'+[heading,...rows].map(r=>r.map(csvCell).join(';')).join('\r\n');
}
