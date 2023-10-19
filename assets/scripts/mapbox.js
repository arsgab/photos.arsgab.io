const MAP_CENTER_COORDS = [20.4568974, 44.8178131];  // Belgrade
const MAP_DEFAULT_ZOOM = 4.3;
const MAPBOX = {
  selector: '#map',
  script: 'https://api.mapbox.com/mapbox-gl-js/v2.14.1/mapbox-gl.js',
  style: 'mapbox://styles/mapbox/dark-v11',
  center: MAP_CENTER_COORDS,
  pointLayout: {
    'circle-color': ['get', 'color'],
    'circle-stroke-width': 2,
    'circle-stroke-color': 'white',
    'circle-opacity': 0.9,
    'circle-radius': 8,
  },
  locationLayout: {
    'circle-color': 'white',
    'circle-stroke-width': 1,
    'circle-stroke-color': 'white',
    'circle-opacity': 0.55,
    'circle-radius': 4,
  },
};

window.addEventListener('DOMContentLoaded', () => {
  let container = document.querySelector(MAPBOX.selector);
  if (!container)
    return;
  let toggle = document.querySelector(`a[data-map-toggle][href='${MAPBOX.selector}']`);
  if (toggle)
    toggle.addEventListener('click', (evt => toggleMap(evt, container)));
  if (window.location.hash === MAPBOX.selector) {
    container.hidden = false;
    loadScript(MAPBOX.script).then(() => createMap(container));
    container.parentElement.scrollIntoView({behavior: 'smooth'});
  }
});

function toggleMap(evt, container) {
  evt.preventDefault();
  container.hidden = !container.hidden;
  if (container.dataset.mapLoaded !== 'true')
    loadScript(MAPBOX.script).then(() => createMap(container));
  if (!container.hidden)
    container.parentElement.scrollIntoView({behavior: 'smooth'});
  history.pushState({}, '', container.hidden ? '#' : MAPBOX.selector);
  return false;
}

function createMap(container, useWebGL2 = true) {
  let token = container.dataset.mapToken;
  if (container.dataset.mapLoaded === 'true' || !token || !mapboxgl)
    return;
  let map = new mapboxgl.Map({
    accessToken: token,
    logoPosition: container.dataset.mapLogoPosition || 'top-right',
    useWebGL2: useWebGL2,
    container: container,
    style: MAPBOX.style,
    center: MAPBOX.center,
    zoom: parseFloat(container.dataset.mapZoom) || MAP_DEFAULT_ZOOM,
    attributionControl: false,
  });
  map.on('load', onMapLoad);
  return map;
}

function onMapLoad({target: map}) {
  addMapPoints(map);
  addMapLocations(map);
  map.getContainer().dataset.mapLoaded = 'true';
  let umami = window.umami || null;
  if (umami)
    umami.track('map-loaded');
}

function addMapPoints(map) {
  let dataSource = map.getContainer().dataset.mapPointsSrc;
  if (!dataSource)
    return;
  map.addSource('points', {type: 'geojson', data: dataSource});
  map.addLayer({
    id: 'points',
    source: 'points',
    type: 'circle',
    paint: MAPBOX.pointLayout,
  });
  let popup = new mapboxgl.Popup({
    closeButton: false,
    closeOnMove: true,
    closeOnClick: false,
    focusAfterOpen: false,
  });
  map.on('mouseenter', 'points', (evt => onPointHover(evt, popup)));
  map.on('click', 'points', onPointClick);
  map.on('mouseleave', 'points', () => map.getCanvas().style.cursor = '');
}

function addMapLocations(map) {
  let dataSource = map.getContainer().dataset.mapLocSrc;
  if (!dataSource)
    return;
  map.addSource('locations', {type: 'geojson', data: dataSource});
  map.addLayer({
    id: 'locations',
    source: 'locations',
    type: 'circle',
    paint: MAPBOX.locationLayout,
  });
}

function onPointHover({target: map, features: [point, ..._]}, popup) {
  let {title, url} = point.properties;
  let coordinates = point.geometry.coordinates.slice();
  let content = `<a href=${url} target=_blank rel=noopener>${title}</a>`;
  map.getCanvas().style.cursor = 'pointer';
  popup.setLngLat(coordinates).setHTML(content).addTo(map);
  popup.getElement().addEventListener('click', () => trackPointClick(point));
  popup.getElement().style.setProperty('--popup-color', point.properties.color);
}

function onPointClick({features: [point, ..._]}) {
  trackPointClick(point);
  window.open(point.properties.url, '_blank', 'noopener');
}

function trackPointClick(point) {
  let umami = window.umami || null;
  if (umami)
    umami.track('map-point-clicked', {url: point.properties.url});
}

function loadScript(src, defer = true) {
  let script = document.createElement('script');
  return new Promise((resolve, reject) => {
    script.src = src;
    script.defer = defer;
    script.onload = () => resolve({status: true});
    script.onerror = () => reject({status: false, message: `Failed loading ${src}`});
    document.head.appendChild(script);
  });
}
