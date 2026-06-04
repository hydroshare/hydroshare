import {
  state, log, setProgress,
  PARQUET_URLS,
  RES_DIVIDES_PMTILES_URL,
  RES_FLOWPATHS_PMTILES_URL,
} from './config.js';
import { useParquet } from './composables/useParquet.js';

const { initHyparquet, readParquetAll } = useParquet();

// ── NAD83 Conus Albers (EPSG:5070) -> WGS84 ───────────────
const _ALB = (() => {
  const D=Math.PI/180, a=6378137.0, f=1/298.257222101;
  const e2=2*f-f*f, e=Math.sqrt(e2);
  const phi0=23*D, lam0=-96*D, phi1=29.5*D, phi2=45.5*D;
  const m=phi=>{const s=Math.sin(phi);return Math.cos(phi)/Math.sqrt(1-e2*s*s);};
  const q=phi=>{const s=Math.sin(phi);return (1-e2)*(s/(1-e2*s*s)-1/(2*e)*Math.log((1-e*s)/(1+e*s)));};
  const m1=m(phi1),m2=m(phi2),q0=q(phi0),q1=q(phi1),q2=q(phi2);
  const n=(m1*m1-m2*m2)/(q2-q1),C=m1*m1+n*q1,rho0=a*Math.sqrt(C-n*q0)/n;
  return (x,y)=>{
    const rho=Math.sqrt(x*x+(rho0-y)*(rho0-y)),theta=Math.atan2(x,rho0-y);
    const qv=(C-(rho*n/a)**2)/n;
    let phi=Math.asin(qv/2);
    for(let i=0;i<10;i++){const sp=Math.sin(phi),cp=Math.cos(phi),f2=1-e2*sp*sp;phi+=f2*f2/(2*cp)*(qv/(1-e2)-sp/f2+1/(2*e)*Math.log((1-e*sp)/(1+e*sp)));}
    return [lam0/D+theta/n/D,phi/D];
  };
})();

function _ensureBytes(v) {
  if (v instanceof Uint8Array) return v;
  if (v instanceof ArrayBuffer) return new Uint8Array(v);
  if (v?.buffer instanceof ArrayBuffer) return new Uint8Array(v.buffer,v.byteOffset,v.byteLength);
  if (typeof v==='string'){const b=new Uint8Array(v.length);for(let i=0;i<v.length;i++)b[i]=v.charCodeAt(i)&0xff;return b;}
  return null;
}

function _stripGpHeader(bytes) {
  if (bytes[0]===0x47&&bytes[1]===0x50) return bytes.subarray(8+[0,32,48,48,64][(bytes[3]&0x0E)>>1]);
  return bytes;
}

function _readRing(dv,off,n,le) {
  const coords=[];
  for(let i=0;i<n;i++,off+=16) coords.push(_ALB(dv.getFloat64(off,le),dv.getFloat64(off+8,le)));
  return {coords,end:off};
}

function geomCol(rows) {
  if (!rows?.length) return null;
  return Object.keys(rows[0]).find(k=>k==='geom'||k==='geometry')??null;
}

function wkbToGeojsonGeom(rawV) {
  let bytes=_ensureBytes(rawV);
  if (!bytes||bytes.length<5) return null;
  try {
    bytes=_stripGpHeader(bytes);
    const le=bytes[0]===1,dv=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);
    const gt=dv.getUint32(1,le)&0xffff;
    if(gt===1) return {type:'Point',coordinates:_ALB(dv.getFloat64(5,le),dv.getFloat64(13,le))};
    if(gt===2){const n=dv.getUint32(5,le);return {type:'LineString',coordinates:_readRing(dv,9,n,le).coords};}
    if(gt===3){const nr=dv.getUint32(5,le);const rings=[];let off=9;for(let r=0;r<nr;r++){const n=dv.getUint32(off,le);off+=4;const res=_readRing(dv,off,n,le);off=res.end;rings.push(res.coords);}return {type:'Polygon',coordinates:rings};}
    if(gt===5){const ng=dv.getUint32(5,le);let off=9;const lines=[];for(let g=0;g<ng;g++){off+=5;const n=dv.getUint32(off,le);off+=4;const res=_readRing(dv,off,n,le);off=res.end;lines.push(res.coords);}return {type:'MultiLineString',coordinates:lines};}
    if(gt===6){const ng=dv.getUint32(5,le);let off=9;const polys=[];for(let g=0;g<ng;g++){off+=5;const nr=dv.getUint32(off,le);off+=4;const rings=[];for(let r=0;r<nr;r++){const n=dv.getUint32(off,le);off+=4;const res=_readRing(dv,off,n,le);off=res.end;rings.push(res.coords);}polys.push(rings);}return {type:'MultiPolygon',coordinates:polys};}
    return null;
  } catch(e){return null;}
}

