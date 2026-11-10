# El país · Atlas abierto de España

## Versión 0.4.1 · Composición de España

Solo España sobre mar azul oscuro, con marcos para Canarias, Ceuta, Melilla y otros territorios; sin países vecinos ni arrastre libre. Las ampliaciones se rotulan y las consultas conservan sus coordenadas reales. [Detalle del atlas](docs/ATLAS.md).

## Versión 0.4.0 · F02.1

Primera entrega de **Población, hogares y migraciones**: 35 tablas completas del INE y 9.958.171 observaciones. Censos con edad, sexo, nacionalidad y nacimiento, hogares, movimiento natural anual y mensual, migraciones, indicadores y proyecciones de hogares identificadas por separado. Selección de todas las categorías y periodos, cronograma, series, pirámides, detalle de los 8.132 municipios por provincia, densidad aproximada y cambio censal.

Datos comprimidos en el repositorio y consulta por partes, con verificación de contenido. Catálogo actualizado: 2.173 tablas anunciadas en 18 operaciones, diferenciadas de las 35 integradas. El mapa sigue empezando sin capas estadísticas activadas. [Cobertura y pendientes de F02](docs/F02.md).


Un atlas para explorar España a través de sus datos oficiales, con un mapa protagonista, capas combinables, consulta territorial y evolución histórica.

**Web:** https://alejandropico.github.io/Pais/

## Versión 0.3.0 · F01: territorio y cartografía

- [Entrega y cobertura de F01](docs/F01.md): 8.132 municipios INE de 2026 con geometría IGN consultable, jerarquía, filtro insular y búsqueda oficial de direcciones.
- Municipios vectoriales, 194 recintos comarcales de seis comunidades y zonas estadísticas canarias; secciones censales en 22 ediciones, límites históricos, poblaciones, curvas, edificios y catastro estatal y foral.
- Modelo de elevaciones oficial IGN. Un solo mapa: Canarias desplazadas al oeste de Portugal con separación ficticia; comparten navegación, zoom y capas. Consultas y descargas mantienen coordenadas reales. Mar azul oscuro.
- Los límites y estadísticas siguen sus propias fechas. La ortofoto y el terreno elevado se conservan como inicio; las capas de información permanecen apagadas por defecto.
- 39 productos utilizables en total. El catálogo añade el inventario de 128 capas anunciadas por nueve servicios cartográficos, sin equipararlas a conjuntos únicos ni capas ya adaptadas.

## Versión 0.2.0 · Interfaz y base común F00

- Menú lateral inspirado en EnRuta: favicon para ampliar, categorías con paneles desplegables y utilidades al pie. Sin cabecera ni textos decorativos. Desplazamiento táctil sin barras visibles.
- Ortofoto por defecto, terreno elevado con cámara vertical, mar azul y países vecinos atenuados. La primera versión utilizaba un mapa de Canarias independiente, sustituido en 0.3.0 por la composición unificada; Ceuta y Melilla permanecen en el encuadre principal. No se activan límites ni estadísticas al abrir una vista nueva.
- Búsqueda, filtros, apariencia, vista general, terreno 3D, pantalla completa, Fuentes y Acerca de en el lateral. Doble clic derecho restablece norte y cámara vertical. La rueda y el pellizco controlan el zoom.
- [F00 implementado](docs/F00.md): fuentes, publicadores, inventarios completos de metadatos, productos disponibles, estados y cobertura por fascículo. Catálogos grandes consultados bajo demanda en un trabajador separado, con comprobación de integridad y resultados paginados.
- Acerca de con la identidad, versión, propósito, autor, portfolio y repositorio. El favicon original permanece en la raíz.

## Investigación de fuentes públicas

La [investigación extensa de datos públicos de España](docs/research/README.md) reúne 182 fichas de fuentes y servicios, el catálogo de 238 publicadores con 116.236 conjuntos federados, y las 758 operaciones del inventario estadístico estatal con variables, responsables y escala territorial. Incluye fuentes estatales, autonómicas, locales, científicas y europeas. Es un inventario para decidir futuras incorporaciones, no un anuncio de que esas capas estén ya en el mapa.

El [plan de entregas](docs/PLAN_DE_ENTREGAS.md) distribuye la incorporación en una base común y 29 fascículos temáticos, reuniendo las fuentes nacionales, autonómicas y locales dentro de cada tema. Incluye alcance, orden, criterios de cierre y un [reparto de las 182 fichas y los 27 sectores estadísticos](docs/planning/COBERTURA_DE_FUENTES.md). El siguiente trabajo será el diseño de la página; la integración de estas nuevas familias vendrá después.

## Capas disponibles

