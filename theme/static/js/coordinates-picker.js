/**
 * Created by Mauriel on 3/28/2017.
 * Updated by Devin on 10/14/2022.
 */

var coordinatesPicker;
var currentInstance; // Keeps track of the instance to work with
var allOverlaysFileType = [];
let leafletFeatureGroup;
const coordPickerBoxMaxZoom = 18;
const coordPickerPointMaxZoom = 7;

(function ($) {
  $.fn.coordinatesPicker = function () {
    // If component already initiated, return
    if ($(this).hasClass("has-coordinates-picker")) {
      return this;
    }
    var selectedItem = $("#fb-files-container li.ui-selected");
    var logical_type = selectedItem
      .children("span.fb-logical-file-type")
      .attr("data-logical-file-type");
    initMapFileType();
    var spatial_form = $(this);
    var items = $(this).find("input[data-map-item]");

    items.each(function () {
      var item = $(this);

      // Wrap the element and append a button next to it to trigger the map modal
      // The button adapts to the size of the input (bootstrap classes: input-sm and input-lg)
      if (item.hasClass("input-sm")) {
        item.wrap('<div class="input-group input-group-sm"></div>');
      } else if (item.hasClass("input-lg")) {
        item.wrap('<div class="input-group input-group-lg"></div>');
      } else {
        item.wrap('<div class="input-group"></div>');
      }

      item
        .parent()
        .append(
          '<span class="input-group-btn btn-choose-coordinates" title="Choose coordinates">' +
            '<span class="btn btn-default" type="button">' +
            '<i class="fa fa-map-marker" aria-hidden="true"></i>' +
            "</span>" +
            "</span>"
        );

      item.toggleClass("form-control", true);

      // Reset Leaflet size on modal popup
      $("#coordinates-picker-modal").on("shown.bs.modal", function () {
        coordinatesPicker.invalidateSize();
      });

      // Map trigger event handler
      item
        .parent()
        .find(".btn-choose-coordinates")
        .click(function () {
          currentInstance = item.closest("[data-coordinates-type]");
          var type = currentInstance.attr("data-coordinates-type");

          leafletFeatureGroup.clearLayers();

          // Set the type of controls
          if (type === "point") {
            var lat_field;
            var lon_field;
            if (logical_type === "TimeSeriesLogicalFile") {
              lat_field = spatial_form.find("#id_latitude_filetype");
              lon_field = spatial_form.find("#id_longitude_filetype");
            } else {
              lat_field = spatial_form.find("#id_north_filetype");
              lon_field = spatial_form.find("#id_east_filetype");
            }
            var myLatLng = {
              lat: parseFloat(lat_field.val()),
              lng: parseFloat(lon_field.val()),
            };
            if (myLatLng.lat && myLatLng.lng) {
              drawPickerMarker(L.latLng(myLatLng.lat, myLatLng.lng));
            }
          } else if (type === "rectangle") {
            var bounds = {
              north: parseFloat(
                spatial_form.find("#id_northlimit_filetype").val()
              ),
              south: parseFloat(
                spatial_form.find("#id_southlimit_filetype").val()
              ),
              east: parseFloat(
                spatial_form.find("#id_eastlimit_filetype").val()
              ),
              west: parseFloat(
                spatial_form.find("#id_westlimit_filetype").val()
              ),
            };
            if (bounds.north && bounds.south && bounds.east && bounds.west) {
              drawPickerRectangle(bounds);
            }
          }

          // Set default behavior. It is overridden once coordinates are selected.
          $("#btn-confirm-coordinates").unbind("click");
          $("#btn-confirm-coordinates").click(function () {
            $("#coordinates-picker-modal").modal("hide");
          });

          $("#coordinates-picker-modal").modal("show");
        });
    });

    $(this).addClass("has-coordinates-picker");

    return this;
  };
})(jQuery);

function drawPickerMarker(latLng) {
  const marker = L.marker(latLng);
  leafletFeatureGroup.addLayer(marker);

  marker.addTo(coordinatesPicker);

  // Center map at new marker
  coordinatesPicker.fitBounds(leafletFeatureGroup.getBounds(), { maxZoom: coordPickerPointMaxZoom });
  processDrawingFileType(marker.getLatLng(), "marker");
}

function drawPickerRectangle(bounds) {
  const rectangle = L.rectangle([
    [bounds.north, bounds.east],
    [bounds.south, bounds.west],
  ]);
  leafletFeatureGroup.addLayer(rectangle);

  rectangle.addTo(coordinatesPicker);

  coordinatesPicker.fitBounds(rectangle.getBounds(), { maxZoom: coordPickerBoxMaxZoom });
  processDrawingFileType(rectangle.getBounds(), "rectangle");
}

