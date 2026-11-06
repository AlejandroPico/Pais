# El país · Plan de fascículos

**Propuesta de integración: 6 de noviembre de 2026.** Basada en la [investigación del 5 de noviembre](research/README.md). Estado: planificación; este documento no incorpora nuevas capas ni modifica el diseño.

## Decisión general

Organizar el trabajo en **30 entregas: una base común (F00) y 29 fascículos temáticos (F01–F29)**. Son unidades de trabajo, no treinta botones nuevos en la página. El catálogo visible se organizará mediante categorías, subcategorías y filtros que se concretarán en el siguiente trabajo de diseño.

La unidad de consulta será el **tema y el indicador**, no el organismo que los publica. INE, ministerios, comunidades, diputaciones y ayuntamientos alimentarán un mismo catálogo temático. Los portales europeos y las fuentes internacionales se repartirán también por tema; no tendrán un fascículo separado que repita los datos españoles.

Ejemplo: **Vivienda → Alquiler → indicador → periodo → ámbito territorial**. Los recursos de Madrid y Cataluña se encontrarán juntos en Vivienda. Se conservarán el publicador, el territorio y la metodología de cada recurso. Cataluña, la provincia de Barcelona y el municipio de Barcelona son ámbitos distintos. Si dos productos miden conceptos diferentes, aparecerán como indicadores diferentes dentro del mismo tema; no se unirán sus cifras artificialmente.

## Cómo incorporar un servicio por completo

Un organismo puede publicar muchos temas. No intentaremos integrar todo el INE en una sola entrega: sus productos de población se completarán en F02, los de trabajo en F04, los de salud en F13, etc. Un servicio especializado, como una confederación hidrográfica, tendrá la mayor parte de sus productos en F16 y referencias a otros fascículos cuando corresponda.

En cada fascículo se seguirá el mismo recorrido:

1. **Delimitar el inventario:** enumerar los productos de esa familia en cada fuente y fijar la fecha de revisión, incluyendo series históricas y productos descontinuados que sigan publicados. Conservar la relación entre catálogo, conjunto, distribución, tabla e indicador para no contar lo mismo varias veces.
2. **Revisar el contenido completo:** variables, dimensiones, periodos, territorios, formatos, condiciones de uso y acceso. Una tabla no se considerará integrada por haber importado una sola columna o el último año.
3. **Unificar los conceptos compatibles:** códigos territoriales, unidades, periodos y definiciones. Conservar las variantes metodológicas y los cambios de serie. Si hay duplicados, identificar su origen y escoger una presentación principal justificada, manteniendo la procedencia alternativa.
4. **Integrar por lotes comprobables:** descargar, transformar, representar, consultar y verificar cada producto. Las entregas grandes podrán publicarse como F16.1, F16.2, etc., conservando el alcance y los pendientes del fascículo completo.
5. **Publicar una ficha de cobertura:** qué productos funcionan, qué años y territorios cubren, qué no tiene dato y qué sigue pendiente. Las nuevas publicaciones de una fuente reabrirán su inventario; «completo» siempre se referirá a una revisión fechada.

Estados del inventario: **por revisar → revisado → en integración → integrado**. Los productos con impedimentos tendrán el estado **bloqueado**, con causa y siguiente acción. Los que no proceda integrar tendrán una justificación concreta: duplicado identificado, fuera del ámbito español, ausencia de permiso de reutilización, etc. Un bloqueo o una descarga parcial no contarán como integración completa.

No todo se representará coloreando municipios: habrá polígonos, puntos, redes, superficies continuas, imágenes y series. Un dato exclusivamente nacional se consultará en la ficha de España o en un gráfico, sin inventar un reparto municipal. Los documentos sin datos estructurados se registrarán y enlazarán; extraer sus tablas será un trabajo identificado, no una incorporación ficticia al mapa.

## Orden de las entregas

El orden propone empezar por lo que facilita el resto y después recorrer familias completas. Cada entrega temática usa F00 y F01. Los históricos, las fuentes autonómicas y locales, la consulta al pulsar y la procedencia forman parte de **cada** entrega desde el principio.

