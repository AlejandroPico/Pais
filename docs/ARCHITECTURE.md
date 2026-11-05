# Arquitectura y evolución

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

## Prioridades siguientes

1. Incorporar población reciente identificando operación, continuidad y metodología, y las series municipales del INE. Particionar por provincia y cargar por vista.
2. Clasificar automáticamente el inventario INE por tema y detectar candidatos cartografiables a partir de dimensiones y códigos, con revisión de cada adaptador.
3. Añadir renta (INE), vivienda/alquiler (MIVAU y fuentes oficiales con cobertura verificada), empleo y elecciones definitivas (Interior).
4. Integrar bosque, espacios protegidos, masas de agua, acuíferos, costa y medio marino (MITECO, IGME y organismos competentes).
5. Tiempo/clima AEMET mediante ingesta fuera del navegador; la clave gratuita se mantendría en secretos del entorno, nunca en Git ni en la web publicada.
6. Comarcas autonómicas tipificadas, secciones censales y otras geometrías mediante PMTiles; correspondencias por fecha, sin suponer una jerarquía idéntica en todo el país.
7. Comparación temporal, búsqueda municipal, selección de dimensiones, orden de superposición y exportación de vistas.

El JSON local facilita comenzar sin infraestructura. No se propone almacenar terabytes de imágenes en Git. Antes de superar los límites de Pages/GitHub, separar catálogo pequeño, tablas particionadas y objetos geográficos optimizados. SQLite/DuckDB/Parquet pueden tener sentido en ingesta o consultas analíticas; no son necesarios para servir esta primera versión estática.
