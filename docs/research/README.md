# Investigación de datos públicos de España

**Captura y revisión: 5 de noviembre de 2026.**

Este trabajo amplía el proyecto desde unos ejemplos iniciales a un inventario sistemático de publicadores, operaciones, familias temáticas y vías de acceso. No modifica la interfaz ni incorpora todavía esas capas al mapa.

## Qué contiene

- **182 fichas editoriales de fuentes y servicios**, agrupadas en **22 bloques** y con **1953 menciones de familias**. Se repiten temas entre organismos y una institución puede tener varios servicios: no son recuentos de organismos ni conjuntos únicos.
- **238 publicadores** del catálogo nacional federado, con nombre, identificador oficial, enlace de consulta y ejemplos de sus conjuntos.
- **116,236 títulos de conjuntos**, únicos por URI, con su publicador y enlace al catálogo. El recuento coincide con la suma agregada del catálogo en esta captura.
- **758 operaciones estadísticas estatales**, con las fichas completas recuperadas y sin errores de lectura. Incluyen las variables, el responsable, la unidad ejecutora, la escala, la periodicidad y los enlaces publicados.
- **27 sectores oficiales** para recorrer las operaciones. Las fichas se agrupan también por **147 combinaciones de servicio responsable y unidad ejecutora**.
- **216 puertas de entrada comprobadas por HTTP**: 195 respondieron 200; las restantes 21 quedan registradas, sin equiparar bloqueos, errores de certificado o timeout con inexistencia del organismo.

## Empieza aquí

1. [Guía extensa de organismos, servicios y familias de datos](GUIA_DE_FUENTES.md): lista de sublistas para decidir qué incorporar.
2. [Publicadores del catálogo nacional](PUBLICADORES_NACIONALES.md): todos los publicadores obtenidos, con muestras de lo que ofrecen.
3. [IOE por entidad responsable](IOE_POR_ENTIDAD.md): fichas de operaciones agrupadas por organismo y unidad ejecutora. Por su tamaño, puede ser más cómodo abrir las versiones por sector de abajo.
4. [IOE por tema](IOE_POR_TEMA.md): índice de operaciones y escala territorial.
5. [Accesos pendientes de revisión](ACCESOS_PENDIENTES.md): incidencias de acceso, sin ocultarlas.

## Fichas completas por sector

- [Administraciones públicas y asociaciones · 81 operaciones](sectores/administraciones-publicas-y-asociaciones.md)
- [Agricultura, ganadería, selvicultura y caza · 43 operaciones](sectores/agricultura-ganaderia-selvicultura-y-caza.md)
- [Comercio interior y exterior · 20 operaciones](sectores/comercio-interior-y-exterior.md)
- [Construcción y vivienda · 15 operaciones](sectores/construccion-y-vivienda.md)
- [Cuentas económicas · 52 operaciones](sectores/cuentas-economicas.md)
- [Cultura, deporte y ocio · 43 operaciones](sectores/cultura-deporte-y-ocio.md)
- [Demografía y población · 35 operaciones](sectores/demografia-y-poblacion.md)
- [Educación y formación · 43 operaciones](sectores/educacion-y-formacion.md)
- [Estadísticas de empresas y unidades de producción no referidas a sectores particulares · 23 operaciones](sectores/estadisticas-de-empresas-y-unidades-de-produccion-no-referidas-a-sectores-particulares.md)
- [Estadísticas no desglosables por sector o tema · 18 operaciones](sectores/estadisticas-no-desglosables-por-sector-o-tema.md)
- [Extracción de productos energéticos y energía en general · 21 operaciones](sectores/extraccion-de-productos-energeticos-y-energia-en-general.md)
- [Financieras y seguros · 8 operaciones](sectores/financieras-y-seguros.md)
- [Hostelería y turismo · 17 operaciones](sectores/hosteleria-y-turismo.md)
- [Investigación científica y desarrollo tecnológico · 12 operaciones](sectores/investigacion-cientifica-y-desarrollo-tecnologico.md)
- [Medio ambiente y desarrollo sostenible · 35 operaciones](sectores/medio-ambiente-y-desarrollo-sostenible.md)
- [Mercado laboral y salarios · 43 operaciones](sectores/mercado-laboral-y-salarios.md)
- [Minería e industria · 18 operaciones](sectores/mineria-e-industria.md)
- [Nivel, calidad y condiciones de vida · 48 operaciones](sectores/nivel-calidad-y-condiciones-de-vida.md)
- [Normalización y metodología general · 5 operaciones](sectores/normalizacion-y-metodologia-general.md)
- [Pesca y acuicultura · 7 operaciones](sectores/pesca-y-acuicultura.md)
- [Precios · 31 operaciones](sectores/precios.md)
- [Protección social y servicios sociales · 26 operaciones](sectores/proteccion-social-y-servicios-sociales.md)
- [Salud · 42 operaciones](sectores/salud.md)
- [Seguridad y justicia · 41 operaciones](sectores/seguridad-y-justicia.md)
- [Servicios (estadísticas generales) · 4 operaciones](sectores/servicios-estadisticas-generales.md)
- [Tecnologías de la información y las comunicaciones (TIC) · 7 operaciones](sectores/tecnologias-de-la-informacion-y-las-comunicaciones-tic.md)
- [Transporte y actividades conexas · 20 operaciones](sectores/transporte-y-actividades-conexas.md)

