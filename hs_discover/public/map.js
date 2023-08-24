((exports) => {
  const mapDefaultZoom = 16;
  const mapCenter = { lat: 42, lng: -71 };
  const spiderified_marker_url =
    "https://maps.google.com/mapfiles/ms/icons/red.png";
  // eslint-disable-next-line no-unused-vars
  let googMarkers = [];
  let markerCluster;
  let oms;

  const deleteMarkers = () => {
    if (oms) {
      oms.removeAllMarkers();
    }
    googMarkers.forEach((marker) => {
      marker.setMap(null);
    });
    googMarkers = [];
    if (markerCluster) {
      markerCluster.clearMarkers();
    }
  };

  const recenterMap = () => {
    exports.map.panTo(mapCenter);
  };

  // create an svg literal matching the markerclusterer svg
  // https://github.com/googlemaps/js-markerclusterer/blob/v2.3.1/src/renderer.ts#L117
  const get_svg = function (count = 2, color = "#0000ff") {
    const svg = `<svg fill="${color}" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" width="50" height="50">
    <circle cx="120" cy="120" opacity=".6" r="70" />
    <circle cx="120" cy="120" opacity=".3" r="90" />
    <circle cx="120" cy="120" opacity=".2" r="110" />
    <text x="50%" y="50%" style="fill:#fff" text-anchor="middle" font-size="50" dominant-baseline="middle" font-family="roboto,arial,sans-serif">${count}</text>
    </svg>`;
    return `data:image/svg+xml;base64,${btoa(svg)}`;
  };

  const generate_cluster_icon = function (marker) {
    const near = oms.markersNearMarker(marker, (firstOnly = false)).length;
    if (near > 0) {
      return get_svg((count = near + 1));
    } else {
      return spiderified_marker_url;
    }
  };

  const createBatchMarkers = (locations, hsUid, labels) => {
    document.body.style.cursor = "wait";
    const minClusterZoom = exports.map.maxZoom;

    // https://github.com/jawj/OverlappingMarkerSpiderfier
    // minZoomLevel and nearbyDistance must be "tuned" to find a good match for the maxZoom of the map
    oms = new OverlappingMarkerSpiderfier(exports.map, {
      markersWontMove: true,
      markersWontHide: true,
      basicFormatEvents: true,
      minZoomLevel: minClusterZoom,
      keepSpiderfied: true,
      circleSpiralSwitchover: 9,
      spiralFootSeparation: 40,
      circleFootSeparation: 40,
      nearbyDistance: .01,
    });
    const infoWindows = [];

    googMarkers = locations.map((location, k) => {
      const marker = new google.maps.Marker({ // eslint-disable-line
        map: exports.map,
        position: location,
        hsUid: hsUid[k % hsUid.length],
      });
      const infowindow = new google.maps.InfoWindow({ maxWidth: 400 }); // eslint-disable-line
      infowindow.setContent(`
        <a href="/resource/${hsUid[k % hsUid.length]}" target="_blank">${labels[k % labels.length]}</a>
        <br>lat: ${location.lat.toFixed(2)} lng: ${location.lng.toFixed(2)}
      `);
      infoWindows.push(infowindow);

      google.maps.event.addListener(marker, "spider_click", function (e) {
        closeInfoWindows(infoWindows);
        infowindow.open(exports.map, marker);
      });
      oms.addMarker(marker); // adds the marker to the spiderfier AND the map
      return marker;
    });

    oms.addListener("spiderfy", (spiderified) => {
      spiderified.forEach((marker) => {
        marker.setIcon({
          url: spiderified_marker_url,
        });
      });
      closeInfoWindows(infoWindows);
    });

    oms.addListener("unspiderfy", () => {
      reset_clusters(oms);
      closeInfoWindows(infoWindows);
    });

    const algorithm = new markerClusterer.SuperClusterAlgorithm({
      maxZoom: minClusterZoom - 1,
      zoomOnClick: false,
    });
    markerCluster = new markerClusterer.MarkerClusterer({
      markers: googMarkers,
      map: exports.map,
      algorithm: algorithm,
    });

    google.maps.event.addListenerOnce(markerCluster, "click", function () {
      if (exports.map.getZoom() > minClusterZoom) {
        exports.map.setZoom(minClusterZoom);
      }
    });

    exports.map.addListener("zoom_changed", () => {
      closeInfoWindows(infoWindows);
    });
    exports.map.addListener("dragstart", () => {
      closeInfoWindows(infoWindows);
    });
    document.body.style.cursor = "default";
  };

  const closeInfoWindows = (infoWindows) => {
    infoWindows.forEach(function (win) {
      win.close();
    });
  };
  const reset_clusters = (oms) => {
    oms.markersNearAnyOtherMarker().forEach((spider) => {
      spider.setIcon({
        url: generate_cluster_icon(spider),
      });
    });
  };

  const gotoBounds = () => {
    reset_clusters(oms);
    const bounds = new google.maps.LatLngBounds();
    googMarkers.forEach((marker) => bounds.extend(marker.position));
    exports.map.fitBounds(bounds);
  };

  const toggleMap = () => {
    document.getElementById("map-view").style.display =
      document.getElementById("map-view").style.display === "block"
        ? "none"
        : "block";
  };

  const initMap = () => {
    // eslint-disable-next-line no-param-reassign,no-undef
    exports.map = new google.maps.Map(document.getElementById("map"), {
      center: mapCenter,
      zoom: mapDefaultZoom,
      gestureHandling: "greedy",
      mapTypeId: google.maps.MapTypeId.TERRAIN, // eslint-disable-line
    });

    exports.map.addListener("bounds_changed", () => {
      const visMarkers = [];
      const bounds = exports.map.getBounds();
      googMarkers.forEach((marker) => {
        if (bounds.contains(marker.position)) {
          visMarkers.push(marker.hsUid);
        }
      });
      this.visMarkers = visMarkers; // window
    });
    exports.map.setOptions({ minZoom: 2, maxZoom: mapDefaultZoom });
  };
  exports.initMap = initMap; // eslint-disable-line
  exports.createBatchMarkers = createBatchMarkers; // eslint-disable-line
  exports.toggleMap = toggleMap; // eslint-disable-line
  exports.deleteMarkers = deleteMarkers; // eslint-disable-line
  exports.gotoBounds = gotoBounds; // eslint-disable-line
  exports.recenterMap = recenterMap; //eslint-disable-line
})((this.window = this.window || {}));
