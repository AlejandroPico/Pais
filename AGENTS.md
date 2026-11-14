# El país · Guía de trabajo para agentes

Lee también [tareas.md](tareas.md). Contiene la revisión de partida, el trabajo pendiente por fascículo y la evidencia que debe quedar antes de cerrarlo. Este archivo fija las reglas permanentes del proyecto. El [plan temático](docs/PLAN_DE_ENTREGAS.md), su [matriz de fuentes](docs/planning/COBERTURA_DE_FUENTES.md) y [su versión estructurada](docs/planning/fasciculos.json) describen el alcance de F00 a F29. Las decisiones más recientes de este archivo prevalecen sobre las descripciones históricas de diseño de esos documentos.

## Objetivo y alcance

El país es un atlas público de España. Reúne datos oficiales estatales, autonómicos, insulares, provinciales y locales, y las series europeas o internacionales que amplíen la cobertura española o permitan comparaciones explícitas. El objetivo comprende cada distribución, variable, desglose y edición pública pertinente de los inventarios revisados, incluidos históricos y productos discontinuados. Las fuentes y ejemplos de una conversación son puntos de partida. Amplía la búsqueda con el IOE, INEbase, datos.gob.es, IDEE y los catálogos de los organismos competentes.

La navegación se organiza por tema e indicador. El mismo apartado reúne recursos equivalentes de Madrid, Barcelona y cualquier otro territorio, con un filtro común donde las definiciones lo permitan. La comunidad, provincia y municipio pueden compartir nombre y siguen siendo entidades distintas. Conserva bajo el mismo tema las variantes metodológicas que no sean comparables. Una capa puede aparecer enlazada desde varias categorías mediante una única ficha y una sola copia de sus datos.

Representa según la naturaleza del recurso. Usa polígonos para áreas, líneas para redes o trayectos, puntos para centros y observaciones, teselas o imágenes para superficies, y ficha o gráfico para series nacionales, documentos y datos sin geometría. Una ficha de catálogo con un enlace demuestra descubrimiento. La integración exige que la información utilizable sea realmente consultable por el público. Las condiciones oficiales de reutilización se comprueban por recurso.

## Protocolo obligatorio de cada fascículo

1. **Fija el alcance y la fecha de revisión.** Lee su bloque de `tareas.md`, los documentos F00–F04 cuando correspondan y las rutas de `docs/planning/fasciculos.json`. Enumera organismos, operaciones, conjuntos, distribuciones, tablas, capas, ediciones y coberturas relevantes. Incluye portales territoriales y archivos históricos. Identifica los nuevos recursos de la revisión y los ya conservados.
2. **Resuelve cada fila del inventario.** Registra el identificador del publicador y del recurso, ficha, descarga o servicio, licencia, periodicidad, fechas de referencia y publicación, territorio, formatos, variables, limitaciones y siguiente acción. Distingue conjuntos de sus distribuciones y capas de sus ediciones. Una edición de un conjunto también puede ser una fuente de procedencia por fila.
3. **Contrasta con el recurso original.** Verifica cabeceras, paginación, formatos, CRS, dimensiones, diccionarios y cobertura efectiva. Una respuesta HTTP satisfactoria puede ser una portada o un fichero incompleto. Comprueba las cuentas, los huecos, las revisiones, los códigos territoriales y las metodologías antes de elegir un formato interno.
4. **Integra la captura completa.** Utiliza el adaptador apropiado en `scripts/` y escribe en el directorio temático de `datos/`. Descarga todas las páginas, archivos, hojas, ediciones y desgloses publicables de la revisión. Los lotes pequeños son pasos internos. Sigue con el resto de las filas del fascículo dentro del encargo. Conserva cada original en la caché local cuando esté permitido y registra su URL, fecha, tamaño y huella SHA-256.
5. **Normaliza y enlaza.** Conserva el identificador y periodo originales, la unidad, los valores y estados, la metodología y el ámbito territorial. Versión y código forman la clave geográfica cuando existe cambio de límites. Procesa las equivalencias oficiales con evidencia y mantén accesible la serie de un código histórico aunque carezca de geometría.
6. **Conecta el visor.** Registra fichas, filtros, leyendas, fechas, incertidumbre, fuente, controles de apariencia, consulta de objetos, serie y exportación según el producto. Enlaza las referencias cruzadas por un identificador estable. Usa la ficha de España para observaciones nacionales y la ficha tabular si el área publicada carece de cartografía verificable.
7. **Comprueba y vuelve a iterar.** Revisa recuentos, hashes, categorías, unidades, fechas, ediciones, uniones territoriales, cifras de contraste y comportamiento del navegador. Continúa por todas las filas pendientes y revisa las alternativas oficiales de los bloqueos. Una incompatibilidad demostrada se documenta con fichero, endpoint, caso concreto y siguiente acción. Si un dataset carece de geometría, prueba la consulta tabular o una fuente geográfica oficial antes de considerarlo bloqueado.
8. **Cierra con evidencia.** Actualiza `tareas.md`, las fichas y el inventario fechado. El fascículo queda completo cuando cada entrada pertinente se puede consultar y verificar, y los duplicados y las derivaciones están justificados con su destino comprobado. Cualquier edición pertinente pendiente, parcial o bloqueada mantiene abierta la fase. Una nueva publicación posterior a la revisión abre su actualización. Si el usuario encarga varios fascículos, cumple el alcance completo de cada uno y respeta el orden que indique.

