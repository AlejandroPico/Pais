import {normalize} from './data.ts';

export type RegistryProduct = {
  id:string; title:string; sourceId:string; categoryIds:string[]; suggestedCategoryIds?:string[];
  status:string; url:string; coverage?:string; period?:string|{from?:string;to?:string};
  license:string|null; notes?:string; unit?:string; mapAction?:string;
  fields?:Record<string,string>; links?:Record<string,string>; responsible?:string;
  review?:{reason:string;updatedAt:string;nextAction?:string};
};
export type RegistrySource = {
  id:string;name:string;url:string;kind:string;group?:string;families:string[];notes:string;
  coverage?:string;access?:string;license?:string|null;candidateCategories:string[];datasetCount?:number;
};
export type RegistryIndex = {
  schemaVersion:number;researchSnapshot:string;revision:string;scope:string;
  categories:{id:string;name:string}[];sources:RegistrySource[];statusLabels:Record<string,string>;
  files:Record<string,{file:string;count:number;bytes:number;sha256:string;contentSha256:string}>;
  categoryCoverage:{categoryId:string;available:number;ioeCandidates:number;status:string}[];
};
export type ProductQuery = {kind:string;q:string;category:string;source:string;status:string;page:number};
export function matchesProduct(p:RegistryProduct, query:ProductQuery) {
  if(query.status&&p.status!==query.status)return false;
  if(query.source&&p.sourceId!==query.source)return false;
  if(query.category&&!p.categoryIds.includes(query.category)&&!p.suggestedCategoryIds?.includes(query.category))return false;
  const terms=normalize(query.q.trim()).split(/\s+/).filter(Boolean);
  if(!terms.length)return true;
  const text=normalize([p.id,p.title,p.responsible,p.coverage,...Object.values(p.fields||{})].join(' '));
  return terms.every(t=>text.includes(t));
}
