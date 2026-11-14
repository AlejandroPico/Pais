"""Validate and package the source research; does not modify the application."""
import csv
import gzip
import hashlib
import json
import re
import unicodedata
import zipfile
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs'/'research'
DATA = ROOT / 'datos/catalogo/investigacion'
read=lambda name:json.loads((DATA/name).read_text(encoding='utf-8'))

def build():
    guide=read('fuentes-tematicas.json')
    national=read('publicadores-catalogo-nacional.json')
    ioe=read('operaciones-ioe-detalladas.json')
    audit=read('comprobacion-enlaces.json')
    checks={r['url']:r for r in audit['results']}
    for source in guide['sources']:
        source['landingPageCheck']=checks.get(source['url'])
        source['linkedPageChecks']=[checks[l['url']] for l in source.get('links',[]) if l['url'] in checks]
    (DATA/'fuentes-tematicas.json').write_text(json.dumps(guide,ensure_ascii=False,indent=2),encoding='utf-8')
    with gzip.open(DATA/'datasets-catalogo-nacional.csv.gz','rt',encoding='utf-8',newline='') as f:
        datasets=list(csv.DictReader(f,delimiter=';'))
    assert len(datasets)==national['datasetCount']==len({d['url_catalogo'] for d in datasets})
    assert len(datasets)==sum(p['datasets'] for p in national['publishers'])
    assert not ioe['detailErrors']
    assert len(ioe['operations'])==len({o['code'] for o in ioe['operations']})
    assert len(guide['sources'])==len({s['id'] for s in guide['sources']})
    assert not any(d['titulo'].lstrip().startswith(('=','+','-','@')) for d in datasets)
    sectors=defaultdict(list)
    for op in ioe['operations']:sectors[op['fields'].get('Sector o tema','Sin sector')].append(op)
    sector_dir=OUT/'sectores';sector_dir.mkdir(exist_ok=True)
    sector_index=[]
    for sector,ops in sorted(sectors.items()):
        slug=re.sub(r'[^a-z0-9]+','-',unicodedata.normalize('NFKD',sector).encode('ascii','ignore').decode().lower()).strip('-')
        filename=slug+'.md';sector_index.append((sector,len(ops),filename))
        lines=['# '+sector,'',f'{len(ops)} operaciones del IOE actual. Fuente: [Inventario estatal]({ioe["source"]}). Captura del 5 de noviembre de 2026.','', 'Las fichas describen operaciones y su acceso publicado; no acreditan que todos los datos sean abiertos, gratuitos o directamente cartografiables.','']
        for op in ops:
            lines.extend([f'## {op["code"]} · {op["title"]}','',f'- [Ficha oficial]({op["url"]})'])
            fields=op['fields']
            for key in ['Servicio responsable','Unidad ejecutora','Participación de otros organismos','Subsector o subtema','Nivel de desagregación','Ámbito territorial','Objetivo general','Variables de estudio','Variables de clasificación','Periodicidad de la difusión']:
                if fields.get(key):lines.append('- **'+key+':** '+fields[key])
            for key,label in [('enlaceDatos','Resultados'),('enlaceMetodologia','Metodología'),('enlaceInforme','Informe metodológico')]:
                if op['links'].get(key):lines.append('- ['+label+']('+op['links'][key]+')')
            lines.append('')
        (sector_dir/filename).write_text('\n'.join(lines),encoding='utf-8')
    failed=[r for r in audit['results'] if r['status']!=200]
    issue_lines=['# Accesos que requieren revisión','', 'Una fuente pública puede bloquear consultas automatizadas, exigir registro o fallar temporalmente. Se conserva el resultado de la prueba; no se ha rebajado la seguridad TLS ni se han saltado barreras. Un HTTP 200 tampoco valida licencia, descarga o contenido completo.','']
    for r in failed:
        related=[s['name'] for s in guide['sources'] if s['url']==r['url'] or any(l['url']==r['url'] for l in s.get('links',[]))]
        issue_lines.extend(['## '+(' / '.join(related) or r['url']),'',f'- [Puerta de entrada]({r["url"]})',f'- Respuesta observada: {r["status"] if r["status"] else "no se obtuvo respuesta verificable"}.','- Detalle técnico conservado en [comprobacion-enlaces.json](../../datos/catalogo/investigacion/comprobacion-enlaces.json).','- Estado de incorporación: pendiente de comprobar el acceso y los recursos concretos.',''])
    (OUT/'ACCESOS_PENDIENTES.md').write_text('\n'.join(issue_lines),encoding='utf-8')
    lines=['# Investigación de datos públicos de España','', '**Captura y revisión: 5 de noviembre de 2026.**','', 'Este trabajo amplía el proyecto desde unos ejemplos iniciales a un inventario sistemático de publicadores, operaciones, familias temáticas y vías de acceso. No modifica la interfaz ni incorpora todavía esas capas al mapa.','', '## Qué contiene','',f'- **{len(guide["sources"])} fichas editoriales de fuentes y servicios**, agrupadas en **{len(guide["groups"])} bloques** y con **{guide["familyMentions"]} menciones de familias**. Se repiten temas entre organismos y una institución puede tener varios servicios: no son recuentos de organismos ni conjuntos únicos.',f'- **{national["publisherCount"]} publicadores** del catálogo nacional federado, con nombre, identificador oficial, enlace de consulta y ejemplos de sus conjuntos.',f'- **{national["datasetCount"]:,} títulos de conjuntos**, únicos por URI, con su publicador y enlace al catálogo. El recuento coincide con la suma agregada del catálogo en esta captura.',f'- **{len(ioe["operations"])} operaciones estadísticas estatales**, con las fichas completas recuperadas y sin errores de lectura. Incluyen las variables, el responsable, la unidad ejecutora, la escala, la periodicidad y los enlaces publicados.',f'- **{len(sectors)} sectores oficiales** para recorrer las operaciones. Las fichas se agrupan también por **147 combinaciones de servicio responsable y unidad ejecutora**.',f'- **{audit["checked"]} puertas de entrada comprobadas por HTTP**: {audit["successful"]} respondieron 200; las restantes {len(failed)} quedan registradas, sin equiparar bloqueos, errores de certificado o timeout con inexistencia del organismo.','', '## Empieza aquí','', '1. [Guía extensa de organismos, servicios y familias de datos](GUIA_DE_FUENTES.md): lista de sublistas para decidir qué incorporar.', '2. [Publicadores del catálogo nacional](PUBLICADORES_NACIONALES.md): todos los publicadores obtenidos, con muestras de lo que ofrecen.', '3. [IOE por entidad responsable](IOE_POR_ENTIDAD.md): fichas de operaciones agrupadas por organismo y unidad ejecutora. Por su tamaño, puede ser más cómodo abrir las versiones por sector de abajo.', '4. [IOE por tema](IOE_POR_TEMA.md): índice de operaciones y escala territorial.', '5. [Accesos pendientes de revisión](ACCESOS_PENDIENTES.md): incidencias de acceso, sin ocultarlas.','', '## Fichas completas por sector','']
    lines.extend(f'- [{sector} · {count} operaciones](sectores/{filename})' for sector,count,filename in sector_index)
    lines.extend(['','## Archivos reutilizables','', '- [Fuentes temáticas, JSON](../../datos/catalogo/investigacion/fuentes-tematicas.json) y [CSV](../../datos/catalogo/investigacion/fuentes-tematicas.csv).', '- [Publicadores nacionales, JSON](../../datos/catalogo/investigacion/publicadores-catalogo-nacional.json).', '- [Catálogo completo de títulos, CSV comprimido](../../datos/catalogo/investigacion/datasets-catalogo-nacional.csv.gz). El paquete ZIP de entrega contiene el CSV ya descomprimido.', '- [Operaciones con variables y responsables, JSON](../../datos/catalogo/investigacion/operaciones-ioe-detalladas.json) y [CSV](../../datos/catalogo/investigacion/operaciones-ioe-detalladas.csv).', '- [Resultado de la comprobación HTTP](../../datos/catalogo/investigacion/comprobacion-enlaces.json).','', '## Cómo se obtuvo','', '- [API de datos.gob.es](https://datos.gob.es/es/accessible-apidata) y [punto SPARQL](https://datos.gob.es/es/sparql): consulta agregada de publicadores; extracción ordenada de identificador, publicador y título español o sin idioma, en páginas de 5.000 registros; deduplicación por URI.', '- [Listado actual del IOE](https://www.ine.es/dyngs/IOE/listadoIoeActualAvan.htm?opc=todas): lista de operaciones y lectura de sus fichas con un máximo de cuatro peticiones simultáneas. Se conservan los textos metodológicos y los enlaces originales.', '- Investigación editorial de portales oficiales, directorios geográficos, fuentes autonómicas, locales y europeas. No se han enviado solicitudes de transparencia ni contactado con entidades.', '- Comprobación HTTP de puertas de entrada y corrección de direcciones obsoletas encontradas. Se conservan las limitaciones pendientes.','', '## Interpretación de los recuentos','', 'Un **publicador** es una entrada del catálogo; un **conjunto** puede ser un registro federado con múltiples distribuciones; una **operación** puede generar miles de tablas y series; una **familia temática** es una agrupación editorial. No se suman entre sí ni se consideran capas ya implementadas.', '', 'El IOE no es la API INEbase: aquí aparecen operaciones de ministerios, Banco de España y CGPJ. Las 166 operaciones y 6.913 tablas de la primera versión del mapa eran un inventario distinto y más limitado.', '', '## Alcance y límites','', '- El catálogo federado no es el universo completo de toda la información oficial española. Existen portales y recursos no federados; la guía incluye rutas para seguir ampliándolo.', '- Los títulos y metadatos no son una descarga de todas las observaciones ni de todos los ficheros; muchos conjuntos solo enlazan a un visor o a una página de publicación.', '- Una fuente oficial no implica que todos sus datos sean abiertos, gratuitos, redistribuibles o accesibles sin registro. Verificar licencia y acceso por recurso antes de integrarlo.', '- No se afirma haber validado cada una de las miles de combinaciones de formato, año, variable, geografía y licencia. La revisión de puerta de entrada está separada de la validación de un conector.', '- Las fichas territoriales, las series recientes, las series históricas y las publicaciones descontinuadas deben distinguirse; los cambios de límites y metodología no se ocultan.', '- Los datos de organismos privados regulados se encuentran en un apartado complementario y no se presentan como entidades oficiales.', '- Los recuentos del catálogo pueden variar después de la captura.','', '## Próximo paso concreto','', 'Seleccionar recursos del inventario, no inventar una lista a partir de ejemplos. Para cada candidato: comprobar descarga y licencia; registrar variables, periodo y unidad territorial; probar una muestra; definir su representación; y después incorporarlo con fecha y procedencia.', '', 'Para actualización reproducible: ejecutar research_collect.py (catálogo), research_collect.py --details (fichas IOE), research_guide.py, research_check_links.py y research_package.py. Los originales de la captura están en la caché local ignorada por Git; los metadatos normalizados y el resultado de la investigación están versionados. `--refresh` vuelve a consultar las fuentes en el recopilador.'])
    (OUT/'README.md').write_text('\n'.join(lines),encoding='utf-8')
    for p in OUT.rglob('*.md'):
        p.write_text('\n'.join(line.rstrip() for line in p.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8')
    files = sorted(p for directory in (OUT, DATA) for p in directory.rglob('*') if p.is_file())
    manifest_path = DATA / 'manifest.json'
    manifest = {p.relative_to(ROOT).as_posix(): {'bytes': p.stat().st_size,
                'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in files if p != manifest_path}
    manifest_path.write_text(json.dumps({'date':'2026-11-05','files':manifest},ensure_ascii=False,indent=2),encoding='utf-8')
    archive=ROOT.parent/'El-pais-investigacion-datos-publicos-2026-11-05.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=7) as z:
        for p in sorted(set([*files, manifest_path])):
            z.write(p,p.relative_to(ROOT))
        z.writestr('catalogo-completo-116236-conjuntos.csv',
                   b'\xef\xbb\xbf'+gzip.decompress((DATA/'datasets-catalogo-nacional.csv.gz').read_bytes()))
    print('Integrity checks passed; research package:',archive,'bytes:',archive.stat().st_size)

if __name__=='__main__':build()
