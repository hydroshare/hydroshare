import { S3_MAP, S3_ORIGIN, REF_DIVIDES_PMTILES_URL, REF_FLOWPATHS_PMTILES_URL, log, state } from '../config.js';
import { ensurePmtilesProtocol } from '../auth.js';

export function useMap() {
    function initMap() {
        ensurePmtilesProtocol();

        const darkStyle = `${S3_MAP}/styles/dark-style.json`;
        const lightStyle = `${S3_MAP}/styles/light-style.json`;
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

        state.map = new maplibregl.Map({
        container: 'map',
        style: prefersDark ? darkStyle : lightStyle,
        center: [-96, 40],
        zoom: 4,
        transformRequest: (url) => {
            if(url.startsWith(S3_ORIGIN)) return { url, credentials: 'include' };
        },
        });
      
        state.map.on("styledata", () => {
        if (state.map.getSource("oconus_ref_flowpaths")) return;
        state.map.addSource("oconus_ref_flowpaths", {
            type: "vector",
            url: `pmtiles://${REF_FLOWPATHS_PMTILES_URL}`,
        });
        state.map.addLayer(
            {
            id: "ref_flowpaths",
            type: "line",
            source: "oconus_ref_flowpaths",
            "source-layer": "conus_flowpaths",
            layout: { visibility: "none" },
            paint: {
                "line-width": 1,
                "line-color": document.getElementById('color-flowpaths').value,
                "line-opacity": 1,
            },
            },
            "flowpaths"
        );
        state.map.addSource("oconus_ref_divides", {
            type: "vector",
            url: `pmtiles://${REF_DIVIDES_PMTILES_URL}`,
        });
        state.map.addLayer(
            {
            id: "ref_divides",
            type: "line",
            source: "oconus_ref_divides",
            "source-layer": "conus_divides",
            layout: { visibility: "none" },
            paint: {
                "line-width": 0.5,
                "line-color": document.getElementById('color-divides').value,
                "line-opacity": 0.9,
            },
            },
            "catchments"
        );
        });

        state.map.on('load', () => {
        state.map.on('click', 'catchments', (e) => {
            if (e.features && e.features.length > 0) {
            const catId = e.features[0].properties.divide_id;
            if (catId) selectOutlet(catId);
            }
        });
        state.map.on('mouseenter', 'catchments', () => { state.map.getCanvas().style.cursor = 'pointer'; });
        state.map.on('mouseleave', 'catchments', () => { state.map.getCanvas().style.cursor = ''; });
        log('Map loaded. Zoom in to see catchments, then click one.', 'success');
        });
    }

    function updateMapFilters() {
        const maps = [state.map];
        if (state.splitActive && state.mapRight && state.mapRight.isStyleLoaded()) maps.push(state.mapRight);

        for (const m of maps) {
        if (!m || !m.isStyleLoaded()) continue;
        if (!outletCatId) {
            m.setFilter('selected-catchments', ['any', ['in', 'divide_id', '']]);
            m.setFilter('upstream-catchments', ['any', ['in', 'divide_id', '']]);
            continue;
        }
        m.setFilter('selected-catchments', ['any', ['in', 'divide_id', outletCatId]]);
        const upstreamList = upstreamCatIds.filter(id => id !== outletCatId);
        if (upstreamList.length > 0) {
            m.setFilter('upstream-catchments', ['any', ['in', 'divide_id', ...upstreamList]]);
        } else {
            m.setFilter('upstream-catchments', ['any', ['in', 'divide_id', '']]);
        }
        }
    }

    // ============================================================
    // SPLIT VIEW
    // ============================================================
    function initMapRight() {
        ensurePmtilesProtocol();
        const darkStyle = `${S3_MAP}/styles/dark-style.json`;
        const lightStyle = `${S3_MAP}/styles/light-style.json`;
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

        state.mapRight = new maplibregl.Map({
        container: 'map-right',
        style: prefersDark ? darkStyle : lightStyle,
        center: state.map.getCenter(),
        zoom: state.map.getZoom(),
        bearing: state.map.getBearing(),
        pitch: state.map.getPitch(),
        transformRequest: (url) => {
            if(url.startsWith(S3_ORIGIN)) return { url, credentials: 'include' };
        },
        });

        state.mapRight.on("styledata", () => {
        // Hide base catchments/flowpaths on the reference map
        if (state.mapRight.getLayer("catchments")) state.mapRight.setLayoutProperty("catchments", "visibility", "none");
        if (state.mapRight.getLayer("flowpaths")) state.mapRight.setLayoutProperty("flowpaths", "visibility", "none");

        if (state.mapRight.getSource("oconus_ref_flowpaths")) return;
        state.mapRight.addSource("oconus_ref_flowpaths", {
            type: "vector",
            url: `pmtiles://${REF_FLOWPATHS_PMTILES_URL}`,
        });
        state.mapRight.addLayer({
            id: "ref_flowpaths",
            type: "line",
            source: "oconus_ref_flowpaths",
            "source-layer": "conus_flowpaths",
            layout: { visibility: document.getElementById('toggle-flowpaths').checked ? 'visible' : 'none' },
            paint: {
            "line-width": 1,
            "line-color": document.getElementById('color-flowpaths').value,
            "line-opacity": 1,
            },
        });
        state.mapRight.addSource("oconus_ref_divides", {
          type: "vector",
          url: `pmtiles://${REF_DIVIDES_PMTILES_URL}`,
        });
        state.mapRight.addLayer({
          id: "ref_divides",
          type: "line",
          source: "oconus_ref_divides",
          "source-layer": "conus_divides",
          layout: { visibility: document.getElementById('toggle-divides').checked ? 'visible' : 'none' },
          paint: {
            "line-width": 0.5,
            "line-color": document.getElementById('color-divides').value,
            "line-opacity": 0.9,
          },
        });

        // Apply any existing selection to the right map
        updateMapFilters();
    });

    // Sync camera between maps
    function onMove(source, target) {
        if (state.syncing) return;
        state.syncing = true;
        target.jumpTo({
            center: source.getCenter(),
            zoom: source.getZoom(),
            bearing: source.getBearing(),
            pitch: source.getPitch(),
        });
        state.syncing = false;
        }
        state.map.on('move', () => { if (state.splitActive && state.mapRight) onMove(state.map, state.mapRight); });
        state.mapRight.on('move', () => { if (state.splitActive) onMove(state.mapRight, state.map); });
    }

    function toggleSplitView(active) {
        state.splitActive = active;
        document.body.classList.toggle('split-view', active);

        if (active) {
        // Hide ref layers on main map
        if (state.map.getLayer('ref_flowpaths')) state.map.setLayoutProperty('ref_flowpaths', 'visibility', 'none');
        if (state.map.getLayer('ref_divides')) state.map.setLayoutProperty('ref_divides', 'visibility', 'none');

        if (!state.mapRight) {
            // Show container first so MapLibre can measure it, then init
            setTimeout(() => {
            initMapRight();
            // Auto-enable both ref layers on the right map
            document.getElementById('toggle-flowpaths').checked = true;
            document.getElementById('toggle-flowpaths').dispatchEvent(new Event('change'));
            document.getElementById('toggle-divides').checked = true;
            document.getElementById('toggle-divides').dispatchEvent(new Event('change'));
            state.map.resize();
            }, 0);
        } else {
            setTimeout(() => {
            state.map.resize();
            state.mapRight.resize();
            // Sync position
            state.mapRight.jumpTo({ center: state.map.getCenter(), zoom: state.map.getZoom(), bearing: state.map.getBearing(), pitch: state.map.getPitch() });
            }, 0);
        }
        } else {
        // Transfer ref layer state back to main map
        const fpVisible = document.getElementById('toggle-flowpaths').checked;
        const dvVisible = document.getElementById('toggle-divides').checked;
        if (state.map.getLayer('ref_flowpaths')) {
            state.map.setLayoutProperty('ref_flowpaths', 'visibility', fpVisible ? 'visible' : 'none');
            state.map.setPaintProperty('ref_flowpaths', 'line-color', document.getElementById('color-flowpaths').value);
        }
        if (state.map.getLayer('ref_divides')) {
            state.map.setLayoutProperty('ref_divides', 'visibility', dvVisible ? 'visible' : 'none');
            state.map.setPaintProperty('ref_divides', 'line-color', document.getElementById('color-divides').value);
        }
        setTimeout(() => state.map.resize(), 0);
        }
        }
        return { initMap, updateMapFilters, toggleSplitView };
}

