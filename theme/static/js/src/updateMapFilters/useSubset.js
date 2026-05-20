import { log, state, PARQUET_URLS } from "../config.js";
import { useParquet } from "../composables/useParquet.js";
import { useGpkg } from "./useGpkg.js";
import { useNetwork } from "../composables/useNetwork.js";

const { initHyparquet, readParquetFiltered } = useParquet();
const { buildGeoPackage } = useGpkg();
const { getUpstreamIds } = useNetwork();

export function useSubset() {
    // ============================================================
    // SUBSET & DOWNLOAD
    //
    // Table order and inter-table dependencies match the Python
    // subsetting logic in subset_table() / create_subset_gpkg():
    //
    //   divides            -> filter by divide_id using catIds
    //   divide-attributes  -> filter by divide_id from subset divides
    //   flowpath-attributes    -> filter by id using wbIds
    //   flowpath-attributes-ml -> filter by id using wbIds
    //   flowpaths          -> filter by id using wbIds
    //   hydrolocations     -> filter by id using wbIds
    //   nexus              -> filter by id using nexIds + flowpath toids
    //   pois               -> filter by id using wbIds
    //   lakes              -> filter by poi_id from subset pois
    //   network            -> filter by id using the full upstream id set
    // ============================================================
    async function subsetAndDownload() {
      if (!state.outletCatId || state.upstreamNumericIds.size === 0) return;
      const btn = document.getElementById('btn-subset');
      btn.disabled = true;
      logEl.innerHTML = '';
      setProgress(0);

      try {
        const nums = Array.from(state.upstreamNumericIds);
        log(`Subsetting ${nums.length} catchments from ${state.outletCatId}`, 'step');

        await initHyparquet();

        // Build ID arrays matching Python's upstream_ids prefixing
        const catIds = nums.map(n => `cat-${n}`);
        const wbIds  = nums.map(n => `wb-${n}`);

        // The Python subset_table passes the same ids list to every table.
        // The SQL WHERE key_name IN (...) naturally ignores non-matching prefixes.
        // We replicate this by building the right ID list per table, matching
        // the column each table actually filters on.

        // allTableData stores { rows, url } per table so buildGeoPackage can
        // fetch parquet schema even when a table has 0 matching rows.
        const allTableData = {};
        const totalSteps = 12; // 10 tables + gpkg build + download
        let step = 0;

        async function doTable(name, url, filterCol, ids) {
          step++;
          setProgress((step / totalSteps) * 100);
          log(`  ${name}...`, 'info');
          const t0 = performance.now();
          try {
            const rows = await readParquetFiltered(url, filterCol, ids);
            allTableData[name] = { rows, url };
            log(`    ${rows.length} rows (${((performance.now()-t0)/1000).toFixed(1)}s)`, 'success');
          } catch (err) {
            log(`    Error: ${err.message}`, 'error');
            allTableData[name] = { rows: [], url };
          }
        }

        // Compute nexus IDs from network topology (no need to fetch flowpaths first)
        // Include nex-N for every N in the selection that has an upstream parent also in the selection
        const computedNexIds = [];
        for (const n of state.upstreamNumericIds) {
          const parents = state.adjacency.get(n);
          if (parents) {
            for (const p of parents) {
              if (state.upstreamNumericIds.has(p)) { computedNexIds.push(`nex-${n}`); break; }
            }
          }
        }
        // Add the outlet's downstream nexus (not in the upstream selection itself)
        const outletNumeric = parseInt(state.outletCatId.split('-')[1]);
        const outletDownstream = state.downstream.get(outletNumeric);
        if (outletDownstream != null) computedNexIds.push(`nex-${outletDownstream}`);
        const allNexIds = [...new Set(computedNexIds)];

        // --- Wave 1: all tables whose IDs are derived from the network graph ---
        await Promise.all([
          doTable('divides',              PARQUET_URLS['divides'],              'divide_id', catIds),
          doTable('divide-attributes',    PARQUET_URLS['divide-attributes'],    'divide_id', catIds),
          doTable('flowpaths',            PARQUET_URLS['flowpaths'],            'id', wbIds),
          doTable('flowpath-attributes',  PARQUET_URLS['flowpath-attributes'],  'id', wbIds),
          doTable('flowpath-attributes-ml', PARQUET_URLS['flowpath-attributes-ml'], 'id', wbIds),
          doTable('hydrolocations',       PARQUET_URLS['hydrolocations'],       'id', wbIds),
          doTable('nexus',                PARQUET_URLS['nexus'],                'id', allNexIds),
          doTable('pois',                 PARQUET_URLS['pois'],                 'id', wbIds),
          doTable('network',              PARQUET_URLS['network'],              'id', [...wbIds, ...allNexIds]),
        ]);

        // --- Wave 2: lakes depends on pois results ---
        const poiIds = (allTableData['pois']?.rows || []).map(r => r.poi_id).filter(x => x != null);
        if (poiIds.length > 0) {
          await doTable('lakes', PARQUET_URLS['lakes'], 'poi_id', poiIds);
        } else {
          step++;
          setProgress((step / totalSteps) * 100);
          allTableData['lakes'] = { rows: [], url: PARQUET_URLS['lakes'] };
          log('  lakes... 0 rows (no poi_ids)', '');
        }

        // Build GeoPackage
        step++;
        setProgress((step / totalSteps) * 100);
        log('Building GeoPackage...', 'step');
        const gpkgBlob = await buildGeoPackage(allTableData);

        setProgress(100);
        const filename = `${state.outletCatId}_subset.gpkg`;
        const a = document.createElement('a');
        a.href = URL.createObjectURL(gpkgBlob);
        a.download = filename;
        a.click();
        URL.revokeObjectURL(a.href);
        log(`Downloaded ${filename} (${(gpkgBlob.size/1024/1024).toFixed(1)} MB)`, 'success');
      } catch (err) {
        log(`FATAL: ${err.message}`, 'error');
        console.error(err);
      } finally {
        btn.disabled = false;
      }
    }
    return { subsetAndDownload };
}