/**
 * Created by Mauriel on 2/9/2016.
 * Updated by Devin on 10/14/2022.
 */
// Map js
let coverageMap;
let leafletMarkers;
let allOverlays = [];
const coverageMapBoxMaxZoom = 18;
const coverageMapPointMaxZoom = 7;

$(document).ready(function () {
  // Draw marker on text change
  $("#id_east").bind("input", drawMarkerOnTextChange);
  $("#id_north").bind("input", drawMarkerOnTextChange);

  // Draw rectangle on text change
  $("#id_northlimit").bind("input", drawRectangleOnTextChange);
  $("#id_eastlimit").bind("input", drawRectangleOnTextChange);
  $("#id_southlimit").bind("input", drawRectangleOnTextChange);
  $("#id_westlimit").bind("input", drawRectangleOnTextChange);

  const $radioPoint = $('input[type="radio"][value="point"]'); // id_type_2
  const $radioBox = $('input[type="radio"][value="box"]'); // id_type_1
  // Set initial coverage fields state
  if ($radioBox.is(":checked")) {
    //box type coverage
    $("#div_id_north").hide();
    $("#div_id_east").hide();
    $("#div_id_elevation").hide();
  }
  if ($radioPoint.is(":checked")) {
    // point type coverage
    $("#div_id_northlimit").hide();
    $("#div_id_eastlimit").hide();
    $("#div_id_southlimit").hide();
    $("#div_id_westlimit").hide();
    $("#div_id_uplimit").hide();
    $("#div_id_downlimit").hide();
  }

  if ($("#coverageMap").length) {
    initMap();
  }
  $("#div_id_type input:radio").change(function () {
    leafletMarkers.clearLayers();
    if ($(this).val() == "point") {
      $("#div_id_north").show();
      $("#div_id_east").show();
      $("#div_id_elevation").show();
      $("#div_id_northlimit").hide();
      $("#div_id_eastlimit").hide();
      $("#div_id_southlimit").hide();
      $("#div_id_westlimit").hide();
      $("#div_id_uplimit").hide();
      $("#div_id_downlimit").hide();
      drawMarkerOnTextChange();
    } else {
      $("#div_id_north").hide();
      $("#div_id_east").hide();
      $("#div_id_elevation").hide();
      $("#div_id_northlimit").show();
      $("#div_id_eastlimit").show();
      $("#div_id_southlimit").show();
      $("#div_id_westlimit").show();
      $("#div_id_uplimit").show();
      $("#div_id_downlimit").show();
      drawRectangleOnTextChange();
    }
    // Show save changes button
    $("#coverage-spatial").find(".btn-primary").show();
  });
});

async function drawInitialShape() {
  // This field is populated if the page is in view mode
  const shapeType = $("#coverageMap")[0].getAttribute("data-shape-type");
  const resourceType = $("#resource-type").val();
  // Center the map
  if (shapeType || resourceType === "Time Series") {
    leafletMarkers.clearLayers();
    if (
      shapeType == "point" ||
      (resourceType === "Time Series" && spatial_coverage_type == "point")
    ) {
      let myLatLng;
      if (shapeType == "point") {
        // resource view mode
        myLatLng = {
          lat: parseFloat($("#cov_north").text()),
          lng: parseFloat($("#cov_east").text()),
        };
      } else {
        // time series resource in edit mode
        myLatLng = {
          lat: parseFloat($("#id_north").val()),
          lng: parseFloat($("#id_east").val()),
        };
        if ($("#id_north").val()) {
          $("#id_name").prop("readonly", false);
        }
      }

      if (!myLatLng.lat || !myLatLng.lng) {
        return;
      }
      drawMarker(L.latLng(myLatLng.lat, myLatLng.lng));
    } else if (
      shapeType == "box" ||
      (resourceType === "Time Series" && spatial_coverage_type == "box")
    ) {
      let bounds;
      if (shapeType == "box") {
        //resource view mode
        bounds = {
          north: parseFloat($("#cov_northlimit").text()),
          south: parseFloat($("#cov_southlimit").text()),
          east: parseFloat($("#cov_eastlimit").text()),
          west: parseFloat($("#cov_westlimit").text()),
        };
      } else {
        // time series resource edit mode
        bounds = {
          north: parseFloat($("#id_northlimit").val()),
          south: parseFloat($("#id_southlimit").val()),
          east: parseFloat($("#id_eastlimit").val()),
          west: parseFloat($("#id_westlimit").val()),
        };
        if ($("#id_northlimit").val()) {
          $("#id_name").prop("readonly", false);
        }
      }

      if (
        bounds.north === null ||
        bounds.south === null ||
        bounds.east === null ||
        bounds.west === null
      ) {
        return;
      }
      // Define the rectangle and set its editable property to true.
      drawRectangle(bounds);
    }
  } else {
    let $radioBox = $('input[type="radio"][value="box"]'); // id_type_1
    if ($radioBox.is(":checked")) {
      drawRectangleOnTextChange();
    } else {
      drawMarkerOnTextChange();
    }
  }

  coverageMap.initialShapesDrawn = true;
}