### F00 · Base común del catálogo y de la integración

- **Contenido:** inventarios de fuentes y productos, categorías, indicadores, dimensiones, licencias, procedencia, cobertura, fechas, estados y actualizaciones. Reparto de los catálogos generales por tema y detección de duplicados.
- **Fuentes:** datos.gob.es, IOE, Plan Estadístico Nacional, IDEE y catálogos generales estatales, autonómicos y locales. La API INEbase y el IOE se mantendrán como inventarios distintos.
- **Resultado:** una forma común de incorporar cualquier fuente, un registro de pendientes y una ficha de cobertura por fascículo. No requiere descargar todos los datos para abrir la web.

### F01 · Territorio, cartografía y mapa base

- **Contenido:** relieve, ortofoto, callejero, costa terrestre, límites del país, comunidades, provincias, municipios, entidades de población, secciones y otras divisiones publicadas; direcciones, edificios y parcelas públicas no protegidas. Comarcas y divisiones insulares según la autoridad competente.
- **Fuentes:** IGN/CNIG, CartoCiudad, Catastro y fuentes catastrales competentes, institutos cartográficos y geoportales autonómicos, entidades locales y GISCO cuando aporte correspondencias útiles.
- **Integración:** jerarquía de límites distinguible, búsqueda y selección territorial, niveles adecuados al zoom y versiones temporales de las geometrías. España como protagonista, incluyendo islas, Ceuta y Melilla; contexto vecino atenuado. La geometría de una parcela no incorpora automáticamente información protegida de sus titulares.

### F02 · Población, hogares y migraciones

- **Contenido:** censos y padrón, población residente, estructura por edad y sexo, nacionalidad, lugar de nacimiento, hogares y familias, nacimientos, defunciones, matrimonios, fecundidad, movimientos migratorios y despoblación; extranjería y protección internacional según su definición.
- **Fuentes:** INE, Observatorio Permanente de la Inmigración, Interior y estadísticas autonómicas y locales; Eurostat para productos comparables o complementarios.
- **Integración:** series y pirámides territoriales, densidades con superficie identificada, cambios demográficos e históricos completos disponibles. Las estadísticas administrativas de residencia o asilo no se confundirán con los recuentos de población.

### F03 · Renta, pobreza, consumo y condiciones de vida

- **Contenido:** renta personal y de hogares, distribución, desigualdad, pobreza y privación, gasto familiar, consumo, equipamiento de hogares, uso del tiempo, calidad de vida, hábitos y percepciones sociales con cobertura territorial publicada.
- **Fuentes:** INE, AEAT, CIS, servicios de consumo, institutos autonómicos y observatorios locales; Eurostat y OCDE cuando proceda.
- **Integración:** indicadores comparables por territorio y año, distinguiendo renta bruta/neta, persona/hogar, media/mediana y resultados de encuestas. No se ubicarán respuestas individuales en el mapa.

### F04 · Trabajo, empleo, salarios y relaciones laborales

- **Contenido:** actividad, ocupación, paro, contratos, afiliación, salarios y costes laborales, autónomos, empleo público y privado, negociación colectiva, huelgas, expedientes laborales, accidentes, enfermedades profesionales y garantías salariales.
- **Fuentes:** INE, Trabajo, SEPE, Seguridad Social, INSST, FOGASA y servicios autonómicos de empleo; OIT y Eurostat como complemento temático.
- **Integración:** separar paro registrado y estimaciones de encuestas, residencia del trabajador y ubicación del empleo; enlazar profesiones, sectores y colectivos cuando el producto lo permita.

### F05 · Pensiones, protección social, cuidados e igualdad

- **Contenido:** pensiones, prestaciones contributivas y no contributivas, desempleo protegido, ingreso mínimo, dependencia, discapacidad, residencias, servicios sociales, infancia, juventud, envejecimiento, igualdad y violencia de género.
- **Fuentes:** Seguridad Social, SEPE, IMSERSO, Derechos Sociales, organismos de igualdad, mujeres, infancia y juventud; sistemas autonómicos y locales.
- **Integración:** prestaciones, beneficiarios, cuantías y equipamientos como medidas distintas; indicadores por colectivos sin duplicar personas entre programas. Relacionar con población, empleo y salud mediante enlaces entre categorías.