- Relieve IGN con elevación 3D real (modelo oficial IGN), ortofoto PNOA y callejero IGN. Ninguna clave de pago.
- España destacada; países vecinos y contexto marítimo atenuados. Navegación limitada al entorno de España, con acceso a Canarias, Baleares, Ceuta y Melilla.
- Comunidades y provincias con distinta jerarquía visual. Geometrías oficiales descargadas del WFS INSPIRE del IGN, simplificadas aproximadamente 28 m en latitud para visualización. No son cartografía para deslindes legales.
- Población histórica, densidad aproximada, proporción de mujeres y variación desde 1996, por provincia o comunidad. Cronograma, reproducción y CSV por territorio.
- Ríos y masas de agua, red ferroviaria (no solo alta velocidad), carreteras, caminos de Santiago como capas de imagen oficiales; municipios mediante teselas vectoriales IGN, con opacidad independiente. Consulta de objetos WMS donde el servicio la permita.
- Catálogo buscable de **166 operaciones, 6.913 tablas únicas y 7.007 asociaciones operación-tabla** expuestas por la API JSON del INE al realizar la ingesta. 60 operaciones con desglose geográfico. No se afirma haber descargado todas las observaciones de esas tablas, ni haber catalogado otras interfaces del INE que no expone este inventario.
- Directorio de organismos, estado de integración, fuentes, licencias y límites metodológicos.
- Enlaces compartibles con año, capa, división territorial y vista; interfaz adaptable y navegación por teclado.
- Botón discreto «Acerca de» arriba a la derecha, con icono, nombre, versión, propósito y enlaces al repositorio y al portfolio de Alejandro Pico. El `favicon.svg` editable está en la raíz; al preparar la web se copia a la raíz publicada.

La serie inicial de población es **1996–2021**, a 1 de enero, tablas INE 2852 y 2853. No hay dato de 1997 y no se interpola. No es la población más reciente. Las superficies son aproximaciones esféricas sobre límites actuales; la densidad y la variación se calculan en la aplicación. El cronograma no cambia la fecha de las imágenes ni reconstruye fronteras históricas.

## Desarrollo

Requisitos: Node.js 24 y Python 3.10 o posterior para actualizar datos.

```sh
npm ci
npm run dev
npm test
npm run build
npm run catalog:build
```

La compilación genera `dist/`, con rutas relativas compatibles con `/Pais/`. El workflow de GitHub Actions ejecuta las pruebas y publica en Pages al actualizar `main`; las propuestas de cambio solo verifican y construyen. El origen de Pages debe ser **GitHub Actions**.

## Datos en el repositorio

Los datos estadísticos normalizados, límites y metadatos están en `public/data/`. Los servicios de imágenes se consultan al proveedor: no se descarga ni se incluye un mapa mundial completo en el repositorio. Las fuentes de mapa requieren conexión; no hay promesa de funcionamiento sin conexión.

```sh
npm run data:refresh
python scripts/ingest.py --only catalog --refresh
python scripts/ingest.py --only population --refresh
python scripts/ingest.py --only geo --refresh
```

Sin `--refresh`, la ingesta reutiliza respuestas de `.cache/` para poder reproducir la transformación sin repetir descargas. Los originales se conservan en esa caché local ignorada por Git; `provenance.json` registra URL, fecha de obtención, tamaño y SHA-256. Revisar siempre los cambios de datos y ejecutar las pruebas antes de publicarlos. Si una operación del catálogo falla, queda identificada en `errors` y la interfaz advierte del inventario incompleto. Las comprobaciones previenen publicar pérdidas silenciosas de cobertura.

**Almacenamiento elegido:** JSON y GeoJSON versionados para esta fase, sin servidor ni base de datos de pago. Un catálogo amplio no justifica cargar todas sus observaciones al abrir la página: el catálogo se descarga solo al consultarlo. Cuando crezca el volumen, particionar observaciones por indicador, territorio y año, y usar teselas vectoriales/PMTiles para geometrías. Ver [arquitectura y siguientes pasos](docs/ARCHITECTURE.md) y [fuentes](docs/SOURCES.md).

## Atribución

Proyecto independiente, no afiliado a los organismos citados. Datos INE: CC BY 4.0. Cartografía IGN/CNIG y colaboradores: CC BY 4.0, con las condiciones y créditos de cada servicio. Modelo de elevaciones de esta versión: IGN, con su atribución correspondiente. El catálogo conserva la referencia del modelo Mapzen/USGS utilizado en la primera entrega. La inclusión de una fuente pendiente no presupone una licencia común a todos sus productos.

Bibliotecas: MapLibre GL JS, Lucide y polygon-clipping, con sus respectivas licencias. Las tipografías se sirven desde Google Fonts y tienen alternativas locales del sistema.

El mar y el contexto terrestre se separan con los límites de España del IGN y cartografía de países de [Natural Earth](https://www.naturalearthdata.com/about/terms-of-use/), de dominio público, recortada al entorno de España. [Procedencia del contexto](public/data/context-provenance.json). Esa máscara no define jurisdicciones marítimas.
