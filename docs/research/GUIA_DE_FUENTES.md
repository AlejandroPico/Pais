# España: organismos y familias de datos para el atlas

**Investigación del 5 de noviembre de 2026.**

Guía editorial de organismos, servicios y familias de datos potencialmente incorporables. Las fichas de servicio no se cuentan como organismos jurídicos distintos. Identificación no implica descarga, licencia validada o integración en el mapa.

Esta guía contiene **182 fichas de fuentes y servicios** y **1953 menciones de familias de datos**; hay solapamientos intencionados. No son 182 organismos jurídicos diferentes ni 1953 conjuntos únicos.

El inventario comprobado acompaña esta guía: **238 publicadores y 116.236 títulos de conjuntos federados en datos.gob.es**, más **758 operaciones del IOE**, con fichas detalladas agrupadas en **147 combinaciones de servicio responsable y unidad ejecutora**. No sumar estas cifras: son unidades distintas y se solapan.

## Cómo leer la lista

- **Organismo / servicio → familias de datos → acceso y geografía.** Cada familia puede contener muchas series, tablas, capas, años y dimensiones.
- **API documentada** solo se indica donde se ha identificado documentación. “Consulta”, “visor” o “informe” no significan que se haya probado una descarga masiva.
- **Público** no siempre significa abierto, gratuito, sin registro o autorizado para cualquier redistribución. La licencia se comprueba por recurso, no por el nombre del organismo.
- **Disponible** no significa actualizado: conservar año observado, fecha de publicación, versión y revisiones.
- **Cartografiable** puede significar punto, línea, polígono, rejilla o dato agregado territorial. Un indicador solo nacional pertenece al contexto del país; no se reparte artificialmente entre municipios.
- Las fuentes internacionales se limitan a productos con información sobre España. Los operadores privados regulados están separados del núcleo oficial.

## Índice

- Inventarios que permiten descubrir más fuentes · 4 fichas
- Estadística general, población, sociedad y economía · 1 fichas
- Cartografía, relieve, direcciones, parcelas y subsuelo · 6 fichas
- Agua continental, cuencas, calidad y riesgos hidrológicos · 14 fichas
- Clima, aire, contaminación, biodiversidad y bosques · 11 fichas
- Mar, litoral, oceanografía y pesca científica · 4 fichas
- Hacienda, economía, finanzas, ayudas y contratación · 13 fichas
- Trabajo, empleo, salarios, pensiones y protección laboral · 5 fichas
- Protección social, igualdad, juventud y migraciones · 8 fichas
- Salud, sanidad, epidemiología, medicamentos y alimentación · 6 fichas
- Educación, universidad, investigación e innovación · 7 fichas
- Cultura, patrimonio, archivos, religión, memoria y deporte · 7 fichas
- Agricultura, ganadería, pesca, alimentación y medio rural · 7 fichas
- Energía, industria y conectividad · 7 fichas
- Movilidad, carreteras, ferrocarril, aviación y puertos · 8 fichas
- Turismo, vivienda, suelo y organización urbana · 3 fichas
- Elecciones, parlamentos, administración, justicia y seguridad · 18 fichas
- Fuentes europeas oficiales con datos sobre España · 15 fichas
- Fuentes internacionales públicas complementarias · 4 fichas
- Operadores regulados complementarios, separados del núcleo de organismos oficiales · 2 fichas
- Las 17 comunidades autónomas y las 2 ciudades autónomas · 19 fichas
- Administración local y supramunicipal · ejemplos y expansión · 13 fichas

## Inventarios que permiten descubrir más fuentes

### F001 · [datos.gob.es · Iniciativa Aporta](https://datos.gob.es/es/apidata)

- **Acceso identificado:** API y SPARQL documentados.
- **Geografía:** Todas las administraciones.
- **Datos y familias:**
  - Publicadores oficiales.
  - Catálogos federados.
  - Títulos de conjuntos.
  - Distribuciones y formatos.
  - Licencias declaradas.
  - Cobertura geográfica.
  - Frecuencia de actualización.
  - Temáticas del sector público.
- **Para integrarlo bien:** Se ha extraído el inventario federado completo de títulos. No equivale al universo de todos los datos oficiales españoles.

### F002 · [INE · Inventario de Operaciones Estadísticas](https://www.ine.es/dyngs/IOE/index.htm)

- **Acceso identificado:** Fichas y listados descargables.
- **Geografía:** Estado y organismos responsables.
- **Datos y familias:**
  - Operaciones vigentes.
  - Servicios responsables.
  - Unidades ejecutoras.
  - Variables de estudio.
  - Variables de clasificación.
  - Desagregación territorial.
  - Periodicidad.
  - Metodología.
  - Enlaces a resultados.
  - Inventario histórico.
- **Para integrarlo bien:** Se han recuperado las 758 fichas del inventario actual. Una operación inventariada no garantiza microdatos abiertos ni cobertura municipal.

### F003 · [INE · Plan Estadístico Nacional](https://www.ine.es/dyngs/IOE/consultaPlan.htm?cid=9)

- **Acceso identificado:** Consulta y documentos.
- **Geografía:** Estatal.
- **Datos y familias:**
  - Planes plurianuales.
  - Programas anuales.
  - Calendarios de difusión.
  - Operaciones previstas.
  - Organismos participantes.
  - Infraestructura y normalización estadística.
- **Para integrarlo bien:** Distinguir operaciones previstas de datos efectivamente publicados.

### F004 · [IGN · Infraestructura de Datos Espaciales de España](https://www.idee.es/segun-tipo-de-servicio)

- **Acceso identificado:** Directorios de servicios geográficos.
- **Geografía:** Estado, CCAA y administraciones locales.
- **Datos y familias:**
  - Catálogos CSW.
  - Servicios WMS.
  - Servicios WMTS.
  - Servicios WFS.
  - Coberturas WCS.
  - OGC API.
  - Descargas ATOM.
  - Nodos autonómicos.
  - Nodos locales.
  - Servicios INSPIRE.
- **Para integrarlo bien:** El directorio identifica servicios. Hay que consultar capacidades, capas, escala y condiciones de cada uno.


## Estadística general, población, sociedad y economía

### F005 · [Instituto Nacional de Estadística · INEbase](https://www.ine.es/inebmenu/indice.htm)

- **Acceso identificado:** API JSON, tablas, descargas y microdatos según operación.
- **Geografía:** Nacional, autonómica, provincial, municipal, secciones y mallas según producto.
- **Datos y familias:**
  - Censos de población.
  - Censo anual.
  - Estadística continua de población.
  - Padrón y nomenclátor.
  - Nacimientos.
  - Defunciones y causas.
  - Matrimonios.
  - Migraciones internas y exteriores.
  - Nacionalidad y lugar de nacimiento.
  - Estructura por edad y sexo.
  - Hogares y familias.
  - Fecundidad.
  - Esperanza de vida.
  - Proyecciones demográficas.
  - Nombres y apellidos.
  - EPA.
  - Empleo y paro.
  - Salarios y costes laborales.
  - Presupuestos familiares.
  - Condiciones de vida.
  - Pobreza y desigualdad.
  - Atlas de renta de los hogares.
  - Cuentas nacionales.
  - Contabilidad regional.
  - PIB y valor añadido.
  - IPC e inflación.
  - Precios de vivienda.
  - Alquiler declarado.
  - Compraventas e hipotecas.
  - Directorio de empresas DIRCE.
  - Demografía empresarial.
  - Industria.
  - Comercio.
  - Servicios.
  - Turismo y ocupación.
  - Agricultura y censo agrario.
  - Agua y residuos.
  - Energía ambiental.
  - Discapacidad y dependencia.
  - Uso del tiempo.
  - TIC de hogares y empresas.
  - I+D e innovación.
  - Indicadores urbanos.
  - ODS.
  - Movilidad experimental.
  - Cartografía censal.
  - Mallas de población.
  - Microdatos anonimizados.
- **Para integrarlo bien:** La unidad territorial cambia por operación. Los nombres/apellidos no autorizan localizar individuos; una encuesta nacional no permite fabricar resultados municipales.


## Cartografía, relieve, direcciones, parcelas y subsuelo

### F006 · [Instituto Geográfico Nacional y CNIG](https://www.ign.es/web/ide-area-nodo-ide-ign)

- **Acceso identificado:** Descargas y servicios geográficos.
- **Geografía:** España, con escalas y fechas por producto.
- **Datos y familias:**
  - Límites administrativos.
  - Municipios y enclaves.
  - Provincias.
  - Comunidades autónomas.
  - Líneas límite.
  - Nomenclátor geográfico.
  - Base Topográfica Nacional.
  - Mapa Topográfico Nacional.
  - Ortofotos PNOA.
  - Vuelos históricos.
  - Imágenes de satélite.
  - Nubes LiDAR.
  - Modelos digitales del terreno.
  - Modelos digitales de superficies.
  - Pendientes.
  - Curvas de nivel.
  - Altura de vegetación y edificios según producto.
  - SIOSE.
  - CORINE Land Cover.
  - Redes de transporte.
  - Hidrografía.
  - Redes geodésicas.
  - Mapas históricos.
  - Atlas Nacional.
  - Información geográfica de referencia.
- **Para integrarlo bien:** No todos los productos tienen la misma resolución, año o cobertura. La cartografía visual no sustituye a un deslinde legal.

### F007 · [IGN · CartoCiudad](https://www.cartociudad.es/web/portal/directorio-de-servicios/descarga)

- **Acceso identificado:** Descargas, geocodificación y servicios geográficos.
- **Geografía:** Direcciones, entidades y vías.
- **Datos y familias:**
  - Portales y puntos de dirección.
  - Calles y carreteras.
  - Topónimos.
  - Poblaciones.
  - Entidades de población.
  - Códigos postales y relación con direcciones.
  - Manzanas.
  - Tablas de códigos territoriales.
  - Conversión coordenadas-direcciones.
- **Para integrarlo bien:** Validar la cobertura y las condiciones de los datos procedentes de Correos y otros colaboradores; no presuponer polígonos postales libres para cualquier uso.

### F008 · [Dirección General del Catastro](https://www.catastro.hacienda.gob.es/es-ES/datos_abiertos.html)

- **Acceso identificado:** Descargas y servicios; algunos accesos tienen restricciones.
- **Geografía:** Parcelas, edificios y municipios de su competencia.
- **Datos y familias:**
  - Parcelas catastrales.
  - Huella de edificios.
  - Direcciones.
  - Uso y características constructivas no protegidas.
  - Cartografía rústica y urbana.
  - Superficies.
  - Antigüedad constructiva según producto.
  - Estadísticas inmobiliarias.
  - Valores catastrales agregados.
  - IBI y características de inmuebles.
  - Cartografía INSPIRE.
  - Historia cartográfica donde se publique.
- **Para integrarlo bien:** No es precio de mercado. Titularidad protegida fuera de alcance. Navarra y territorios forales vascos requieren sus fuentes competentes. WMS no permite descargas masivas indiscriminadas.

### F009 · [IGME-CSIC](https://www.igme.es/datos-y-mapas/)

- **Acceso identificado:** Inventarios, descargas y servicios geográficos.
- **Geografía:** Hojas cartográficas, puntos y zonas geológicas.
- **Datos y familias:**
  - Mapa geológico MAGNA.
  - GEODE.
  - Litología.
  - Geología marina.
  - Unidades hidrogeológicas.
  - Puntos de agua.
  - Aguas minerales y termales.
  - Recursos minerales BDMIN.
  - Minas e indicios.
  - Explotaciones.
  - Lugares de interés geológico IELIG.
  - Fallas activas QAFI.
  - Geofísica SIGEOF.
  - Sondeos.
  - Geoquímica.
  - Riesgos geológicos.
  - Subsidencia.
  - Movimientos del terreno.
- **Para integrarlo bien:** Comprobar escala, fecha, licencia y nivel de acceso por inventario; no todo son capas nacionales homogéneas.

### F010 · [IGN · Sismología y volcanología](https://www.ign.es/web/ign/portal/sis-area-sismicidad)

- **Acceso identificado:** Catálogos, informes y servicios según producto.
- **Geografía:** Eventos y redes de observación.
- **Datos y familias:**
  - Catálogo sísmico.
  - Epicentros.
  - Profundidades.
  - Magnitudes.
  - Intensidades.
  - Series temporales.
  - Red de estaciones.
  - Peligrosidad sísmica.
  - Vigilancia volcánica.
  - Deformación del terreno.
  - Fenómenos geofísicos publicados.
- **Para integrarlo bien:** Separar eventos revisados, automáticos y mapas de peligrosidad. No asumir disponibilidad abierta de toda telemetría instrumental.

### F011 · [Instituto Hidrográfico de la Marina · IDEIHM](https://ideihm.covam.es/portal/)

- **Acceso identificado:** Servicios INSPIRE y catálogo público.
- **Geografía:** Litoral y áreas marítimas.
- **Datos y familias:**
  - Línea de costa.
  - Objetos hidrográficos publicados.
  - Batimetría disponible.
  - Cobertura de cartas náuticas.
  - Límites y zonas marítimas publicados.
  - Ayudas a navegación según servicio.
  - Puertos.
  - Nombres geográficos marinos.
- **Para integrarlo bien:** El catálogo público de cartas no convierte todas las cartas ENC o productos de navegación en descargas gratuitas reutilizables. Ver condiciones del producto concreto.


## Agua continental, cuencas, calidad y riesgos hidrológicos

### F012 · [MITECO · Dirección General del Agua](https://www.miteco.gob.es/es/agua.html)

- **Acceso identificado:** Cartografía, descargas e informes.
- **Geografía:** Cuencas, demarcaciones, masas de agua y estaciones.
- **Datos y familias:**
  - Demarcaciones hidrográficas.
  - Cuencas y subcuencas.
  - Ríos.
  - Lagos.
  - Masas superficiales.
  - Masas subterráneas.
  - Estado químico.
  - Estado ecológico.
  - Redes de seguimiento.
  - Inventario de presas.
  - Embalses y capacidad.
  - Reservas de agua.
  - Boletín hidrológico.
  - Zonas protegidas por planificación.
  - Sequía.
  - Escasez.
  - Planes hidrológicos.
  - Zonas inundables SNCZI.
  - Áreas de riesgo potencial.
  - Peligrosidad por periodo de retorno.
  - Riesgo de inundación.
  - Infraestructuras hidráulicas publicadas.
  - Caudales ecológicos de planes.
- **Para integrarlo bien:** Distinguir masa de agua, cuenca y municipio. No confundir peligro con riesgo ni datos de presa con volumen actual del embalse.

### F013 · [Confederación Hidrográfica del Cantábrico](https://www.chcantabrico.es/)

- **Acceso identificado:** SAIH, visor, series e informes.
- **Geografía:** Demarcación bajo su competencia.
- **Datos y familias:**
  - Aforos.
  - Caudales.
  - Pluviómetros.
  - Niveles.
  - Calidad del agua.
  - Planificación.
  - Masas de agua.
  - Zonas protegidas.
  - Riesgo de inundación.
- **Para integrarlo bien:** Ver disponibilidad, formato, histórico y estado provisional en el servicio concreto.

### F014 · [Confederación Hidrográfica del Duero](https://www.chduero.es/)

- **Acceso identificado:** SAIH, cartografía e informes.
- **Geografía:** Cuenca del Duero de competencia estatal.
- **Datos y familias:**
  - Aforos.
  - Caudales.
  - Embalses.
  - Precipitación.
  - Niveles piezométricos publicados.
  - Calidad.
  - Sequía.
  - Plan hidrológico.
  - Cartografía de masas.
- **Para integrarlo bien:** La cuenca no coincide con los límites autonómicos.

### F015 · [Confederación Hidrográfica del Ebro](https://www.chebro.es/)

- **Acceso identificado:** SAIH, SITEbro, cartografía y descargas según producto.
- **Geografía:** Cuenca del Ebro.
- **Datos y familias:**
  - Aforos.
  - Caudales.
  - Niveles.
  - Precipitación.
  - Embalses.
  - Piezometría publicada.
  - Calidad.
  - Planificación.
  - Masas de agua.
  - Concesiones y aprovechamientos públicos cuando estén publicados.
- **Para integrarlo bien:** No asumir que todos los registros administrativos sean descargables sin restricciones.

### F016 · [Confederación Hidrográfica del Tajo](https://www.chtajo.es/)

- **Acceso identificado:** SAIH, información hidrológica y cartografía.
- **Geografía:** Cuenca del Tajo.
- **Datos y familias:**
  - Aforos.
  - Caudales.
  - Embalses.
  - Precipitación.
  - Calidad.
  - Masas de agua.
  - Sequía.
  - Plan hidrológico.
  - Zonas protegidas.
- **Para integrarlo bien:** Versionar la información de planificación y las series de medición por separado.

### F017 · [Confederación Hidrográfica del Guadiana](https://www.chguadiana.es/)

- **Acceso identificado:** SAIH, redes, visor e informes.
- **Geografía:** Cuenca del Guadiana.
- **Datos y familias:**
  - Aforos.
  - Caudales.
  - Embalses.
  - Precipitación.
  - Piezometría publicada.
  - Calidad.
  - Masas subterráneas.
  - Sequía.
  - Planificación.
  - Cartografía hidráulica.
- **Para integrarlo bien:** Las lecturas en tiempo real pueden ser provisionales.

### F018 · [Confederación Hidrográfica del Guadalquivir](https://www.chguadalquivir.es/)