### F06 · Vivienda, suelo y organización urbana

- **Contenido:** parque de viviendas, alquiler, compraventa, precios, tasaciones, hipotecas, vivienda protegida, construcción, rehabilitación, suelo, planeamiento, usos urbanos, vulnerabilidad residencial y equipamientos de proximidad.
- **Fuentes:** Vivienda y Agenda Urbana, INE, Catastro, administraciones urbanísticas autonómicas y locales y estadísticas públicas relacionadas.
- **Integración:** precios de oferta, alquiler declarado, transmisiones y tasaciones se consultarán bajo conceptos separados. El planeamiento conservará su vigencia y fuente; una capa informativa no se presentará como certificación urbanística.

### F07 · Economía, empresas, industria y producción

- **Contenido:** PIB, valor añadido, cuentas económicas territoriales, productividad, tejido empresarial, establecimientos, demografía y tamaño de empresas, producción industrial, minería no energética, actividad y estructura de servicios, economía social e internacionalización empresarial.
- **Fuentes:** INE, Industria, Trabajo, AEAT y estadística autonómica y local; Eurostat y OCDE por producto.
- **Integración:** clasificaciones de actividad y sus versiones; sede de empresa y centro productivo diferenciados. Los importes corrientes, los volúmenes y los índices tendrán unidades y bases explícitas.

### F08 · Precios, comercio, finanzas y seguros

- **Contenido:** índices de precios, inflación, comercio interior y exterior, inversión exterior, crédito, depósitos, oficinas, financiación, mercados y valores, seguros y fondos de pensiones privados; productos regulados como juego y tabaco según el contenido publicado.
- **Fuentes:** INE, Comercio —DataComex/DataInvex—, AEAT, Banco de España, CNMV, DGSFP, CNMC, Tesoro, DGOJ y Comisionado del Tabaco; BCE y Eurostat.
- **Integración:** precios específicos de vivienda, energía o agricultura tendrán una sola ficha canónica, enlazada desde sus temas. Las series financieras exclusivamente nacionales se mostrarán como contexto de España.

### F09 · Hacienda, presupuestos, fiscalidad y deuda pública

- **Contenido:** ingresos, impuestos, recaudación, presupuestos y ejecución, gasto por función, déficit, deuda, financiación autonómica y local, cuentas del sector público y evaluación fiscal.
- **Fuentes:** Hacienda, AEAT, IGAE, AIReF, Tesoro, Banco de España y haciendas autonómicas, forales y locales.
- **Integración:** distinguir presupuesto aprobado y ejecutado, nivel de administración y consolidación. La ubicación de un organismo no se confundirá con el territorio al que beneficia todo su gasto.

### F10 · Contratación, subvenciones y proyectos financiados

- **Contenido:** licitaciones, contratos, adjudicaciones, lotes, convocatorias y concesiones de ayudas, fondos europeos, proyectos financiados y cooperación al desarrollo en su vertiente pública y agregada.
- **Fuentes:** PLACSP, BDNS, plataformas autonómicas y locales, organismos concedentes, TED, Kohesio y Cooperación Española. AEI, CDTI y CORDIS se enlazarán con F12.
- **Integración:** separar anuncio, adjudicación, formalización, modificación, convocatoria, concesión y pago. Geolocalizar solo cuando se conozca el lugar de ejecución o la cobertura real; una sede no equivale al destino de la inversión.

### F11 · Educación, formación y universidad

- **Contenido:** centros, alumnado, profesorado, enseñanzas, FP, becas, resultados, abandono, formación de adultos, universidades, titulaciones, movilidad e inserción según las publicaciones disponibles.
- **Fuentes:** EDUCAbase, SIIU, administraciones educativas, universidades públicas y estadísticas autonómicas y locales; INE y Eurostat.
- **Integración:** centros como puntos y resultados en su escala publicada; cursos académicos diferenciados de años naturales. Conexiones con población, empleo y accesibilidad.

