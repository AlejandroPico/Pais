# Fuentes y condiciones de integración

La lista siguiente describe la primera versión del atlas. Para el inventario ampliado de organismos y conjuntos, consultar la [investigación de fuentes públicas](research/README.md) y su [guía de 182 fuentes y servicios](research/GUIA_DE_FUENTES.md).

Inventario inicial verificado el 5 de noviembre de 2026. Las fechas de los datos son independientes de la consulta del catálogo.

| Organismo | Recursos | Estado inicial y acceso |
| --- | --- | --- |
| [INE](https://www.ine.es/datosabiertos/) | Demografía, sociedad, economía, vivienda, agricultura, empresas y muchas otras operaciones | API JSON inventariada: 166 operaciones, 6.913 tablas únicas. Padrón 2852/2853 descargado. CC BY 4.0. El inventario no es una descarga de todas las observaciones. |
| [IGN / CNIG / IDEE](https://www.ign.es/web/ide-area-nodo-ide-ign) | Límites, relieve, PNOA, callejero, hidrografía, ferrocarriles, carreteras, caminos | Límites descargados por WFS INSPIRE; otras capas por servicios raster/TMS/WMTS/WMS. Atribuir IGN y colaboradores; CC BY 4.0 según servicio. |
| [Mapzen / AWS Terrain Tiles](https://registry.opendata.aws/terrain-tiles/) | Elevación Terrarium global | Integrado para elevación 3D. No confundir con el MDT de máxima resolución del IGN. [Atribuciones de origen](https://github.com/tilezen/joerd/blob/master/docs/attribution.md). |
| [MITECO](https://www.miteco.gob.es/es/cartografia-y-sig/ide/directorio_datos_servicios.html) | Agua, bosques, biodiversidad, protección del territorio, costas y medio marino | Directorio identificado; pendiente de adaptar. Validar versión, licencia y escala por conjunto. [Biodiversidad y bosques](https://www.miteco.gob.es/es/cartografia-y-sig/ide/directorio_datos_servicios/biodiversidad.html). |
| [AEMET OpenData](https://opendata.aemet.es/centrodedescargas/inicio) | Observaciones, predicciones, climatología y avisos | Pendiente. API gratuita que requiere clave. Ingesta fuera del navegador; no publicar secretos. No confundir tiempo previsto con clima histórico. |
| [Interior · Infoelectoral](https://infoelectoral.interior.gob.es/es/elecciones-celebradas/area-de-descargas/) | Resultados y participación por proceso electoral | Pendiente. Adaptar ficheros de cada elección y códigos territoriales; distinguir escrutinio provisional y definitivo. |
| [Catastro](https://www.catastro.hacienda.gob.es/es-ES/wms.html) | Parcelas y cartografía catastral | Pendiente. WMS de consulta gratuito, con limitación a descargas masivas. Cobertura foral y precios de mercado requieren otras fuentes. |
| [IGME](https://info.igme.es/) | Geología e hidrogeología | Fuente identificada, pendiente de seleccionar productos y verificar condiciones específicas. |
| [MIVAU](https://www.mivau.gob.es/) | Vivienda, alquiler y suelo | Fuente identificada, pendiente de seleccionar series, cobertura y acceso. |
| [datos.gob.es](https://datos.gob.es/es/catalogo) | Descubrimiento transversal de conjuntos públicos | Catálogo de descubrimiento; acudir al publicador original para calidad, vigencia y licencia. |
| [IDEE y servicios autonómicos](https://www.idee.es/segun-tema-inspire) | Comarcas, cartografía e información regional | Pendiente. No existe una malla comarcal administrativa homogénea: conservar organismo, tipología, cobertura y periodo de vigencia. [Contexto territorial del IGN](https://educativo.ign.es/atlas-didactico/organizacion-territorial-eso/estructuracin_interna.html). |

## Endpoints actualmente consumidos

- INE: `https://servicios.ine.es/wstempus/js/ES/OPERACIONES_DISPONIBLES`, `TABLAS_OPERACION/{id}` y `DATOS_TABLA/{id}?tip=AM`.
- Límites: `https://www.ign.es/wfs-inspire/unidades-administrativas` con filtro explícito `2ndOrder` y `3rdOrder`; respuesta GML EPSG:4258, eje latitud-longitud convertido a GeoJSON longitud-latitud.
- Relieve: `https://tms-relieve.idee.es/1.0.0/relieve/{z}/{x}/{-y}.jpeg`, esquema TMS.
- Ortofoto: `https://www.ign.es/wmts/pnoa-ma`, capa `OI.OrthoimageCoverage`, matriz `GoogleMapsCompatible`.
- Callejero: `https://www.ign.es/wmts/ign-base`, capa `IGNBaseTodo`.
- Elevación: `https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png`.
- Hidrografía: `https://servicios.idee.es/wms-inspire/hidrografia`.
- Redes: `https://servicios.idee.es/wms-inspire/transportes`.
- Rutas: `https://www.ign.es/wms-inspire/camino-santiago`.
- Municipios: `https://www.ign.es/wms-inspire/unidades-administrativas`, estilo `municipios-gris` de `AU.AdministrativeUnit`.

Los límites simplificados y los datos transformados conservan sus fuentes y atribuciones. Las geometrías de frontera pueden incluir particularidades territoriales, enclaves y dominios sin asignación provincial que no deben eliminarse para cuadrar un recuento estadístico.
