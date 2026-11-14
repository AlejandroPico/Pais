# El país · Tareas para completar el atlas

Última revisión de partida: 14 de noviembre de 2026. Consulta [AGENTS.md](AGENTS.md) para el protocolo, la arquitectura y la estructura definitiva de los datos. Esta lista incluye todos los fascículos, las familias ya identificadas y la enumeración verificable de los inventarios. Añade las distribuciones, ediciones y lagunas concretas a medida que se comprueben. Las listas de familias siguientes no sustituyen la revisión fila a fila de los inventarios enlazados.

## Cómo utilizar esta lista

1. Abre la fase solicitada, marca la revisión y guarda una lista por organismo, operación, producto, distribución y edición. Identifica cada fila mediante su URL oficial o código, no por el título. Usa [fasciculos.json](docs/planning/fasciculos.json) y [la matriz de fuentes](docs/planning/COBERTURA_DE_FUENTES.md) para no perder organismos, temas derivados o archivos históricos.
2. Parte de la [guía de organismos](docs/research/GUIA_DE_FUENTES.md), [IOE por sector](docs/research/IOE_POR_TEMA.md), [IOE por organismo](docs/research/IOE_POR_ENTIDAD.md), [publicadores nacionales](docs/research/PUBLICADORES_NACIONALES.md) y [accesos pendientes](docs/research/ACCESOS_PENDIENTES.md). Contrasta esas capturas con los catálogos oficiales vigentes. La [investigación estructurada](datos/catalogo/investigacion/) contiene las tablas y CSV completos disponibles para enumeración sin depender del Markdown.
3. Inspecciona el [índice compilado](datos/catalogo/index.json) y sus archivos comprimidos. Lee `available.json.gz` para las fichas con acción activa, `ioe.json.gz`, `ine.json.gz` y `national.json.gz` para descubrimiento, y `territory.json.gz`, `demography.json.gz`, `welfare.json.gz`, `labor.json.gz` para los inventarios específicos de las fases con capturas. Conserva y comprueba sus [decisiones editoriales](registry/reviews.json). Para enumerar lo pendiente, compara el inventario temático con los IDs de productos completos, con los IDs de sus ediciones en los manifiestos y con las decisiones justificadas.
4. Para cada fuente, revisa paginación, resultados publicados, ediciones discontinuadas y desgloses complementarios. Haz la misma ronda para las 17 comunidades y las dos ciudades autónomas, diputaciones, cabildos, consejos insulares, institutos estadísticos y ayuntamientos con series propias. Enlaza las publicaciones duplicadas y conserva las series territoriales complementarias dentro del tema.
5. Recorre las filas por su estado real. Continúa integrando cualquier fila que puedas resolver en el mismo encargo. Registra con evidencia los impedimentos y agota opciones oficiales como archivos históricos, servicios alternativos, descargas manuales legítimas o consulta tabular. Un ámbito sin mapa puede seguir teniendo ficha, filtros y exportación de serie. Una fase queda abierta mientras quede una edición pertinente sin integrar o un impedimento.
6. Sustituye cada casilla por evidencia concreta al cerrarla. Registra producto activo, ediciones, ámbitos, cifras de contraste, pruebas y enlaces a sus fuentes. Conserva el enlace a la revisión anterior cuando exista. La publicación por Actions se verifica aparte si forma parte del encargo.

## Estado de partida

| Fascículo | Estado al comienzo de esta revisión |
| --- | --- |
| F00 | Base de Fuentes operativa. Quedan clasificación individual de los inventarios amplios, licencias y distribuciones por verificar, relaciones de publicadores y el estado comprobable de cierre por fascículo. |
| F01 | Parcial. Está operativa la composición del atlas, la cartografía básica y territorial, capas locales, series históricas seleccionadas y una parte amplia del inventario de servicios. |
| F02 | Parcial. 66 tablas INE con 68.090.658 observaciones, más el Nomenclátor y las fichas intercensales. |
| F03 | Parcial. 51 productos, 104 respuestas tabulares, 3.651.281 observaciones. La deuda de datos se detalla abajo. |
| F04 | Parcial. 15 tablas del INE, 338.935 observaciones y tres productos del SEPE con 70.990.402 observaciones municipales. |
| F05–F29 | Los inventarios de estos fascículos siguen por completar. F16, F22, F24 y F26 ya tienen referencias disponibles a algunas capas base o productos compartidos. Conserva esos enlaces y verifica cada nueva ficha individualmente. |

Los números proceden de la captura de trabajo. Diferentes inventarios se solapan y los recuentos de tablas, operaciones, fichas y observaciones miden cosas distintas. Confirma en Git y en el sitio público qué revisión está desplegada si el encargo incluye publicar.

## F00 · Catálogo común · `datos/catalogo/`

Punto de partida: [estado de F00](docs/F00.md), [inventario compilado](datos/catalogo/index.json), [configuración de productos](registry/products.json), [revisiones](registry/reviews.json), [metadatos de investigación](datos/catalogo/investigacion/) y `scripts/build_registry.py`.