### F12 · Ciencia, investigación, innovación y patentes

- **Contenido:** I+D, personal y gasto investigador, innovación empresarial, centros e infraestructuras científicas, convocatorias y proyectos, patentes y otras modalidades de propiedad industrial, producción científica y repositorios públicos.
- **Fuentes:** INE, SICTI, AEI, CDTI, OEPM, CSIC, universidades y CORDIS.
- **Integración:** proyectos y centros consultables, series territoriales y enlaces a resultados. Los repositorios documentales aportarán metadatos y referencias geográficas cuando existan; no se convertirá cada publicación en un punto inventado ni se copiarán obras sin permiso.

### F13 · Salud, sanidad, epidemiología y alimentación saludable

- **Contenido:** hospitales y atención primaria, recursos y personal, actividad y listas de espera, gasto, salud y mortalidad, enfermedades, vigilancia epidemiológica, medicamentos, trasplantes, adicciones, seguridad alimentaria y nutrición.
- **Fuentes:** Sanidad, ISCIII/CNE, AEMPS, ONT, AESAN, OEDA y servicios autonómicos de salud; INE, ECDC y OMS por producto.
- **Integración:** centros sanitarios y estadísticas agregadas; separar incidencia, prevalencia, tasas y recuentos, así como fechas y definiciones. Los datos suprimidos o no publicados no se reconstruirán como ceros.

### F14 · Agricultura, ganadería, pesca, alimentación y medio rural

- **Contenido:** cultivos, superficies, rendimientos, calendarios, regadío, explotaciones, cabaña ganadera, producción y precios agrarios, industria y cadena alimentaria, ayudas agrarias, seguros, flota, capturas y acuicultura, desarrollo rural y caminos naturales.
- **Fuentes:** MAPA, FEGA/SIGPAC, SIAR, SIGA, AICA, ENESA, INE, administraciones autonómicas y FAO. IEO aporta productos científicos vinculados a pesca y F19.
- **Integración:** campañas, especies, usos y unidades compatibles. Las ayudas se referenciarán también desde F10; los caminos desde F22/F26; las observaciones agroclimáticas desde F17, manteniendo un único producto de origen.

### F15 · Naturaleza, biodiversidad, bosques y usos del territorio

- **Contenido:** hábitats, especies y observaciones, espacios protegidos, Red Natura, parques, bosques e inventarios forestales, cobertura y uso del suelo, fragmentación, restauración y estado de los ecosistemas.
- **Fuentes:** MITECO, Parques Nacionales, GBIF.ES, IGN/CNIG, administraciones autonómicas, Copernicus Land, AEMA y JRC.
- **Integración:** distinguir límites de protección, distribución estimada, observaciones de especies y muestreos. Las versiones y resoluciones de las superficies permitirán evaluar cambios sin comparar productos incompatibles.

### F16 · Agua continental, cuencas y acuíferos

- **Contenido:** ríos, lagos, humedales, cuencas y demarcaciones, masas superficiales y subterráneas, acuíferos, aforos, embalses, reservas, usos y demandas, abastecimiento, saneamiento, calidad, sequía, planificación e inundabilidad.
- **Fuentes:** MITECO, todas las confederaciones inventariadas, ACA, URA, Augas de Galicia y administraciones hidráulicas autonómicas e insulares; IGME y sistemas locales relacionados.
- **Integración:** una categoría común para todas las cuencas, con capas y series de estaciones. Cuenca, demarcación y división administrativa serán ámbitos distintos; cada servicio conservará su fecha y frecuencia.

### F17 · Tiempo, clima y cambio climático

- **Contenido:** estaciones, observaciones, predicciones, avisos, temperatura, precipitación, viento, nieve y otras variables publicadas, climatologías, extremos, índices, escenarios y proyecciones.
- **Fuentes:** AEMET, Meteocat, Euskalmet, MeteoGalicia, SIAR y redes oficiales territoriales; Oficina Española de Cambio Climático, Copernicus C3S y JRC.
- **Integración:** separar observación, predicción y escenario. Tiempo de validez, hora de actualización, periodo climatológico y resolución serán visibles. Las credenciales gratuitas que exija un servicio se gestionarán fuera del código público.

