export const overlays = [
  {id:'rivers',name:'Ríos y masas de agua',icon:'waves',group:'Agua y naturaleza',url:'https://servicios.idee.es/wms-inspire/hidrografia',layers:'HY.Network,HY.PhysicalWaters.Waterbodies',note:'Hidrografía IGN · detalle según escala'},
  {id:'rail',name:'Red ferroviaria',icon:'train-front',group:'Movilidad y recorridos',url:'https://servicios.idee.es/wms-inspire/transportes',layers:'TN.RailTransportNetwork.RailwayLink',note:'Red ferroviaria IGN · no solo alta velocidad'},
  {id:'roads',name:'Carreteras',icon:'route',group:'Movilidad y recorridos',url:'https://servicios.idee.es/wms-inspire/transportes',layers:'TN.RoadTransportNetwork.RoadLink',note:'Red viaria IGN · detalle según escala'},
  {id:'camino',name:'Caminos de Santiago',icon:'footprints',group:'Movilidad y recorridos',url:'https://www.ign.es/wms-inspire/camino-santiago',layers:'camino_frances,caminos_galicia,caminos_norte,caminos_andaluces,caminos_centro,caminos_este,caminos_nordeste,caminos_sureste,caminos_insulares,caminos_portugueses',note:'Rutas IGN · no incluye todos los senderos GR'},
  {id:'municipal',name:'Límites municipales',icon:'scan',group:'Organización territorial',url:'https://www.ign.es/wms-inspire/unidades-administrativas',layers:'AU.AdministrativeUnit',styles:'municipios-gris',note:'Cartografía IGN · acercar para ver el detalle',minzoom:8}
];