function initMapFileType() {
  if (coordinatesPicker) return; // already initialized

  // Initialize Map
  leafletFeatureGroup = L.featureGroup();

  const southWest = L.latLng(-90, -180),
    northEast = L.latLng(90, 180);
  const bounds = L.latLngBounds(southWest, northEast);

  coordinatesPicker = L.map("picker-map-container", {
    scrollWheelZoom: false,
    zoomControl: false,
    maxBounds: bounds,
    maxBoundsViscosity: 1.0,
  });
  // USA
  // coordinatesPicker.setView([41.850033, -87.6500523], 3);
  coordinatesPicker.setView([30, 0], 1);

  const terrain = L.tileLayer(
    "https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.jpg",
    {
      attribution:
        'Map tiles by <a href="http://stamen.com" target="_blank">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0" target="_blank">CC BY 3.0</a>. Data by <a href="http://openstreetmap.org" target="_blank">OpenStreetMap</a>, under <a href="http://www.openstreetmap.org/copyright" target="_blank">ODbL</a>.',
      maxZoom: coordPickerBoxMaxZoom,
    }
  );

  const streets = L.tileLayer(
    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
      attribution:
        'Map data &copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors',
      maxZoom: coordPickerBoxMaxZoom,
    }
  );

  const googleSat = L.tileLayer(
    "http://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
    {
      maxZoom: coordPickerBoxMaxZoom,
      subdomains: ["mt0", "mt1", "mt2", "mt3"],
    }
  );

  coordinatesPicker.attributionControl.setPrefix('<a href="https://leafletjs.com/" target="blank">Leaflet</a>');

  const baseMaps = {
    Streets: streets,
    Terrain: terrain,
    Satelite: googleSat,
  };

  const overlayMaps = {
    Extent: leafletFeatureGroup,
  };
  L.control
    .zoom({
      position: "bottomright",
    })
    .addTo(coordinatesPicker);

  const layerControl = L.control.layers(baseMaps, overlayMaps, {
    position: "topright",
  });
  layerControl.addTo(coordinatesPicker);

  const drawControl = new L.Control.Draw({
    draw: {
      featureGroup: leafletFeatureGroup,
      polygon: false,
      circle: false,
      circlemarker: false,
      polyline: false,
    },
    edit: {
      featureGroup: leafletFeatureGroup,
      remove: false,
    },
  });
  if (RESOURCE_MODE === "Edit") {
    coordinatesPicker.addControl(drawControl);
  }
  coordinatesPicker.on(L.Draw.Event.EDITSTART, function (e) {
    $("#btn-confirm-coordinates").hide();
  });
  coordinatesPicker.on(L.Draw.Event.CREATED, function (e) {
    let coordinates;
    const type = e.layerType,
      layer = e.layer;
    leafletFeatureGroup.addLayer(layer);

    if (type === "rectangle") {
      coordinates = layer.getBounds();
    } else {
      coordinates = layer.getLatLng();
    }
    $("#btn-confirm-coordinates").show();
    processDrawingFileType(coordinates, type);
  });

  coordinatesPicker.on(L.Draw.Event.DRAWSTART, function (e) {
    leafletFeatureGroup.clearLayers();
  });

  coordinatesPicker.on(L.Draw.Event.EDITED, function (e) {
    const layers = e.layers;
    layers.eachLayer(function (layer) {
      let coordinates;
      let type = "rectangle";
      if (layer instanceof L.Marker) {
        coordinates = layer.getLatLng();
        type = "marker";
      } else {
        coordinates = layer.getBounds();
      }
      processDrawingFileType(coordinates, type);
    });
    $("#btn-confirm-coordinates").show();
  });

  L.control
    .fullscreen({
      position: "bottomright",
      title: {
        false: "Toggle fullscreen view",
        true: "Exit Fullscreen",
      },
      content: `<i class="fa fa-expand fa-2x" aria-hidden="true"></i>`,
    })
    .addTo(coordinatesPicker);

  // show the default layers at start
  coordinatesPicker.addLayer(streets);
  coordinatesPicker.addLayer(leafletFeatureGroup);

  $(".has-coordinates-picker").each(function () {
    const instance = $(this);
    instance.coordinatesPicker();
  });
}

function processDrawingFileType(coordinates, shape) {
  if (shape === "rectangle") {
    const bounds = {
      north: parseFloat(coordinates.getNorthEast().lat),
      south: parseFloat(coordinates.getSouthWest().lat),
      east: parseFloat(coordinates.getNorthEast().lng),
      west: parseFloat(coordinates.getSouthWest().lng),
    };

    $("#btn-confirm-coordinates").unbind("click");
    $("#btn-confirm-coordinates").click(function () {
      currentInstance
        .find("input[data-map-item='northlimit']")
        .val(bounds.north.toFixed(4));
      currentInstance
        .find("input[data-map-item='eastlimit']")
        .val(bounds.east.toFixed(4));
      currentInstance
        .find("input[data-map-item='southlimit']")
        .val(bounds.south.toFixed(4));
      currentInstance
        .find("input[data-map-item='westlimit']")
        .val(bounds.west.toFixed(4));

      // Issue a text change
      currentInstance
        .find("input[data-map-item='northlimit']")
        .trigger("change");
      currentInstance
        .find("input[data-map-item='eastlimit']")
        .trigger("change");
      currentInstance
        .find("input[data-map-item='southlimit']")
        .trigger("change");
      currentInstance
        .find("input[data-map-item='westlimit']")
        .trigger("change");

      $("#coordinates-picker-modal").modal("hide");

      // Update the coordinate picker radio type
      $("#id_type_filetype input[type='radio'][value='box']").prop(
        "checked",
        true
      );
      $("#id_type_filetype input:radio").trigger("change");
    });
  } else {
    $("#btn-confirm-coordinates").unbind("click");
    $("#btn-confirm-coordinates").click(function () {
      currentInstance
        .find("input[data-map-item='longitude']")
        .val(coordinates.lng.toFixed(4));
      currentInstance
        .find("input[data-map-item='latitude']")
        .val(coordinates.lat.toFixed(4));

      // Issue a text change
      currentInstance
        .find("input[data-map-item='longitude']")
        .trigger("change");
      currentInstance.find("input[data-map-item='latitude']").trigger("change");

      $("#coordinates-picker-modal").modal("hide");

      // Update the coordinate picker radio type
      $("#id_type_filetype input[type='radio'][value='point']").prop(
        "checked",
        true
      );
      $("#id_type_filetype input:radio").trigger("change");
    });
  }
}