### F18 · Geología, suelos y riesgos naturales

- **Contenido:** mapas geológicos y edafológicos, litología, geodiversidad, recursos del subsuelo, sismicidad, volcanismo, movimientos del terreno y cartografía de peligrosidad y exposición publicada.
- **Fuentes:** IGME-CSIC, IGN, geoportales autonómicos, JRC y Copernicus Emergency. Productos de inundación, incendios, sequía y fenómenos meteorológicos se enlazarán con F15–F17.
- **Integración:** separar sucesos observados, peligrosidad, exposición y riesgo; respetar escala y vigencia. Las delimitaciones de una emergencia no sustituirán a la cartografía permanente del territorio.

### F19 · Mar, litoral y oceanografía

- **Contenido:** batimetría, cartografía hidrográfica, costa y dominio público, ámbitos marítimos publicados, boyas, oleaje, mareas, corrientes, temperatura, salinidad, hábitats y seguimiento del medio marino.
- **Fuentes:** Instituto Hidrográfico de la Marina, Puertos del Estado, IEO-CSIC, UTM-CSIC, MITECO, Copernicus Marine y EMODnet.
- **Integración:** ampliar la consulta a las zonas marinas relacionadas con España según la cobertura oficial de cada producto. Identificar autoridad, fecha y significado de las delimitaciones; no deducir fronteras marítimas a partir de la máscara terrestre.

### F20 · Aire, contaminación, residuos y presión ambiental

- **Contenido:** estaciones y calidad del aire, emisiones, focos industriales, gases de efecto invernadero, ruido, residuos, reciclaje, instalaciones de tratamiento, suelos contaminados, indicadores ambientales y vigilancia radiológica pública.
- **Fuentes:** MITECO, PRTR, CSN, redes autonómicas y locales, AEMA, Copernicus CAMS e INE.
- **Integración:** distinguir emisiones y concentraciones, mediciones y modelos, instalaciones y áreas afectadas. Separar fecha de medición, validación y publicación; vincular actividad industrial con F07 y energía con F21.

### F21 · Energía y recursos energéticos

- **Contenido:** generación, potencia y tecnologías, instalaciones y redes publicadas, demanda, consumo, renovables, hidrocarburos, gas, reservas, eficiencia, precios y puntos de suministro, gasolineras y recarga según la cobertura ofrecida.
- **Fuentes:** MITECO, IDAE, CORES, CNMC y administraciones territoriales. REData/eSIOS y Enagás permanecerán identificados como operadores complementarios del núcleo oficial.
- **Integración:** separar potencia y energía, producción y consumo, series reales y estimaciones. Infraestructuras y mercados se vincularán sin atribuir a cada municipio datos que solo existan por sistema eléctrico o a escala nacional.

### F22 · Transporte, movilidad, redes y logística

- **Contenido:** carreteras y caminos, ferrocarril de todas las clases publicadas, estaciones, servicios, transporte colectivo, horarios y paradas, tráfico y movilidad, vehículos y siniestralidad, aeropuertos, espacio e información aeronáutica pública, puertos, mercancías, faros y ayudas a la navegación.
- **Fuentes:** IGN, Transportes/OTLE y Punto de Acceso Nacional, DGT, Adif, Renfe, Aena, ENAIRE, Puertos del Estado y autoridades/operadores públicos territoriales.
- **Integración:** diferenciar infraestructura, servicio, frecuencia y uso; una vía dibujada no asegura servicio activo. Completar cada inventario dentro de su cobertura, con estado y fechas cuando existan. Senderos y rutas tendrán enlaces a F14, F24 y F26.

### F23 · Conectividad, telecomunicaciones y sociedad digital