- **Acceso identificado:** SAIH, cartografía e informes.
- **Geografía:** Cuenca del Guadalquivir.
- **Datos y familias:**
  - Caudales.
  - Aforos.
  - Precipitación.
  - Embalses.
  - Calidad.
  - Sequía.
  - Masas superficiales.
  - Masas subterráneas.
  - Planificación.
  - Zonas inundables publicadas.
- **Para integrarlo bien:** Ver la licencia y la serie histórica de cada red.

### F019 · [Confederación Hidrográfica del Júcar](https://www.chj.es/)

- **Acceso identificado:** SAIH, redes, visor y descargas.
- **Geografía:** Demarcación del Júcar.
- **Datos y familias:**
  - Caudales.
  - Niveles.
  - Precipitación.
  - Embalses.
  - Piezometría publicada.
  - Calidad.
  - Masas.
  - Sequía.
  - Escasez.
  - Planificación.
- **Para integrarlo bien:** No equiparar nivel piezométrico, volumen almacenado y disponibilidad del recurso.

### F020 · [Confederación Hidrográfica del Segura](https://www.chsegura.es/)

- **Acceso identificado:** SAIH, cartografía e informes.
- **Geografía:** Demarcación del Segura.
- **Datos y familias:**
  - Caudales.
  - Niveles.
  - Embalses.
  - Precipitación.
  - Calidad.
  - Aguas subterráneas.
  - Sequía.
  - Planificación.
  - Masas de agua.
  - Infraestructuras publicadas.
- **Para integrarlo bien:** Desgloses y años según producto.

### F021 · [Confederación Hidrográfica del Miño-Sil](https://www.chminosil.es/)

- **Acceso identificado:** SAIH, cartografía e informes.
- **Geografía:** Demarcación Miño-Sil.
- **Datos y familias:**
  - Aforos.
  - Caudales.
  - Precipitación.
  - Embalses.
  - Calidad.
  - Sequía.
  - Masas.
  - Planificación.
  - Cartografía hidráulica.
- **Para integrarlo bien:** Distinguir datos medidos de productos de planificación.

### F022 · [Agència Catalana de l'Aigua](https://aca.gencat.cat/)

- **Acceso identificado:** Datos abiertos, visor y servicios según producto.
- **Geografía:** Cuencas de su competencia en Cataluña.
- **Datos y familias:**
  - Embalses.
  - Aforos.
  - Estado de sequía.
  - Calidad de ríos.
  - Aguas subterráneas.
  - Saneamiento.
  - Depuradoras.
  - Masas de agua.
  - Planificación.
  - Inundabilidad.
- **Para integrarlo bien:** Comprobar competencias entre cuencas internas y demarcaciones intercomunitarias.

### F023 · [URA · Agencia Vasca del Agua](https://www.uragentzia.euskadi.eus/)

- **Acceso identificado:** Catálogo, cartografía y redes.
- **Geografía:** Ámbito de competencia en Euskadi.
- **Datos y familias:**
  - Hidrografía.
  - Aforos.
  - Calidad.
  - Zonas inundables.
  - Dominio público hidráulico publicado.
  - Masas de agua.
  - Planificación.
  - Zonas protegidas.
  - Vertidos agregados publicados.
- **Para integrarlo bien:** Conservar la autoridad de origen y fecha de la capa.

### F024 · [Augas de Galicia](https://augasdegalicia.xunta.gal/)

- **Acceso identificado:** Visores, redes e informes.
- **Geografía:** Galicia-Costa y competencias propias.
- **Datos y familias:**
  - Embalses.
  - Aforos.
  - Sequía.
  - Calidad.
  - Masas de agua.
  - Saneamiento.
  - Planificación.
  - Zonas protegidas.
  - Inundabilidad.
- **Para integrarlo bien:** No cubre por sí sola toda la cuenca Miño-Sil.

### F025 · [Administraciones hidráulicas autonómicas e insulares](https://www.miteco.gob.es/es/cartografia-y-sig/ide/enlace_interes/ides-oocc.html)

- **Acceso identificado:** Directorios; acceso según cada autoridad.
- **Geografía:** Andalucía intracomunitaria, Baleares y Canarias.
- **Datos y familias:**
  - Demarcaciones intracomunitarias.
  - Consejos insulares de aguas.
  - Planificación insular.
  - Acuíferos.
  - Galerías y pozos publicados.
  - Reservas.
  - Desalación publicada.
  - Saneamiento.
  - Redes de control.
- **Para integrarlo bien:** Es una familia de publicadores, no una supuesta base única nacional. Identificar cada autoridad y catálogo antes de integrar.


## Clima, aire, contaminación, biodiversidad y bosques

### F026 · [AEMET](https://opendata.aemet.es/centrodedescargas/inicio)

- **Acceso identificado:** API gratuita con clave y otros servicios públicos.
- **Geografía:** Estaciones, municipios, zonas y rejillas según producto.
- **Datos y familias:**
  - Observación meteorológica.
  - Temperaturas.
  - Precipitaciones.
  - Viento.
  - Humedad.
  - Presión.
  - Radiación.
  - Insolación.
  - Valores climatológicos diarios.
  - Normales climáticas.
  - Extremos.
  - Inventario de estaciones.
  - Avisos.
  - Predicción municipal.
  - Predicción de montaña.
  - Predicción marítima.
  - Radar según acceso.
  - Rayos según producto.
  - Sequía meteorológica.
  - Índices climáticos.
- **Para integrarlo bien:** La API requiere clave; confirmar cuotas y productos. Observación, predicción y normal climática son capas distintas.

### F027 · [Servei Meteorològic de Catalunya · Meteocat](https://www.meteo.cat/wpweb/serveis/dades-obertes/)

- **Acceso identificado:** Datos abiertos y servicios con condiciones por API.
- **Geografía:** Cataluña.
- **Datos y familias:**
  - Estaciones automáticas.
  - Series diarias.
  - Temperatura.
  - Precipitación.
  - Viento.
  - Radar según producto.
  - Rayos según producto.
  - Avisos.
  - Climatología.
- **Para integrarlo bien:** No mezclar datos invalidados o provisionales con series validadas.

### F028 · [Euskalmet](https://www.euskalmet.euskadi.eus/servicios/open-data/)

- **Acceso identificado:** Catálogo y API meteorológica.
- **Geografía:** Euskadi.
- **Datos y familias:**
  - Estaciones.
  - Observaciones.
  - Temperatura.
  - Precipitación.
  - Viento.
  - Humedad.
  - Predicciones.
  - Avisos.
  - Radar y rayos según catálogo.
- **Para integrarlo bien:** Ver condiciones y actualización de cada recurso.

### F029 · [MeteoGalicia](https://www.meteogalicia.gal/)

- **Acceso identificado:** Servicios y descargas documentados por producto.
- **Geografía:** Galicia.
- **Datos y familias:**
  - Estaciones meteorológicas.
  - Datos diarios.
  - Datos horarios.
  - Temperatura.
  - Precipitación.
  - Viento.
  - Humedad.
  - Predicción.
  - Información marítima según producto.
- **Para integrarlo bien:** Servicio autonómico complementario a AEMET; mantener identificadores propios de estación.

### F030 · [MITECO · Patrimonio natural, biodiversidad y bosques](https://www.miteco.gob.es/es/cartografia-y-sig/ide/directorio_datos_servicios/biodiversidad.html)

- **Acceso identificado:** Descargas y servicios geográficos.
- **Geografía:** Polígonos, mallas, inventarios y territorios.
- **Datos y familias:**
  - Inventario Español del Patrimonio Natural y la Biodiversidad.
  - Banco de Datos de la Naturaleza.
  - Mapa Forestal.
  - Inventario Forestal Nacional.
  - Tipos de bosque.
  - Especies forestales.
  - Biomasa y existencias.
  - Red Natura 2000.
  - Espacios naturales protegidos.
  - Hábitats.
  - Distribución de especies.
  - Especies amenazadas.
  - Especies exóticas invasoras.
  - Montes de utilidad pública.
  - Vías pecuarias publicadas.
  - Humedales.
  - Zonas de protección de aves.
  - Incendios forestales EGIF.
  - Aprovechamientos forestales.
  - Estado y daños de bosques.
- **Para integrarlo bien:** Algunos datos sensibles de especies se generalizan. La ausencia de una cita no prueba ausencia de la especie.

### F031 · [Organismo Autónomo Parques Nacionales](https://www.miteco.gob.es/es/parques-nacionales-oapn.html)

- **Acceso identificado:** Cartografía, publicaciones y seguimiento.
- **Geografía:** Parques nacionales y otras redes gestionadas.
- **Datos y familias:**
  - Límites de parques.
  - Zonificación publicada.
  - Red de seguimiento.
  - Visitantes.
  - Usos públicos.
  - Itinerarios publicados.
  - Red de Reservas de la Biosfera.
  - Indicadores de conservación.
- **Para integrarlo bien:** Comprobar qué productos proceden del OAPN y cuáles de cada administración gestora.

### F032 · [MITECO · Calidad y evaluación ambiental](https://www.miteco.gob.es/es/calidad-y-evaluacion-ambiental.html)

- **Acceso identificado:** Descargas, cartografía, indicadores e informes.
- **Geografía:** Estaciones, instalaciones, aglomeraciones y territorios.
- **Datos y familias:**
  - Redes de calidad del aire.
  - Concentraciones de contaminantes.
  - Zonas y aglomeraciones de evaluación.
  - Inventario de emisiones.
  - Mapas estratégicos de ruido.
  - Exposición al ruido.
  - Residuos.
  - Tratamiento de residuos.
  - Suelos contaminados en lo publicado.
  - Evaluación ambiental.
  - Indicadores ambientales.
  - Perfil Ambiental de España.
- **Para integrarlo bien:** Los inventarios de emisiones y las concentraciones medidas en estaciones son productos distintos.

### F033 · [MITECO · PRTR-España](https://prtr-es.miteco.gob.es/)

- **Acceso identificado:** Consulta y descargas.
- **Geografía:** Complejos industriales y territorios.
- **Datos y familias:**
  - Instalaciones declarantes.
  - Actividad industrial.
  - Emisiones al aire.
  - Emisiones al agua.
  - Emisiones al suelo.
  - Transferencias de residuos.
  - Sustancias contaminantes.
  - Series anuales.
  - Metadatos de validación.
- **Para integrarlo bien:** Conservar umbrales y criterios de reporte. Un valor no publicado no implica emisión cero.

### F034 · [MITECO · Oficina Española de Cambio Climático](https://www.miteco.gob.es/es/cambio-climatico.html)

- **Acceso identificado:** Indicadores, cartografía y documentos.
- **Geografía:** Nacional y territorial según producto.
- **Datos y familias:**
  - Inventario de gases de efecto invernadero.
  - Emisiones por sectores.
  - Escenarios de cambio climático.
  - Impactos y adaptación.
  - Indicadores de vulnerabilidad.
  - Proyecciones.
  - Planes de adaptación.
- **Para integrarlo bien:** Los escenarios son proyecciones, no observaciones futuras conocidas.

### F035 · [CSIC · Nodo nacional GBIF.ES](https://gbif.es/portal-nacional-de-datos/)

- **Acceso identificado:** Portal de datos, descargas y servicios de biodiversidad.
- **Geografía:** Registros de presencia y muestreo.
- **Datos y familias:**
  - Registros de ocurrencia.
  - Especies.
  - Colecciones biológicas.
  - Observaciones.
  - Muestreos.
  - Listas taxonómicas.
  - Fechas de registros.
  - Distribuciones documentadas.
  - Instituciones proveedoras.
- **Para integrarlo bien:** GBIF agrega también fuentes no oficiales: para el núcleo oficial filtrar por institución publicadora y licencia. No asumir muestreo uniforme.

### F036 · [Consejo de Seguridad Nuclear](https://www.csn.es/)

- **Acceso identificado:** Visores, datos e informes.
- **Geografía:** Estaciones, instalaciones y territorios.
- **Datos y familias:**
  - Vigilancia radiológica ambiental.
  - REA.
  - REVIRA.
  - Medidas de radiación publicadas.
  - Redes autonómicas asociadas.
  - Mapa de potencial de radón.
  - Instalaciones nucleares y radiactivas publicadas.
  - Informes de seguridad.
- **Para integrarlo bien:** Ver unidad, intervalo, carácter medido/modelizado y detalle territorial permitido.


## Mar, litoral, oceanografía y pesca científica

### F037 · [Puertos del Estado · Oceanografía](https://portuscopia.puertos.es/)

- **Acceso identificado:** Visualización y descarga.
- **Geografía:** Boyas, mareógrafos, radares y rejillas.
- **Datos y familias:**
  - Oleaje.
  - Altura significativa.
  - Periodos de ola.
  - Dirección del oleaje.
  - Nivel del mar.
  - Mareas.
  - Corrientes.
  - Viento.
  - Presión.
  - Temperatura del agua.
  - Salinidad según estación.
  - Radares HF.
  - Series históricas.
  - Predicciones.
  - Reanálisis.
- **Para integrarlo bien:** Separar series medidas, simuladas y previstas; no todos los instrumentos miden todas las variables.

### F038 · [Instituto Español de Oceanografía · IEO-CSIC](https://www.ieo.es/)

- **Acceso identificado:** Centro de datos, repositorios e informes por producto.
- **Geografía:** Campañas, estaciones y áreas marinas.
- **Datos y familias:**
  - Oceanografía física.
  - Temperatura.
  - Salinidad.
  - Biogeoquímica.
  - Recursos pesqueros.
  - Campañas oceanográficas.
  - Ecosistemas marinos.
  - Series de observación.
  - Cartografía marina publicada.
- **Para integrarlo bien:** El acceso a una campaña o informe no garantiza que todos sus datos brutos estén liberados; comprobar repositorio, embargo y licencia.

### F039 · [CSIC · Unidad de Tecnología Marina](https://www.utm.csic.es/index.php/es)

- **Acceso identificado:** Catálogos y servicios de datos de campañas.
- **Geografía:** Buques y campañas oceanográficas.
- **Datos y familias:**
  - Derrotas de campañas publicadas.
  - Datos oceanográficos.
  - Meteorología a bordo.
  - Geofísica marina.
  - Batimetría de campañas disponible.
  - Metadatos de instrumentación.
- **Para integrarlo bien:** Seleccionar campañas sobre España y aguas de interés; la UTM produce también datos de otras regiones del mundo.

### F040 · [MITECO · Costa y medio marino](https://www.miteco.gob.es/es/costas.html)

- **Acceso identificado:** Cartografía, visor y documentos.
- **Geografía:** Litoral, demarcaciones marinas y polígonos.
- **Datos y familias:**
  - Dominio público marítimo-terrestre publicado.
  - Deslindes.
  - Servidumbres.
  - Línea de costa.
  - Playas.
  - Erosión costera.
  - Estrategias marinas.
  - Ordenación del espacio marítimo.
  - Hábitats marinos.
  - Espacios protegidos marinos.
  - Vertidos e infraestructuras publicados.
- **Para integrarlo bien:** La máscara terrestre del atlas no define aguas jurisdiccionales. Distinguir deslinde aprobado, línea de costa y propuesta de planificación.


## Hacienda, economía, finanzas, ayudas y contratación

### F041 · [Banco de España](https://www.bde.es/wbe/es/estadisticas/)

- **Acceso identificado:** Series, descargas y API JSON documentada.
- **Geografía:** Principalmente nacional; territorial según serie.
- **Datos y familias:**
  - Instituciones financieras.
  - Tipos de interés.
  - Depósitos.
  - Crédito.
  - Oficinas bancarias por territorio.
  - Deuda pública.
  - Cuentas financieras.
  - Balanza de pagos.
  - Posición de inversión internacional.
  - Financiación empresarial.
  - Central de Balances agregada.
  - Encuesta Financiera de las Familias.
  - Riqueza.
  - Indicadores económicos.
  - Estadísticas territoriales disponibles.
- **Para integrarlo bien:** Gran parte es nacional. No convertir promedios del país en datos de cada municipio. Microdatos de acceso restringido se mantienen fuera del conjunto abierto.

### F042 · [Agencia Estatal de Administración Tributaria](https://sede.agenciatributaria.gob.es/Sede/estadisticas.html)

- **Acceso identificado:** Tablas y descargas según estadística.
- **Geografía:** Territorio fiscal común, con desglose según producto.
- **Datos y familias:**
  - IRPF.
  - Renta bruta y disponible de declarantes.
  - Estadística municipal de IRPF.
  - Datos por códigos postales en grandes municipios.
  - Salarios declarados.
  - Pensiones declaradas.
  - Prestaciones de desempleo.
  - Patrimonio.
  - Impuesto de sociedades.
  - IVA.
  - Recaudación tributaria.
  - Ventas y empleo empresarial.
  - Aduanas.
  - Comercio exterior.
  - Actividades económicas.
  - Distribuciones tributarias.
- **Para integrarlo bien:** Cobertura foral, umbrales de población y secreto estadístico según operación. Renta por declaración no equivale a renta por hogar ni por persona.

### F043 · [Ministerio de Hacienda · Información territorial y financiación](https://www.hacienda.gob.es/es-ES/CDI/Paginas/centraldeinformacion.aspx)

