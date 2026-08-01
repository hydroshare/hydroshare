<template>
  <v-card class="cd-spatial-coverage-map">
    <div ref="map" class="map-container"></div>
  </v-card>
</template>

<script lang="ts">
import L from "leaflet";
import { FullScreen } from "leaflet.fullscreen";
import "leaflet.fullscreen/dist/Control.FullScreen.css";
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";

// Fix Leaflet's broken default icon paths when bundled with Vite
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
});

const coverageMapBoxMaxZoom = 18;
const coverageMapPointMaxZoom = 7;

</script>

<script setup lang="ts">
const props = defineProps<{
  feature: any;
}>();

const mapContainer = useTemplateRef<HTMLElement>("map");

let coverageMap: L.Map;
let leafletMarkers: L.FeatureGroup<any>;

onMounted(async () => {
  await initMap();
  drawInitialShape();
});

async function initMap() {
  // setup a marker group
  leafletMarkers = L.featureGroup();

    const southWest = L.latLng(-90, -180),
      northEast = L.latLng(90, 180);
    const bounds = L.latLngBounds(southWest, northEast);

    coverageMap = L.map(mapContainer.value!, {
      scrollWheelZoom: true,
      zoomControl: false,
      maxBounds: bounds,
      maxBoundsViscosity: 1.0,
    });

    // leaflet.fullscreen@5 dropped the auto-register `fullscreenControl: true`
    // map option, so add the control manually.
    new FullScreen({
      position: "bottomright",
      content: `<i class="fa-solid fa-expand" aria-hidden="true"></i>`,
      forceSeparateButton: true,
    }).addTo(coverageMap);

    const streets = L.tileLayer(
      "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
      {
        attribution:
          'Map data &copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors',
        maxZoom: coverageMapBoxMaxZoom,
      },
    );

    const googleSat = L.tileLayer(
      "https://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
      {
        maxZoom: coverageMapBoxMaxZoom,
        subdomains: ["mt0", "mt1", "mt2", "mt3"],
      },
    );
    coverageMap.attributionControl.setPrefix(
      '<a href="https://leafletjs.com/" target="blank">Leaflet</a>',
    );

    const baseMaps = {
      Streets: streets,
      // Terrain: terrain,
      Satelite: googleSat,
    };

    const overlayMaps = {
      "Spatial Extent": leafletMarkers,
    };

    L.control
      .zoom({
        position: "bottomright",
      })
      .addTo(coverageMap);

    const layerControl = L.control.layers(baseMaps, overlayMaps, {
      position: "topright",
    });
    layerControl.addTo(coverageMap);

    L.Control.RecenterButton = L.Control.extend({
      onAdd: (_map: L.Map) => {
        let recenterButton = L.DomUtil.create(
          "div",
          "leaflet-bar leaflet-control",
        );
        recenterButton.setAttribute("data-toggle", "tooltip");
        recenterButton.setAttribute("data-placement", "right");
        recenterButton.setAttribute("title", "Recenter");

        recenterButton.innerHTML = `<a role="button"><i class="fa-regular fa-circle-dot" style="padding-top:3px"></i></a>`;

        L.DomEvent.on(recenterButton, "click", (e) => {
          e.stopPropagation();
          try {
            coverageMap.fitBounds(leafletMarkers.getBounds(), {
              maxZoom:
                props.feature?.["@type"] === "GeoCoordinates"
                  ? coverageMapPointMaxZoom
                  : coverageMapBoxMaxZoom,
            });
          } catch (error) {
            coverageMap.setView([30, 0], 1);
          }
        });

        return recenterButton;
      },
    });

    L.control.watermark = (opts) => {
      return new L.Control.RecenterButton(opts);
    };

    L.control
      .watermark({
        position: "bottomright",
      })
      .addTo(coverageMap);

    // show the default layers at start
    coverageMap.addLayer(streets);
    coverageMap.addLayer(leafletMarkers);
  }

function drawInitialShape() {
  // Center the map
  leafletMarkers.clearLayers();
    if (props.feature?.["@type"] === "GeoCoordinates") {
      const point = new L.LatLng(props.feature.latitude, props.feature.longitude);
      drawMarker(L.latLng(point));
    } else if (props.feature?.["@type"] === "GeoShape") {
      const extents = props.feature.box
        .trim()
        .split(" ")
        .map((n: string) => +n);

      if (extents.length === 4) {
        const rectangle = {
          north: extents[0],
          east: extents[1],
          south: extents[2],
          west: extents[3],
        };
        drawRectangle(rectangle);
      }
    }
  }

function drawRectangle(bounds: any) {
  leafletMarkers.clearLayers();
    let rectangle = L.rectangle([
      [bounds.north, bounds.east],
      [bounds.south, bounds.west],
    ]);
    leafletMarkers.addLayer(rectangle);

    coverageMap.fitBounds(rectangle.getBounds(), {
      maxZoom: coverageMapBoxMaxZoom,
    });
  }

function drawMarker(latLng: L.LatLng) {
  leafletMarkers.clearLayers();
    let marker = L.marker(latLng);
    leafletMarkers.addLayer(marker);

    // Center map at new marker
    coverageMap.fitBounds(leafletMarkers.getBounds(), {
      maxZoom: coverageMapPointMaxZoom,
    });
}
</script>

<style lang="scss" scoped>
.map-container {
  width: 100%;
  min-height: 15rem;
}

.cd-spatial-coverage-map {
  padding: 2px;
}
</style>
