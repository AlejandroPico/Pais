export type DemographicArea={id:string;level:string;code:string;name:string;provinceCode?:string};
export type DemographicTable={id:number;label:string;title:string;family:string;unit:string;unitsByCategory?:{dimension:string;values:Record<string,string>};note:string;sourceUrl:string;downloadUrl:string;license:string;rows:number;dimensions:{name:string;values:string[]}[];periods:{id:string;label:string}[];territories:DemographicArea[];shards:{id:string;file:string;rows:number;bytes:number;sha256:string;contentSha256:string}[];missingTokens:Record<string,number>};
export type DemographicIndex={revision:string;tables:DemographicTable[];inventoryTables:number;operations:number};
export type DemographicQuery={period:number;dims:number[];level:string;territory:number};
export type Cube={rows:(number|string|null)[][]};
export type DemographicResult={values:{area:number;value:number|null;status:string}[];domain:{area:number;period:number;value:number}[];series:{period:number;value:number|null;status:string}[];pyramid:{age:string;men:number|null;women:number|null}[]};
export function totalIndex(values:string[]){const i=values.findIndex(v=>/^(total|ambos sexos|todas las edades|todos|total nacional)$/i.test(v));return i<0?0:i;}
export function defaultDimensions(table:DemographicTable){return table.dimensions.map(d=>totalIndex(d.values));}
export function unitFor(table:DemographicTable,dims:number[]){const rule=table.unitsByCategory,i=table.dimensions.findIndex(d=>d.name===rule?.dimension);return i>=0?rule!.values[table.dimensions[i].values[dims[i]]]||table.unit:table.unit;}
export function queryCube(table:DemographicTable,cube:Cube,q:DemographicQuery):DemographicResult{
  const n=table.dimensions.length,vi=2+n,values:DemographicResult['values']=[],series:DemographicResult['series']=[],domain:DemographicResult['domain']=[];
  const age=table.dimensions.findIndex(d=>/^edad$/i.test(d.name)),sex=table.dimensions.findIndex(d=>/^sexo$/i.test(d.name));
  const pyramid=new Map<number,{age:string;men:number|null;women:number|null}>();
  for(const row of cube.rows){
    const area=Number(row[0]),period=Number(row[1]);let match=true,other=true;
    for(let i=0;i<n;i++)if(row[i+2]!==q.dims[i]){match=false;if(i!==age&&i!==sex)other=false;}
    const value=typeof row[vi]==='number'?row[vi] as number:null,status=String(row[vi+1]||'');
    if(match){if(table.territories[area].level===q.level){if(period===q.period)values.push({area,value,status});if(value!==null)domain.push({area,period,value});}if(area===q.territory)series.push({period,value,status});}
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
export function relativeChange(value:number|null,baseline:number|undefined){return value!==null&&baseline!==undefined&&baseline>0?(value/baseline-1)*100:null;}
export function csvCell(value:unknown){return '"'+String(value??'').replace(/"/g,'""')+'"';}
export function seriesCsv(table:DemographicTable,q:DemographicQuery,series:DemographicResult['series']){
  const a=table.territories[q.territory];
  return '\uFEFF'+[['tabla_ine','territorio','codigo','nivel','periodo',...table.dimensions.map(d=>d.name),'valor','estado','unidad','fuente'],...series.map(r=>[table.id,a.name,a.code,a.level,table.periods[r.period].label,...table.dimensions.map((d,i)=>d.values[q.dims[i]]),r.value,r.status,unitFor(table,q.dims),table.sourceUrl])].map(r=>r.map(csvCell).join(';')).join('\r\n');
}
