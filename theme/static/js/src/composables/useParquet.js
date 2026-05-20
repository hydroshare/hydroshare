import { log, state } from '../config.js';

export function useParquet() {
    async function initHyparquet() {
      if (state.hp) return;
      log('Loading hyparquet...', 'info');
      const t0 = performance.now();

      state.hp = await import('https://cdn.jsdelivr.net/npm/hyparquet/+esm');

      try {
        const hpc = await import('https://cdn.jsdelivr.net/npm/hyparquet-compressors/+esm');
        state.compressors = hpc.compressors;
        log(`  hyparquet + compressors ready (${((performance.now()-t0)/1000).toFixed(1)}s)`, 'success');
      } catch (e) {
        log(`  hyparquet ready, compressors unavailable (${e.message})`, 'info');
        state.compressors = undefined;
      }
    }

    async function getFileHandle(url) {
      if (!state.fileHandleCache[url]) {
        state.fileHandleCache[url] = await state.hp.asyncBufferFromUrl({ url, requestInit: { credentials: 'include' } });
      }
      return state.fileHandleCache[url];
    }

    /**
    * Read rows from a remote parquet file using hyparquet's $in filter.
    * Row groups whose min/max stats don't overlap the $in values are
    * skipped entirely (no range request made).
    */
    const _td = new TextDecoder();

    async function readParquetFiltered(url, filterCol, idArray) {
      const file = await getFileHandle(url);
      const opts = {
        file,
        geoparquet: false,
        rowFormat: 'object',
        utf8: false, // keep BYTE_ARRAY as Uint8Array so binary geom isn't corrupted by UTF-8 decoding
        filter: { [filterCol]: { $in: idArray } },
      };
      if (state.compressors) opts.compressors = state.compressors;

      const rows = await state.hp.parquetReadObjects(opts);
      return rows.map(row => {
        const out = {};
        for (const [k, v] of Object.entries(row)) {
          if (typeof v === 'bigint') {
            out[k] = Number(v);
          } else if (v instanceof Uint8Array && k !== 'geom' && k !== 'geometry') {
            // Non-geom BYTE_ARRAY columns are text — decode them back to strings
            out[k] = _td.decode(v);
          } else {
            out[k] = v;
          }
        }
        return out;
      });
    }
    return { initHyparquet, readParquetFiltered };
}