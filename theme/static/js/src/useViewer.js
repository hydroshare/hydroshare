import {
  state, log, setProgress,
  PARQUET_URLS,
  RES_DIVIDES_PMTILES_URL,
  RES_FLOWPATHS_PMTILES_URL,
} from './config.js';
import { useParquet } from './composables/useParquet.js';
import { _ensureBytes } from './updateMapFilters/useGpkg.js'

const { initHyparquet, readParquetAll } = useParquet();

function geomCol(rows) {
  if (!rows?.length) return null;
  return Object.keys(rows[0]).find(k => k === 'geom' || k === 'geometry') ?? null;
}

function wkbToGeojsonGeom(rawV) {
  let bytes = _ensureBytes(rawV);
  if (!bytes || bytes.length < 5) return null;
  try {
    bytes = _stripGpHeader(bytes);
    const le = bytes[0] === 1;
    const dv = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    const gt = dv.getUint32(1, le) & 0xffff;

    if (gt === 1) {
      return { type: 'Point', coordinates: _ALB(dv.getFloat64(5, le), dv.getFloat64(13, le)) };
    }
    if (gt === 2) {
      const n = dv.getUint32(5, le);
      return { type: 'LineString', coordinates: _readRing(dv, 9, n, le).coords };
    }
    if (gt === 3) {
      const nr = dv.getUint32(5, le); const rings = []; let off = 9;
      for (let r = 0; r < nr; r++) {
        const n = dv.getUint32(off, le); off += 4;
        const res = _readRing(dv, off, n, le); off = res.end;
        rings.push(res.coords);
      }
      return { type: 'Polygon', coordinates: rings };
    }
    if (gt === 5) { // MULTILINESTRING
      const ng = dv.getUint32(5, le); let off = 9; const lines = [];
      for (let g = 0; g < ng; g++) {
        off += 5;
        const n = dv.getUint32(off, le); off += 4;
        const res = _readRing(dv, off, n, le); off = res.end;
        lines.push(res.coords);
      }
      return { type: 'MultiLineString', coordinates: lines };
    }
    if (gt === 6) { // MULTIPOLYGON
      const ng = dv.getUint32(5, le); let off = 9; const polys = [];
      for (let g = 0; g < ng; g++) {
        off += 5;
        const nr = dv.getUint32(off, le); off += 4; const rings = [];
        for (let r = 0; r < nr; r++) {
          const n = dv.getUint32(off, le); off += 4;
          const res = _readRing(dv, off, n, le); off = res.end;
          rings.push(res.coords);
        }
        polys.push(rings);
      }
      return { type: 'MultiPolygon', coordinates: polys };
    }
    return null;
  } catch(e) { return null; }
}

function rowsToGeojson(rows, geomCol) {
  const features = [];
  let bbox = null;

  for (const row of rows) {
    const rawGeom = row[geomCol];
    if (!rawGeom) continue;
    const geom = wkbToGeojsonGeom(rawGeom);
    if (!geom) continue;

    const props = {};
    for (const [k, v] of Object.entries(row)) {
      if (k !== geomCol) props[k] = (v instanceof Uint8Array) ? null : v;
    }
    features.push({ type: 'Feature', geometry: geom, properties: props });

    // Expand bbox from the first ring/coords of each feature
    const sample =
      geom.type === 'Point'            ? [geom.coordinates]
      : geom.type === 'LineString'     ? geom.coordinates
      : geom.type === 'MultiLineString'? geom.coordinates[0]
      : geom.type === 'Polygon'        ? geom.coordinates[0]
      : geom.type === 'MultiPolygon'   ? geom.coordinates[0][0]
      : [];
    for (const [lon, lat] of sample) {
      if (!isFinite(lon) || !isFinite(lat)) continue;
      if (!bbox) bbox = [lon, lat, lon, lat];
      else {
        if (lon < bbox[0]) bbox[0] = lon;
        if (lat < bbox[1]) bbox[1] = lat;
        if (lon > bbox[2]) bbox[2] = lon;
        if (lat > bbox[3]) bbox[3] = lat;
      }
    }
  }
  return { type: 'FeatureCollection', features, bbox };
}