- **Acceso identificado:** Central de información, tablas y descargas.
- **Geografía:** CCAA, diputaciones y entidades locales.
- **Datos y familias:**
  - Presupuestos.
  - Liquidaciones.
  - Deuda viva.
  - Ingresos.
  - Gastos.
  - Financiación autonómica.
  - Financiación local.
  - Transferencias.
  - Periodo medio de pago.
  - Tipos impositivos locales publicados.
  - IBI.
  - Esfuerzo y capacidad fiscal según producto.
- **Para integrarlo bien:** Identificar el ámbito presupuestario, el perímetro de consolidación y el ejercicio; no confundir presupuesto con ejecución.

### F044 · [Intervención General de la Administración del Estado](https://www.igae.pap.hacienda.gob.es/)

- **Acceso identificado:** Estadísticas, tablas y descargas.
- **Geografía:** Administraciones y subsectores.
- **Datos y familias:**
  - Contabilidad nacional de AAPP.
  - Déficit y superávit.
  - Ingresos y gastos.
  - Ejecución presupuestaria.
  - Clasificación funcional COFOG.
  - Cuentas del sector público.
  - Inventario de entes.
  - Inversión pública territorializada cuando se publique.
  - Fondos europeos.
  - Informes de control públicos.
- **Para integrarlo bien:** Mantener cuentas nacionales y contabilidad presupuestaria como magnitudes diferentes.

### F045 · [IGAE · BDNS / Sistema Nacional de Publicidad de Subvenciones](https://www.infosubvenciones.es/bdnstrans/doc/swagger)

- **Acceso identificado:** API REST pública y descargas.
- **Geografía:** Convocatorias, órganos y ayudas publicadas.
- **Datos y familias:**
  - Convocatorias.
  - Concesiones publicadas.
  - Importes.
  - Administraciones concedentes.
  - Finalidad.
  - Sectores.
  - Instrumentos de ayuda.
  - Fondos financiadores.
  - Ayudas de Estado.
  - De minimis.
  - Ámbitos territoriales declarados.
- **Para integrarlo bien:** La sede del beneficiario no es necesariamente el lugar donde se ejecuta la ayuda. No completar campos que no se publican.

### F046 · [Dirección General del Patrimonio del Estado · PLACSP](https://www.hacienda.gob.es/es-ES/GobiernoAbierto/Datos%20Abiertos/Paginas/licitaciones_plataforma_contratacion.aspx)

- **Acceso identificado:** Ficheros abiertos y sindicación.
- **Geografía:** Órganos de contratación y contratos.
- **Datos y familias:**
  - Licitaciones.
  - Contratos menores publicados.
  - Adjudicaciones.
  - Importes.
  - Fechas.
  - CPV.
  - Procedimiento.
  - Estado de tramitación.
  - Órganos contratantes.
  - Lugares de ejecución declarados.
  - Lotes.
  - Perfiles de contratante.
- **Para integrarlo bien:** Importe máximo, adjudicado y ejecutado no son lo mismo. La publicación depende del perfil y del sistema de agregación.

### F047 · [Autoridad Independiente de Responsabilidad Fiscal · AIReF](https://www.airef.es/es/datalab/ccll-lab/)

- **Acceso identificado:** Observatorios y herramientas con datos consultables.
- **Geografía:** CCAA y entidades locales según observatorio.
- **Datos y familias:**
  - Ingresos locales.
  - Gastos locales.
  - Deuda.
  - Sostenibilidad financiera.
  - Situación de CCAA.
  - Déficit.
  - PIB.
  - Previsiones.
  - Seguimiento del PRTR.
  - Indicadores fiscales.
- **Para integrarlo bien:** Diferenciar datos observados, previsiones y evaluaciones de riesgo. Muchos datos reutilizan Hacienda: conservar ambas procedencias y evitar duplicados.

### F048 · [Comisión Nacional de los Mercados y la Competencia](https://data.cnmc.es/)

- **Acceso identificado:** Datos abiertos descargables.
- **Geografía:** Nacional y territorial según conjunto.
- **Datos y familias:**
  - Electricidad.
  - Gas.
  - Carburantes.
  - Telecomunicaciones.
  - Banda ancha.
  - Líneas fijas.
  - Líneas móviles.
  - Ingresos y tráfico.
  - Sector audiovisual.
  - Mercado postal.
  - Transporte ferroviario.
  - Panel de hogares.
  - Consumos y gastos.
  - Calidad de servicio.
- **Para integrarlo bien:** La escala de mercado o panel no debe convertirse automáticamente en detalle local.

### F049 · [Comisión Nacional del Mercado de Valores](https://www.cnmv.es/portal/Publicaciones/SeriesWeb/Inicio)

- **Acceso identificado:** Series y publicaciones estadísticas.
- **Geografía:** Nacional y entidades según conjunto.
- **Datos y familias:**
  - Emisiones de valores.
  - Mercados secundarios.
  - Fondos de inversión.
  - Sociedades de inversión.
  - Empresas de servicios de inversión.
  - Indicadores de estrés financiero.
  - Registros públicos de entidades.
  - Información financiera pública.
- **Para integrarlo bien:** Muchos indicadores solo tienen significado nacional. La sede de una entidad no representa dónde están todos sus inversores o activos.

### F050 · [Dirección General de Seguros y Fondos de Pensiones](https://dgsfp.mineco.gob.es/)

- **Acceso identificado:** Estadísticas, balances y registros públicos.
- **Geografía:** Nacional y entidades según publicación.
- **Datos y familias:**
  - Seguros.
  - Primas.
  - Prestaciones.
  - Entidades aseguradoras.
  - Planes de pensiones.
  - Fondos de pensiones.
  - Gestoras.
  - Balances.
  - Solvencia agregada.
- **Para integrarlo bien:** Comprobar el nivel de publicación y la reutilización de cada registro.

### F051 · [Secretaría de Estado de Comercio · DataComex y DataInvex](https://comercio.gob.es/datacomex-datainvex/Paginas/Index.aspx)

- **Acceso identificado:** Consulta multidimensional y descargas.
- **Geografía:** Nacional, autonómica y otros desgloses publicados.
- **Datos y familias:**
  - Exportaciones.
  - Importaciones.
  - Productos.
  - País de origen y destino.
  - Sectores.
  - Número de operadores.
  - Inversión extranjera en España.
  - Inversión española exterior.
  - Flujos.
  - Stocks.
  - Empleo asociado publicado.
- **Para integrarlo bien:** La localización de comercio o inversión puede responder a criterios aduaneros o de sede, no al lugar físico de producción.

### F052 · [Tesoro Público](https://www.tesoro.es/)

- **Acceso identificado:** Series, resultados y documentos.
- **Geografía:** Nacional.
- **Datos y familias:**
  - Deuda del Estado.
  - Emisiones.
  - Subastas.
  - Tipos y rentabilidades.
  - Vencimientos.
  - Financiación del Tesoro.
  - Tenencias agregadas publicadas.
- **Para integrarlo bien:** Indicadores de contexto nacional; no inventar desgloses geográficos.

### F053 · [Oficina Española de Patentes y Marcas](https://www.oepm.es/es/sobre-OEPM/estadisticas/)

- **Acceso identificado:** Estadísticas y consulta por producto.
- **Geografía:** Nacional, CCAA y provincias según serie.
- **Datos y familias:**
  - Solicitudes de patentes.
  - Modelos de utilidad.
  - Marcas.
  - Nombres comerciales.
  - Diseños industriales.
  - Evolución temporal.
  - Solicitudes por territorio.
  - Solicitantes agregados.
- **Para integrarlo bien:** La dirección del solicitante no prueba el lugar exacto de desarrollo de la invención.


## Trabajo, empleo, salarios, pensiones y protección laboral

### F054 · [Ministerio de Trabajo y Economía Social](https://www.mites.gob.es/es/estadisticas/)

- **Acceso identificado:** Tablas, anuarios y descargas.
- **Geografía:** Nacional, CCAA y provincia según operación.
- **Datos y familias:**
  - Accidentes de trabajo.
  - Enfermedades profesionales según fuente.
  - Convenios colectivos.
  - Salarios pactados.
  - Huelgas.
  - Cierres patronales.
  - Regulación de empleo.
  - Despidos y conciliaciones publicados.
  - Cooperativas.
  - Sociedades laborales.
  - Economía social.
  - Empresas inscritas.
  - Autorizaciones de trabajo.
  - Condiciones laborales.
  - Anuario de estadísticas.
- **Para integrarlo bien:** El inventario detallado indica variables, unidad responsable y desagregación real de cada operación.

### F055 · [Servicio Público de Empleo Estatal](https://www.sepe.es/HomeSepe/que-es-el-sepe/estadisticas.html)

- **Acceso identificado:** Tablas y ficheros descargables según serie.
- **Geografía:** Municipios, provincias, CCAA y nacional.
- **Datos y familias:**
  - Paro registrado.
  - Contratos.
  - Sexo y edad.
  - Actividad económica.
  - Ocupaciones.
  - Prestaciones por desempleo.
  - Demandantes de empleo.
  - Estadísticas municipales.
  - Observatorio de ocupaciones.
  - Informes del mercado de trabajo.
  - Formación para el empleo.
- **Para integrarlo bien:** Paro registrado no equivale al paro de la EPA. Los valores censurados como menos de cinco no son cero ni un valor exacto.

### F056 · [Seguridad Social · TGSS / INSS y servicios estadísticos](https://www.seg-social.es/wps/portal/wss/internet/EstadisticasPresupuestosEstudios)

- **Acceso identificado:** Series, tablas, eSTADISS y ficheros según operación.
- **Geografía:** Nacional, CCAA, provincia y municipio según serie.
- **Datos y familias:**
  - Afiliación.
  - Altas y bajas.
  - Regímenes.
  - CNAE.
  - Autónomos.
  - Afiliación extranjera.
  - Empresas cotizantes.
  - Pensiones contributivas.
  - Jubilación.
  - Viudedad.
  - Orfandad.
  - Incapacidad permanente.
  - Importes medios.
  - Incapacidad temporal.
  - Nacimiento y cuidado.
  - Ingreso Mínimo Vital.
  - Convenios especiales.
  - Estadísticas presupuestarias.
- **Para integrarlo bien:** Distinguir lugar de residencia, cuenta de cotización y centro de trabajo. No toda variable se publica con todos los cruces territoriales.

### F057 · [Instituto Nacional de Seguridad y Salud en el Trabajo](https://www.insst.es/el-observatorio)

- **Acceso identificado:** Indicadores, encuestas e informes.
- **Geografía:** Nacional y territorial según producto.
- **Datos y familias:**
  - Siniestralidad laboral.
  - Índices de incidencia.
  - Gravedad.
  - Ocupaciones.
  - Sectores de actividad.
  - Condiciones de trabajo.
  - Exposiciones laborales.
  - Enfermedades relacionadas con el trabajo.
  - Colectivos de trabajadores.
- **Para integrarlo bien:** Conservar metodología, denominador y cambios de clasificación de actividad.

### F058 · [Fondo de Garantía Salarial](https://www.mites.gob.es/fogasa/)

- **Acceso identificado:** Estadísticas públicas.
- **Geografía:** Territorial según publicación.
- **Datos y familias:**
  - Prestaciones abonadas.
  - Personas beneficiarias agregadas.
  - Empresas.
  - Salarios garantizados.
  - Indemnizaciones.
  - Expedientes.
  - Evolución temporal.
- **Para integrarlo bien:** Consultar detalle publicado y distinguir expedientes de personas y empresas.


## Protección social, igualdad, juventud y migraciones

### F059 · [Instituto de Mayores y Servicios Sociales](https://imserso.es/el-imserso/documentacion/estadisticas)

- **Acceso identificado:** Estadísticas, datos abiertos e informes.
- **Geografía:** CCAA, provincias, centros y nacional según producto.
- **Datos y familias:**
  - Dependencia SAAD.
  - Solicitudes.
  - Valoraciones.
  - Personas con derecho.
  - Prestaciones.
  - Servicios.
  - Listas de espera según definición.
  - Discapacidad valorada.
  - Pensiones no contributivas.
  - Centros residenciales.
  - Servicios para mayores.
  - Teleasistencia.
  - Ayuda a domicilio.
  - Centros de día.
- **Para integrarlo bien:** Bases de discapacidad y dependencia no equivalen a prevalencia poblacional total. Se publican resultados agregados, no historias personales.

### F060 · [Ministerio de Derechos Sociales, Consumo y Agenda 2030](https://www.dsca.gob.es/)

- **Acceso identificado:** Estadísticas, indicadores y documentos.
- **Geografía:** Nacional y CCAA según sistema.
- **Datos y familias:**
  - Servicios sociales SIUSS.
  - Rentas mínimas de inserción.
  - Prestaciones sociales.
  - Personas usuarias agregadas.
  - Recursos sociales.
  - Familias.
  - Discapacidad.
  - Indicadores sociales.
  - Agenda 2030 y ODS.
  - Consumo y reclamaciones en lo publicado.
- **Para integrarlo bien:** La ficha de cada operación determina cobertura y disponibilidad; parte se presenta en informes.

### F061 · [Observatorio Permanente de la Inmigración](https://www.inclusion.gob.es/es/web/opi/estadisticas/catalogo)

- **Acceso identificado:** Tablas y descargas según producto.
- **Geografía:** Principalmente CCAA y provincia.
- **Datos y familias:**
  - Documentación de residencia en vigor.
  - Autorizaciones concedidas.
  - Régimen comunitario.
  - Estancias por estudios.
  - Concesiones de nacionalidad.
  - Visados.
  - Personas ucranianas documentadas.
  - Menores no acompañados y extutelados en estadísticas publicadas.
  - Indicadores por nacionalidad.
- **Para integrarlo bien:** Población documentada, nacida en el extranjero y de nacionalidad extranjera son universos diferentes.

### F062 · [Instituto de las Mujeres](https://www.inmujeres.gob.es/MujerCifras/Home.htm)

- **Acceso identificado:** Tablas, indicadores e informes.
- **Geografía:** Nacional y territorial según indicador.
- **Datos y familias:**
  - Demografía.
  - Educación.
  - Empleo.
  - Salarios.
  - Cuidados.
  - Uso del tiempo.
  - Poder y representación.
  - Salud.
  - Violencia.
  - Protección social.
  - Indicadores de igualdad.
- **Para integrarlo bien:** Muchos indicadores proceden de otras fuentes oficiales: registrar fuente original y evitar contabilizarlos como datos independientes.

### F063 · [Delegación del Gobierno contra la Violencia de Género](https://violenciagenero.igualdad.gob.es/violenciaencifras/)

- **Acceso identificado:** Portal estadístico, fichas e informes.
- **Geografía:** Nacional, CCAA y provincia según producto.
- **Datos y familias:**
  - Víctimas mortales.
  - Menores.
  - Denuncias publicadas.
  - Órdenes de protección según fuente.
  - 016.
  - ATENPRO.
  - Dispositivos telemáticos.
  - Macroencuesta.
  - Recursos de atención.
  - Indicadores de seguimiento.
- **Para integrarlo bien:** No equiparar denuncias con prevalencia ni ausencia de denuncia con ausencia de violencia. Respetar nivel territorial publicado.

### F064 · [Instituto de la Juventud](https://www.injuve.es/observatorio)

- **Acceso identificado:** Encuestas, indicadores e informes.
- **Geografía:** Nacional y territorial según estudio.
- **Datos y familias:**
  - Demografía juvenil.
  - Empleo.
  - Educación.
  - Emancipación en estudios publicados.
  - Participación.
  - Valores.
  - Hábitos.
  - Salud.
  - Condiciones de vida.
  - Informe Juventud en España.
- **Para integrarlo bien:** No atribuir a INJUVE series de otros observatorios que no sean suyas; comprobar autoría y escala de cada estudio.

### F065 · [Ministerio de Juventud e Infancia · Observatorio de la Infancia](https://observatoriodelainfancia.juventudeinfancia.gob.es/infancia-en-datos)

- **Acceso identificado:** Indicadores, boletines y documentos.
- **Geografía:** Nacional y CCAA según producto.
- **Datos y familias:**
  - Bienestar infantil.
  - Pobreza infantil.
  - Educación.
  - Salud.
  - Protección de menores.
  - Acogimiento residencial.
  - Acogimiento familiar.
  - Adopciones.
  - Medidas del sistema de protección.
  - Indicadores de derechos.
- **Para integrarlo bien:** No hay acceso abierto a expedientes individuales de menores. Mantener comparabilidad entre boletines y sistemas de protección.

### F066 · [Centro de Investigaciones Sociológicas](https://www.cis.es/)

- **Acceso identificado:** Banco de estudios y microdatos; accesos específicos según servicio.
- **Geografía:** Ámbito de cada muestra.
- **Datos y familias:**
  - Barómetros.
  - Opinión pública.
  - Problemas percibidos.
  - Confianza institucional.
  - Actitudes políticas.
  - Intención y recuerdo de voto.
  - Religión.
  - Valores.
  - Hábitos sociales.
  - Encuestas territoriales.
  - Cuestionarios.
  - Series temporales.
- **Para integrarlo bien:** Una muestra nacional no permite estimar cada municipio. Distinguir respuestas, estimaciones, ponderaciones y tamaño muestral.


## Salud, sanidad, epidemiología, medicamentos y alimentación

### F067 · [Ministerio de Sanidad · Sistema de Información Sanitaria](https://www.sanidad.gob.es/estadEstudios/)