- **Contenido:** cobertura de banda ancha y móvil, infraestructuras públicas o publicables, despliegue, servicios de comunicaciones, acceso y uso de internet, equipamiento TIC, competencias y brecha digital, digitalización de empresas y administraciones.
- **Fuentes:** Secretaría de Estado de Telecomunicaciones/Conectemos, Red.es/ONTSI, CNMC, INE y administraciones autonómicas y locales.
- **Integración:** diferenciar cobertura declarada, disponibilidad comercial, contratación y uso observado. Cada malla o área conservará su resolución, tecnología, fecha y condición de medición.

### F24 · Turismo, destinos y alojamientos

- **Contenido:** visitantes, viajes, gasto, ocupación, alojamientos y registros turísticos, empleo turístico, estacionalidad, destinos, recursos y rutas turísticas oficiales.
- **Fuentes:** INE, Turespaña, SEGITTUR y registros y observatorios autonómicos y locales.
- **Integración:** separar origen del viajero y destino, turista y excursionista, plazas y pernoctaciones. Los recursos culturales, naturales o de transporte se referenciarán sin volver a importar el mismo objeto.

### F25 · Cultura, patrimonio, archivos, memoria y diversidad religiosa

- **Contenido:** bienes patrimoniales, museos, bibliotecas, archivos, artes y actividades culturales, industrias y empleo cultural, hábitos y participación, patrimonio documental, lugares de memoria, fosas y centros de culto publicados.
- **Fuentes:** CULTURABase, BNE, PARES, IPCE, Memoria Democrática, Observatorio del Pluralismo Religioso y administraciones territoriales.
- **Integración:** puntos, recintos, estadísticas y referencias documentales según el producto. Ubicar documentos históricos solo cuando tengan referencia geográfica justificable y conservar fechas y derechos de cada recurso.

### F26 · Deporte, ocio y actividades al aire libre

- **Contenido:** instalaciones deportivas, licencias, clubes, práctica, empleo y gasto deportivo, competiciones y actividades publicadas, senderos y grandes recorridos, itinerarios recreativos y equipamientos de ocio.
- **Fuentes:** CSD/DEPORTEData, administraciones deportivas autonómicas y locales, IGN y MAPA para redes de caminos, y gestores públicos de espacios naturales.
- **Integración:** separar recorridos oficiales, señalización y accesibilidad publicada. Las condiciones de uso conservarán fecha y entidad responsable. Las rutas turísticas y los caminos compartidos serán referencias al mismo objeto de F14/F22/F24.

### F27 · Elecciones y representación política

- **Contenido:** resultados, participación, censo electoral en su escala pública, candidaturas, escaños, composición y actividad representativa de las cámaras, y elecciones estatales, europeas, autonómicas y locales con datos oficiales.
- **Fuentes:** Interior/Infoelectoral, autoridades electorales competentes, administraciones autonómicas, Congreso, Senado y cámaras territoriales.
- **Integración:** separar procesos, convocatorias, resultados provisionales y definitivos. Las series históricas preservarán cambios de circunscripción, candidaturas y reglas; no se asumirá que un nombre de partido mantiene siempre la misma entidad histórica.

### F28 · Administración, organización territorial y normativa

- **Contenido:** entidades locales, organismos y unidades administrativas, sedes y servicios, estructura del sector público, personal y empleo público, transparencia, disposiciones, normativa y referencias territoriales publicadas.
- **Fuentes:** Registro de Entidades Locales, DIR3, Función Pública, INVENTE, Portal de Transparencia, BOE y boletines y registros autonómicos y locales.
- **Integración:** directorio institucional con sus relaciones y vigencias, enlazado a presupuestos, contratación y servicios. La sede de una entidad no se confundirá con su ámbito competencial; la normativa será información contextual salvo que tenga una geometría publicada.

### F29 · Justicia, seguridad, emergencias y defensa pública

- **Contenido:** órganos y demarcaciones judiciales, actividad judicial y fiscal, criminalidad agregada, instituciones penitenciarias, protección civil y recursos de emergencias publicables, y estadísticas abiertas de defensa.
- **Fuentes:** CGPJ, Fiscalía, Interior, Instituciones Penitenciarias, Defensa y autoridades autonómicas y locales. Violencia de género se enlaza con F05; protección internacional con F02; riesgos naturales con F18.
- **Integración:** conservar demarcaciones y definiciones de cada sistema. Distinguir denuncias, hechos registrados, procedimientos y sentencias; no construir localizaciones individuales a partir de estadísticas agregadas.