function rowsToGeojson(rows,col) {
  const features=[];let bbox=null;
  for(const row of rows){
    const rawGeom=row[col];if(!rawGeom)continue;
    const geom=wkbToGeojsonGeom(rawGeom);if(!geom)continue;
    const props={};
    for(const [k,v] of Object.entries(row)){if(k!==col)props[k]=(v instanceof Uint8Array)?null:v;}
    features.push({type:'Feature',geometry:geom,properties:props});
    const sample=geom.type==='Point'?[geom.coordinates]:geom.type==='LineString'?geom.coordinates:geom.type==='MultiLineString'?geom.coordinates[0]:geom.type==='Polygon'?geom.coordinates[0]:geom.type==='MultiPolygon'?geom.coordinates[0][0]:[];
    for(const [lon,lat] of sample){
      if(!isFinite(lon)||!isFinite(lat))continue;
      if(!bbox)bbox=[lon,lat,lon,lat];
      else{if(lon<bbox[0])bbox[0]=lon;if(lat<bbox[1])bbox[1]=lat;if(lon>bbox[2])bbox[2]=lon;if(lat>bbox[3])bbox[3]=lat;}
    }
  }
  return {type:'FeatureCollection',features,bbox};
}

function inferVpuid(rows) {
  if (!rows?.length) return null;
  const keys=Object.keys(rows[0]);
  const col=keys.find(k=>k==='vpuid')??keys[5];
  if (!col) return null;
  const val=rows[0][col];
  return val!=null?String(val):null;
}

// ── Layer adders ──────────────────────────────────────────
function addPmtilesLayers() {
  const { map } = state;
  map.addSource('res-divides-src', {
    type: 'vector',
    url: `pmtiles://${RES_DIVIDES_PMTILES_URL}`,
  });
  map.addLayer({
    id: 'res-divides-fill',
    type: 'fill',source:'res-divides-src',
    'source-layer':'divides',
    layout: {
      visibility: 'visible'

    },
    paint:{
      'fill-color': '#a78bfa',
      'fill-opacity': 0.15

    }
  });
  map.addLayer({
    id: 'res-divides-line',
    type: 'line',
    source: 'res-divides-src',
    'source-layer': 'divides',
    layout: {
      visibility: 'visible'

    },
    paint:{
      'line-color': '#a78bfa',
      'line-width': 0.8,
      'line-opacity': 0.9

    }
  });
  map.addSource('res-flowpaths-src',
    {
    type: 'vector',
    url: `pmtiles://${RES_FLOWPATHS_PMTILES_URL}` 
  });
  map.addLayer({
    id:  'res-flowpaths-line',
    type: 'line',
    source: 'res-flowpaths-src',
    'source-layer': 'flowpaths',
    ayout:{
      visibility:'visible'

    },
    paint:{
      'line-color': '#38bdf8',
      'line-width': 1.2,
      'line-opacity': 0.9

    }
  });

  // Fit to bounds once source metadata is loaded
  map.on('sourcedata', function onSourceData(e) {
    if (e.sourceId !== 'res-divides-src' || !e.isSourceLoaded) return;
    const src = map.getSource('res-divides-src');
    if (src?.bounds) {
      state.researcherBbox = src.bounds;
      map.fitBounds( [[src.bounds[0], src.bounds[1]], [src.bounds[2], src.bounds[3]]],{padding: 60, maxZoom: 12, duration: 1200});
      map.off('sourcedata',onSourceData);
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
    const col = geomCol(rows);
    if (col && rows.length > 0) {
      const gj = rowsToGeojson(rows, col);
      map.addSource('res-nexus-src',
        {
        type: 'geojson',
        data: gj
        }
      );
      map.addLayer({
        id: 'res-nexus-circle',
        type: 'circle',
        source: 'res-nexus-src',
        layout: {
        visibility: 'none' },
        paint: {
        'circle-color': '#f59e0b',
        'circle-radius': 3,
        'circle-opacity': 0.85

      }
      });
      log(`  nexus: ${rows.length} points`, 'success');
    }
  } catch(e){log(`nexus error: ${e.message}`, 'error');}
}

// ── Main boot ─────────────────────────────────────────────
export function useViewer() {
  async function bootViewer() {
    await initHyparquet();
    log('Loading viewer...','info');
    setProgress(20);
    addPmtilesLayers();

    log('Reading metadata...','info');
    setProgress(40);
    try {
      const divRows = await readParquetAll(PARQUET_URLS['divides']);
      state.inferredVpuid = inferVpuid(divRows);
      let fpCount=null;
      try{fpCount=(await readParquetAll(PARQUET_URLS['flowpaths'])).length;}catch(_){}
      log(`  vpuid: ${state.inferredVpuid}, catchments: ${divRows.length}`,'success');
      setProgress(100);
      return {
        vpuid: state.inferredVpuid,
        catchments: divRows.length,
        flowpaths: fpCount,
        renderMode: 'PMTiles',
        bbox: state.researcherBbox

      };
    } catch(e) {
      log(`  metadata error: ${e.message}`,'warn');
      setProgress(100);
      return {
        vpuid: '?',
        catchments: null,
        flowpaths: null,
        renderMode: 'PMTiles',
        bbox: null
      };
    }
  }

  function setLayerVisibility(layerIds, visible) {
    const v = visible ? 'visible' : 'none';
    for(const id of layerIds){
      if(state.map?.getLayer(id)) state.map.setLayoutProperty(id, 'visibility', v);
    }
  }

  return { bootViewer, setLayerVisibility };
}