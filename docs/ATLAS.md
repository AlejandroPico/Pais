# Composición de España · versión 0.4.1

La vista general contiene únicamente la cartografía española seleccionada: península, Baleares y cuatro marcos al oeste, para Canarias, Ceuta, Melilla y otros territorios. Francia, Portugal, el continente africano y las islas extranjeras quedan completamente cubiertos por una única máscara opaca de mar azul oscuro. No existe un escenario gris alrededor.

Los marcos son geometrías ancladas en un único mapa, cámara y zoom. No son ventanas de pantalla. Ceuta y Melilla se amplían ×16; el marco de otros territorios incluye Vélez de la Gomera (×128), Alhucemas (×64), Chafarinas (×32) y Alborán (×128). Cada ampliación se rotula; no se muestra una escala de distancia única que pudiera inducir a error. Los pequeños islotes tienen un contorno de apoyo para distinguirlos donde la ortofotografía es oscura.

El encuadre inicial y el mínimo de zoom se ajustan al espacio disponible. Se desactivan el arrastre libre, giro y cabeceo. La rueda o el pellizco permiten ampliar para consultar detalle, y Vista general recupera la composición completa. El mapa no permite alejarse hasta un escenario mundial. La selección y las búsquedas pueden encuadrar un territorio.

Imágenes, elevaciones, límites y consultas utilizan transformaciones afines reversibles en Mercator. Las teselas vectoriales se remiten a su dirección real a partir de un zoom compatible con la alineación; las ciudades autónomas utilizan sus polígonos completos para el sombreado estadístico municipal en cualquier escala de la composición. Los códigos, superficies, descargas y datos canónicos siguen en coordenadas reales. La superficie no aumenta por ampliar un dibujo.

## Selección de geometrías

Los archivos originales de provincias y comunidades del IGN se conservan sin alteración. La categoría cartográfica 54, «Territorios no asociados a ninguna provincia», contiene polígonos con situaciones distintas y no constituye por sí misma una relación de territorios españoles. Para este atlas se seleccionan sus polígonos correspondientes a Vélez, Alhucemas y Chafarinas; Alborán procede de Almería. No se incorporan automáticamente Gibraltar, la isla de los Faisanes ni Perejil a la silueta por figurar en esa misma categoría. Esta composición no se presenta como un inventario exhaustivo de enclaves ni como una certificación de deslinde.

Referencias: unidades administrativas IGN preservadas en F01 y [descripción de los destacamentos de Alhucemas, Vélez y Chafarinas por el Ejército de Tierra](https://ejercito.defensa.gob.es/ca/actualidad/2024/08/9700-ministra-visita-destacamentos.html?__locale=ca).

`npm run catalog:build` reconstruye el contorno seleccionado, la máscara mundial de presentación y los islotes. Las pruebas comprueban la reversibilidad de los siete desplazamientos, su separación, la conservación de los originales, la desaparición de terreno extranjero y la equivalencia entre direcciones de teselas y coordenadas de dibujo.