La entrega ordinaria comprende el fascículo entero, con datos, visor y comprobaciones. Los lotes internos no son entregas Fxx.1 o Fxx.2. Una versión de interfaz puede publicarse por separado si corresponde al encargo. Cuando existe un impedimento material, agota lo que pueda resolverse y señala exactamente el recurso, la evidencia, la alternativa que probaste y lo que falta para completarlo. La amplitud de un inventario no equivale a un impedimento técnico.

### Estados del registro

| Estado interno | Criterio |
| --- | --- |
| `por_revisar` | Ficha descubierta, alcance o distribución aún sin comprobar. |
| `revisado` | Recurso, formatos, cobertura y relación con el tema documentados. |
| `en_integracion` | Implementación iniciada con trabajo verificable aún pendiente. |
| `integrado` | Producto y ediciones definidos en su ficha disponibles y comprobados en el visor o la consulta correspondiente. |
| `bloqueado` | Impedimento verificable, con evidencia y `nextAction`. |
| `no_procede` | Motivo concreto, como duplicado de una ficha canónica, derivación a otro tema o ámbito ajeno al proyecto. Registra el destino o el vínculo. |

Registra las decisiones editoriales en `registry/reviews.json`. Conserva `inventory`, `productId`, `updatedAt`, `reason`, `categoryIds`, `status` e historial `history` para cada cambio. Los estados integrados necesitan `implementedProductId` y una acción existente. Las entradas de descubrimiento pueden tener temas candidatos en `suggestedCategoryIds`. Revisa esos candidatos antes de asignar una categoría definitiva. La situación de un producto y la de su operación estadística son independientes.

## Estructura permanente