- [ ] Revisar las operaciones del IOE frente a INEbase y las publicaciones de sus responsables, conservando el código de operación y enlazando sus resultados, metodología, catálogo nacional y organismo real. La captura contiene 758 operaciones y 6.913 tablas INE. Completar los enlaces por código; tratar variantes y operaciones descontinuadas.
- [ ] Para los 116.236 títulos federados de la captura, comprobar cuáles siguen publicados, cubrir los cambios en el nuevo inventario y enumerar las distribuciones. Reintentar, entre otras, las 306 fichas sin coincidencia en la revisión de metadatos. Recuperar licencias, cobertura y periodicidad desde las fichas y distribuciones que las declaren. Revisar los posibles duplicados y relaciones entre organismos o publicadores del mismo recurso.
- [ ] Revisar los 238 publicadores federados y las 182 fichas editoriales, y completar lo que aporten los catálogos oficiales no federados. Confirmar los enlaces de las administraciones autonómicas y locales, responsables, cambios de nombre y alternativas oficiales de los accesos fallidos.
- [ ] Clasificar cada recurso por producto y tema a partir del contenido y las variables originales. Documentar destinos múltiples con una ficha canónica. Incorporar PEN e IDEE a la trazabilidad común cuando aporten información. Las tablas y capas asignadas se integran en su fascículo temático.
- [ ] Completar el estado de cierre verificable del catálogo. Distinguir metadatos revisados y producto integrado, y cotejar filtros, paginación, procedencia y enlaces de «Fuentes». Mantener cobertura e historial con el generador y validar los enlaces a acciones de mapa. Publicar inventarios fechados de revisión y método de actualización.

## F01 · Territorio, cartografía y mapa base · `datos/territorio/`

Punto de partida: [estado de F01](docs/F01.md), [geometría del atlas](docs/ATLAS.md), [inventario de servicios](datos/territorio/official-wms.json), [capas habilitadas](datos/territorio/official-layers.json), [manifiesto](datos/territorio/manifest.json) y [productos](registry/territory-products.json).

- [ ] Resolver las 250 entradas del inventario de servicios pendientes en la captura, incluidas las 133 capas con imagen que no se puede cargar desde el visor público. Revisar el diagnóstico por capa, URL, escala, cabeceras y origen. Probar WMS, WMTS, WFS, OGC API o descarga oficial compatible, y preservar las condiciones de uso. Anotar por separado disponibilidad de imagen y consulta de atributos.
- [ ] Inventariar y completar por organismo las ortofotos PNOA y autonómicas, vuelos y mosaicos históricos, relieve, MDT, curvas y puntos, superficies LiDAR, mapas topográficos, callejeros, etiquetas y mapas de contexto. Comprobar CRS, edición, resoluciones y escala útil. Incluir las distribuciones que publiquen los servicios oficiales completos, incluidos Fototeca y mosaicos. Conservar un selector global de mapas base, ajuste de tierra y mar, y controles utilizables en el visor.
- [ ] Completar límites actuales e históricos, y las ediciones documentadas de municipios, provincias, comunidades, ciudades autónomas, islas y otros territorios. Partir de las 14 tablas de cada GeoPackage del CNIG de 2023 y 2024 ya integradas. Buscar nuevas ediciones y series anteriores, incluida la trazabilidad geográfica de códigos que cambian, se segregan o se fusionan. Revisar [decisiones y fuentes de las ediciones](registry/cnig-history.json) y `territory_cnig_history.py`. Diferenciar líneas oficiales de geometrías derivadas, límites en vigor y trazados históricos.
- [ ] Completar división supramunicipal, foral, comarcal, insular y local. Priorizar cuadrillas y concejos de Álava y el resto de divisiones advertidas en la ficha F01. Comprobar comunidad a comunidad los ámbitos administrativos, estadísticos y funcionales y cómo se diferencian por autoridad. Revisar los distritos, barrios y subdivisiones más pequeñas, sus versiones y equivalencias. Los paquetes comprobados de Madrid, Barcelona, València, Zaragoza, Málaga y Asturias dan modelos que deben mantenerse.
- [ ] Enumerar todo el archivo censal con [section-archives.json](registry/section-archives.json) y [section-vectors.json](datos/territorio/section-vectors.json). Contrastar las 25 descargas anunciadas y los archivos nacionales ya materializados de 2003–2006 con los servicios remotos de otras ediciones. Garantizar selección, descarga de geometría e identificación por año y código. Preparar la unión con los censos F02 y el Atlas de renta F03 con la misma fecha o correspondencia oficial.
- [ ] Completar direcciones, portales, edificios, núcleos, entidades de población y toponimia pública. Conciliar los códigos del Nomenclátor con CartoCiudad, NORA y otros callejeros autonómicos o locales, incluyendo registros sin coordenadas que sí se puedan consultar. Abordar parcelas, construcciones, direcciones y zonas de la DGC y cada catastro foral, con ámbito y licencias propios.
- [ ] Comprobar la representación diferenciada de cada jerarquía, posiciones originales en descarga, ficha, búsqueda, zoom útil y accesibilidad de los ajustes. Verificar arrastre y salida de los marcos al hacer zoom, y cobertura en península, archipiélagos y ciudades autónomas. Las delimitaciones marítimas oficiales se enlazan desde F19.

## F02 · Población, hogares y migraciones · `datos/poblacion/`

