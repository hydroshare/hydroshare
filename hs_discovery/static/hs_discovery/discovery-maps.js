(function () {
  var app = window.HSDiscovery = window.HSDiscovery || {};
  var BOX_MAX_ZOOM = 18;
  var POINT_MAX_ZOOM = 7;
  var mapRegistry = new WeakMap();

  function parseGeoShapeBounds(rawBox) {
    if (!rawBox) {
      return null;
    }
    var extents = rawBox.trim().split(/\s+/).map(function (value) {
      return parseFloat(value);
    });
    if (extents.length !== 4 || extents.some(function (value) { return Number.isNaN(value); })) {
      return null;
    }
    return {
      north: extents[0],
      east: extents[1],
      south: extents[2],
      west: extents[3]
    };
  }

  function fitToSpatialExtent(mapState) {
    if (!mapState || !mapState.markers || !mapState.map || !mapState.markers.getLayers().length) {
      return;
    }
    mapState.map.fitBounds(mapState.markers.getBounds(), {
      maxZoom: mapState.extentType === "GeoCoordinates" ? POINT_MAX_ZOOM : BOX_MAX_ZOOM
    });
  }

  function buildMap(container) {
    if (!window.L) {
      return null;
    }

    var markers = L.featureGroup();
    var worldBounds = L.latLngBounds(L.latLng(-90, -180), L.latLng(90, 180));
    var map = L.map(container, {
      scrollWheelZoom: true,
      zoomControl: false,
      maxBounds: worldBounds,
      maxBoundsViscosity: 1
    });

    var streets = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors',
      maxZoom: BOX_MAX_ZOOM
    });

    var satellite = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", {
      attribution: "Tiles &copy; Esri",
      maxZoom: BOX_MAX_ZOOM
    });

    map.attributionControl.setPrefix('<a href="https://leafletjs.com/" target="_blank">Leaflet</a>');
    L.control.zoom({ position: "bottomright" }).addTo(map);
    L.control.layers({ Streets: streets, Satellite: satellite }, { "Spatial Extent": markers }, { position: "topright" }).addTo(map);

    var RecenterControl = L.Control.extend({
      options: { position: "bottomright" },
      onAdd: function () {
        var wrapper = L.DomUtil.create("div", "leaflet-bar leaflet-control");
        var button = L.DomUtil.create("a", "", wrapper);
        button.href = "#";
        button.title = "Recenter";
        button.setAttribute("role", "button");
        button.innerHTML = "&#9678;";
        L.DomEvent.disableClickPropagation(wrapper);
        L.DomEvent.on(button, "click", function (event) {
          L.DomEvent.preventDefault(event);
          fitToSpatialExtent(mapState);
        });
        return wrapper;
      }
    });

    var mapState = {
      container: container,
      map: map,
      markers: markers,
      extentType: null
    };

    map.addLayer(streets);
    map.addLayer(markers);
    map.addControl(new RecenterControl());

    return mapState;
  }

  function drawSpatialExtent(mapState) {
    if (!mapState) {
      return;
    }
    var container = mapState.container;
    var markers = mapState.markers;
    markers.clearLayers();

    var type = container.dataset.spatialType;
    mapState.extentType = type;
    if (type === "GeoCoordinates") {
      var latitude = parseFloat(container.dataset.latitude || "");
      var longitude = parseFloat(container.dataset.longitude || "");
      if (!Number.isNaN(latitude) && !Number.isNaN(longitude)) {
        markers.addLayer(L.marker([latitude, longitude]));
      }
    } else if (type === "GeoShape") {
      var bounds = parseGeoShapeBounds(container.dataset.box || "");
      if (bounds) {
        markers.addLayer(L.rectangle([
          [bounds.north, bounds.east],
          [bounds.south, bounds.west]
        ]));
      }
    }
  }

  function ensureSpatialMap(container) {
    if (!container || mapRegistry.has(container)) {
      return mapRegistry.get(container) || null;
    }
    var mapState = buildMap(container);
    if (!mapState) {
      return null;
    }
    drawSpatialExtent(mapState);
    mapRegistry.set(container, mapState);
    return mapState;
  }

  function isVisible(element) {
    return !!(element && element.offsetParent !== null && element.clientWidth > 0 && element.clientHeight > 0);
  }

  function refreshMapLayout(mapState) {
    if (!mapState) {
      return;
    }
    mapState.map.invalidateSize({ pan: false });
    if (mapState.markers && mapState.markers.getLayers().length) {
      fitToSpatialExtent(mapState);
      return;
    }
    mapState.map.setView([0, 0], 2, { animate: false });
  }

  app.activateSpatialMaps = function (root) {
    if (!root || !root.querySelectorAll) {
      return;
    }
    var containers = root.querySelectorAll(".discovery-spatial-map");
    containers.forEach(function (container) {
      if (!isVisible(container)) {
        return;
      }
      var mapState = ensureSpatialMap(container);
      if (!mapState) {
        return;
      }

      requestAnimationFrame(function () {
        refreshMapLayout(mapState);
        setTimeout(function () {
          refreshMapLayout(mapState);
        }, 80);
      });
    });
  };
})();