## Archivos reutilizables

- [Fuentes temáticas, JSON](fuentes-tematicas.json) y [CSV](fuentes-tematicas.csv).
- [Publicadores nacionales, JSON](publicadores-catalogo-nacional.json).
- [Catálogo completo de títulos, CSV comprimido](datasets-catalogo-nacional.csv.gz). El paquete ZIP de entrega contiene el CSV ya descomprimido.
- [Operaciones con variables y responsables, JSON](operaciones-ioe-detalladas.json) y [CSV](operaciones-ioe-detalladas.csv).
- [Resultado de la comprobación HTTP](comprobacion-enlaces.json).

## Cómo se obtuvo

- [API de datos.gob.es](https://datos.gob.es/es/accessible-apidata) y [punto SPARQL](https://datos.gob.es/es/sparql): consulta agregada de publicadores; extracción ordenada de identificador, publicador y título español o sin idioma, en páginas de 5.000 registros; deduplicación por URI.
- [Listado actual del IOE](https://www.ine.es/dyngs/IOE/listadoIoeActualAvan.htm?opc=todas): lista de operaciones y lectura de sus fichas con un máximo de cuatro peticiones simultáneas. Se conservan los textos metodológicos y los enlaces originales.
- Investigación editorial de portales oficiales, directorios geográficos, fuentes autonómicas, locales y europeas. No se han enviado solicitudes de transparencia ni contactado con entidades.
- Comprobación HTTP de puertas de entrada y corrección de direcciones obsoletas encontradas. Se conservan las limitaciones pendientes.

## Interpretación de los recuentos

Un **publicador** es una entrada del catálogo; un **conjunto** puede ser un registro federado con múltiples distribuciones; una **operación** puede generar miles de tablas y series; una **familia temática** es una agrupación editorial. No se suman entre sí ni se consideran capas ya implementadas.

El IOE no es la API INEbase: aquí aparecen operaciones de ministerios, Banco de España y CGPJ. Las 166 operaciones y 6.913 tablas de la primera versión del mapa eran un inventario distinto y más limitado.

## Alcance y límites

- El catálogo federado no es el universo completo de toda la información oficial española. Existen portales y recursos no federados; la guía incluye rutas para seguir ampliándolo.
- Los títulos y metadatos no son una descarga de todas las observaciones ni de todos los ficheros; muchos conjuntos solo enlazan a un visor o a una página de publicación.
- Una fuente oficial no implica que todos sus datos sean abiertos, gratuitos, redistribuibles o accesibles sin registro. Verificar licencia y acceso por recurso antes de integrarlo.
- No se afirma haber validado cada una de las miles de combinaciones de formato, año, variable, geografía y licencia. La revisión de puerta de entrada está separada de la validación de un conector.
- Las fichas territoriales, las series recientes, las series históricas y las publicaciones descontinuadas deben distinguirse; los cambios de límites y metodología no se ocultan.
- Los datos de organismos privados regulados se encuentran en un apartado complementario y no se presentan como entidades oficiales.
- Los recuentos del catálogo pueden variar después de la captura.

## Próximo paso concreto

Seleccionar recursos del inventario, no inventar una lista a partir de ejemplos. Para cada candidato: comprobar descarga y licencia; registrar variables, periodo y unidad territorial; probar una muestra; definir su representación; y después incorporarlo con fecha y procedencia.

Para actualización reproducible: ejecutar research_collect.py (catálogo), research_collect.py --details (fichas IOE), research_guide.py, research_check_links.py y research_package.py. Los originales de la captura están en la caché local ignorada por Git; los metadatos normalizados y el resultado de la investigación están versionados. `--refresh` vuelve a consultar las fuentes en el recopilador.
