<template>
  <v-card class="cd-spatial-coverage-map">
    <div ref="map" class="map-container"></div>
  </v-card>
</template>

<script lang="ts">
import { Component, Vue, Prop, Ref, toNative } from "vue-facing-decorator";
import L from "leaflet";
import "leaflet.fullscreen";

const coverageMapBoxMaxZoom = 18;
const coverageMapPointMaxZoom = 7;

@Component({
  name: "cd-spatial-coverage-map",
  components: {},
})
class CdSpatialCoverageMap extends Vue {
  @Prop() feature!: any;
  @Ref("map") mapContainer!: HTMLElement;

  protected coverageMap!: L.Map;
  protected leafletMarkers!: L.FeatureGroup<any>;
  protected allOverlays = [];

  async mounted() {
    await this.initMap();
    this.drawInitialShape();
  }

  protected async initMap() {
    // setup a marker group
    this.leafletMarkers = L.featureGroup();

    const southWest = L.latLng(-90, -180),
      northEast = L.latLng(90, 180);
    const bounds = L.latLngBounds(southWest, northEast);

    this.coverageMap = L.map(this.mapContainer, {
      scrollWheelZoom: true,
      zoomControl: false,
      maxBounds: bounds,
      maxBoundsViscosity: 1.0,
      // @ts-ignore added by 'leaflet.fullscreen'
      fullscreenControl: true,
      fullscreenControlOptions: {
        position: "bottomright",
        content: `<i class="fa-solid fa-expand" aria-hidden="true"></i>`,
      },
    });

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
    this.coverageMap.attributionControl.setPrefix(
      '<a href="https://leafletjs.com/" target="blank">Leaflet</a>',
    );

    const baseMaps = {
      Streets: streets,
      // Terrain: terrain,
      Satelite: googleSat,
    };

    const overlayMaps = {
      "Spatial Extent": this.leafletMarkers,
    };

    L.control
      .zoom({
        position: "bottomright",
      })
      .addTo(this.coverageMap);

    const layerControl = L.control.layers(baseMaps, overlayMaps, {
      position: "topright",
    });
    layerControl.addTo(this.coverageMap);

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
            this.coverageMap.fitBounds(this.leafletMarkers.getBounds(), {
              maxZoom:
                this.feature["type"] === "GeoCoordinates"
                  ? coverageMapPointMaxZoom
                  : coverageMapBoxMaxZoom,
            });
          } catch (error) {
            this.coverageMap.setView([30, 0], 1);
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
      .addTo(this.coverageMap);

    // show the default layers at start
    this.coverageMap.addLayer(streets);
    this.coverageMap.addLayer(this.leafletMarkers);
  }

  drawInitialShape() {
    // Center the map
    this.leafletMarkers.clearLayers();
    if (this.feature["type"] === "GeoCoordinates") {
      const point = new L.LatLng(this.feature.latitude, this.feature.longitude);
      this.drawMarker(L.latLng(point));
    } else if (this.feature["type"] === "GeoShape") {
      const extents = this.feature.box
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
        this.drawRectangle(rectangle);
      }
    }
  }

  drawRectangle(bounds: any) {
    this.leafletMarkers.clearLayers();
    let rectangle = L.rectangle([
      [bounds.north, bounds.east],
      [bounds.south, bounds.west],
    ]);
    this.leafletMarkers.addLayer(rectangle);

    this.coverageMap.fitBounds(rectangle.getBounds(), {
      maxZoom: coverageMapBoxMaxZoom,
    });
  }

  drawMarker(latLng: L.LatLng) {
    this.leafletMarkers.clearLayers();
    let marker = L.marker(latLng);
    this.leafletMarkers.addLayer(marker);

    // Center map at new marker
    this.coverageMap.fitBounds(this.leafletMarkers.getBounds(), {
      maxZoom: coverageMapPointMaxZoom,
    });
  }
}
export default toNative(CdSpatialCoverageMap);
</script>

<style lang="scss" scoped>
.map-container {
  min-width: 25rem;
  min-height: 15rem;
}

.cd-spatial-coverage-map {
  padding: 2px;
}
</style>