function initMap() {
  if (coverageMap != undefined) {
    coverageMap.remove();
  }

  // setup a marker group
  leafletMarkers = L.featureGroup();

  const southWest = L.latLng(-90, -180),
    northEast = L.latLng(90, 180);
  const bounds = L.latLngBounds(southWest, northEast);

  coverageMap = L.map("coverageMap", {
    scrollWheelZoom: false,
    zoomControl: false,
    maxBounds: bounds,
    maxBoundsViscosity: 1.0,
  });
  // USA
  // coverageMap.setView([41.850033, -87.6500523], 3);
  coverageMap.setView([30, 0], 1);

  // https://leaflet.github.io/Leaflet.draw/docs/leaflet-draw-latest.html#l-draw

  const terrain = L.tileLayer(
    "https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.jpg",
    {
      attribution:
        'Map tiles by <a href="http://stamen.com" target="_blank">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0" target="_blank">CC BY 3.0</a>. Data by <a href="http://openstreetmap.org" target="_blank">OpenStreetMap</a>, under <a href="http://www.openstreetmap.org/copyright" target="_blank">ODbL</a>.',
      maxZoom: coverageMapBoxMaxZoom,
    }
  );

  const streets = L.tileLayer(
    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
      attribution:
        'Map data &copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors',
      maxZoom: coverageMapBoxMaxZoom,
    }
  );

  const googleSat = L.tileLayer(
    "http://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
    {
      maxZoom: coverageMapBoxMaxZoom,
      subdomains: ["mt0", "mt1", "mt2", "mt3"],
    }
  );
  coverageMap.attributionControl.setPrefix('<a href="https://leafletjs.com/" target="blank">Leaflet</a>');


  const baseMaps = {
    Streets: streets,
    Terrain: terrain,
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

  const coverageDrawControl = new L.Control.Draw({
    draw: {
      featureGroup: leafletMarkers,
      polygon: false,
      circle: false,
      circlemarker: false,
      polyline: false,
    },
    edit: {
      featureGroup: leafletMarkers,
      remove: false,
    },
  });

  L.drawLocal.edit.toolbar.buttons.edit = "Edit drawn coverage";
  L.drawLocal.draw.toolbar.buttons.rectangle = "Add box coverage";
  L.drawLocal.draw.toolbar.buttons.marker = "Add point coverage";

  L.drawLocal.edit.toolbar.actions.save.text = "Finish";
  L.drawLocal.edit.toolbar.actions.save.title = "Complete edit";
  if (RESOURCE_MODE === "Edit") {
    coverageMap.addControl(coverageDrawControl);
  }
  coverageMap.on(L.Draw.Event.EDITSTART, function (e) {
    $("#spatial-coverage-save").hide();
  });

  coverageMap.on(L.Draw.Event.CREATED, function (e) {
    let coordinates;
    let type = e.layerType,
      layer = e.layer;
    leafletMarkers.clearLayers();
    leafletMarkers.addLayer(layer);

    if (type === "rectangle") {
      coordinates = layer.getBounds();
    } else {
      coordinates = layer.getLatLng();
    }
    $("#spatial-coverage-save").show();
    processDrawing(coordinates, type);
  });

  coverageMap.on(L.Draw.Event.DRAWSTART, function (e) {
    leafletMarkers.clearLayers();
  });

  coverageMap.on(L.Draw.Event.EDITED, function (e) {
    let layers = e.layers;
    layers.eachLayer(function (layer) {
      let coordinates;
      let type = "rectangle";
      if (layer instanceof L.Marker) {
        coordinates = layer.getLatLng();
        type = "marker";
      } else {
        coordinates = layer.getBounds();
      }
      processDrawing(coordinates, type);
    });
    $("#spatial-coverage-save").show();
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
    .addTo(coverageMap);

  L.Control.RecenterButton = L.Control.extend({
    onAdd: function (map) {
      let recenterButton = L.DomUtil.create(
        "div",
        "leaflet-bar leaflet-control"
      );
      recenterButton.setAttribute("data-toggle", "tooltip");
      recenterButton.setAttribute("data-placement", "right");
      recenterButton.setAttribute("title", "Recenter");

      recenterButton.innerHTML = `<a role="button"><i class="fa fa-dot-circle-o fa-2x" style="padding-top:3px"></i></a>`;

      L.DomEvent.on(recenterButton, "click", (e) => {
        e.stopPropagation();
        try {
          const checked = $("#div_id_type input:checked").val();
          const spatialType = checked || spatial_coverage_type;
          coverageMap.fitBounds(leafletMarkers.getBounds(), {
            maxZoom:
              spatialType === "point"
                ? coverageMapPointMaxZoom
                : coverageMapBoxMaxZoom,
          });
        } catch (error) {
          coverageMap.setView([30, 0], 1);
        }
      });

      return recenterButton;
    },

    onRemove: function (map) {
      //   L.DomEvent.off();
    },
  });

  L.control.watermark = function (opts) {
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
  drawInitialShape();
}

function drawMarkerOnTextChange() {
  $("#coverageMap .leaflet-draw-draw-marker").show();
  $("#coverageMap .leaflet-draw-draw-rectangle").hide();
  let north = parseFloat($("#id_north").val());
  let east = parseFloat($("#id_east").val());
  let myLatLng = { lat: north, lng: east };

  // Bounds validation
  let badInput = false;

  if (isNaN(north) || isNaN(east)) {
    return;
  }
  if (myLatLng.lat > 90 || myLatLng.lat < -90) {
    $("#id_north").addClass("invalid-input");
    badInput = true;
  } else {
    $("#id_north").removeClass("invalid-input");
  }
  if (myLatLng.lng > 180 || myLatLng.lng < -180) {
    $("#id_east").addClass("invalid-input");
    badInput = true;
  } else {
    $("#id_east").removeClass("invalid-input");
  }
  if (badInput) {
    return;
  }
  let latlng = L.latLng(north, east);
  // Define the marker.
  drawMarker(latlng);
}

function drawMarker(latLng) {
  leafletMarkers.clearLayers();
  let marker = L.marker(latLng);
  leafletMarkers.addLayer(marker);

  // Center map at new marker
  coverageMap.fitBounds(leafletMarkers.getBounds(), { maxZoom: coverageMapPointMaxZoom });
}

function drawRectangleOnTextChange() {
  $("#coverageMap .leaflet-draw-draw-marker").hide();
  $("#coverageMap .leaflet-draw-draw-rectangle").show();
  let bounds = {
    north: parseFloat($("#id_northlimit").val()),
    south: parseFloat($("#id_southlimit").val()),
    east: parseFloat($("#id_eastlimit").val()),
    west: parseFloat($("#id_westlimit").val()),
  };
  // Bounds validation
  let badInput = false;
  // North
  if (bounds.north > 90 || bounds.north < -90) {
    $("#id_northlimit").addClass("invalid-input");
    badInput = true;
  } else {
    $("#id_northlimit").removeClass("invalid-input");
  }
  // East
  if (bounds.east > 180 || bounds.east < -180) {
    badInput = true;
    $("#id_eastlimit").addClass("invalid-input");
  } else {
    $("#id_eastlimit").removeClass("invalid-input");
  }
  // South
  if (bounds.south < -90 || bounds.south > 90) {
    badInput = true;
    $("#id_southlimit").addClass("invalid-input");
  } else {
    $("#id_southlimit").removeClass("invalid-input");
  }
  // West
  if (bounds.west < -180 || bounds.west > 180) {
    badInput = true;
    $("#id_westlimit").addClass("invalid-input");
  } else {
    $("#id_westlimit").removeClass("invalid-input");
  }
  if (
    badInput ||
    isNaN(bounds.north) ||
    isNaN(bounds.south) ||
    isNaN(bounds.east) ||
    isNaN(bounds.west)
  ) {
    return;
  }

  // Define the rectangle and set its editable property to true.
  drawRectangle(bounds);
}
function drawRectangle(bounds) {
  leafletMarkers.clearLayers();
  let rectangle = L.rectangle([
    [bounds.north, bounds.east],
    [bounds.south, bounds.west],
  ]);
  leafletMarkers.addLayer(rectangle);

  coverageMap.fitBounds(rectangle.getBounds(), { maxZoom: coverageMapBoxMaxZoom });
}

function processDrawing(coordinates, shape) {
  // Show save changes button
  $("#coverage-spatial")
    .find(".btn-primary")
    .not("#btn-update-resource-spatial-coverage")
    .show();

  if (shape === "rectangle") {
    let $radioBox = $('input[type="radio"][value="box"]'); // id_type_1
    $radioBox.prop("checked", true);
    $("#div_id_north").hide();
    $("#div_id_east").hide();
    $("#div_id_elevation").hide();
    $("#div_id_northlimit").show();
    $("#div_id_eastlimit").show();
    $("#div_id_southlimit").show();
    $("#div_id_westlimit").show();
    $("#div_id_uplimit").show();
    $("#div_id_downlimit").show();
    let bounds = {
      north: parseFloat(coordinates.getNorthEast().lat),
      south: parseFloat(coordinates.getSouthWest().lat),
      east: parseFloat(coordinates.getNorthEast().lng),
      west: parseFloat(coordinates.getSouthWest().lng),
    };
    // Update fields
    $("#id_northlimit").val(bounds.north.toFixed(4));
    $("#id_eastlimit").val(bounds.east.toFixed(4));
    $("#id_southlimit").val(bounds.south.toFixed(4));
    $("#id_westlimit").val(bounds.west.toFixed(4));
    // Remove red borders
    $("#id_northlimit").removeClass("invalid-input");
    $("#id_eastlimit").removeClass("invalid-input");
    $("#id_southlimit").removeClass("invalid-input");
    $("#id_westlimit").removeClass("invalid-input");
  } else {
    let $radioPoint = $('input[type="radio"][value="point"]'); // id_type_2
    $radioPoint.prop("checked", true);
    $("#div_id_north").show();
    $("#div_id_east").show();
    $("#div_id_elevation").show();
    $("#div_id_northlimit").hide();
    $("#div_id_eastlimit").hide();
    $("#div_id_southlimit").hide();
    $("#div_id_westlimit").hide();
    $("#div_id_uplimit").hide();
    $("#div_id_downlimit").hide();
    $("#id_east").val(coordinates.lng.toFixed(4));
    $("#id_north").val(coordinates.lat.toFixed(4));
    // Remove red borders
    $("#id_east").removeClass("invalid-input");
    $("#id_north").removeClass("invalid-input");
  }
}