- **Acceso identificado:** Banco de datos, aplicaciones y descargas según sistema.
- **Geografía:** CCAA, áreas de salud, centros y nacional según producto.
- **Datos y familias:**
  - Indicadores clave del SNS.
  - Hospitales.
  - Centros de salud.
  - Centros de atención urgente.
  - REGCESS.
  - Profesionales.
  - Camas.
  - Actividad hospitalaria.
  - Altas RAE-CMBD agregadas.
  - Atención primaria BDCAP agregada.
  - Gasto sanitario.
  - Farmacia.
  - Listas de espera.
  - Encuesta de salud.
  - Vacunación.
  - Interrupciones voluntarias del embarazo agregadas.
  - Salud sexual y reproductiva.
  - Sanidad ambiental.
  - Calidad del agua SINAC pública.
  - Aguas de baño NÁYADE.
  - Cobertura y recursos.
  - Seguridad del paciente en lo publicado.
- **Para integrarlo bien:** Una base clínica existente no es una base de historias individuales abiertas. Publicar solo agregados y variables efectivamente disponibles.

### F068 · [Instituto de Salud Carlos III · Centro Nacional de Epidemiología](https://cne.isciii.es/)

- **Acceso identificado:** Datos, tablas e informes según sistema.
- **Geografía:** Nacional, CCAA, provincia y otras unidades publicadas.
- **Datos y familias:**
  - RENAVE.
  - Enfermedades de declaración obligatoria.
  - Vigilancia respiratoria SiVIRA.
  - Gripe.
  - COVID-19.
  - Mortalidad MoMo.
  - Exceso de mortalidad.
  - Mortalidad atribuible a temperatura.
  - Alertas Kairós.
  - Mortalidad por causas en productos publicados.
  - Epidemiología ambiental.
  - Indicadores de vigilancia.
- **Para integrarlo bien:** Distinguir vigilancia provisional, datos consolidados y estimaciones modelizadas. No hay promesa de datos individuales abiertos.

### F069 · [Agencia Española de Medicamentos y Productos Sanitarios](https://sede.aemps.gob.es/datos-abiertos/)

- **Acceso identificado:** CIMA y servicios REST documentados; otros productos según acceso.
- **Geografía:** Nacional, productos y centros según sistema.
- **Datos y familias:**
  - Medicamentos autorizados.
  - Principios activos.
  - Presentaciones.
  - Situación de comercialización.
  - Fichas técnicas.
  - Prospectos.
  - Nomenclátor.
  - Problemas de suministro publicados.
  - Ensayos clínicos públicos REec.
  - Medicamentos veterinarios según catálogo.
- **Para integrarlo bien:** Muchos datos son de productos, no geográficos: pueden complementar fichas de centros, no producir un mapa municipal de consumo inexistente.

### F070 · [Organización Nacional de Trasplantes](https://www.ont.es/)

- **Acceso identificado:** Balances, memorias y estadísticas.
- **Geografía:** CCAA, hospitales y nacional según publicación.
- **Datos y familias:**
  - Donación.
  - Trasplantes por órgano.
  - Tejidos.
  - Listas de espera agregadas.
  - Actividad por centros publicada.
  - Donantes agregados.
  - Receptores agregados.
  - Evolución temporal.
- **Para integrarlo bien:** La información clínica individual no es abierta. La actividad hospitalaria no representa residencia de los pacientes.

### F071 · [Agencia Española de Seguridad Alimentaria y Nutrición](https://www.aesan.gob.es/)

- **Acceso identificado:** Estudios, informes y datos según producto.
- **Geografía:** Ámbito muestral y territorial publicado.
- **Datos y familias:**
  - ALADINO.
  - Sobrepeso y obesidad.
  - Hábitos alimentarios.
  - Nutrición infantil.
  - Consumo alimentario en estudios.
  - Riesgos alimentarios.
  - Alertas publicadas.
  - Seguridad alimentaria.
- **Para integrarlo bien:** No convertir una encuesta nacional en estimaciones locales sin diseño y soporte estadístico.

### F072 · [Plan Nacional sobre Drogas · OEDA](https://pnsd.sanidad.gob.es/profesionales/sistemasInformacion/)

- **Acceso identificado:** Encuestas, tablas e informes.
- **Geografía:** Nacional y CCAA según estudio.
- **Datos y familias:**
  - EDADES.
  - ESTUDES.
  - Consumo de alcohol.
  - Tabaco.
  - Cannabis y otras drogas.
  - Adicciones comportamentales.
  - Admisiones a tratamiento.
  - Urgencias.
  - Mortalidad relacionada.
  - Oferta y decomisos según fuente.
- **Para integrarlo bien:** Separar encuesta de consumo, indicador sanitario y actividad policial.


## Educación, universidad, investigación e innovación

### F073 · [Ministerio de Educación, Formación Profesional y Deportes · EDUCAbase](https://www.educacionfpydeportes.gob.es/servicios-al-ciudadano/estadisticas.html)

- **Acceso identificado:** Tablas multidimensionales y descargas.
- **Geografía:** CCAA, provincias, centros y otras unidades según operación.
- **Datos y familias:**
  - Centros educativos.
  - Enseñanzas.
  - Alumnado.
  - Profesorado.
  - Ratios.
  - Escolarización.
  - Repetición.
  - Idoneidad.
  - Abandono educativo.
  - Alumnado extranjero.
  - Necesidades específicas.
  - Becas y ayudas.
  - Gasto educativo.
  - FP.
  - Formación de adultos.
  - Inserción laboral de FP.
  - Resultados educativos.
  - Lenguas de enseñanza según publicación.
- **Para integrarlo bien:** No todos los resultados o características se publican por centro; el registro de centros y las estadísticas tienen coberturas diferentes.

### F074 · [Ministerio de Ciencia, Innovación y Universidades · SIIU](https://www.ciencia.gob.es/Ministerio/Estadisticas/SIIU.html)

- **Acceso identificado:** Tablas y descargas.
- **Geografía:** Universidades, campus, centros y CCAA según producto.
- **Datos y familias:**
  - Universidades.
  - Centros.
  - Titulaciones.
  - Estudiantes.
  - Matrículas.
  - Egresados.
  - Rendimiento.
  - Abandono.
  - Movilidad.
  - Personal universitario.
  - Becas.
  - Financiación.
  - Inserción laboral.
  - Precios públicos.
- **Para integrarlo bien:** Una universidad puede tener centros en distintas provincias; no asignar todo a su sede central.

### F075 · [Ministerio de Ciencia, Innovación y Universidades · SICTI](https://www.ciencia.gob.es/Ministerio/Estadisticas.html)

- **Acceso identificado:** Indicadores y estadísticas.
- **Geografía:** Nacional y territorial según indicador.
- **Datos y familias:**
  - Gasto en I+D.
  - Personal investigador.
  - Financiación científica.
  - Innovación.
  - Recursos humanos.
  - Resultados científicos.
  - Ayudas públicas.
  - Transferencia.
  - Indicadores de ciencia y tecnología.
- **Para integrarlo bien:** Parte procede del INE y otras entidades: conservar la procedencia original.

### F076 · [Agencia Estatal de Investigación](https://www.aei.gob.es/)

- **Acceso identificado:** Resoluciones y datos de convocatorias.
- **Geografía:** Proyectos y entidades beneficiarias publicadas.
- **Datos y familias:**
  - Convocatorias.
  - Proyectos concedidos.
  - Importes.
  - Programas.
  - Áreas científicas.
  - Centros beneficiarios.
  - Ayudas de recursos humanos.
  - Resultados agregados.
- **Para integrarlo bien:** La geografía de una sede beneficiaria no describe necesariamente dónde se realiza todo el trabajo científico.

### F077 · [Centro para el Desarrollo Tecnológico y la Innovación](https://www.cdti.es/)

- **Acceso identificado:** Estadísticas, resultados y datos publicados.
- **Geografía:** Proyectos, entidades y territorios publicados.
- **Datos y familias:**
  - Proyectos financiados.
  - Ayudas a I+D empresarial.
  - Innovación tecnológica.
  - Importes.
  - Sectores.
  - Programas.
  - Distribución territorial.
  - Participación internacional.
- **Para integrarlo bien:** Confirmar la disponibilidad de ficheros y no convertir información confidencial de proyectos en datos abiertos.

### F078 · [CSIC · DIGITAL.CSIC y repositorios de investigación](https://digital.csic.es/)

- **Acceso identificado:** Catálogo, repositorio y datos de investigación por depósito.
- **Geografía:** Cobertura de cada investigación.
- **Datos y familias:**
  - Conjuntos científicos.
  - Series experimentales.
  - Datos ambientales.
  - Ecología.
  - Geociencias.
  - Ciencias marinas.
  - Arqueología.
  - Ciencias sociales.
  - Datos históricos.
  - Software y documentación.
- **Para integrarlo bien:** Filtrar España y las aguas de interés. No todo depósito es dato ni todo fichero está abierto; revisar licencia, embargo y relación con el artículo.

### F079 · [Universidades públicas · portales y repositorios](https://www.universidata.es/)

- **Acceso identificado:** Portales propios, repositorios y agregadores.
- **Geografía:** Campus, centros y ámbitos de cada universidad.
- **Datos y familias:**
  - Docencia.
  - Estudiantes.
  - Personal.
  - Presupuestos.
  - Contratos.
  - Investigación.
  - Proyectos.
  - Equipamientos.
  - Inventarios científicos.
  - Conjuntos de investigación.
  - Empleo y resultados universitarios.
- **Para integrarlo bien:** UniversiDATA es una plataforma de descubrimiento; verificar el publicador universitario original. No atribuir carácter oficial estadístico a todo resultado de investigación.


## Cultura, patrimonio, archivos, religión, memoria y deporte

### F080 · [Ministerio de Cultura · CULTURABase](https://www.cultura.gob.es/servicios-a-la-ciudadania/estadisticas/cultura/mc/culturabase/portada.html)

- **Acceso identificado:** Tablas, anuarios y descargas.
- **Geografía:** CCAA y otras unidades según operación.
- **Datos y familias:**
  - Museos.
  - Colecciones museográficas.
  - Bibliotecas.
  - Archivos.
  - Patrimonio protegido.
  - Libros ISBN.
  - Edición musical ISMN.
  - Artes escénicas.
  - Música y danza.
  - Cinematografía.
  - Cines y exhibición.
  - Hábitos y prácticas culturales.
  - Empleo cultural.
  - Empresas culturales.
  - Gasto público.
  - Gasto de hogares.
  - Comercio exterior cultural.
  - Propiedad intelectual.
  - Asuntos taurinos.
- **Para integrarlo bien:** Los registros de bienes y las estadísticas de oferta, empleo y visitantes son capas diferentes.

### F081 · [Biblioteca Nacional de España](https://www.bne.es/es/perfiles/bibliotecarios/suministro-registros)

- **Acceso identificado:** Datos abiertos, catálogos y servicios bibliográficos.
- **Geografía:** Obras, autores, lugares y colecciones.
- **Datos y familias:**
  - Registros bibliográficos.
  - Autoridades.
  - Lugares de publicación.
  - Mapas y planos.
  - Cartografía histórica.
  - Hemeroteca.
  - Colecciones digitalizadas.
  - Datos de actividad de la biblioteca.
  - Datos enlazados.
  - Recursos de BNElab.
- **Para integrarlo bien:** Que un registro sea abierto no implica que todas las imágenes de la obra puedan redistribuirse sin revisar derechos.

### F082 · [Ministerio de Cultura · PARES y archivos estatales](https://pares.cultura.gob.es/)

- **Acceso identificado:** Catálogos, registros e imágenes según derechos.
- **Geografía:** Archivos, documentos y lugares descritos.
- **Datos y familias:**
  - Archivos estatales.
  - Fondos documentales.
  - Descripciones archivísticas.
  - Documentos digitalizados.
  - Referencias históricas territoriales.
  - Mapas y planos de archivo.
  - Estadísticas de descripción y digitalización.
- **Para integrarlo bien:** Revisar derechos de reproducción y extracción; la existencia del visor no acredita una API masiva libre.

### F083 · [Instituto del Patrimonio Cultural de España](https://www.cultura.gob.es/cultura/areas/patrimonio/mc/ipce/inicio.html)

- **Acceso identificado:** Inventarios, proyectos y catálogos publicados.
- **Geografía:** Bienes y lugares.
- **Datos y familias:**
  - Patrimonio histórico.
  - Proyectos de conservación.
  - Patrimonio industrial.
  - Arquitectura tradicional.
  - Patrimonio inmaterial.
  - Fototecas.
  - Planes nacionales de patrimonio.
- **Para integrarlo bien:** Las fichas y fotografías pueden tener condiciones de reutilización distintas.

### F084 · [Consejo Superior de Deportes · DEPORTEData](https://www.csd.gob.es/es/datos-abiertos)

- **Acceso identificado:** Estadísticas y ficheros abiertos.
- **Geografía:** CCAA, instalaciones y otras unidades según conjunto.
- **Datos y familias:**
  - Licencias federativas.
  - Clubes.
  - Federaciones.
  - Modalidades deportivas.
  - Deporte universitario.
  - Deporte de alto nivel.
  - Competiciones.
  - Instalaciones en censos publicados.
  - Empleo y economía deportiva según fuente.
  - Hábitos deportivos.
  - Discapacidad y deporte en lo publicado.
- **Para integrarlo bien:** No asumir un inventario actualizado de todas las instalaciones si el producto procede de un censo antiguo.

### F085 · [Fundación Pluralismo y Convivencia · Observatorio del Pluralismo Religioso](https://www.observatorioreligion.es/directorio-lugares-culto/)

- **Acceso identificado:** Directorio, mapa e informes.
- **Geografía:** Lugares de culto y territorios.
- **Datos y familias:**
  - Lugares de culto.
  - Confesiones.
  - Distribución territorial.
  - Tipología de equipamientos.
  - Series e informes publicados.
- **Para integrarlo bien:** Validar cobertura, actualización y licencia del directorio; no inferir creencias personales de la población por la proximidad a un lugar de culto.

### F086 · [Secretaría de Estado de Memoria Democrática](https://mpt.gob.es/memoria-democratica/mapa-de-fosas/guia-de-fosas-por-comunidades-autonomas)

- **Acceso identificado:** Mapas, directorios y documentos.
- **Geografía:** Lugares y CCAA.
- **Datos y familias:**
  - Mapas de fosas.
  - Localizaciones publicadas.
  - Exhumaciones.
  - Actuaciones.
  - Mapas autonómicos institucionales.
  - Lugares de memoria publicados.
- **Para integrarlo bien:** Distinguir inventario, investigación y localización confirmada; condiciones y detalle según autoridad.


## Agricultura, ganadería, pesca, alimentación y medio rural

### F087 · [Ministerio de Agricultura, Pesca y Alimentación](https://www.mapa.gob.es/es/estadistica/temas/)

- **Acceso identificado:** Tablas, anuarios, descargas y cartografía.
- **Geografía:** Nacional, CCAA, provincia y otras unidades según producto.
- **Datos y familias:**
  - ESYRCE.
  - Superficies cultivadas.
  - Rendimientos.
  - Producciones agrícolas.
  - Calendarios de siembra.
  - Calendarios de recolección.
  - Regadío y secano.
  - Ganado bovino.
  - Ganado porcino.
  - Ovino y caprino.
  - Avicultura.
  - Producción láctea.
  - Sacrificios.
  - Producción ecológica.
  - Precios agrarios.
  - Renta agraria.
  - Cuentas económicas.
  - Medios de producción.
  - Maquinaria agrícola.
  - Fertilizantes.
  - Fitosanitarios.
  - Consumo alimentario.
  - Industria alimentaria.
  - DOP e IGP.
  - Pesca marítima.
  - Flota pesquera.
  - Capturas y desembarques.
  - Acuicultura.
  - Precios pesqueros.
  - Seguros agrarios.
  - Medio rural.
- **Para integrarlo bien:** Cada operación tiene su propio desglose. Un desembarque en un puerto no identifica el lugar donde se capturó el pescado.

### F088 · [Fondo Español de Garantía Agraria · FEGA](https://www.fega.gob.es/)

- **Acceso identificado:** SIGPAC, datos e informes.
- **Geografía:** Recintos agrícolas y ámbitos PAC.
- **Datos y familias:**
  - Recintos SIGPAC.
  - Usos de parcela.
  - Superficies.
  - Campañas.
  - Elegibilidad.
  - Ayudas PAC agregadas.
  - Beneficiarios publicados.
  - Importes.
  - FEAGA.
  - FEADER.
  - Indicadores de gestión.
- **Para integrarlo bien:** Un recinto no es necesariamente una parcela catastral. No reutilizar datos personales no necesarios para la representación estadística.

### F089 · [MAPA · Sistema de Información Agroclimática para el Regadío](https://servicio.mapa.gob.es/siarweb/home)

- **Acceso identificado:** Consultas, series e API según condiciones del servicio.
- **Geografía:** Estaciones agroclimáticas.
- **Datos y familias:**
  - Temperatura.
  - Humedad.
  - Precipitación.
  - Viento.
  - Radiación.
  - Evapotranspiración.
  - Ubicación de estaciones.
  - Series históricas.
  - Informes agroclimáticos.
- **Para integrarlo bien:** Red orientada al regadío; no sustituye una malla climática uniforme.

### F090 · [MAPA · Sistema de Información Geográfica de Datos Agrarios](https://www.mapa.gob.es/es/agricultura/temas/sistema-de-informacion-geografica-de-datos-agrarios)