## Fuentes autonómicas y locales: dentro de todos los temas

Los catálogos de las **17 comunidades y las 2 ciudades autónomas**, y los servicios municipales, provinciales e insulares, se examinarán en F00 y se distribuirán producto por producto entre los fascículos. No habrá que esperar a una última entrega «de autonomías» para utilizarlos.

En cada tema se mantendrá una matriz **indicador × territorio × periodo × fuente**. Permitirá saber qué puede compararse en toda España, dónde hay más detalle y dónde falta cobertura. Las diferencias metodológicas se explicarán junto al indicador. Que una comunidad publique una variable no implicará que las demás también lo hagan ni autorizará a interpolar sus valores.

Los **238 publicadores y 116.236 títulos catalogados** son una cola de revisión que puede descubrir más productos y fuentes. No son 116.236 capas listas, ni están clasificados individualmente por este plan. El [reparto de fuentes y sectores](planning/COBERTURA_DE_FUENTES.md) asigna las 182 fichas editoriales y los 27 sectores del IOE a destinos de trabajo. Los catálogos amplios conservan una ruta transversal hasta revisar cada producto. Ninguna fuente queda descartada por no caber en los primeros ejemplos.

## Qué debe entregar cada fascículo

- Inventario fechado de todos los productos de la familia encontrados en las fuentes revisadas, con su estado y pendientes.
- Datos reutilizables importados con sus variables, dimensiones y series disponibles; descarga o acceso original y procedencia verificable.
- Capas, fichas y gráficos adecuados al producto; búsqueda y filtros por variable, territorio y periodo; leyenda, unidades y cobertura visibles.
- Consulta de objetos y territorios, superposición cuando tenga sentido y uso del cronograma cuando exista serie. Una capa sin dimensión temporal no aparentará cambiar de año.
- Comprobaciones de códigos, unidades, periodos, cobertura, duplicados y valores ausentes; contraste de valores y geometrías con la fuente.
- Método de actualización con registro de cambios y fallos. Una actualización fallida no borrará silenciosamente los datos válidos anteriores.

Una entrega se podrá **publicar con alcance parcial explícito**, pero el fascículo seguirá abierto hasta completar el alcance acordado o registrar los impedimentos. Los productos nuevos ampliarán la siguiente revisión, sin exigir que una fuente deje de publicar para poder avanzar.

## Almacenamiento y tamaño

Mantener en el repositorio el catálogo, las definiciones, los procesos de importación, la procedencia y las tablas y geometrías de tamaño razonable. Particionar por producto, periodo o territorio y cargar solo lo necesario para la consulta. El catálogo completo no debe descargarse al abrir el mapa.

No se compromete una base de datos o infraestructura de pago para este plan. Las imágenes, los modelos y los históricos muy grandes requerirán evaluar distribución oficial, compresión y alojamiento adecuado antes de copiarlos. Preferir conservar datos reutilizables propios cuando sea viable; identificar expresamente los productos que dependan de un servicio externo. La elección entre archivos, SQLite, Parquet o teselas se hará por necesidad real de cada familia.

## Secuencia de trabajo después de este reparto

1. **Diseño de la página:** aspecto del mapa, jerarquía territorial, botón de capas, navegación temática, filtros, leyendas, cronograma y paneles de consulta. Mantener el favicon en la raíz y «Acerca de» discreto en la esquina superior derecha, con identidad, versión y enlaces.
2. **Implementación de F00 y F01:** adaptar el prototipo existente a la estructura acordada, sin presentar lo ya construido como si cubriera todos los productos del fascículo.
3. **Integración de F02 en adelante:** completar familias y publicar lotes revisables siguiendo este orden de referencia. Los cambios de orden se documentarán por dependencia o disponibilidad, sin perder el inventario pendiente.

Este reparto no fija plazos ni equipara el tamaño de todos los fascículos. El trabajo de diseño es el siguiente paso; la integración de nuevos datos vendrá después.
