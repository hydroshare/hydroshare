export const S3_ORIGIN = `http://localhost:9002`;

// Detect which tool we're running as based on the URL path segment
const parts = window.location.pathname.split('/').filter(Boolean);
const _subsetIdx  = parts.indexOf('hydrofabric-fdxubsetter');
const _viewerIdx  = parts.indexOf('hydrofabric-subsetter');
const _matchIdx   = _subsetIdx >= 0 ? _subsetIdx : _viewerIdx;

export const VIEWER_MODE = true;
export const RESOURCE_ID = (_matchIdx >= 0 && parts[_matchIdx + 1])
  ? parts[_matchIdx + 1]
  : '';

const S3_BUCKET_NAME = 'resource';
export const S3_PARQUET = `${S3_ORIGIN}/${S3_BUCKET_NAME}/${RESOURCE_ID}/data/contents/parquet`;
export const S3_MAP = `${S3_ORIGIN}/${S3_BUCKET_NAME}/${RESOURCE_ID}/data/contents/map`;
export const NETWORK_GRAPH_URL = `${S3_PARQUET}/network_graph.json`;
export const REF_FLOWPATHS_PMTILES_URL = `${S3_MAP}/only_geometry/reference/flowpaths.pmtiles`;
export const REF_DIVIDES_PMTILES_URL = `${S3_MAP}/only_geometry/reference/divides.pmtiles`;

//researcher's pre-generated pmtiles
export const RES_DIVIDES_PMTILES_URL   = `${S3_MAP}/only_geometry/reference/divides.pmtiles`;
export const RES_FLOWPATHS_PMTILES_URL = `${S3_MAP}/only_geometry/reference/flowpaths.pmtiles`;

//styles
export const MERGED_PMTILES_URL = `${S3_MAP}/merged.pmtiles`;
export const VPU_PMTILES_URL = `${S3_MAP}/only_geometry/reference/vpu.pmtiles`;

//community hydrofabric reference
export const COMMUNITY_HF_ORIGIN     = `${S3_ORIGIN}/${S3_BUCKET_NAME}/${RESOURCE_ID}/data/contents/community`;
export const COMMUNITY_HF_MAP        = `${COMMUNITY_HF_ORIGIN}/map`;
export const COMMUNITY_HF_DIVIDES = `${COMMUNITY_HF_MAP}/only_geometry/reference/divides.pmtiles`;
export const COMMUNITY_HF_FLOWPATHS = `${COMMUNITY_HF_MAP}/only_geometry/reference/flowpaths.pmtiles`;

export let pmtilesProtocolRegistered = false;
export function isPmtilesProtocolRegistered() {
  return pmtilesProtocolRegistered;
}
export function setPmtilesProtocolRegistered(val) { pmtilesProtocolRegistered = val;}


export const PARQUET_URLS = {
  'divides':                `${S3_PARQUET}/divides.parquet`,
  'divide-attributes':      `${S3_PARQUET}/divide-attributes.parquet`,
  'flowpaths':              `${S3_PARQUET}/flowpaths.parquet`,
  'flowpath-attributes':    `${S3_PARQUET}/flowpath-attributes.parquet`,
  'flowpath-attributes-ml': `${S3_PARQUET}/flowpath-attributes-ml.parquet`,
  'hydrolocations':         `${S3_PARQUET}/hydrolocations.parquet`,
  'nexus':                  `${S3_PARQUET}/nexus.parquet`,
  'pois':                   `${S3_PARQUET}/pois.parquet`,
  'lakes':                  `${S3_PARQUET}/lakes.parquet`,
  'network':                `${S3_PARQUET}/network.parquet`,
};

export const state = {
  networkGraph: null,
  adjacency: null,
  downstream: null,


  //for selection
  outletCatId: null,
  upstreamCatIds: [],
  upstreamNumericIds: new Set(),

  //map stuff
  map: null,
  mapRight: null,
  splitActive: false,
  syncing: false,

  // hyparquet
  hp: null,
  compressors: null,
  fileHandleCache: {},

  // viewer
  inferredVpuid: null,
  researcherBbox: null,
  usingPmtiles: false,
};

// ============================================================
// LOGGING
// ============================================================
const logEl = document.getElementById('log');
export function log(msg, cls = '') {
  const span = document.createElement('span');
  span.className = cls;
  span.textContent = msg + '\n';
  logEl.appendChild(span);
  logEl.parentElement.scrollTop = logEl.parentElement.scrollHeight;
}
export function setProgress(pct) {
  document.getElementById('progress-fill').style.width = pct + '%';
}