- **Acceso identificado:** Visor e información cartográfica.
- **Geografía:** Municipios, estaciones y cartografía temática.
- **Datos y familias:**
  - Cultivos y aprovechamientos.
  - Variables agroclimáticas.
  - Caracterización municipal.
  - Estaciones.
  - Información agraria territorial.
- **Para integrarlo bien:** Ver la antigüedad y escala de cada capa; no confundir un producto histórico con cobertura actual.

### F091 · [MAPA · Caminos Naturales](https://www.mapa.gob.es/es/desarrollo-rural/temas/caminos-naturales)

- **Acceso identificado:** Fichas, mapas y recursos según itinerario.
- **Geografía:** Rutas y tramos de su programa.
- **Datos y familias:**
  - Itinerarios.
  - Trazados publicados.
  - Etapas.
  - Distancias.
  - Características de uso.
  - Equipamientos.
  - Patrimonio asociado.
  - Conexiones territoriales.
- **Para integrarlo bien:** No es un inventario de todos los senderos españoles ni de todos los GR homologados.

### F092 · [Agencia de Información y Control Alimentarios](https://www.aica.gob.es/)

- **Acceso identificado:** Estadísticas y publicaciones.
- **Geografía:** Mercados y desgloses publicados.
- **Datos y familias:**
  - Información de mercados agroalimentarios.
  - Aceite de oliva.
  - Aceituna de mesa.
  - Existencias y movimientos publicados.
  - Actividad inspectora agregada.
  - Cadena alimentaria.
- **Para integrarlo bien:** Comprobar qué series continúan bajo AICA y cuáles bajo el ministerio competente tras reorganizaciones.

### F093 · [Entidad Estatal de Seguros Agrarios](https://www.mapa.gob.es/es/enesa/)

- **Acceso identificado:** Estadísticas, mapas e informes.
- **Geografía:** Ámbitos de contratación y siniestralidad publicados.
- **Datos y familias:**
  - Contratación de seguros.
  - Superficie asegurada.
  - Producción asegurada.
  - Capital asegurado.
  - Subvenciones.
  - Siniestralidad agregada.
  - Líneas de seguro.
- **Para integrarlo bien:** No trasladar riesgo actuarial individual ni información privada de explotaciones al mapa.


## Energía, industria y conectividad

### F094 · [MITECO · Energía y minas](https://www.miteco.gob.es/es/energia.html)

- **Acceso identificado:** Estadísticas, registros públicos y cartografía.
- **Geografía:** Nacional y territorial según producto.
- **Datos y familias:**
  - Balances energéticos.
  - Producción eléctrica.
  - Consumo energético.
  - Renovables.
  - Potencia instalada.
  - Instalaciones de generación publicadas.
  - Hidrocarburos.
  - Gas.
  - Eficiencia energética.
  - Estadística minera.
  - Producciones minerales.
  - Explotaciones publicadas.
  - Carburantes.
  - Puntos de recarga publicados.
- **Para integrarlo bien:** No todos los registros administrativos ni características técnicas de redes son abiertos.

### F095 · [MITECO · Geoportal de gasolineras y recarga](https://geoportalgasolineras.es/geoportal-instalaciones/Inicio)

- **Acceso identificado:** Consulta y servicios públicos según recurso.
- **Geografía:** Estaciones e instalaciones publicadas.
- **Datos y familias:**
  - Localización.
  - Precios de carburantes.
  - Combustibles.
  - Horarios.
  - Servicios.
  - Instalaciones marítimas publicadas.
  - Puntos de recarga publicados.
  - Características de recarga disponibles.
- **Para integrarlo bien:** Los datos proceden de comunicaciones de titulares. Precio, fecha y hora deben conservarse juntos.

### F096 · [Instituto para la Diversificación y Ahorro de la Energía](https://www.idae.es/)

- **Acceso identificado:** Estudios, estadísticas e inventarios publicados.
- **Geografía:** Ámbitos de cada estudio.
- **Datos y familias:**
  - Consumos finales.
  - Eficiencia.
  - Edificación.
  - Usos energéticos.
  - Renovables.
  - Balance de energías.
  - Movilidad energética.
  - Programas de ayudas.
- **Para integrarlo bien:** Parte son estudios o estimaciones; confirmar si existe fichero reutilizable y detalle territorial.

### F097 · [Corporación de Reservas Estratégicas de Productos Petrolíferos · CORES](https://www.cores.es/estadisticas)

- **Acceso identificado:** Series y descargas.
- **Geografía:** Nacional y desgloses publicados.
- **Datos y familias:**
  - Demanda.
  - Consumos.
  - Producción.
  - Refino.
  - Capacidad de refinerías.
  - Importaciones.
  - Exportaciones.
  - Existencias.
  - Reservas.
  - GLP.
  - Gas natural.
  - Productos petrolíferos.
- **Para integrarlo bien:** Corporación de derecho público con función estadística. No toda serie tiene desglose autonómico o provincial.

### F098 · [Ministerio de Industria y Turismo · Estadísticas industriales](https://www.mintur.gob.es/es-es/IndicadoresyEstadisticas/Paginas/Estadisticas.aspx)

- **Acceso identificado:** Estadísticas, registros y documentos.
- **Geografía:** Nacional y territorial según producto.
- **Datos y familias:**
  - Coyuntura industrial.
  - Sectores industriales.
  - PYME.
  - Actividad empresarial.
  - Registro industrial publicado.
  - Áreas industriales publicadas.
  - Ayudas industriales.
  - Indicadores de política industrial.
- **Para integrarlo bien:** El INE publica muchas estadísticas industriales: diferenciar fuente original, registro y explotación derivada.

### F099 · [Secretaría de Estado de Telecomunicaciones · Conectemos](https://conectemos.digital.gob.es/es/mapas-y-graficos/cobertura-banda-ancha-fija)

- **Acceso identificado:** Mapas y ficheros reutilizables por publicación.
- **Geografía:** CCAA, provincias, municipios y otras unidades publicadas.
- **Datos y familias:**
  - Cobertura fija.
  - Fibra.
  - Otras tecnologías.
  - Velocidades.
  - Cobertura 4G.
  - Cobertura 5G.
  - Zonas de actuación.
  - Brecha territorial.
  - Evolución histórica.
  - Servicios disponibles publicados.
- **Para integrarlo bien:** La cobertura teórica no es medición de velocidad real ni garantía de contratación en cada domicilio.

### F100 · [Red.es · Observatorio Nacional de Tecnología y Sociedad](https://www.ontsi.es/)

- **Acceso identificado:** Indicadores, estudios y descargas según producto.
- **Geografía:** Nacional y territorial según indicador.
- **Datos y familias:**
  - Sociedad digital.
  - Uso de internet.
  - Competencias digitales.
  - Digitalización empresarial.
  - Economía digital.
  - Comercio electrónico.
  - Sector TIC.
  - Brechas digitales.
  - Servicios públicos digitales.
- **Para integrarlo bien:** Algunos indicadores son reutilizaciones de INE o Eurostat: conservar trazabilidad.


## Movilidad, carreteras, ferrocarril, aviación y puertos

### F101 · [Ministerio de Transportes y Movilidad Sostenible · OTLE y estadísticas](https://www.transportes.gob.es/)

- **Acceso identificado:** Observatorios, datos, mapas e informes.
- **Geografía:** Redes y territorios según operación.
- **Datos y familias:**
  - Red de carreteras.
  - Longitudes.
  - Aforos de tráfico.
  - Intensidades medias diarias.
  - Transporte de mercancías por carretera.
  - Transporte de viajeros.
  - Ferrocarril.
  - Aviación.
  - Transporte marítimo.
  - Logística.
  - Movilidad.
  - Costes del transporte.
  - Emisiones del transporte.
  - Infraestructuras.
  - Accesibilidad.
  - Licitación y obras públicas.
  - Observatorio del transporte de mercancías.
  - Atlas de movilidad publicados.
- **Para integrarlo bien:** Hay estudios y series con cobertura temporal específica. No confundir vehículos, viajeros, viajes y viajeros-kilómetro.

### F102 · [Ministerio de Transportes · Punto de Acceso Nacional multimodal](https://nap.transportes.gob.es/Home/)

- **Acceso identificado:** Descargas y API documentada con condiciones de acceso.
- **Geografía:** Operadores, líneas, paradas y regiones.
- **Datos y familias:**
  - Paradas.
  - Rutas.
  - Horarios.
  - Calendarios.
  - Servicios.
  - Operadores.
  - GTFS.
  - NeTEx donde se publique.
  - Accesibilidad incluida en el feed.
  - Cobertura territorial de oferta.
- **Para integrarlo bien:** La cobertura depende de cada operador y fecha del feed. El catálogo puede incluir operadores privados: mantener procedencia.

### F103 · [Dirección General de Tráfico](https://www.dgt.es/menusecundario/dgt-en-cifras/)

- **Acceso identificado:** Estadísticas, descargas y NAP.
- **Geografía:** Tramos, puntos, municipios, provincias y CCAA según producto.
- **Datos y familias:**
  - Siniestros.
  - Fallecidos.
  - Heridos.
  - Parque de vehículos.
  - Distintivo ambiental.
  - Propulsión.
  - Antigüedad.
  - Matriculaciones.
  - Transferencias.
  - Bajas.
  - Censo de conductores.
  - Permisos.
  - Autoescuelas.
  - Radares publicados.
  - Incidencias.
  - Restricciones.
  - Equipamiento.
  - Recarga y otros feeds del NAP.
- **Para integrarlo bien:** Ver cobertura específica de Cataluña y País Vasco y las competencias de sus autoridades. Estadística anual y tráfico en directo son productos distintos.

### F104 · [Adif y Adif Alta Velocidad](https://www.adif.es/sobre-adif/declaracion-red)

- **Acceso identificado:** Declaración de red, anexos e información pública.
- **Geografía:** Líneas, tramos, estaciones y terminales.
- **Datos y familias:**
  - Red ferroviaria administrada.
  - Características de líneas.
  - Anchos de vía.
  - Electrificación.
  - Estaciones.
  - Terminales.
  - Instalaciones de servicio.
  - Capacidad publicada.
  - Tráfico agregado.
  - Obras y actuaciones publicadas.
- **Para integrarlo bien:** No cubre automáticamente todas las redes autonómicas, metropolitanas, privadas o históricas. Completar con sus gestores y con IGN.

### F105 · [Renfe · Renfe Data](https://data.renfe.com/es/)

- **Acceso identificado:** Catálogo de datos abiertos.
- **Geografía:** Servicios, estaciones y vehículos publicados.
- **Datos y familias:**
  - Horarios.
  - Cercanías.
  - Media distancia.
  - Larga distancia.
  - Alta velocidad.
  - Estaciones.
  - Accesibilidad.
  - Avisos.
  - Incidencias.
  - Posición de vehículos donde esté publicada.
  - Actualizaciones de viaje.
- **Para integrarlo bien:** No asumir tiempo real universal ni cobertura de operadores distintos de Renfe.

### F106 · [Aena](https://www.aena.es/es/estadisticas/inicio.html)

- **Acceso identificado:** Informes y hojas de cálculo; consultas detalladas con registro.
- **Geografía:** Aeropuertos gestionados y series publicadas.
- **Datos y familias:**
  - Pasajeros.
  - Operaciones.
  - Mercancías.
  - Tráfico mensual.
  - Tráfico anual.
  - Rutas y destinos en consultas.
  - Series históricas.
  - Datos por aeropuerto.
- **Para integrarlo bien:** No incluye por sí sola todos los aeródromos españoles. El detalle personalizado puede requerir registro.

### F107 · [ENAIRE · Información aeronáutica](https://aip.enaire.es/AIP/DatosDigitales-en.html)

- **Acceso identificado:** AIP y conjuntos digitales públicos según producto.
- **Geografía:** Espacio aéreo, aeropuertos y puntos aeronáuticos.
- **Datos y familias:**
  - Aeródromos.
  - Pistas.
  - Espacios aéreos.
  - Zonas restringidas publicadas.
  - Rutas ATS.
  - Puntos de navegación.
  - Radioayudas.
  - Obstáculos publicados.
  - Cartas aeronáuticas.
  - Información de procedimientos.
- **Para integrarlo bien:** Datos operacionales sujetos a ciclos y condiciones. El atlas no sustituye documentación vigente de navegación.

### F108 · [Puertos del Estado · Estadística y ayudas a la navegación](https://www.puertos.es/)

- **Acceso identificado:** Estadísticas, anuarios y portales públicos.
- **Geografía:** Puertos y autoridades portuarias.
- **Datos y familias:**
  - Mercancías.
  - Pasajeros.
  - Buques.
  - Contenedores.
  - Tráfico por productos.
  - Cruceros.
  - Infraestructura portuaria.
  - Conexiones ferroviarias publicadas.
  - Faros.
  - Balizas.
  - Ayudas a navegación.
  - Series mensuales y anuales.
- **Para integrarlo bien:** Las autoridades autonómicas gestionan otros puertos. Distinguir movimiento de mercancía de origen o destino final.


## Turismo, vivienda, suelo y organización urbana

### F109 · [Turespaña](https://conocimiento.tourspain.es/es/)

- **Acceso identificado:** Estadísticas, estudios y descargas.
- **Geografía:** CCAA y mercados de origen según producto.
- **Datos y familias:**
  - Turismo internacional.
  - Coyuntura de mercados.
  - Gasto.
  - Estancias.
  - Llegadas aéreas.
  - Empleo turístico.
  - Satisfacción turística.
  - Motivación del viaje.
  - Segmentos de demanda.
  - Históricos FAMILITUR y EGATUR de su etapa de producción.
- **Para integrarlo bien:** Parte de los datos actuales proceden del INE. No contarlos como nuevas observaciones independientes.

### F110 · [SEGITTUR](https://www.segittur.es/)

- **Acceso identificado:** Plataformas, estudios e indicadores públicos según producto.
- **Geografía:** Destinos turísticos participantes.
- **Datos y familias:**
  - Destinos turísticos inteligentes.
  - Indicadores de destino publicados.
  - Recursos turísticos.
  - Sostenibilidad.
  - Digitalización.
  - Conocimiento turístico.
  - Proyectos y actuaciones.
- **Para integrarlo bien:** No dar por abierto todo dato de las plataformas de gestión de destinos: revisar acceso y producto.

### F111 · [Ministerio de Vivienda y Agenda Urbana](https://www.mivau.gob.es/)

- **Acceso identificado:** Tablas, atlas, visores y descargas.
- **Geografía:** CCAA, provincia, municipio y sección según producto.
- **Datos y familias:**
  - Valor tasado de vivienda.
  - Transacciones.
  - Vivienda protegida.
  - Vivienda libre.
  - Parque residencial.
  - Rehabilitación.
  - Alquiler SERPAVI.
  - Atlas del alquiler.
  - Suelo urbano.
  - Sistema de Información Urbana.
  - Planeamiento publicado.
  - Sectores residenciales.
  - Atlas de áreas urbanas.
  - Vulnerabilidad urbana.
  - Áreas urbanas funcionales.
  - Agenda Urbana.
- **Para integrarlo bien:** Precio de oferta, valor tasado, renta declarada y referencia de alquiler no son intercambiables. Los atlas históricos tienen sus años propios.


## Elecciones, parlamentos, administración, justicia y seguridad

### F112 · [Ministerio del Interior · Infoelectoral](https://infoelectoral.interior.gob.es/es/elecciones-celebradas/area-de-descargas/)

- **Acceso identificado:** Resultados y ficheros descargables por proceso.
- **Geografía:** Circunscripción, municipio y mesa según elección.
- **Datos y familias:**
  - Censo electoral.
  - Participación.
  - Abstención.
  - Votos.
  - Candidaturas.
  - Voto blanco.
  - Voto nulo.
  - Escaños.
  - Referéndums.
  - Elecciones generales.
  - Elecciones europeas.
  - Elecciones municipales.
  - Series históricas.
  - Resultados por mesa publicados.
- **Para integrarlo bien:** Los procesos autonómicos y algunos datos locales requieren sus autoridades electorales. Distinguir provisional y definitivo y las geometrías de cada fecha.

### F113 · [Congreso de los Diputados](https://www.congreso.es/datos-abiertos)

- **Acceso identificado:** Datos abiertos y consulta parlamentaria.
- **Geografía:** Representación por circunscripción y actividad nacional.
- **Datos y familias:**
  - Diputados.
  - Grupos.
  - Circunscripciones.
  - Iniciativas.
  - Votaciones.
  - Comisiones.
  - Publicaciones.
  - Actividad parlamentaria.
- **Para integrarlo bien:** Las iniciativas se pueden vincular a territorios cuando exista relación documentada; no inferirla solo de una palabra en el título.

### F114 · [Senado](https://www.senado.es/web/relacionesciudadanos/datosabiertos/informaciodatosabiertos/index.html?lang=es_ES)

- **Acceso identificado:** Catálogos reutilizables, incluidos XML.
- **Geografía:** Representación territorial y actividad nacional.
- **Datos y familias:**
  - Senadores.
  - Circunscripciones.
  - Grupos.
  - Órganos.
  - Iniciativas.
  - Votaciones.
  - Mociones.
  - Publicaciones.
  - Presupuestos publicados.
- **Para integrarlo bien:** Mantener legislatura, fecha y mandato.