| Ruta | Contenido y responsabilidad |
| --- | --- |
| `datos/` | Raíz canónica y versionada de los datos, índices, cubos, manifiestos e inventarios estructurados. |
| `datos/catalogo/` | F00. Índice y ficheros compilados de Fuentes, procedencia transversal y `investigacion/` con las capturas JSON, CSV y GZIP de los inventarios. |
| `datos/territorio/` | Geometrías y manifiestos oficiales, capas locales, límites de atlas de presentación, `contexto/` auxiliar y `nomenclator/` para entidades geográficas. |
| `datos/poblacion/` | Serie inicial del Padrón, cubos en `ine/` y fichas históricas en `intercensal/`. |
| `datos/renta/` | Cubos e inventario INE en `ine/`. Los siguientes proveedores tienen su propio subdirectorio cuando corresponda. |
| `datos/trabajo/` | Cubos e inventario del INE en `ine/` y series municipales en `sepe/`. |
| `registry/` | Configuración versionada de tablas, productos, revisiones, servicios y coberturas. Los generadores compilan aquí `*-products.json`. Separa configuración de observaciones. |
| `docs/` | Arquitectura, plan, fichas F00–F04, método, matriz e informes de investigación. `docs/research/` conserva la documentación legible de las capturas de F00. |
| `src/` | Frontend, catálogo, consultas, interfaz, mapa, representación y trabajadores. |
| `scripts/` | Recopiladores, constructores, auditores y migraciones reproducibles. |
| `tests/` | Pruebas de integridad y cobertura geográfica y estadística. |
| `.cache/` | Descargas originales y temporales locales ignorados por Git. No guardar aquí la única copia de un dato normalizado necesario para compilar. |
| `public/` y `dist/` | Recursos públicos auxiliares y salida de compilación. El favicon editable está en la raíz. La compilación publica sus datos en `dist/datos/`. |

### Carpetas por categoría

Usa nombres de carpeta en español, en minúsculas, sin tildes, con guiones para varias palabras. El orden y los identificadores del menú están en `src/categories.ts`. El ámbito de cada carpeta se desarrolla en [tareas.md](tareas.md).

| ID | Carpeta | ID | Carpeta |
| --- | --- | --- | --- |
| F00 | `datos/catalogo/` | F15 | `datos/naturaleza/` |
| F01 | `datos/territorio/` | F16 | `datos/agua/` |
| F02 | `datos/poblacion/` | F17 | `datos/clima/` |
| F03 | `datos/renta/` | F18 | `datos/geologia/` |
| F04 | `datos/trabajo/` | F19 | `datos/mar/` |
| F05 | `datos/cuidados/` | F20 | `datos/ambiente/` |
| F06 | `datos/vivienda/` | F21 | `datos/energia/` |
| F07 | `datos/economia/` | F22 | `datos/transporte/` |
| F08 | `datos/comercio/` | F23 | `datos/conectividad/` |
| F09 | `datos/hacienda/` | F24 | `datos/turismo/` |
| F10 | `datos/ayudas/` | F25 | `datos/cultura/` |
| F11 | `datos/educacion/` | F26 | `datos/deporte/` |
| F12 | `datos/ciencia/` | F27 | `datos/elecciones/` |
| F13 | `datos/salud/` | F28 | `datos/administracion/` |
| F14 | `datos/medio-rural/` | F29 | `datos/justicia/` |

Dentro de cada carpeta, usa un subdirectorio por fuente o producto cuando tenga varios recursos. Sigue los facsímiles y formatos tal como los publique cada organismo. Guarda solo una representación canónica por conjunto y enlaza sus usos transversales. Una carpeta con `.gitkeep` está reservada y vacía de datos. Elimina ese marcador al incorporar el primer recurso. No pongas un marcador como índice o ficha publicable.

El desarrollo sirve `datos/` desde la raíz de Vite. La compilación copia la estructura a `dist/datos/`, donde conservan sus rutas los índices, los nombres de archivo y los fragmentos. Construye las URL con `import.meta.env.BASE_URL` y una ruta relativa. GitHub Pages sirve el sitio bajo `/Pais/`. Conserva `mapAction`, identificadores de capa y claves existentes de enlaces compartidos. Los campos `dataFile` se resuelven con respecto a `datos/`; los `file` dentro de un índice se resuelven con respecto a la carpeta de dicho índice. No crees una segunda copia manual de los datos en la carpeta pública.

## Tecnologías y componentes

