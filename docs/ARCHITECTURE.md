# Arquitectura y evolución

La ampliación vigente de territorio está descrita en [F01](F01.md), versión 0.3.0. Añade la relación municipal completa de 2026, teselas vectoriales, búsqueda, cartografía por fecha y servicios catastrales, con su cobertura efectiva. Las limitaciones de la primera entrega que aparecen debajo se conservan como contexto histórico; la ficha F01 identifica qué ha cambiado.

Canarias utiliza ahora una transformación de presentación dentro del único mapa. Las geometrías fuente, códigos, observaciones, consultas y descargas mantienen sus referencias reales. Las capas derivadas para componer el atlas están identificadas como auxiliares de visualización.

## Separar descubrimiento, observaciones y representación

1. **Descubrimiento:** inventario conservado de operaciones/tablas de la API INE, metadatos y directorio de publicadores. Una entrada catalogada nunca se marca automáticamente como capa disponible.
2. **Ingesta:** un adaptador por fuente descarga y registra respuestas originales, fecha y hash. Reintentos acotados, cuatro consultas simultáneas como máximo, caché y errores explícitos. Las operaciones del INE se paginan según su API.
3. **Normalización:** claves territoriales oficiales, unidad, periodo de referencia, valor, estado del dato y metodología. Se preserva el cero; una ausencia sigue siendo nula. No se asigna un desglose más fino del publicado.
4. **Geografía:** claves INE 01–52 para provincias/ciudades y 01–19 para comunidades/ciudades; el IGN también publica los territorios sin provincia (54 / comunidad 20), conservados sin inventarles población. Geometrías simplificadas para pantalla y máscara de contexto calculada por unión/diferencia.
5. **Representación:** MapLibre carga estadísticas locales y teselas externas sin claves. Colores y leyendas fijas entre años para que el color mantenga su significado. Solo se combina un indicador de relleno a la vez, con múltiples redes y límites superpuestos. La opacidad conserva legibilidad.

## Contrato propuesto para nuevos conjuntos

Cada nuevo indicador necesita `id`, título, categoría, organismo, URL de origen, licencia, fecha de descarga, periodicidad, unidad, cobertura geográfica y temporal, nivel territorial, versión de límites, política de valores ausentes y notas de comparabilidad. Cada observación necesita `indicatorId`, `territoryCode`, `territoryLevel`, `period`, `value` y, cuando proceda, estado provisional/definitivo y dimensiones adicionales. La fecha de publicación no sustituye al periodo observado.

Nunca se mezclan precios de oferta, alquiler declarado y valor tasado; resultados electorales de diferentes procesos; observaciones y predicciones meteorológicas; ni población de operaciones distintas sin identificar su ruptura metodológica. No todo dato del INE es cartografiable: algunas tablas son exclusivamente nacionales, o contienen múltiples dimensiones que requieren selección previa.

## Límites de esta entrega

- Serie de Padrón histórica 1996–2021; las operaciones recientes no se han empalmado artificialmente.
- Municipios mediante imagen WMS, visibles desde zoom 8. No hay estadísticas ni búsqueda municipal todavía.
- Las comarcas se incorporarán por su autoridad y tipología. No se ofrece una falsa malla comarcal nacional uniforme.
- Las capas de imagen pueden omitir detalle según escala y disponibilidad del publicador. La red ferroviaria refleja la cobertura del servicio IGN, no una certificación de todas las vías históricas, abandonadas o privadas.
- GetFeatureInfo consulta las capas activas alrededor del punto pulsado; muestra atributos de origen o indisponibilidad explícita. Algunos servicios no ofrecen esa operación o no permiten su lectura desde el navegador.
- El tiempo del cronograma solo afecta a estadísticas. Imágenes, límites y redes tienen sus propias fechas y cobertura.
- La máscara de contexto destaca el territorio terrestre. No pretende definir zonas económicas exclusivas, aguas jurisdiccionales ni resolver delimitaciones marítimas.
- La densidad se calcula sobre superficie esférica aproximada de límites actuales; no representa superficies oficiales ni fronteras históricas.
- No se garantiza disponibilidad de terceros, ni funcionamiento sin conexión. No se almacena información de visitantes, ni se necesitan cuentas para consultar el atlas.

## Plan de incorporación

El [plan de entregas del 6 de noviembre de 2026](PLAN_DE_ENTREGAS.md) organiza la ampliación en F00 —base común— y 29 fascículos temáticos. Sustituye la lista inicial de prioridades: primero se revisará el diseño de la página; después se implementarán F00 y F01 y se integrarán las familias siguientes por lotes comprobables.

Las fuentes nacionales, autonómicas y locales se reunirán por indicador y tema, conservando diferencias de metodología y cobertura. El reparto del inventario es una planificación de revisión, no una declaración de capas disponibles. Cada familia incluirá sus series históricas, consulta territorial y registro de productos pendientes desde su primera integración.

El JSON local facilita comenzar sin infraestructura. No se propone almacenar terabytes de imágenes en Git. Antes de superar los límites de Pages/GitHub, separar catálogo pequeño, tablas particionadas y objetos geográficos optimizados. SQLite/DuckDB/Parquet pueden tener sentido en ingesta o consultas analíticas; no son necesarios para servir esta primera versión estática.
