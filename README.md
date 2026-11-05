# El país · Atlas abierto de España

Un atlas para explorar España a través de sus datos oficiales, con un mapa protagonista, capas combinables, consulta territorial y evolución histórica.

**Web:** https://alejandropico.github.io/Pais/

## Primera entrega

- Relieve IGN con elevación 3D real (DEM global Mapzen/USGS), ortofoto PNOA y callejero IGN. Ninguna clave de pago.
- España destacada; países vecinos y contexto marítimo atenuados. Navegación limitada al entorno de España, con acceso a Canarias, Baleares, Ceuta y Melilla.
- Comunidades y provincias con distinta jerarquía visual. Geometrías oficiales descargadas del WFS INSPIRE del IGN, simplificadas aproximadamente 28 m en latitud para visualización. No son cartografía para deslindes legales.
- Población histórica, densidad aproximada, proporción de mujeres y variación desde 1996, por provincia o comunidad. Cronograma, reproducción y CSV por territorio.
- Ríos y masas de agua, red ferroviaria (no solo alta velocidad), carreteras, caminos de Santiago y municipios como capas de imagen oficiales, con opacidad independiente. Consulta de objetos WMS donde el servicio la permita.
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

Proyecto independiente, no afiliado a los organismos citados. Datos INE: CC BY 4.0. Cartografía IGN/CNIG y colaboradores: CC BY 4.0, con las condiciones y créditos de cada servicio. DEM: Mapzen, USGS y demás [fuentes originales de Tilezen](https://github.com/tilezen/joerd/blob/master/docs/attribution.md). La inclusión de una fuente pendiente no presupone una licencia común a todos sus productos.

Bibliotecas: MapLibre GL JS, Lucide y polygon-clipping, con sus respectivas licencias. Las tipografías se sirven desde Google Fonts y tienen alternativas locales del sistema.