- Frontend estático en TypeScript estricto, CSS y HTML. Vite compila con base relativa. MapLibre GL JS dibuja teselas, capas vectoriales, ráster y terreno. Lucide aporta los iconos. Esta implementación no requiere servidor de aplicación ni base de datos en ejecución. No hace falta migrar a Angular para mantener el diseño inspirado por En Ruta.
- `src/main.ts` arranca el atlas. `src/atlas.ts` une categorías, mapa base, fuentes, búsqueda, mapa, leyendas, selección y estado compartible. `src/categories.ts` define el menú. `src/layer-menu.ts` gestiona paneles a la derecha en escritorio y desplegables en móvil. `src/layer-appearance.ts` conserva los ajustes por capa. `src/theme.ts` calcula el modo solar para el punto de referencia de Madrid y adapta las preferencias antiguas.
- `src/atlas-coordinates.ts` transforma e invierte las coordenadas de visualización. `src/atlas-geography.ts` aplica las transformaciones y las capas auxiliares. `src/territory.ts`, `territory-config.ts` y `territory-data.ts` implementan los límites, proveedores y objetos territoriales.
- `src/catalog.ts` y `catalog.worker.ts` abren y consultan los inventarios a demanda. `src/registry.ts` describe sus tipos. `demography.ts`, `demography.worker.ts` y `demography-data.ts` comparten la consulta de F02 a F04, con rutas y controles por tema. `intercensal.ts` y `nomenclator.ts` sirven sus índices y consultas especializados. Los trabajadores descargan, comprueban y filtran los fragmentos.
- Python construye las capturas e índices. Los conectores utilizan la biblioteca estándar cuando basta. La cartografía local puede requerir `pyshp`, `pyproj` y Shapely 2. Las hojas XLS del SEPE se leen con `xlrd`. El proceso de publicación usa las capturas versionadas y no instala esos conectores para consultar fuentes en vivo.
- GitHub Actions usa Node 24, `npm ci`, generación del catálogo, pruebas y compilación. Publica `dist/` desde `main`. Las solicitudes de cambios compilan y comprueban el proyecto. Un commit local se informa como local. Si la publicación está incluida en el encargo, verifica la ejecución de Actions y la URL del visor con los archivos esperados. [Repositorio](https://github.com/AlejandroPico/Pais) · [Visor](https://alejandropico.github.io/Pais/)

## Contratos de datos e ingesta

| Tipo | Forma y comprobaciones |
| --- | --- |
| Fuente y producto | ID estable, título, ID del organismo, tema, acceso, URL oficial, licencia, cobertura temporal y territorial, unidad, estado, notas y acción o ubicación del recurso. `F001` a `F182` son fichas de organismos en la captura, `F01` a `F29` son temas. Los publicadores federados usan `publisher:`. |
| Catálogo | `datos/catalogo/index.json` anuncia ficheros comprimidos por inventario, número de entradas, bytes, SHA-256 comprimido y SHA-256 del contenido. Se conserva el organismo responsable real de las operaciones del IOE. El índice incluye la procedencia de las entradas de construcción. |
| Cubo estadístico | Índice por tabla con dimensiones y sus categorías, territorios, periodos, unidad y fuente. Un fichero `*-main.json.gz` sirve ámbitos generales, y partes provinciales sirven municipios, distritos o secciones. La fila general contiene índices de territorio, periodo y categorías, valor, estado y procedencia cuando corresponde. El visor demográfico comparte los diccionarios territoriales idénticos. |
| Series del SEPE | `datos/trabajo/sepe/sepe.json` declara `compactColumns`. Filas `[territorio, periodo, edición, ...valores]` por provincia. Cada columna es un desglose publicado. El manifiesto conserva el año y la descarga oficial de cada edición, incluidas las hojas históricas complementarias. |
| Geometría | GeoJSON en longitud y latitud para coordenadas de intercambio, o teselas y servicios con una proyección explícita. Conserva ID, nivel, jerarquía, fuente y edición. Prueba topología, contención, islas, enclaves y la correspondencia territorial. Los GeoPackage, SHP y GML originales se procesan en ingesta donde proceda. |
| Servicios geográficos | Conserva origen, versión, identificador exacto de capa, escala, ámbito, CRS, dimensiones como `TIME` y formato de consulta. Comprueba WMS/WMTS, WFS, OGC API Features o ArcGIS conforme al recurso. Audita mapa desde el origen de Pages y la consulta de atributos cuando se anuncie. |
| Exportación | CSV UTF-8 legible en castellano. Conserva códigos, periodo de referencia, filtros, valor original, unidad, estado y enlace oficial de la observación. Si la vista calcula un derivado, explica su base y conserva el original claramente identificado. Mantén las descargas de geometrías en coordenadas reales. |

- **Códigos.** Conserva ceros a la izquierda. Comunidades y provincias usan códigos INE/IGN en su contexto. Municipios de cinco posiciones, secciones con su código completo y edición, y comarcas/entidades con el identificador de su autoridad. Distingue nacimientos por residencia o por lugar del hecho, empleo por residencia o centro de trabajo y cada ámbito administrativo o físico.
- **Ausencias.** Un cero oficial es un valor. Las supresiones, los umbrales como «<5», los blancos, los datos provisionales y los ámbitos fuera de cobertura tienen su propio significado. No estimes valores protegidos ni atribuyas un dato a un territorio más detallado. Las tasas y porcentajes se calculan solo con denominadores y compatibilidad demostrados, con unidad y periodo explícitos.
- **Periodos.** Conserva el periodo de referencia y sus límites, con fechas ISO cuando proceda y códigos del tipo `AAAA`, `AAAAMmm` y `AAAATt` donde se utilicen. La fecha de captura y la fecha de publicación son metadatos distintos. El cronograma recorre los periodos observados y mantiene una escala comparable para la misma selección.
- **Licencias y atribución.** Comprueba licencia y condiciones de copia e inserción por fichero, capa o API. Conserva los créditos en mapa y ficha. Protege los datos personales y mantén el nivel de publicación oficial. No pongas claves, datos privados ni descargas que exijan autorización de redistribución en el sitio público.
- **Identidad y duplicados.** Relaciona los catálogos mediante códigos oficiales y URI. Los nombres similares son candidatos. Distingue licencias, versiones y poblaciones de referencia. Emplea equivalencias explícitas para códigos administrativos históricos y conserva ambas ediciones cuando cambie el significado.
- **Fuentes grandes.** Parte por provincia, periodo, indicador o tesela, según el acceso real. Descarga a demanda y evita leer todos los cubos desde la página inicial. Conserva compresión y checksums. Evalúa tamaño del sitio y del historial antes de añadir archivos grandes. Si la distribución estática resulta insuficiente, prueba un servicio oficial o una alternativa de almacenamiento y documenta la evidencia y el impacto antes de cambiar de arquitectura.
- **Reproducibilidad.** Identifica los originales por URL y huella. Para una migración conserva los bytes donde sea posible. En actualizaciones, comprueba argumentos, recuentos y descargas antes de sustituir la captura. Conserva la edición válida frente a fallos parciales. Los scripts de refresco deben funcionar con sus rutas publicadas. Especifica dependencias y opciones particulares en la ficha del fascículo.
- **Auditoría.** Usa consultas de contraste contra el original, con al menos una cifra o un objeto de referencia y un caso de ausencia o código histórico cuando exista. Para una capa externa registra peticiones válidas con la escala real y comprueba CORS desde el navegador. Un fallo puntual conserva fecha, diagnóstico y siguiente acción.

## Interfaz y cartografía

- Conserva el arranque limpio con ortofoto, terreno habilitado visto verticalmente, mar azul oscuro y capas temáticas apagadas. Respeta la vista general de península, Baleares y demás territorios españoles. Canarias, Ceuta, Melilla y otros territorios disponen de marcos discontinuos situados en las coordenadas de presentación del mismo mapa. Los marcos deben acompañar la cámara y salir de la vista al navegar. Portugal, Francia y África quedan ocultos por la máscara del atlas. La máscara tiene función visual, no jurisdiccional. Mantén la navegación con arrastre, rueda y gestos, y el doble clic derecho para orientar al norte.
- Conserva el menú fijo a la izquierda. Marca/favicon amplía la barra, los iconos de categorías visibles dependen del alto disponible y el resto está bajo «Todas las categorías». En escritorio, las ramas se abren en paneles laterales solapados con retorno directo a niveles anteriores. En móvil, se usan desplegables en la jerarquía del panel. Mantén navegación por teclado, foco al volver y controles accesibles. Evita barras visibles y aprovecha paginación y desplazamiento táctil.
- Mapa base es transversal y se puede cambiar desde Visualización, Filtros y los paneles de categorías habilitados. Conserva ortofoto, relieve, callejero, topografía, contorno, silueta y ediciones históricas disponibles. Las capacidades dependen del producto. Ofrece color y opacidad para capas que permitan recoloración, y controles adecuados para imágenes. Mantén el color y la opacidad de tierra y mar donde el modo de base lo permita. Comprueba el contraste sobre ortofoto, relieve, callejero y contorno.
- El ojo de Visualización agrupa vista general, mapa base, terreno 3D, aspecto y pantalla completa. Conserva Mañana, Tarde, Noche y Automático en toda la interfaz incluida la barra lateral. Fuentes mantiene navegación por pestañas, filtros, recuentos y paginación. Acerca de reúne el SVG de España, nombre, versión, propósito y enlaces al repositorio y porfolio con pie accesible.
- Un producto cartográfico debe poder inspeccionarse y explicarse. Los paneles muestran objeto, valores, unidad, fecha, fuente y límites de cobertura. Las capas compatibles pueden superponerse con controles independientes. En la implementación actual se usa un relleno estadístico a la vez junto a capas de otros tipos. Conserva legibilidad, orden, escala y leyenda cuando se amplíe esa capacidad.
- Mantén el título del navegador «El país», el favicon en raíz y la URL inicial limpia. Los enlaces compartidos pueden guardar la selección cuando el usuario la solicita. Evita activar estadísticas o introducir parámetros por defecto al entrar por la URL principal.

## Arranque, actualización y comprobación

```sh
npm ci
npm run catalog:build
npm test
npm run build
npm run dev
```

- Usa `npm run preview` para verificar lo compilado. Comprueba portada, límites, catálogo, un fragmento de cada familia modificada, filtros, ficha, cronograma y descarga. Para cambios de rutas, prueba también una URL bajo el prefijo de Pages. Comprueba referencias de `dataFile` y que el servidor entrega JSON o GZIP en lugar de la portada HTML.
- `npm run catalog:build` encadena `build_atlas_layout.mjs`, `build_territory_catalog.mjs`, `build_demography_registry.py` para F02, F03 y F04, y `build_registry.py`. No requiere red. Revisa las salidas generadas y sus diferencias. `python -m compileall -q scripts` detecta errores de sintaxis de adaptadores.
- Consulta `package.json` y las fichas F00–F04 para los comandos de actualización. `territory:refresh`, `territory:sections:refresh`, `territory:local:refresh`, `intercensal:refresh`, `nomenclator:refresh`, `demography:refresh`, `welfare:refresh` y `labor:refresh` acceden a las fuentes y pueden usar caché. Ejecuta la construcción del catálogo después de actualizar los datos.
- Comprueba Git antes y después. Aparte de los datos necesarios, guarda las recetas y el registro de cobertura. Evita incluir caché, `dist/`, archivos personales o descargas intermedias. Revisa los recuentos de la salida y el historial cuando existan cambios amplios.
- Actualiza [tareas.md](tareas.md) al resolver un punto con datos y evidencia. Si el repositorio y el documento discrepan, comprueba primero los archivos, el catálogo resultante, las pruebas y, cuando el encargo sea publicar, el despliegue. Solo después actualiza el estado de cierre.