### F115 · [Agencia Estatal Boletín Oficial del Estado](https://www.boe.es/datosabiertos/api/api.php)

- **Acceso identificado:** API de legislación, sumarios y tablas auxiliares.
- **Geografía:** Normas y anuncios con ámbito territorial identificable.
- **Datos y familias:**
  - Legislación consolidada.
  - Sumarios BOE.
  - Sumarios BORME.
  - Metadatos ELI.
  - Tablas auxiliares.
  - Normas territoriales enlazables.
  - Anuncios oficiales publicados.
- **Para integrarlo bien:** La API de sumarios BORME no equivale a una base completa abierta del Registro Mercantil. Versionar vigencia y fecha de cada norma.

### F116 · [Ministerio de Política Territorial · Registro de Entidades Locales](https://ssweb.seap.minhap.es/REL/)

- **Acceso identificado:** Registro y consulta pública.
- **Geografía:** Entidades locales.
- **Datos y familias:**
  - Municipios.
  - Provincias.
  - Islas.
  - Mancomunidades.
  - Comarcas administrativas inscritas.
  - Entidades de ámbito inferior al municipio.
  - Códigos.
  - Denominaciones.
  - Adscripciones.
- **Para integrarlo bien:** El registro administrativo no define todas las comarcas geográficas, históricas o funcionales.

### F117 · [Administración digital · DIR3](https://administracionelectronica.gob.es/ctt/dir3)

- **Acceso identificado:** Directorio y servicios públicos según modalidad.
- **Geografía:** Unidades administrativas y oficinas.
- **Datos y familias:**
  - Organismos.
  - Unidades orgánicas.
  - Oficinas.
  - Códigos DIR3.
  - Dependencias.
  - Vigencias.
  - Relaciones administrativas.
- **Para integrarlo bien:** Comprobar qué campos son descargables públicamente y cuáles están orientados a integraciones administrativas.

### F118 · [Función Pública · Estadística del personal público](https://digital.gob.es/funcion-publica.html)

- **Acceso identificado:** Boletines, series y tablas.
- **Geografía:** Administraciones y territorios publicados.
- **Datos y familias:**
  - BEPSAP.
  - Empleo público.
  - Administración de adscripción.
  - Sexo.
  - Edad.
  - Tipo de personal.
  - Distribución territorial.
  - Oferta de empleo público publicada.
- **Para integrarlo bien:** No confundir personal del Registro Central de Personal con todas las personas empleadas del sector público.

### F119 · [IGAE · INVENTE](https://www.pap.hacienda.gob.es/invente2/PagMenuPrincipalV2.aspx?Entorno=2)

- **Acceso identificado:** Inventario público.
- **Geografía:** Sector público estatal, autonómico y local.
- **Datos y familias:**
  - Entidades.
  - Naturaleza jurídica.
  - Adscripción.
  - Sector institucional.
  - Órgano de control.
  - Participación.
  - Situación y evolución registral publicadas.
- **Para integrarlo bien:** Las denominaciones cambian y algunas entidades se extinguen: conservar historia e identificadores.

### F120 · [Portal de la Transparencia de la AGE](https://transparencia.gob.es/)

- **Acceso identificado:** Publicidad activa y documentos.
- **Geografía:** Organismos y ámbitos declarados.
- **Datos y familias:**
  - Organigramas.
  - Puestos de trabajo.
  - Retribuciones publicadas.
  - Contratos.
  - Convenios.
  - Subvenciones.
  - Inmuebles públicos publicados.
  - Planes.
  - Información presupuestaria.
  - Resoluciones y estadísticas de acceso.
- **Para integrarlo bien:** No toda información publicada tiene descarga estructurada. Las solicitudes de información son otra vía y no se han enviado en esta investigación.

### F121 · [Consejo General del Poder Judicial](https://www.poderjudicial.es/cgpj/es/Temas/Estadistica-Judicial/)

- **Acceso identificado:** Estadística judicial y bases PC-Axis/PXWeb.
- **Geografía:** Órganos, partidos judiciales, provincias y CCAA.
- **Datos y familias:**
  - Asuntos ingresados.
  - Asuntos resueltos.
  - Asuntos pendientes.
  - Carga de trabajo.
  - Litigiosidad.
  - Duración estimada.
  - Ejecuciones.
  - Desahucios y lanzamientos.
  - Concursos.
  - Violencia sobre la mujer.
  - Recursos judiciales.
  - Personal judicial.
  - Sistema socioeconómico de partidos judiciales.
- **Para integrarlo bien:** Definiciones y unidad geográfica judicial propias. CENDOJ y reutilización de resoluciones tienen condiciones específicas distintas de las tablas estadísticas.

### F122 · [Fiscalía General del Estado](https://www.fiscal.es/)

- **Acceso identificado:** Memorias, estadísticas y documentos.
- **Geografía:** Fiscalías y territorios publicados.
- **Datos y familias:**
  - Actividad del Ministerio Fiscal.
  - Especialidades.
  - Delitos en la actividad fiscal.
  - Menores.
  - Medio ambiente.
  - Seguridad vial.
  - Violencia.
  - Extranjería.
  - Evolución anual.
- **Para integrarlo bien:** Estadística de actividad fiscal no equivale al total de hechos delictivos ni a condenas.

### F123 · [Ministerio del Interior · Portal Estadístico de Criminalidad](https://estadisticasdecriminalidad.ses.mir.es/)

- **Acceso identificado:** Tablas, balances y descargas.
- **Geografía:** Municipios, provincias, CCAA y nacional según producto.
- **Datos y familias:**
  - Infracciones penales.
  - Tipologías.
  - Balances trimestrales.
  - Victimizaciones agregadas.
  - Detenidos e investigados agregados.
  - Ciberdelincuencia.
  - Delitos de odio.
  - Violencia.
  - Series históricas.
- **Para integrarlo bien:** Distinguir hechos conocidos, denuncias, detenciones y condenas. La cobertura de cuerpos policiales y municipios cambia por operación.

### F124 · [Secretaría General de Instituciones Penitenciarias](https://www.interior.gob.es/opencms/es/archivos-y-documentacion/documentacion-y-publicaciones/anuarios-y-estadisticas/)

- **Acceso identificado:** Estadísticas y anuarios.
- **Geografía:** Centros, CCAA y ámbitos de gestión publicados.
- **Datos y familias:**
  - Población reclusa.
  - Situación procesal.
  - Sexo.
  - Edad.
  - Nacionalidad.
  - Centros penitenciarios.
  - Medidas alternativas.
  - Evolución temporal.
  - Recursos y actividad publicados.
- **Para integrarlo bien:** Comprobar transferencias y competencias autonómicas para construir el total de España.

### F125 · [Ministerio del Interior · Protección internacional](https://proteccion-asilo.interior.gob.es/)

- **Acceso identificado:** Estadísticas, avances e informes.
- **Geografía:** Nacional y territorios según producto.
- **Datos y familias:**
  - Solicitudes de protección internacional.
  - Resoluciones.
  - Nacionalidad agregada.
  - Edad y sexo publicados.
  - Protección temporal.
  - Apatridia.
  - Evolución temporal.
- **Para integrarlo bien:** Solicitud, concesión, documento de residencia y persona residente son magnitudes distintas.

### F126 · [Ministerio de Defensa · Estadística pública](https://www.defensa.gob.es/)

- **Acceso identificado:** Anuarios, planes y publicaciones estadísticas.
- **Geografía:** Nacional y desgloses efectivamente publicados.
- **Datos y familias:**
  - Personal militar.
  - Personal civil.
  - Centros formativos.
  - Recursos sanitarios militares publicados.
  - Patrimonio cultural.
  - Bibliotecas.
  - Museos.
  - Archivos.
  - Presupuestos y contratación públicos.
  - Estadística de reclutamiento publicada.
- **Para integrarlo bien:** Solo información ya publicada; no se presupone apertura de ubicaciones, capacidades o datos operativos no divulgados.

### F127 · [Dirección General de Ordenación del Juego](https://ordenacionjuego.es/datos-estudios/estudios/descarga-datos-mercado-juego)

- **Acceso identificado:** CSV, XLSX y estudios.
- **Geografía:** Principalmente nacional y ámbitos publicados.
- **Datos y familias:**
  - Mercado del juego online.
  - Operadores autorizados.
  - Ingresos.
  - Participación agregada.
  - Segmentos.
  - Cuentas activas.
  - Evolución temporal.
  - Encuestas y estudios publicados.
- **Para integrarlo bien:** No supone disponer de ubicaciones o historiales de jugadores; muchos indicadores solo son nacionales.

### F128 · [Comisionado para el Mercado de Tabacos](https://www.hacienda.gob.es/es-es/areas%20tematicas/cmtabacos/paginas/estadisticascmt2026.aspx)

- **Acceso identificado:** Estadísticas y hojas de cálculo.
- **Geografía:** CCAA y provincias según serie.
- **Datos y familias:**
  - Ventas en unidades.
  - Ventas en euros.
  - Productos.
  - Cigarrillos.
  - Cigarros.
  - Picadura.
  - Evolución mensual.
  - Evolución histórica.
  - Red de expendedurías publicada.
- **Para integrarlo bien:** Conservar territorio fiscal, precios, unidades físicas y periodo; ventas no equivalen a consumo individual de residentes.

### F129 · [Cooperación Española · Estadísticas AOD y TOSSD](https://www.cooperacionespanola.es/area-de-estadistica/)

- **Acceso identificado:** Datos, estadísticas y documentos según producto.
- **Geografía:** Administración financiadora y países receptores.
- **Datos y familias:**
  - Ayuda oficial al desarrollo.
  - Cooperación descentralizada.
  - Organismos financiadores.
  - Países receptores.
  - Sectores.
  - Instrumentos.
  - Desembolsos.
  - Compromisos.
  - TOSSD.
- **Para integrarlo bien:** Distinguir territorio financiador de lugar receptor. Parte del dato describe actividad exterior de España.


## Fuentes europeas oficiales con datos sobre España

### F130 · [Eurostat](https://ec.europa.eu/eurostat/data)

- **Acceso identificado:** API gratuita y descargas.
- **Geografía:** NUTS, ciudades, áreas funcionales, mallas y nacional según conjunto.
- **Datos y familias:**
  - Población.
  - Demografía.
  - Economía regional.
  - PIB.
  - Empleo.
  - Salarios.
  - Renta.
  - Pobreza.
  - Educación.
  - Salud.
  - Turismo.
  - Agricultura.
  - Industria.
  - Energía.
  - Medio ambiente.
  - Ciencia.
  - Digitalización.
  - Comercio.
  - Ciudades.
  - ODS.
- **Para integrarlo bien:** Filtrar España y mantener versión NUTS. Muchas series duplican o armonizan datos nacionales.

### F131 · [Eurostat · GISCO](https://gisco-services.ec.europa.eu/distribution/v2/)

- **Acceso identificado:** Descargas y API de distribución geográfica.
- **Geografía:** NUTS, LAU, ciudades, mallas y otras unidades.
- **Datos y familias:**
  - NUTS.
  - LAU.
  - Países.
  - Ciudades.
  - Áreas urbanas funcionales.
  - Mallas de población publicadas.
  - Correspondencias geográficas.
  - Límites por versiones.
- **Para integrarlo bien:** NUTS3 no equivale siempre a provincia española, especialmente en Canarias. Usar correspondencias oficiales.

### F132 · [Comisión Europea · Copernicus Land](https://land.copernicus.eu/)

- **Acceso identificado:** Datos geográficos; registro o condiciones según producto.
- **Geografía:** Rásteres y polígonos con cobertura de España.
- **Datos y familias:**
  - CORINE.
  - Urban Atlas.
  - Impermeabilización.
  - Cobertura arbórea.
  - Bosques.
  - Pastizales.
  - Humedad y agua.
  - Nieve.
  - Vegetación.
  - Fenología.
  - Cambios de cobertura.
- **Para integrarlo bien:** Revisar resolución, año, método y licencia de cada producto; no confundir clasificación satelital con registro administrativo.

### F133 · [Comisión Europea · Copernicus Climate / C3S](https://climate.copernicus.eu/)

- **Acceso identificado:** Catálogo y acceso gratuito con registro para productos.
- **Geografía:** Rejillas y series climáticas.
- **Datos y familias:**
  - ERA5.
  - Reanálisis.
  - Temperaturas.
  - Precipitación.
  - Viento.
  - Variables atmosféricas.
  - Indicadores climáticos.
  - Proyecciones.
  - Extremos.
  - Estadísticas derivadas.
- **Para integrarlo bien:** No todas las series son observaciones de estaciones. Conservar escenario, modelo y resolución.

### F134 · [Comisión Europea · Copernicus Atmosphere / CAMS](https://atmosphere.copernicus.eu/)

- **Acceso identificado:** Catálogo, descargas y servicios según producto.
- **Geografía:** Rejillas con cobertura de España.
- **Datos y familias:**
  - Calidad del aire modelizada.
  - Aerosoles.
  - Ozono.
  - Partículas.
  - Gases.
  - Transporte atmosférico.
  - Previsiones.
  - Reanálisis.
- **Para integrarlo bien:** Distinguir concentración modelizada, satelital y medida en estación.

### F135 · [Comisión Europea · Copernicus Marine](https://marine.copernicus.eu/)

- **Acceso identificado:** Catálogo, descargas y servicios; registro según acceso.
- **Geografía:** Mallas marinas.
- **Datos y familias:**
  - Temperatura.
  - Salinidad.
  - Corrientes.
  - Nivel del mar.
  - Oleaje.
  - Biogeoquímica.
  - Clorofila.
  - Observaciones in situ.
  - Satélite.
  - Reanálisis.
  - Previsiones.
- **Para integrarlo bien:** Filtrar cuencas y aguas de interés y separar observado/modelizado.

### F136 · [Comisión Europea · Copernicus Emergency](https://emergency.copernicus.eu/)

- **Acceso identificado:** Cartografía y servicios según producto.
- **Geografía:** Áreas afectadas y mallas.
- **Datos y familias:**
  - Cartografía de emergencia.
  - Inundaciones.
  - Incendios.
  - Sequía.
  - Exposición.
  - Riesgo.
  - Activaciones.
  - Daños cartografiados.
- **Para integrarlo bien:** Distinguir pronóstico, activación y mapa posterior al evento.

### F137 · [Agencia Europea de Medio Ambiente](https://www.eea.europa.eu/en/datahub)

- **Acceso identificado:** Datahub y descargas.
- **Geografía:** España, estaciones, zonas y unidades europeas.
- **Datos y familias:**
  - Calidad del aire.
  - Agua.
  - Emisiones industriales.
  - Biodiversidad.
  - Natura 2000.
  - Clima.
  - Ruido.
  - Residuos.
  - Uso del suelo.
  - Indicadores ambientales.
- **Para integrarlo bien:** Muchos productos armonizan reportes españoles: registrar ciclo de reporte y origen.

### F138 · [Comisión Europea · Joint Research Centre](https://data.jrc.ec.europa.eu/)

- **Acceso identificado:** Catálogo y descargas por producto.
- **Geografía:** Mallas y ámbitos europeos o globales.
- **Datos y familias:**
  - ESDAC y suelos.
  - Erosión.
  - Carbono orgánico.
  - EFFIS e incendios.
  - EFAS e inundaciones.
  - Observatorio de sequía.
  - GHSL.
  - Superficie construida.
  - Población modelizada.
  - Exposición.
  - Atlas y recursos científicos.
- **Para integrarlo bien:** No atribuir detalle administrativo a rejillas modelizadas. Algunas colecciones tienen registro o condiciones específicas.

### F139 · [Comisión Europea · EMODnet](https://emodnet.ec.europa.eu/en/emodnet-central-portal)

- **Acceso identificado:** Servicios y descargas documentados.
- **Geografía:** Mares europeos y litoral español.
- **Datos y familias:**
  - Batimetría.
  - Geología marina.
  - Física.
  - Química.
  - Biología.
  - Hábitats del fondo.
  - Actividades humanas.
  - Infraestructuras marinas.
  - Recursos.
  - Procesos costeros.
- **Para integrarlo bien:** Ver procedencia, licencia y resolución por capa; no confundir cobertura cartográfica con delimitación legal de aguas.

### F140 · [Comisión Europea · CORDIS](https://cordis.europa.eu/about/services/es)

- **Acceso identificado:** Descargas masivas y catálogos.
- **Geografía:** Proyectos y participantes.
- **Datos y familias:**
  - Proyectos financiados por programas marco.
  - Entidades españolas.
  - Importes.
  - Temas.
  - Programas.
  - Fechas.
  - Colaboraciones.
  - Resultados públicos.
- **Para integrarlo bien:** La sede del participante no equivale a la ubicación de todos los trabajos ni de todos los beneficios del proyecto.

### F141 · [Oficina de Publicaciones de la UE · TED](https://ted.europa.eu/)

- **Acceso identificado:** Consulta y datos abiertos según servicio.
- **Geografía:** Lugares de ejecución y compradores públicos.
- **Datos y familias:**
  - Anuncios de contratación.
  - Licitaciones.
  - Adjudicaciones.
  - CPV.
  - Compradores.
  - Lotes.
  - Importes publicados.
  - Territorio de ejecución.
- **Para integrarlo bien:** No representa todos los contratos españoles: los umbrales y las obligaciones de publicación importan.

### F142 · [Comisión Europea · Kohesio](https://kohesio.ec.europa.eu/)

