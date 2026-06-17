import { log, state, NETWORK_GRAPH_URL } from "../config.js";

export function useNetwork() {
    async function loadNetworkGraph() {
      log('Loading network graph...', 'info');
      const t0 = performance.now();
      const resp = await fetch(NETWORK_GRAPH_URL, { credentials: 'include' });
      if (!resp.ok) throw new Error(`Failed: ${resp.status}`);
      state.networkGraph = await resp.json();
      log(`  ${state.networkGraph.meta.total_edges} edges in ${((performance.now()-t0)/1000).toFixed(1)}s`, 'success');
        
      const upstream = new Map();
      const fwd = new Map();
      for (const [ft, fn, tt, tn] of state.networkGraph.edges) {
        if ((ft === 0 || ft === 2) && (tt === 1 || tt === 3 || tt === 4)) {
          if (!upstream.has(tn)) upstream.set(tn, new Set());
          upstream.get(tn).add(fn);
          if (!fwd.has(fn)) fwd.set(fn, tn);
        }
      }
      state.adjacency = upstream;
      state.downstream = fwd;
      log(`  Adjacency: ${upstream.size} nodes`, 'success');
    }

    function getUpstreamIds(outletNumeric, includeOutlet = true) {
      const visited = new Set();
      visited.add(outletNumeric);
      const queue = [outletNumeric];

      if (includeOutlet) {
        const ds = state.downstream.get(outletNumeric);
        if (ds != null) queue.unshift(ds);
      }

      while (queue.length > 0) {
        const cur = queue.shift();
        const parents = state.adjacency.get(cur);
        if (!parents) continue;
        for (const p of parents) {
          if (!visited.has(p)) { visited.add(p); queue.push(p); }
        }
      }
      return visited;
    }
    return { loadNetworkGraph, getUpstreamIds };
}