Punto de partida: [F02](docs/F02.md), [inventario INE](datos/poblacion/ine/inventory.json) de 2.173 tablas distintas de 18 operaciones en la captura, [índice implementado](datos/poblacion/ine/index.json), [configuración](registry/demography-tables.json) y `scripts/demography_collect.py`.

- [ ] Comparar por ID el inventario temático y el índice. Revisar el resto de tablas de censos y Padrón, composición y relaciones del hogar, estado civil, tipos de familia y convivencia, estructuras por sexo, edad, nacionalidad y nacimiento. Cubrir los años y escalas publicados, hayan aparecido o no en la primera selección.
- [ ] Completar Estadística Continua de Población, Padrón de residentes en el extranjero, Nomenclátor y censos históricos frente a sus ediciones publicadas. Revisar municipios históricos y entidades singulares. Enlazar la serie por edición al polígono local de F01 cuando exista. Conservar la consulta por código aunque un municipio disuelto carezca de límite válido.
- [ ] Completar movimiento natural, estimaciones semanales disponibles, natalidad, defunciones, mortalidad, fecundidad, nupcialidad e indicadores detallados, con unidades y bases publicadas. Completar migración interior y exterior, migraciones antiguas, cambios de metodología, saldos y otras proyecciones de población y hogares, incluidos todos los escenarios oficiales de sensibilidad.
- [ ] Enlazar las seis tablas nacionales de población por sección censal y las demás tablas de sección o distrito al seccionado de su edición. Revisar el significado de cada código, cubrir los desencajes con un registro auditable y conservar la consulta tabular. Comprobar los diferentes calendarios de censo, geometría, padrón y fecha de referencia.
- [ ] Incorporar los productos administrativos del [OPI](https://www.inclusion.gob.es/es/web/opi/estadisticas/catalogo) sobre residencia, estudios, concesiones y nacionalidad. Añadir las distribuciones oficiales de [Interior sobre asilo, protección internacional, apatridia y protección temporal](https://www.interior.gob.es/opencms/es/archivos-y-documentacion/documentacion-y-publicaciones/publicaciones/publicaciones-descargables/publicaciones-periodicas-anuarios-y-revistas/asilo-en-cifras/). Separar stocks, concesiones, personas, solicitudes y flujos por su unidad y definición.
- [ ] Completar los datos de institutos estadísticos y portales autonómicos, insulares y locales y los complementarios de Eurostat. Agrupar productos compatibles. Comprobar pirámides, densidad con denominador identificado, saldos, cronograma y series de los territorios de referencia.

## F03 · Renta, pobreza, consumo y condiciones de vida · `datos/renta/`

Punto de partida: [F03](docs/F03.md), [inventario INE](datos/renta/ine/inventory.json), [índice integrado](datos/renta/ine/index.json), [productos por grupo](registry/welfare-tables.json), [fichas externas](registry/welfare-external.json) y `scripts/welfare_collect.py`.

- [ ] Completar todas las familias locales del Atlas de distribución de renta, incluidos Gini/P80-P20, fuentes de ingresos y umbrales fijos y relativos en municipios, distritos y secciones. Enumerar las publicaciones territoriales y revisar todas sus variables de sexo, edad, nacionalidad y hogares. La descarga técnica de la API y las fichas territoriales pueden tener coberturas distintas. Distinguirlas en la procedencia sin perder datos.
- [ ] Completar ECV y EPF por edición, módulos especiales, cambios metodológicos, series discontinuadas, gasto, composición, distribución, carencias y tasas. Mantener año de encuesta y año de ingresos separados, escalas de equivalencia y clasificadores COICOP, bases y precisión. Completar las demás tablas de calidad de vida, hábitos, equipamiento y uso del tiempo.
- [ ] Verificar las geometrías por edición para renta de distritos y secciones y enlazarlas a partir del trabajo F01. Mantener una ficha temporal territorial. Contrastar con valores oficiales nacionales, autonómicos, municipales y de sección antes de activar cada escala.
- [ ] Resolver el [Anuario masivo de AEAT](https://sede.agenciatributaria.gob.es/Sede/estadisticas/anuario-estadistico/acceso-descarga-masiva-datos.html) y los [anexos municipales de declarantes de IRPF](https://www3.agenciatributaria.gob.es/Sede/datosabiertos/catalogo/hacienda/Estadistica_de_los_declarantes_del_IRPF_por_municipios.shtml). Localizar los diccionarios completos de variables `MUNI_n` y de identificadores `MUNI_DEF`; cotejar cada edición y código. Contrastar totales con anexos oficiales. Evaluar ingestión directa por anexos u observaciones tabulares si el código municipal normalizado falta. Mantener renta por declaración, renta disponible, cobertura del régimen común y publicaciones forales con sus propios denominadores.
- [ ] Completar distribuciones de institutos autonómicos, haciendas forales y observatorios locales, incluidos los datos de territorios ausentes de operaciones estatales. Revisar CIS, servicios de consumo, Eurostat y OCDE por producto. Integrar solo las agregaciones publicadas, manteniendo muestras, comparabilidad y precisión.
- [ ] Probar todas las dimensiones, años, fuentes y CSV desde un único panel temático de Renta. Comprobar ausencia, solapamientos entre API y sedes oficiales y ruptura metodológica. Confirmar que cada ficha derivada usa el mapa, gráfico o tabla que corresponde a su ámbito real.

## F04 · Trabajo, empleo, salarios y relaciones laborales · `datos/trabajo/`

Punto de partida: [F04](docs/F04.md), [inventario INE](datos/trabajo/ine/inventory.json), [índice INE](datos/trabajo/ine/index.json), [índice SEPE](datos/trabajo/sepe/sepe.json), [configuración](registry/labor-tables.json), `labor_collect.py` y `sepe_collect.py`.

- [ ] Completar por ID las tablas restantes de EPA, EAES y ETCL. La captura tiene 1.124 referencias en esas tres operaciones. Revisar tablas y clasificaciones anteriores, periodicidad anual y trimestral, salarios, SMI, desigualdad, jornada, vacantes y costes. La API devolvió una descarga vacía para la tabla INE 80180 en la revisión anterior; verificar la ficha web, exportaciones y fuentes oficiales alternativas y documentar el resultado.
- [ ] Resolver diciembre de 2020 en demandantes de empleo. Contrastar las distribuciones nacionales de [datos.gob.es](https://datos.gob.es/es/catalogo/ea0041513-demandantes-de-empleo-por-municipio), XLS semestrales, archivo mensual del [SEPE](https://www.sepe.es/HomeSepe/que-es-el-sepe/estadisticas/datos-estadisticos/municipios.html), anuarios y archivos autonómicos. El libro mensual conocido completó paro y contratos, ambos con 250 meses entre 2006M01 y 2026M10; demandantes dispone de 249. Incorporar solo las cifras oficiales verificadas con códigos, definición y URL de edición. Si falta una edición documenta el intento con URLs y cobertura, sin sustituirla por paro ni inventar cifras.
- [ ] Completar los productos del SEPE distintos de las tres series municipales, incluidos desgloses por ocupaciones y colectivos publicados, prestaciones laborales donde correspondan, contratación, temporalidad y movilidad. Integrar los servicios autonómicos de empleo. Enlazar prestaciones y beneficiarios a F05 según el indicador canónico. Preservar original y estados de supresión, incluido «<5».
- [ ] Incorporar [Seguridad Social](https://www.seg-social.es/wps/portal/wss/internet/EstadisticasPresupuestosEstudios): afiliación, series diarias y mensuales en su ámbito, régimen y colectivos, autónomos/RETA y desgloses por sexo, edad, actividad y territorio cuando existan. Mantener afiliaciones, afiliados, medias y fin de mes como medidas distintas, así como centro de trabajo y residencia. Completar fuentes de empleo público y privado y enlazar directorios de F28.
- [ ] Incorporar las estadísticas de Trabajo sobre convenios, negociación colectiva, huelgas, expedientes de regulación y condiciones laborales; accidentes y enfermedades profesionales de Trabajo/INSST y las prestaciones de FOGASA. Reunir series autonómicas, Eurostat y OIT pertinentes, con unidades, códigos y ruptura oficial de las series.
- [ ] Probar cronograma por frecuencia, filtros por edición, desglose municipal y CSV con la fuente correcta. Verificar capas a escala municipal, consulta de códigos históricos, fechas sin dato, abreviaturas y contrastes entre paro registrado, tasa EPA y demandantes. Conservar como referencia Abla en 2020M12, 88 parados registrados y 18 contratos, con sus descargas oficiales.

## F05 · Pensiones, protección social, cuidados e igualdad · `datos/cuidados/`

- [ ] Enumerar y descargar pensiones, afiliaciones que actúen como denominador, incapacidad, prestaciones contributivas y no contributivas, IMV, rentas mínimas y prestaciones por desempleo. Fuentes: Seguridad Social, SEPE, INE y organismos de inclusión. Mantener beneficiarios, prestaciones, cuantías, solicitudes y resoluciones por separado. Referenciar el empleo de F04.
- [ ] Integrar IMSERSO, Derechos Sociales y sistemas autonómicos y locales: dependencia, discapacidad, residencias, servicios sociales, centros de día, atención en domicilio, infancia, juventud y envejecimiento. Localizar equipamientos públicos y mostrar plazas, listas de espera y cobertura como medidas diferentes. Incluir ediciones y cambios de definición.
- [ ] Integrar igualdad, brechas y violencia de género de los organismos de igualdad, mujeres, justicia y administraciones territoriales, en el nivel de agregación publicado. Verificar denominadores y estados. Enlazar las fichas de población, salud y justicia, y comprobar que ninguna persona se cuenta dos veces por sumar programas compatibles.

## F06 · Vivienda, suelo y organización urbana · `datos/vivienda/`

- [ ] Recorrer Vivienda y Agenda Urbana, INE, Banco de España, Catastro, registradores cuando se trate de estadísticas públicas y autoridades territoriales. Integrar parque, ocupación, vivienda vacía, alquiler, precio por superficie, compraventa, tasaciones, transmisiones, hipotecas, protección pública y esfuerzo residencial. Mantener alquiler declarado, oferta, valores fiscales, tasados y de compraventa como conceptos distintos.
- [ ] Incorporar suelo, construcción, rehabilitación, vulnerabilidad, planeamiento y usos urbanos, catálogos urbanísticos y equipamientos de proximidad. Revisar ediciones, escala y vigencia de cada administración. Relacionar con parcelas y límites de F01. Identificar si un plano es informativo, publicado oficialmente, aprobado o en trámite.
- [ ] Probar escala de precios y superficies, periodos de referencia, geometrías y consulta municipal/sección. Conservar las series por comunidad que utilicen definiciones propias y las notas sobre ámbitos con muestras insuficientes.

## F07 · Economía, empresas, industria y producción · `datos/economia/`

- [ ] Inventariar cuentas territoriales, PIB y valor añadido, productividad, tejido empresarial, demografía y tamaño de empresas, economía social, industria, minería no energética, actividad de servicios e internacionalización. Revisar INE, Industria, Trabajo, AEAT, institutos autonómicos, administraciones locales, Eurostat y OCDE.
- [ ] Completar todas las ediciones y medidas de PIB, rendimientos, sectores, actividad, volumen, ocupación, tamaño y forma jurídica. Diferenciar establecimientos, empresas y sedes, productos y actividades, precios corrientes y volúmenes encadenados. Mantener versiones CNAE y bases de índice.
- [ ] Implementar mapas y series por escala real. Validar totales territoriales y cambios de clasificación. Enlazar operaciones laborales de F04, registros fiscales de F09 y minería energética de F21.

## F08 · Precios, comercio, finanzas y seguros · `datos/comercio/`

- [ ] Inventariar IPC y precios, distribución comercial, comercio interior y exterior, operaciones por producto, origen y destino, e inversión exterior. Recorrer INE, Secretaría de Estado de Comercio, DataComex/DataInvex, Aduanas/AEAT, Eurostat y autoridades territoriales.
- [ ] Incorporar crédito, depósitos, oficinas, financiación, mercado de valores, seguros y fondos privados; juego, tabaco y productos regulados donde corresponda. Revisar Banco de España, BCE, CNMV, DGSFP, CNMC, Tesoro, DGOJ y Comisionado del Tabaco. Mantener saldos y flujos separados y preservar frecuencia, moneda y base.
- [ ] Diferenciar origen aduanero, localización de la empresa y mercado de destino. Aplicar fichas nacionales cuando proceda. Enlazar precios canónicos de F06, F14 y F21 sin duplicarlos.

## F09 · Hacienda, presupuestos, fiscalidad y deuda pública · `datos/hacienda/`

- [ ] Completar ingresos, impuestos, recaudación, presupuestos, ejecución, gasto funcional, déficit, deuda, financiación territorial y cuentas públicas. Revisar Hacienda, IGAE, AEAT, AIReF, Tesoro, Banco de España, haciendas forales y portales autonómicos y locales.
- [ ] Normalizar niveles de administración, entidades, ejercicio, devengo y caja, fase presupuestaria, consolidación, función y unidades. Distinguir previsión, aprobado, modificado, obligado y pagado. Relacionar las versiones de clasificaciones y todas las ediciones.
- [ ] Representar el territorio beneficiario solo cuando conste. Validar cifras de contraste en niveles estatal, autonómico y local. Enlazar declaraciones de renta de F03 y contratación y financiación de F10.

## F10 · Contratación, subvenciones y proyectos financiados · `datos/ayudas/`

- [ ] Enumerar PLACSP, BDNS, TED, Kohesio, fondos europeos, Cooperación Española y plataformas públicas territoriales. Importar licitación, lotes, adjudicación, formalización, modificaciones, convocatorias, concesiones y pagos cuando se publiquen.
- [ ] Enlazar registros por identificador de expediente, lote, convocatoria o concesión; conservar estados, importes, fechas e historial. Comprobar origen, moneda, criterio territorial y límites de uso y publicación de datos personales. Relacionar cada proyecto con su financiación sin sumar dos veces notificaciones y adjudicaciones.
- [ ] Situar puntos o regiones sobre el lugar de ejecución identificado. Mantener una ficha tabular cuando solo se conozca la sede. Enlazar AEI/CDTI/CORDIS a F12 y ayudas agrarias a F14.

## F11 · Educación, formación y universidad · `datos/educacion/`

- [ ] Enumerar Ministerio de Educación y Formación Profesional, Universidades, INE, estadísticas de consejerías, centros y universidades públicas y Eurostat por producto. Integrar centros, etapas, enseñanzas, FP, matrículas, profesorado, resultados, becas, itinerarios, abandono, educación de adultos, recursos y oferta universitaria.
- [ ] Completar cada curso y cobertura, con códigos de centro, niveles y cambios de clasificación. Separar curso académico, año natural, curso de matrícula y cohorte de resultados. Distinguir sede del centro, ámbito del servicio y residencia del alumno cuando se publique.
- [ ] Probar búsqueda de centros, series y agregaciones con cobertura real, y enlaces a F02, F04, F12 y accesibilidad de F22.

## F12 · Ciencia, investigación, innovación y patentes · `datos/ciencia/`

- [ ] Enumerar INE, SICTI, AEI, CDTI, OEPM, CSIC, universidades y CORDIS. Integrar personal, gasto de I+D, innovación, centros e infraestructuras, convocatorias, proyectos y resultados, patentes y otras formas de propiedad industrial.
- [ ] Incorporar producción científica y repositorios públicos por su metadato, licencia y enlace. Diferenciar ubicación del investigador, centro, proyecto y solicitante de patente. Separar solicitud, concesión, publicación y vigencia.
- [ ] Probar proyectos por convocatoria, territorio y estado. Vincular su financiación a F10 mediante identificadores exactos. Conservar licencias y acceso original de publicaciones y resultados.

## F13 · Salud, sanidad, epidemiología y alimentación saludable · `datos/salud/`

- [ ] Inventariar Sanidad y los servicios autonómicos, ISCIII/CNE, AEMPS, ONT, AESAN, OEDA, INE, ECDC y OMS. Incorporar hospitales, atención primaria, centros, oferta y personal, actividad, listas de espera, gasto, enfermedades, vigilancia, medicamentos, trasplantes, adicciones, nutrición y seguridad alimentaria.
- [ ] Conservar fecha de medición, publicación y validación, definiciones de caso, población de referencia, unidades y periodicidad. Diferenciar incidencia, prevalencia, mortalidad, recuento, tasa y estimación. Revisar notas metodológicas y supresiones oficiales.
- [ ] Probar puntos de centros y series agregadas por ámbito sanitario publicado. Registrar territorios y periodos ausentes. Relacionar población de F02, cuidados de F05 y alimentación de F14.

## F14 · Agricultura, ganadería, pesca, alimentación y medio rural · `datos/medio-rural/`

- [ ] Inventariar MAPA, FEGA/SIGPAC, SIAR, SIGA, AICA, ENESA, INE, autonomías, IEO y FAO. Integrar cultivos, superficies, rendimientos, campañas, regadío, explotaciones, cabaña, producción y precios, industria y cadena alimentaria, ayudas, seguros, capturas, flota y acuicultura.
- [ ] Incorporar desarrollo rural, pastos y usos, recintos publicados y caminos naturales por sus ediciones. Distinguir campaña y año, captura y desembarque, especie, producto, unidades, precio en origen y fase de la cadena. Identificar cambios de metodología y ámbitos pesqueros.
- [ ] Vincular ayudas F10, estaciones SIAR F17, áreas marítimas F19 y rutas F22/F26. Verificar superficies, unidades, campañas y los permisos de reutilización del parcelario.

## F15 · Naturaleza, biodiversidad, bosques y usos del territorio · `datos/naturaleza/`

- [ ] Recorrer MITECO, Parques Nacionales, GBIF.ES, IGN/CNIG, autoridades autonómicas, AEMA, JRC y Copernicus Land. Integrar hábitats, especies, observaciones, espacios protegidos, Red Natura, parques, inventarios forestales, usos/coberturas, restauración, fragmentación y ecosistemas.
- [ ] Conservar autoridad y vigencia de cada protección, escala y resolución, exactitud de observaciones y políticas de generalización publicadas. Distinguir cartografía de cobertura, inventario, distribución estimada y observación. Relacionar mallas y ediciones compatibles.
- [ ] Probar cronogramas de ediciones, fichas de recintos y resolución de mapas. Enlazar incendios y riesgos con F18, recursos agrícolas con F14 y hábitats marinos con F19.

## F16 · Agua continental, cuencas y acuíferos · `datos/agua/`

- [ ] Inventariar todas las confederaciones, administraciones hidráulicas autonómicas e insulares, MITECO, ACA, URA, Augas de Galicia, IGME y sistemas locales. Incorporar cuencas y demarcaciones, ríos, humedales, lagos, masas superficiales y subterráneas y acuíferos.
- [ ] Incorporar aforos, embalses, reservas, demandas y usos, abastecimiento, saneamiento, calidad, sequía, planificación e inundabilidad. Preservar códigos de estación y masa, unidad, estado hidrológico, día de medida, frecuencia y escala. Registrar los cambios de emplazamiento.
- [ ] Comprobar mapas y series para cada demarcación, incluidas las insulares. Enlazar avisos y observaciones de F17 y peligrosidad F18, sin atribuir a un municipio los totales de una cuenca.

## F17 · Tiempo, clima y cambio climático · `datos/clima/`

- [ ] Revisar AEMET, Meteocat, Euskalmet, MeteoGalicia, SIAR, otras redes oficiales, Oficina Española de Cambio Climático, C3S y JRC. Integrar estaciones, observaciones, predicciones, avisos, climatologías, extremos, índices, escenarios y proyecciones.
- [ ] Enumerar variables, estaciones, mallas, fechas y resoluciones, régimen de acceso y posibles claves de API. Conservar temperatura, viento, precipitación, nieve y demás unidades originales. Diferenciar referencia, emisión, validez, plazo, escenario y periodo climático.
- [ ] Verificar hora local/UTC, huecos, despliegue de raster, leyenda, actualidad y fechas correctas. Probar estaciones y superficies y enlazar datos de sequía F16, riesgos F18 y ambiente F20.

## F18 · Geología, suelos y riesgos naturales · `datos/geologia/`

- [ ] Enumerar IGME-CSIC, IGN, geoportales autonómicos, JRC y Copernicus Emergency. Incorporar litología, cartografía geológica y edafológica, geodiversidad, recursos del subsuelo, sismicidad, volcanismo y movimientos del terreno.
- [ ] Integrar mapas públicos de peligrosidad, exposición y riesgo. Separar un evento observado, la probabilidad a una escala y el escenario de planificación. Conservar geometría, fecha, resolución y edición; mantener metadatos de daños y eventos cuando se publiquen.
- [ ] Comprobar filtros temporales, fuentes de capas, escalas y consulta de eventos. Enlazar inundación F16, meteorología F17, incendios F15 y emergencias F29.

## F19 · Mar, litoral y oceanografía · `datos/mar/`

- [ ] Enumerar Instituto Hidrográfico de la Marina, Puertos del Estado, IEO-CSIC, UTM-CSIC, MITECO, Copernicus Marine y EMODnet. Integrar batimetría, cartas y cartografía hidrográfica, costa, dominio público, ámbitos marítimos oficiales, boyas y estaciones.
- [ ] Incorporar oleaje, mareas, corrientes, temperatura, salinidad, hábitats, calidad y seguimiento del medio marino por edición y cobertura. Conservar resolución, datum horizontal y vertical y fecha de validez. Distinguir observación, modelo y predicción.
- [ ] Habilitar consulta de las áreas marítimas oficiales relacionadas con España y comprobar que la máscara terrestre del atlas no tapa capas marinas al activarlas. Enlazar puertos, faros y navegación de F22, pesca de F14 y protección de F15.

## F20 · Aire, contaminación, residuos y presión ambiental · `datos/ambiente/`

- [ ] Enumerar MITECO, PRTR, CSN, INE, AEMA, CAMS y redes territoriales. Integrar estaciones, calidad del aire, emisiones, GEI, instalaciones y focos, ruido, residuos, reciclaje, plantas, suelos contaminados y vigilancia radiológica pública.
- [ ] Preservar unidad, sustancia, duración, estadístico, periodo, escala, validación y método. Distinguir valor medido, modelo y estimación de emisiones. Separar ubicación de una instalación y territorio afectado.
- [ ] Probar series de estaciones, leyendas por umbral y mapas continuos. Enlazar industria F07, clima F17 y energía F21, con una única fuente canónica.

## F21 · Energía y recursos energéticos · `datos/energia/`

- [ ] Revisar MITECO, IDAE, CORES, CNMC, autoridades territoriales y los operadores complementarios REData/eSIOS y Enagás. Incorporar generación, potencia instalada, demanda, consumo, renovables, hidrocarburos, gas, reservas, eficiencia, instalaciones y redes públicas.
- [ ] Integrar precios, puntos de suministro, gasolineras y recarga publicados. Conservar sistema, tiempo de referencia, resolución y estado estimado/real. Separar potencia de energía, consumo de producción y tarifa publicada de valor facturado.
- [ ] Probar escalas de ámbito eléctrico, consulta de instalaciones, series y signos. Enlazar comercio F08 y emisiones F20. Mantener identificada la naturaleza del organismo o del operador de cada producto.

## F22 · Transporte, movilidad, redes y logística · `datos/transporte/`

- [ ] Inventariar IGN, Transportes/OTLE, Punto de Acceso Nacional, DGT, Adif, Renfe, Aena, ENAIRE, Puertos del Estado y operadores públicos territoriales. Completar redes viarias, ferroviarias de todas las clases publicadas, caminos, estaciones, paradas, recorridos y servicios, incluido material histórico oficial.
- [ ] Incorporar horarios, movilidad, tránsito, vehículos, siniestralidad, aeropuertos, información aeronáutica pública, puertos, mercancías, faros y ayudas a la navegación. Distinguir ruta, tramo, servicio, frecuencia, viaje y aforo. Preservar estados de infraestructuras y ediciones de horarios.
- [ ] Probar continuidad y atributos de redes, consulta de enlaces y desgloses territoriales. Referenciar rutas, senderos y caminos canónicos con F14, F24 y F26 y activos portuarios con F19.

## F23 · Conectividad, telecomunicaciones y sociedad digital · `datos/conectividad/`

- [ ] Inventariar Secretaría de Estado de Telecomunicaciones/Conectemos, Red.es/ONTSI, CNMC, INE y autoridades autonómicas y locales. Integrar banda ancha, móvil, despliegue, servicios, infraestructuras publicables, acceso y uso, equipamiento TIC, competencias, brecha digital y digitalización.
- [ ] Distinguir cobertura declarada, servicio disponible, contratación y uso medido. Conservar tecnología, velocidad, resolución, fuente, fecha, método y unidad. No ampliar el ámbito de las encuestas a áreas demasiado pequeñas.
- [ ] Validar mallas, búsqueda territorial, series de cobertura y cambios de tecnología o estrato. Enlazar digitalización empresarial con F07.

## F24 · Turismo, destinos y alojamientos · `datos/turismo/`

- [ ] Revisar INE, Turespaña, SEGITTUR y administraciones y observatorios territoriales. Incorporar viajes, visitantes, gasto, ocupación, alojamientos, registros, plazas, estacionalidad, empleo turístico, destinos, recursos y rutas oficiales.
- [ ] Diferenciar turista, excursionista, viajero y residente, origen y destino, plaza y pernoctación, vivienda turística y establecimientos. Conservar estados de registro, ámbito de la encuesta, frecuencia y metodología.
- [ ] Probar establecimientos, datos nacionales y locales y series comparables. Vincular recursos de F15, rutas de F22/F26, empleo de F04 y sitios de F25 mediante sus fichas canónicas.

## F25 · Cultura, patrimonio, archivos, memoria y diversidad religiosa · `datos/cultura/`

- [ ] Recorrer CULTURABase, BNE, PARES, IPCE, Memoria Democrática, Observatorio del Pluralismo Religioso y administraciones territoriales. Integrar bienes, museos, bibliotecas, archivos, patrimonio documental, actividades, industrias, empleo y hábitos culturales.
- [ ] Incorporar lugares de memoria, fosas y centros de culto publicados con procedencia, vigencia y condiciones de uso. Revisar los accesos fallidos en la investigación. Asociar documentos solo a geografías justificadas por el original.
- [ ] Probar puntos, recintos, referencias documentales y series. Mantener licencias y créditos por recurso, y relacionar con turismo F24 y empleo F04.

## F26 · Deporte, ocio y actividades al aire libre · `datos/deporte/`

- [ ] Enumerar CSD/DEPORTEData, organismos territoriales, IGN, MAPA y gestores públicos. Incorporar instalaciones, licencias, clubes, práctica, gasto, empleo, competiciones y actividades publicadas.
- [ ] Completar grandes recorridos, senderos, itinerarios, equipamientos, señalización y accesibilidad oficiales. Preservar nombre, entidad responsable, tramo, fecha de edición y estado publicado.
- [ ] Probar itinerarios y fichas consultables, y distinguir disponibilidad y condiciones de un recorrido. Enlazar caminos y rutas de F14, F22 y F24 mediante el mismo objeto de origen.

## F27 · Elecciones y representación política · `datos/elecciones/`

- [ ] Enumerar Interior/Infoelectoral, autoridades electorales, Congreso, Senado, cámaras territoriales y portales autonómicos. Revisar el acceso alternativo oficial cuando una página falle. Integrar elecciones europeas, generales, autonómicas y locales disponibles, incluyendo todas las convocatorias y niveles publicados.
- [ ] Preservar censo, participación, votos, blancos, nulos, candidaturas, escaños y reglas por proceso, y composición y actividad representativa publicadas. Distinguir provisional, definitivo, repetición, convocatoria, circunscripción y agregado. Mantener evolución de candidaturas con identificadores y equivalencias verificadas.
- [ ] Probar mapas, leyendas, cronograma por convocatoria, fichas y contrastes de participación y escrutinio. Respetar el nivel público mínimo, límites por edición y supresiones.

## F28 · Administración, organización territorial y normativa · `datos/administracion/`

- [ ] Revisar Registro de Entidades Locales, DIR3, Función Pública, INVENTE, Portal de Transparencia, BOE y boletines y registros territoriales. Incorporar entidades, unidades, sedes, servicios, empleo público, estructura del sector público, normativa y disposiciones.
- [ ] Mantener jerarquías, vigencia, competencia, ámbito, organismo antecesor/sucesor y fuente. Distinguir sede, zona servida y demarcación oficial. Mantener relaciones de normativa por fecha y alcance, con geometría solo cuando exista una correspondencia verificable.
- [ ] Comprobar enlaces, búsqueda e historial institucional. Vincular presupuestos F09, contratación F10, personal F04 y límites geométricos F01.

## F29 · Justicia, seguridad, emergencias y defensa pública · `datos/justicia/`

- [ ] Revisar CGPJ, Fiscalía, Interior, Instituciones Penitenciarias, Defensa y autoridades territoriales. Incorporar organismos, demarcaciones, actividad judicial y fiscal, criminalidad agregada, estadísticas penitenciarias, protección civil, emergencias y estadísticas públicas de defensa dentro de su cobertura y licencia.
- [ ] Mantener diferencias entre denuncia, hecho, procedimiento, resolución y sentencia. Preservar demarcaciones y ediciones, medidas absolutas y tasas, revisiones y metodologías. Mantener los niveles de agregación publicados.
- [ ] Probar consulta de demarcaciones, recursos y series, y reconciliar cifras publicadas por ámbito. Enlazar igualdad y violencia de género F05, protección internacional F02 y riesgos naturales F18.

## Verificación transversal antes de cerrar

- [ ] Revisar cada producto y edición contra su original. Confirmar fuentes completas, IDs estables, periodos, filtros, unidades, comprobaciones de integridad, cobertura, disponibilidad y casos de ausencia.
- [ ] Comprobar la consulta desde el menú temático y desde Fuentes. Verificar el mapa base, la leyenda, la superposición, reguladores, cronograma, ficha y descarga según el tipo de producto.
- [ ] Probar escritorio y móvil, ortofoto y contraste con otros fondos, territorios peninsulares e insulares, y al menos un caso de ausencia o histórico cuando exista.
- [ ] Ejecutar `npm run catalog:build`, `npm test` y `npm run build`. Añadir pruebas cuando falte cobertura de una regresión concreta. Confirmar que las observaciones se sirven bajo `datos/` y que el sitio abre en la raíz de Pages.
- [ ] Actualizar la matriz, la ficha de la fase y esta lista con la fecha y la evidencia de cierre. Registrar los impedimentos que sigan abiertos y su siguiente acción concreta.