- **Acceso identificado:** Consulta y datos de proyectos según publicación.
- **Geografía:** Proyectos y beneficiarios.
- **Datos y familias:**
  - Fondos de cohesión.
  - Proyectos.
  - Beneficiarios.
  - Importes.
  - Programas.
  - Temas.
  - Ubicaciones publicadas.
- **Para integrarlo bien:** Comprobar el periodo de programación y no confundir coste total, ayuda UE e importe ejecutado.

### F143 · [Banco Central Europeo](https://data.ecb.europa.eu/)

- **Acceso identificado:** Portal y servicios estadísticos.
- **Geografía:** Principalmente nacional y área euro.
- **Datos y familias:**
  - Tipos de interés.
  - Moneda.
  - Banca.
  - Financiación.
  - Pagos.
  - Valores.
  - Estadísticas macrofinancieras.
  - Indicadores de España.
- **Para integrarlo bien:** Datos de contexto; gran parte no tiene representación subnacional.

### F144 · [Centro Europeo para la Prevención y el Control de las Enfermedades](https://www.ecdc.europa.eu/en/data)

- **Acceso identificado:** Datos y atlas según vigilancia.
- **Geografía:** Países y regiones según producto.
- **Datos y familias:**
  - Enfermedades transmisibles.
  - Vigilancia europea.
  - Indicadores comparables.
  - Vacunación en productos publicados.
  - Resistencia antimicrobiana.
  - Series epidemiológicas.
- **Para integrarlo bien:** Mantener la definición europea y no mezclar notificaciones con incidencia real no observada.


## Fuentes internacionales públicas complementarias

### F145 · [OCDE](https://data-explorer.oecd.org/)

- **Acceso identificado:** Datos y servicios estadísticos.
- **Geografía:** Nacional y regional según conjunto.
- **Datos y familias:**
  - Economía.
  - Productividad.
  - Bienestar regional.
  - Áreas metropolitanas.
  - Educación.
  - Salud.
  - Empleo.
  - Finanzas públicas.
  - Innovación.
  - Medio ambiente.
- **Para integrarlo bien:** Filtrar España; no duplicar estadísticas nacionales armonizadas sin etiquetarlas.

### F146 · [FAO · FAOSTAT](https://www.fao.org/faostat/es/)

- **Acceso identificado:** Descargas y servicios documentados.
- **Geografía:** Principalmente nacional.
- **Datos y familias:**
  - Producción agraria.
  - Superficies.
  - Rendimientos.
  - Ganadería.
  - Bosques.
  - Emisiones agroalimentarias.
  - Uso de insumos.
  - Comercio.
  - Balances alimentarios.
  - Seguridad alimentaria.
- **Para integrarlo bien:** Contexto internacional; no atribuir automáticamente a regiones españolas.

### F147 · [OIT · ILOSTAT](https://ilostat.ilo.org/)

- **Acceso identificado:** Descargas y servicios según producto.
- **Geografía:** Nacional y desgloses publicados.
- **Datos y familias:**
  - Empleo.
  - Desempleo.
  - Salarios.
  - Informalidad.
  - Jornadas.
  - Protección social.
  - Seguridad laboral.
  - Indicadores comparables.
- **Para integrarlo bien:** Distinguir datos nacionales observados y estimaciones armonizadas/modelizadas.

### F148 · [Organización Mundial de la Salud](https://data.who.int/)

- **Acceso identificado:** Indicadores y descargas según producto.
- **Geografía:** Principalmente nacional.
- **Datos y familias:**
  - Salud.
  - Mortalidad.
  - Enfermedades.
  - Cobertura sanitaria.
  - Factores de riesgo.
  - Recursos sanitarios.
  - Indicadores internacionales.
- **Para integrarlo bien:** Indicadores comparables de España; no sustituyen el detalle territorial del SNS.


## Operadores regulados complementarios, separados del núcleo de organismos oficiales

### F149 · [Red Eléctrica · REData / eSIOS](https://www.esios.ree.es/es/)

- **Acceso identificado:** Datos, descargas y API según condiciones.
- **Geografía:** Sistema eléctrico, CCAA y ámbitos publicados.
- **Datos y familias:**
  - Demanda.
  - Generación por tecnología.
  - Potencia.
  - Intercambios.
  - Precios regulados publicados.
  - Emisiones estimadas.
  - Renovables.
  - Balance eléctrico.
  - Series temporales.
- **Para integrarlo bien:** Operador del sistema y fuente sectorial regulada; no presentarlo como ministerio ni organismo estadístico público. Algunas API requieren token.

### F150 · [Enagás · Gestor Técnico del Sistema](https://www.enagas.es/)

- **Acceso identificado:** Información pública de operación y transparencia.
- **Geografía:** Sistema gasista y puntos publicados.
- **Datos y familias:**
  - Demanda de gas.
  - Entradas.
  - Salidas.
  - Almacenamientos.
  - Regasificación.
  - Balance.
  - Capacidad publicada.
  - Interconexiones.
- **Para integrarlo bien:** Fuente regulada complementaria, no un organismo público. Revisar condiciones y detalle de cada publicación.


## Las 17 comunidades autónomas y las 2 ciudades autónomas

### F151 · [Andalucía](https://www.juntadeandalucia.es/institutodeestadisticaycartografia/)

- **Acceso identificado:** Estadística, geoportal y catálogo autonómico; formatos por producto.
- **Geografía:** Andalucía.
- **Datos y familias:**
  - BADEA.
  - SIMA.
  - Población por malla.
  - Estadística municipal.
  - Economía.
  - Empleo.
  - Agricultura.
  - Equipamientos.
  - Espacios protegidos.
  - Cartografía de referencia.
