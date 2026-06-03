import { 
  S3_MAP, S3_ORIGIN, REF_DIVIDES_PMTILES_URL, RES_FLOWPATHS_PMTILES_URL, 
  COMMUNITY_HF_DARK_STYLE, COMMUNITY_HF_ORIGIN,
  COMMUNITY_HF_DIVIDES, COMMUNITY_HF_FLOWPATHS,
  log, state,
} from '../config.js';
import { ensurePmtilesProtocol } from '../auth.js';
import { useDarkStyle } from '../updateMapFilters/dark-style.js';
import { useLightStyle } from '../updateMapFilters/light-style.js';

export function useMap() {
    function initMap() {
      ensurePmtilesProtocol();

        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

        state.map = new maplibregl.Map({
        container: 'map',
        style: prefersDark ? useDarkStyle() : useLightStyle(),
        center: [-96, 40],
        zoom: 4,
        transformRequest: (url) => {
          if(url.startsWith(S3_ORIGIN)) return { url, credentials: 'include' };
        },
        });
        state.map.addControl(new maplibregl.NavigationControl(), 'bottom-right');
      }

  function initMapRight() {
    ensurePmtilesProtocol();

    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    state.mapRight = new maplibregl.Map({
      container: 'map-right',
      style: prefersDark ? useDarkStyle() : useLightStyle(),
      center: state.map.getCenter(),
      zoom: state.map.getZoom(),
      bearing: state.map.getBearing(),
      pitch:   state.map.getPitch(),
      transformRequest: (url) => {
        if (url.startsWith(S3_ORIGIN) || url.startsWith(COMMUNITY_HF_ORIGIN))
          return { url, credentials: 'include' };
      },
    });
    state.mapRight.addControl(new maplibregl.NavigationControl(), 'bottom-right');

    state.mapRight.on('styledata', () => {
      if (state.mapRight.getSource('ref-divides-src')) return;

      state.mapRight.addSource('ref-divides-src', {
        type: 'vector', url: `pmtiles://${COMMUNITY_HF_DIVIDES}`,
      });
      state.mapRight.addLayer({
        id: 'ref-divides-fill', type: 'fill',
        source: 'ref-divides-src', 'source-layer': 'conus_divides',
        layout: { visibility: 'visible' },
        paint: { 'fill-color': '#a78bfa', 'fill-opacity': 0.15 },
      });
      state.mapRight.addLayer({
        id: 'ref-divides-line', type: 'line',
        source: 'ref-divides-src', 'source-layer': 'conus_divides',
        layout: { visibility: 'visible' },
        paint: { 'line-color': '#a78bfa', 'line-width': 0.8, 'line-opacity': 0.9 },
      });

      state.mapRight.addSource('ref-flowpaths-src', {
        type: 'vector', url: `pmtiles://${COMMUNITY_HF_FLOWPATHS}`,
      });
      state.mapRight.addLayer({
        id: 'ref-flowpaths-line', type: 'line',
        source: 'ref-flowpaths-src', 'source-layer': 'conus_flowpaths',
        layout: { visibility: 'visible' },
        paint: { 'line-color': '#38bdf8', 'line-width': 1.2, 'line-opacity': 0.9 },
      });
    });

    function onMove(src, tgt) {
      if (state.syncing) return;
      state.syncing = true;
      tgt.jumpTo({
        center: src.getCenter(), zoom: src.getZoom(),
        bearing: src.getBearing(), pitch: src.getPitch(),
      });
      state.syncing = false;
    }
    state.map.on('move',      () => { if (state.splitActive && state.mapRight) onMove(state.map, state.mapRight); });
    state.mapRight.on('move', () => { if (state.splitActive) onMove(state.mapRight, state.map); });
  }

  function toggleSplitView(active) {
    state.splitActive = active;
    document.body.classList.toggle('split-view', active);
    if (active) {
      if (!state.mapRight) {
        setTimeout(() => {
          initMapRight();
          state.map.resize();
        }, 0);
      } else {
        setTimeout(() => {
          state.map.resize();
          state.mapRight.resize();
          state.mapRight.jumpTo({
            center: state.map.getCenter(), zoom: state.map.getZoom(),
            bearing: state.map.getBearing(), pitch: state.map.getPitch(),
          });
        }, 0);
      }
    } else {
      setTimeout(() => state.map.resize(), 0);
    }
  }

  function fitToBbox(bbox, targetMap) {
    if (!bbox) return;
    (targetMap || state.map).fitBounds(
      [[bbox[0], bbox[1]], [bbox[2], bbox[3]]],
      { padding: 60, maxZoom: 12, duration: 1200 }
    );
  }

  return { initMap, toggleSplitView, fitToBbox };
}