// ── Layer adders ──────────────────────────────────────────
function addPmtilesLayers() {
  const { map } = state;
  map.addSource('res-divides-src', {
    type: 'vector', url: `pmtiles://${RES_DIVIDES_PMTILES_URL}`,
  });
  map.addLayer({
    id: 'res-divides-fill', type: 'fill',
    source: 'res-divides-src', 'source-layer': 'divides',
    paint: { 'fill-color': '#a78bfa', 'fill-opacity': 0.15 },
  });
  map.addLayer({
    id: 'res-divides-line', type: 'line',
    source: 'res-divides-src', 'source-layer': 'divides',
    paint: { 'line-color': '#a78bfa', 'line-width': 0.8, 'line-opacity': 0.9 },
  });
  map.addSource('res-flowpaths-src', {
    type: 'vector', url: `pmtiles://${RES_FLOWPATHS_PMTILES_URL}`,
  });
  map.addLayer({
    id: 'res-flowpaths-line', type: 'line',
    source: 'res-flowpaths-src', 'source-layer': 'flowpaths',
    paint: { 'line-color': '#38bdf8', 'line-width': 1.2, 'line-opacity': 0.9 },
  });
  // Fit to bounds once source metadata is loaded
  map.once('sourcedata', (e) => {
    if (e.sourceId !== 'res-divides-src' || !e.isSourceLoaded) return;
    const src = map.getSource('res-divides-src');
    if (src?.bounds) {
      state.researcherBbox = src.bounds;
      map.fitBounds(
        [[src.bounds[0], src.bounds[1]], [src.bounds[2], src.bounds[3]]],
        { padding: 60, maxZoom: 12, duration: 1200 }
      );
    }
  });
}

// Nexus always loaded lazily from parquet — no nexus pmtiles in pipeline
export async function ensureNexusLayer() {
  const { map } = state;
  if (map.getSource('res-nexus-src')) return;
  log('Loading nexus...', 'info');
  try {
    await initHyparquet();
    const rows = await readParquetAll(PARQUET_URLS['nexus']);
    const col  = geomCol(rows);
    if (col && rows.length > 0) {
      const gj = rowsToGeojson(rows, col);
      map.addSource('res-nexus-src', { type: 'geojson', data: gj });
      map.addLayer({
        id: 'res-nexus-circle', type: 'circle', source: 'res-nexus-src',
        layout: { visibility: 'none' },
        paint: { 'circle-color': '#f59e0b', 'circle-radius': 3, 'circle-opacity': 0.85 },
      });
      log(`  nexus: ${rows.length} points`, 'success');
    }
  } catch(e) { log(`  nexus error: ${e.message}`, 'error'); }
}

// ── Main boot ─────────────────────────────────────────────
export function useViewer() {
  async function bootViewer() {
    await initHyparquet();

    log('Checking for pre-generated pmtiles...', 'info');
    setProgress(10);


      log('  pmtiles found — using vector tiles', 'success');
      setProgress(30);
      addPmtilesLayers();
      window._map = state.map;

      // Read divides parquet for vpuid + catchment count + bbox
      log('Reading metadata from parquet...', 'info');
      setProgress(40);
      try {
        const divRows = await readParquetAll(PARQUET_URLS['divides']);
        state.inferredVpuid = inferVpuid(divRows);

        const col = geomCol(divRows);
        if (col) {
          // Sample up to 500 rows for a fast bbox estimate
          const sample = rowsToGeojson(divRows.slice(0, Math.min(divRows.length, 500)), col);
          if (sample.bbox) state.researcherBbox = sample.bbox;
        }

        let fpCount = null;
        try {
          const fpRows = await readParquetAll(PARQUET_URLS['flowpaths']);
          fpCount = fpRows.length;
        } catch(_) {}

        log(`  vpuid: ${state.inferredVpuid}, catchments: ${divRows.length}`, 'success');
        setProgress(80);
        return {
          vpuid: state.inferredVpuid,
          catchments: divRows.length,
          flowpaths: fpCount,
          renderMode: 'PMTiles',
          bbox: state.researcherBbox,
        };
      } catch(e) {
        log(`  metadata error: ${e.message}`, 'warn');
        setProgress(80);
        return { vpuid: '?', catchments: null, flowpaths: null, renderMode: 'PMTiles', bbox: null };
      }
  }

  function inferVpuid(rows) {
    if (!rows || rows.length === 0) return null;
    const keys = Object.keys(rows[0]);
    const col  = keys.find(k => k === 'vpuid') ?? keys[5];
    console.log('inferVpuid: found columns', keys, 'using', col);
    if (!col) return null;
    const val = rows[0][col];
    return val != null ? String(val) : null;
  }

  function setLayerVisibility(layerIds, visible) {
    const v = visible ? 'visible' : 'none';
    for (const id of leftIds) {
      if (state.map?.getLayer(id)) state.map.setLayoutProperty(id, 'visibility', v);
    }
    if (state.mapRight) {
      for (const id of rightIds) {
        if (state.mapRight.getLayer(id)) state.mapRight.setLayoutProperty(id, 'visibility', v);
      }
    }
  }

  return { bootViewer, setLayerVisibility };
}