- **Puertas de entrada:**
  - [IECA](https://www.juntadeandalucia.es/institutodeestadisticaycartografia/)
  - [DERA / IDEAndalucía](https://www.juntadeandalucia.es/institutodeestadisticaycartografia/dega/datos-espaciales-de-referencia-de-andalucia-dera)
  - [Portal de datos / transparencia](https://www.juntadeandalucia.es/datosabiertos/portal/)
- **Para integrarlo bien:** Las familias son un índice de exploración del sistema autonómico: validar disponibilidad, fecha, escala y licencia en cada ficha. No se afirma que todos los indicadores estén publicados para cada municipio.

### F152 · [Aragón](https://www.aragon.es/gobierno/iaest)

- **Acceso identificado:** Estadística, geoportal y catálogo autonómico; formatos por producto.
- **Geografía:** Aragón.
- **Datos y familias:**
  - Comarcas administrativas.
  - SITA.
  - Población.
  - Mercado laboral.
  - Economía municipal.
  - Cartografía.
  - Relieve.
  - Hidrografía.
  - Usos del suelo.
  - Servicios públicos.
- **Puertas de entrada:**
  - [Instituto Aragonés de Estadística](https://www.aragon.es/gobierno/iaest)
  - [IGEAR / ICEARAGON](https://icearagon.aragon.es/)
  - [Portal de datos / transparencia](https://opendata.aragon.es/)
- **Para integrarlo bien:** Las familias son un índice de exploración del sistema autonómico: validar disponibilidad, fecha, escala y licencia en cada ficha. No se afirma que todos los indicadores estén publicados para cada municipio.

### F153 · [Asturias](https://www.sadei.es/)

- **Acceso identificado:** Estadística, geoportal y catálogo autonómico; formatos por producto.
- **Geografía:** Asturias.
- **Datos y familias:**
  - Población.
  - Parroquias.
  - Entidades de población.
  - Economía regional.
  - Estadística municipal.
  - Empleo.
  - Industria.
  - Territorio.
  - Equipamientos.
  - Cartografía.
- **Puertas de entrada:**
  - [SADEI](https://www.sadei.es/)
  - [SITPA / IDEAS](https://ideas.asturias.es/)
  - [Portal de datos / transparencia](https://transparencia.asturias.es/)
- **Para integrarlo bien:** Las familias son un índice de exploración del sistema autonómico: validar disponibilidad, fecha, escala y licencia en cada ficha. No se afirma que todos los indicadores estén publicados para cada municipio.

### F154 · [Illes Balears](https://ibestat.es/)

- **Acceso identificado:** Estadística, geoportal y catálogo autonómico; formatos por producto.
- **Geografía:** Illes Balears.
- **Datos y familias:**
  - Población.
  - Turismo.
  - Islas.
  - Presión humana según producto.
  - Economía.
  - Empleo.
  - Vivienda.
  - Cartografía.
  - Litoral.
  - Equipamientos.
- **Puertas de entrada:**
  - [IBESTAT](https://ibestat.es/)
  - [Institut Cartogràfic i Geogràfic / IDEIB](https://www.caib.es/sites/ideib/es/inicio/)
  - [Portal de datos / transparencia](https://dadesobertes.caib.es/)
- **Para integrarlo bien:** Las familias son un índice de exploración del sistema autonómico: validar disponibilidad, fecha, escala y licencia en cada ficha. No se afirma que todos los indicadores estén publicados para cada municipio.

### F155 · [Canarias](https://www.gobiernodecanarias.org/istac/)

- **Acceso identificado:** Estadística, geoportal y catálogo autonómico; formatos por producto.
- **Geografía:** Canarias.
- **Datos y familias:**
  - e-Base.
  - Atlas estadístico.
  - Islas.
  - Municipios.
  - Turismo.
  - Empleo.
  - Población.
  - Cartografía.
  - Vegetación.
  - Planeamiento.
  - Relieve volcánico.
  - Callejero.
- **Puertas de entrada:**
  - [ISTAC](https://www.gobiernodecanarias.org/istac/)
  - [GRAFCAN / IDECanarias](https://www.grafcan.es/)
  - [Portal de datos / transparencia](https://datos.canarias.es/)
- **Para integrarlo bien:** Las familias son un índice de exploración del sistema autonómico: validar disponibilidad, fecha, escala y licencia en cada ficha. No se afirma que todos los indicadores estén publicados para cada municipio.

### F156 · [Cantabria](https://www.icane.es/)

- **Acceso identificado:** Estadística, geoportal y catálogo autonómico; formatos por producto.
- **Geografía:** Cantabria.
- **Datos y familias:**
  - Banco de datos.
  - Población.
  - Economía.
  - Empleo.
  - Municipios.
  - Turismo.
  - Territorio.
  - Cartografía.
  - Equipamientos.
  - Medio ambiente.
- **Puertas de entrada:**
  - [ICANE](https://www.icane.es/)
  - [Cartografía / IDE Cantabria](https://mapas.cantabria.es/)
  - [Portal de datos / transparencia](https://datos.icane.es/)
- **Para integrarlo bien:** Las familias son un índice de exploración del sistema autonómico: validar disponibilidad, fecha, escala y licencia en cada ficha. No se afirma que todos los indicadores estén publicados para cada municipio.

### F157 · [Castilla y León](https://estadistica.jcyl.es/)

- **Acceso identificado:** Estadística, geoportal y catálogo autonómico; formatos por producto.
- **Geografía:** Castilla y León.
- **Datos y familias:**
  - SIE.
  - Municipios.
  - Población.
  - Despoblación.
  - Empleo.
  - Economía.
  - Agricultura.
  - Montes.
  - Ortofotos.
  - Servicios.
  - Infraestructuras.
- **Puertas de entrada:**
  - [Dirección General competente en estadística](https://estadistica.jcyl.es/)
  - [IDECyL](https://idecyl.jcyl.es/)
  - [Portal de datos / transparencia](https://datosabiertos.jcyl.es/)
- **Para integrarlo bien:** Las familias son un índice de exploración del sistema autonómico: validar disponibilidad, fecha, escala y licencia en cada ficha. No se afirma que todos los indicadores estén publicados para cada municipio.

### F158 · [Castilla-La Mancha](https://estadistica.castillalamancha.es/)

- **Acceso identificado:** Estadística, geoportal y catálogo autonómico; formatos por producto.
- **Geografía:** Castilla-La Mancha.
- **Datos y familias:**
  - Banco de datos.
  - Municipios.
  - Población.
  - Agricultura.
  - Empleo.
  - Economía.
  - Turismo.
  - Planeamiento publicado.
  - Cartografía.
  - Medio ambiente.
- **Puertas de entrada:**
  - [Servicio de Estadística](https://estadistica.castillalamancha.es/)
  - [IDE Castilla-La Mancha](https://ide.castillalamancha.es/)
  - [Portal de datos / transparencia](https://datosabiertos.castillalamancha.es/)
- **Para integrarlo bien:** Las familias son un índice de exploración del sistema autonómico: validar disponibilidad, fecha, escala y licencia en cada ficha. No se afirma que todos los indicadores estén publicados para cada municipio.

### F159 · [Cataluña](https://www.idescat.cat/)

- **Acceso identificado:** Estadística, geoportal y catálogo autonómico; formatos por producto.
- **Geografía:** Cataluña.
- **Datos y familias:**
  - Municipios.
  - Comarcas.
  - Veguerías según producto.
  - Estadística económica.
  - Población.
  - Empleo.
  - Mallas.
  - Cartografía.
  - Ortofotos históricas.
  - LiDAR.
  - Geología.
  - Riesgos.
  - Equipamientos.
- **Puertas de entrada:**
  - [Idescat](https://www.idescat.cat/)
  - [ICGC](https://www.icgc.cat/)
  - [Portal de datos / transparencia](https://analisi.transparenciacatalunya.cat/)
- **Para integrarlo bien:** Las familias son un índice de exploración del sistema autonómico: validar disponibilidad, fecha, escala y licencia en cada ficha. No se afirma que todos los indicadores estén publicados para cada municipio.

### F160 · [Comunitat Valenciana](https://pegv.gva.es/)

- **Acceso identificado:** Estadística, geoportal y catálogo autonómico; formatos por producto.
- **Geografía:** Comunitat Valenciana.
- **Datos y familias:**
  - Banco estadístico.
  - Municipios.
  - Población.
  - Economía.
  - Empleo.
  - Turismo.
  - Cartografía.
  - Ocupación del suelo.
  - Ortofotos.
  - Riesgos.
  - Territorio.
- **Puertas de entrada:**
  - [Institut Valencià d'Estadística](https://pegv.gva.es/)
  - [Institut Cartogràfic Valencià / IDEV](https://icv.gva.es/)
  - [Portal de datos / transparencia](https://dadesobertes.gva.es/)
- **Para integrarlo bien:** Las familias son un índice de exploración del sistema autonómico: validar disponibilidad, fecha, escala y licencia en cada ficha. No se afirma que todos los indicadores estén publicados para cada municipio.

### F161 · [Extremadura](https://www.juntaex.es/ieex/)

- **Acceso identificado:** Estadística, geoportal y catálogo autonómico; formatos por producto.
- **Geografía:** Extremadura.
- **Datos y familias:**
  - Municipios.
  - Población.
  - Empleo.
  - Agricultura.
  - Economía.
  - Comercio.
  - Turismo.
  - Cartografía.
  - Urbanismo.
  - Equipamientos.
- **Puertas de entrada:**
  - [Instituto de Estadística de Extremadura](https://www.juntaex.es/ieex/)
  - [SITEX / IDEEX](https://sitex.juntaex.es/SITEX/pages/ideex)
  - [Portal de datos / transparencia](https://gobiernoabierto.juntaex.es/)
- **Para integrarlo bien:** Las familias son un índice de exploración del sistema autonómico: validar disponibilidad, fecha, escala y licencia en cada ficha. No se afirma que todos los indicadores estén publicados para cada municipio.

### F162 · [Galicia](https://www.ige.gal/)

- **Acceso identificado:** Estadística, geoportal y catálogo autonómico; formatos por producto.
- **Geografía:** Galicia.
- **Datos y familias:**
  - Parroquias.
  - Entidades de población.
  - Municipios.
  - Mallas.
  - Economía.
  - Empleo.
  - Pesca.
  - Industria.
  - Cartografía.
  - Paisaje.
  - Planeamiento publicado.
  - Equipamientos.
- **Puertas de entrada:**
  - [Instituto Galego de Estatística](https://www.ige.gal/)
  - [Instituto de Estudos do Territorio / IDEG](https://mapas.xunta.gal/es)
  - [Portal de datos / transparencia](https://abertos.xunta.gal/es/)
- **Para integrarlo bien:** Las familias son un índice de exploración del sistema autonómico: validar disponibilidad, fecha, escala y licencia en cada ficha. No se afirma que todos los indicadores estén publicados para cada municipio.

### F163 · [Comunidad de Madrid](https://www.comunidad.madrid/gobierno/estadistica)

- **Acceso identificado:** Estadística, geoportal y catálogo autonómico; formatos por producto.
- **Geografía:** Comunidad de Madrid.
- **Datos y familias:**
  - ALMUDENA.
  - DESVAN.
  - Municipios.
  - Población.
  - Empleo.
  - Vivienda.
  - Turismo.
  - Transporte.
  - Equipamientos.
  - Ortofotos.
  - Medio ambiente.
- **Puertas de entrada:**
  - [Instituto de Estadística](https://www.comunidad.madrid/gobierno/estadistica)
  - [IDEM / Geoportal](https://www.comunidad.madrid/geoportal)
  - [Portal de datos / transparencia](https://datos.comunidad.madrid/)
- **Para integrarlo bien:** Las familias son un índice de exploración del sistema autonómico: validar disponibilidad, fecha, escala y licencia en cada ficha. No se afirma que todos los indicadores estén publicados para cada municipio.

### F164 · [Región de Murcia](https://econet.carm.es/)

- **Acceso identificado:** Estadística, geoportal y catálogo autonómico; formatos por producto.
- **Geografía:** Región de Murcia.
- **Datos y familias:**
  - Municipios.
  - Entidades de población.
  - Población.
  - Afiliación.
  - Migraciones.
  - Economía.
  - Agricultura.
  - Agua.
  - Urbanismo.
  - Cartografía.
- **Puertas de entrada:**
  - [Centro Regional de Estadística](https://econet.carm.es/)
  - [SITMURCIA](https://sitmurcia.carm.es/)
  - [Portal de datos / transparencia](https://datosabiertos.regiondemurcia.es/)
- **Para integrarlo bien:** Las familias son un índice de exploración del sistema autonómico: validar disponibilidad, fecha, escala y licencia en cada ficha. No se afirma que todos los indicadores estén publicados para cada municipio.

### F165 · [Navarra](https://nastat.navarra.es/)

- **Acceso identificado:** Estadística, geoportal y catálogo autonómico; formatos por producto.
- **Geografía:** Navarra.
- **Datos y familias:**
  - Municipios.
  - Concejos.
  - Población.
  - Renta y fiscalidad foral.
  - Empleo.
  - Economía.
  - Suelos.
  - Ortofotos.
  - Cartografía.
  - Equipamientos.
  - Redes territoriales.
- **Puertas de entrada:**
  - [Nastat](https://nastat.navarra.es/)
  - [SITNA / IDENA](https://geoportal.navarra.es/)
  - [Portal de datos / transparencia](https://gobiernoabierto.navarra.es/es/open-data)
- **Para integrarlo bien:** Las familias son un índice de exploración del sistema autonómico: validar disponibilidad, fecha, escala y licencia en cada ficha. No se afirma que todos los indicadores estén publicados para cada municipio.

### F166 · [País Vasco](https://www.eustat.eus/)

- **Acceso identificado:** Estadística, geoportal y catálogo autonómico; formatos por producto.
- **Geografía:** País Vasco.
- **Datos y familias:**
  - LurData.
  - Población.
  - Vivienda.
  - Establecimientos.
  - Economía.
  - Empleo.
  - Territorios históricos.
  - Cartografía.
  - LiDAR.
  - Planeamiento.
  - Equipamientos.
  - Mallas.
- **Puertas de entrada:**
  - [Eustat](https://www.eustat.eus/)
  - [geoEuskadi](https://www.geo.euskadi.eus/)
  - [Portal de datos / transparencia](https://opendata.euskadi.eus/)
- **Para integrarlo bien:** Las familias son un índice de exploración del sistema autonómico: validar disponibilidad, fecha, escala y licencia en cada ficha. No se afirma que todos los indicadores estén publicados para cada municipio.

### F167 · [La Rioja](https://www.larioja.org/estadistica/)

- **Acceso identificado:** Estadística, geoportal y catálogo autonómico; formatos por producto.
- **Geografía:** La Rioja.
- **Datos y familias:**
  - Municipios.
  - Población.
  - Economía.
  - Empleo.
  - Vitivinicultura.
  - Agricultura.
  - Cartografía.
  - Hidrografía.
  - Ortofotos.
  - Equipamientos.
- **Puertas de entrada:**
  - [Instituto de Estadística de La Rioja](https://www.larioja.org/estadistica/)
  - [IDErioja](https://iderioja.larioja.org/)
  - [Portal de datos / transparencia](https://web.larioja.org/dato-abierto)
- **Para integrarlo bien:** Las familias son un índice de exploración del sistema autonómico: validar disponibilidad, fecha, escala y licencia en cada ficha. No se afirma que todos los indicadores estén publicados para cada municipio.

### F168 · [Ceuta](https://www.ceuta.es/)

- **Acceso identificado:** Estadística, geoportal y catálogo autonómico; formatos por producto.
- **Geografía:** Ceuta.
- **Datos y familias:**
  - Indicadores de la ciudad.
  - Presupuesto.
  - Servicios públicos.
  - Urbanismo.
  - Equipamientos.
  - Turismo.
  - Cartografía publicada.
- **Puertas de entrada:**
  - [Ciudad Autónoma · estadística y transparencia](https://www.ceuta.es/)
  - [Información territorial de la Ciudad](https://www.ceuta.es/)
  - [Portal de datos / transparencia](https://www.ceuta.es/)
- **Para integrarlo bien:** Las familias son un índice de exploración del sistema autonómico: validar disponibilidad, fecha, escala y licencia en cada ficha. No se afirma que todos los indicadores estén publicados para cada municipio.

### F169 · [Melilla](https://www.melilla.es/)

- **Acceso identificado:** Estadística, geoportal y catálogo autonómico; formatos por producto.
- **Geografía:** Melilla.
- **Datos y familias:**
  - Indicadores de la ciudad.
  - Presupuesto.
  - Servicios públicos.
  - Urbanismo.
  - Equipamientos.
  - Agenda urbana.
  - Cartografía publicada.
- **Puertas de entrada:**
  - [Ciudad Autónoma · estadística y datos abiertos](https://www.melilla.es/)
  - [Información territorial de la Ciudad](https://www.melilla.es/)
  - [Portal de datos / transparencia](https://www.melilla.es/)
- **Para integrarlo bien:** Las familias son un índice de exploración del sistema autonómico: validar disponibilidad, fecha, escala y licencia en cada ficha. No se afirma que todos los indicadores estén publicados para cada municipio.


## Administración local y supramunicipal · ejemplos y expansión

### F170 · [Ayuntamiento de Madrid](https://datos.madrid.es/dataset/)

- **Acceso identificado:** Catálogo, servicios y descargas según conjunto.
- **Geografía:** Ámbito de la entidad.
- **Datos y familias:**
  - Padrón agregado.
  - Distritos.
  - Barrios.
  - Tráfico.
  - EMT y movilidad según fuente.
  - Calidad del aire.
  - Ruido.
  - Arbolado.
  - Parques.
  - Equipamientos.
  - Licencias.
  - Urbanismo.
  - Presupuestos.
  - Limpieza.
  - Residuos.
  - Cultura.
  - Deporte.
- **Para integrarlo bien:** Ejemplo de fuente local, no lista exhaustiva de ayuntamientos. El registro nacional adjunto incluye otros publicadores y sus títulos. Validar cada recurso: algunos feeds o visores tienen condiciones propias.

### F171 · [Ayuntamiento de Barcelona](https://opendata-ajuntament.barcelona.cat/)

- **Acceso identificado:** Catálogo, servicios y descargas según conjunto.
- **Geografía:** Ámbito de la entidad.
- **Datos y familias:**
  - Padrón agregado.
  - Barrios.
  - Secciones.
  - Urbanismo.
  - Vivienda.
  - Actividad económica.
  - Movilidad.
  - Bicicleta.
  - Arbolado.
  - Calidad del aire.
  - Equipamientos.
  - Contratos.
  - Presupuestos.
  - Servicios urbanos.
- **Para integrarlo bien:** Ejemplo de fuente local, no lista exhaustiva de ayuntamientos. El registro nacional adjunto incluye otros publicadores y sus títulos. Validar cada recurso: algunos feeds o visores tienen condiciones propias.

### F172 · [Ayuntamiento de València](https://opendata.vlci.valencia.es/)

- **Acceso identificado:** Catálogo, servicios y descargas según conjunto.
- **Geografía:** Ámbito de la entidad.
- **Datos y familias:**
  - Distritos.
  - Barrios.
  - Población agregada.
  - Movilidad.
  - Bicicleta.
  - Transporte.
  - Equipamientos.
  - Arbolado.
  - Medio ambiente.
  - Presupuestos.
  - Servicios urbanos.
- **Para integrarlo bien:** Ejemplo de fuente local, no lista exhaustiva de ayuntamientos. El registro nacional adjunto incluye otros publicadores y sus títulos. Validar cada recurso: algunos feeds o visores tienen condiciones propias.

### F173 · [Ayuntamiento de Zaragoza](https://www.zaragoza.es/sede/portal/datos-abiertos/)

- **Acceso identificado:** Catálogo, servicios y descargas según conjunto.
- **Geografía:** Ámbito de la entidad.
- **Datos y familias:**
  - Padrón agregado.
  - Barrios.
  - Equipamientos.
  - Urbanismo.
  - Transporte.
  - Bicicleta.
  - Calidad del aire.
  - Agua.
  - Cultura.
  - Contratos.
  - Presupuestos.
  - Cartografía.
- **Para integrarlo bien:** Ejemplo de fuente local, no lista exhaustiva de ayuntamientos. El registro nacional adjunto incluye otros publicadores y sus títulos. Validar cada recurso: algunos feeds o visores tienen condiciones propias.

### F174 · [Ayuntamiento de Málaga](https://datosabiertos.malaga.eu/)

- **Acceso identificado:** Catálogo, servicios y descargas según conjunto.
- **Geografía:** Ámbito de la entidad.
- **Datos y familias:**
  - Población.
  - Tráfico.
  - Movilidad.
  - Equipamientos.
  - Urbanismo.
  - Turismo.
  - Medio ambiente.
  - Presupuesto.
  - Servicios municipales.
  - Cartografía.
- **Para integrarlo bien:** Ejemplo de fuente local, no lista exhaustiva de ayuntamientos. El registro nacional adjunto incluye otros publicadores y sus títulos. Validar cada recurso: algunos feeds o visores tienen condiciones propias.

### F175 · [Ayuntamiento de Gijón](https://www.gijon.es/es/datos-abiertos)

- **Acceso identificado:** Catálogo, servicios y descargas según conjunto.
- **Geografía:** Ámbito de la entidad.
- **Datos y familias:**
  - Población.
  - Movilidad.
  - Transporte.
  - Equipamientos.
  - Medio ambiente.
  - Cultura.
  - Presupuesto.
  - Servicios municipales.
  - Información territorial.
- **Para integrarlo bien:** Ejemplo de fuente local, no lista exhaustiva de ayuntamientos. El registro nacional adjunto incluye otros publicadores y sus títulos. Validar cada recurso: algunos feeds o visores tienen condiciones propias.

### F176 · [Diputación de Barcelona](https://www.diba.cat/es/web/cartografia-sig-local/sitmun.diba.cat)

- **Acceso identificado:** Catálogo, servicios y descargas según conjunto.
- **Geografía:** Ámbito de la entidad.
- **Datos y familias:**
  - SITMUN.
  - Cartografía municipal.
  - Equipamientos.
  - Servicios.
  - Redes locales.
  - Planeamiento publicado.
  - Indicadores territoriales.
  - Infraestructura provincial.
- **Para integrarlo bien:** Ejemplo de fuente local, no lista exhaustiva de ayuntamientos. El registro nacional adjunto incluye otros publicadores y sus títulos. Validar cada recurso: algunos feeds o visores tienen condiciones propias.

### F177 · [Diputación Foral de Álava](https://irekia.araba.eus/es/open-data)

- **Acceso identificado:** Catálogo, servicios y descargas según conjunto.
- **Geografía:** Ámbito de la entidad.
- **Datos y familias:**
  - Fiscalidad foral agregada.
  - Renta.
  - Presupuesto.
  - Carreteras.
  - Cartografía.
  - Servicios.
  - Medio ambiente.
  - Indicadores municipales.
- **Para integrarlo bien:** Ejemplo de fuente local, no lista exhaustiva de ayuntamientos. El registro nacional adjunto incluye otros publicadores y sus títulos. Validar cada recurso: algunos feeds o visores tienen condiciones propias.

### F178 · [Diputación Foral de Bizkaia](https://www.opendatabizkaia.eus/)

- **Acceso identificado:** Catálogo, servicios y descargas según conjunto.
- **Geografía:** Ámbito de la entidad.
- **Datos y familias:**
  - Fiscalidad foral agregada.
  - Renta.
  - Presupuesto.
  - Carreteras.
  - Movilidad.
  - Cartografía.
  - Servicios sociales.
  - Indicadores territoriales.
- **Para integrarlo bien:** Ejemplo de fuente local, no lista exhaustiva de ayuntamientos. El registro nacional adjunto incluye otros publicadores y sus títulos. Validar cada recurso: algunos feeds o visores tienen condiciones propias.

### F179 · [Diputación Foral de Gipuzkoa](https://www.gipuzkoairekia.eus/)

- **Acceso identificado:** Catálogo, servicios y descargas según conjunto.
- **Geografía:** Ámbito de la entidad.
- **Datos y familias:**
  - Fiscalidad foral agregada.
  - Renta.
  - Presupuesto.
  - Carreteras.
  - Movilidad.
  - Cartografía.
  - Servicios.
  - Indicadores municipales.
- **Para integrarlo bien:** Ejemplo de fuente local, no lista exhaustiva de ayuntamientos. El registro nacional adjunto incluye otros publicadores y sus títulos. Validar cada recurso: algunos feeds o visores tienen condiciones propias.

### F180 · [Cabildo de Tenerife](https://datos.tenerife.es/)

- **Acceso identificado:** Catálogo, servicios y descargas según conjunto.
- **Geografía:** Ámbito de la entidad.
- **Datos y familias:**
  - Transporte.
  - Carreteras.
  - Equipamientos.
  - Territorio.
  - Turismo.
  - Medio ambiente.
  - Residuos.
  - Servicios insulares.
  - Presupuesto.
- **Para integrarlo bien:** Ejemplo de fuente local, no lista exhaustiva de ayuntamientos. El registro nacional adjunto incluye otros publicadores y sus títulos. Validar cada recurso: algunos feeds o visores tienen condiciones propias.

### F181 · [Cabildo de La Palma](https://www.opendatalapalma.es/)

- **Acceso identificado:** Catálogo, servicios y descargas según conjunto.
- **Geografía:** Ámbito de la entidad.
- **Datos y familias:**
  - Cartografía.
  - Territorio.
  - Relieve.
  - Medio ambiente.
  - Equipamientos.
  - Servicios.
  - Movilidad.
  - Información insular.
- **Para integrarlo bien:** Ejemplo de fuente local, no lista exhaustiva de ayuntamientos. El registro nacional adjunto incluye otros publicadores y sus títulos. Validar cada recurso: algunos feeds o visores tienen condiciones propias.

### F182 · [Ayuntamientos, diputaciones, cabildos, consells y consorcios del registro nacional](https://datos.gob.es/es/catalogo)

- **Acceso identificado:** Catálogo, servicios y descargas según conjunto.
- **Geografía:** Ámbito de la entidad.
- **Datos y familias:**
  - Padrón agregado.
  - Barrios.
  - Distritos.
  - Presupuestos.
  - Licitaciones.
  - Tributos.
  - Agua.
  - Saneamiento.
  - Residuos.
  - Transporte público.
  - Aparcamiento.
  - Bicicletas.
  - Aire.
  - Ruido.
  - Arbolado.
  - Cementerios publicados.
  - Mercados.
  - Comercio.
  - Instalaciones deportivas.
  - Centros culturales.
  - Urbanismo.
  - Licencias.
  - Planeamiento.
  - Accesibilidad.
  - Playas.
  - Incidencias urbanas.
- **Para integrarlo bien:** Ejemplo de fuente local, no lista exhaustiva de ayuntamientos. El registro nacional adjunto incluye otros publicadores y sus títulos. Validar cada recurso: algunos feeds o visores tienen condiciones propias.


## Otros nodos que hay que seguir recorriendo

- Consejerías sectoriales: salud, educación, vivienda, transporte, medio ambiente, cultura, agricultura y empleo. Sus datos no siempre están federados en el portal general.
- Servicios autonómicos de salud y redes hospitalarias públicas: centros, actividad y recursos en el nivel que publiquen.
- Agencias autonómicas del agua, meteorología, energía, innovación, evaluación y medio ambiente.
- Parlamentos autonómicos, boletines oficiales autonómicos y provinciales, órganos de fiscalización y consejos de transparencia.
- Autoridades portuarias, puertos autonómicos, consorcios y autoridades de transporte, redes ferroviarias autonómicas, metros, tranvías y operadores municipales.
- Universidades públicas, institutos de investigación, museos y archivos públicos con repositorios propios.
- Entidades locales no federadas en datos.gob.es: explorar sus catálogos, geoportales y portales de transparencia.

No se han inventado catálogos para estos nodos: son rutas de descubrimiento que se verifican entidad por entidad.

## Antes de convertir una familia en capa

1. Identificar el recurso exacto, organismo de origen y responsable de actualización.
2. Confirmar licencia, gratuidad, registro, cuotas y posibilidad de almacenar una copia.
3. Descargar metadatos y una muestra; verificar formato, coordenadas, códigos y fechas.
4. Identificar cobertura real y censura estadística; mantener nulos, provisionales y revisiones.
5. Definir cómo se representa: punto, línea, área, rejilla, flujo o ficha contextual nacional.
6. Registrar correspondencias territoriales y sus cambios históricos.
7. Versionar datos y procedencia y habilitar consulta a la ficha original.

## Alcance de esta investigación

Se ha recopilado un mapa de fuentes, metadatos y títulos, no 116.236 bases de observaciones. No se han descargado los terabytes de todos los ficheros ni se afirma que todas las fuentes sean integrables sin trabajo adicional. El catálogo nacional es una gran puerta de entrada, pero no contiene todos los datos oficiales. Los nombres y recuentos corresponden a la captura de esta fecha y pueden cambiar.
