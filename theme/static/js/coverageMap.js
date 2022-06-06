/**
 * Created by Mauriel on 2/9/2016.
 */
// Map js
var coverageMap;
var leafletMarkers;
var allOverlays = [];
// TODO: coordinates-picker.js and allShapes push
var allShapes = []; // Keeps track of shapes added by text change events
var drawingManager;

$(document).ready(function () {
    // Draw marker on text change
    $("#id_east").bind('input', drawMarkerOnTextChange);
    $("#id_north").bind('input', drawMarkerOnTextChange);

    // Draw rectangle on text change
    $("#id_northlimit").bind('input', drawRectangleOnTextChange);
    $("#id_eastlimit").bind('input', drawRectangleOnTextChange);
    $("#id_southlimit").bind('input', drawRectangleOnTextChange);
    $("#id_westlimit").bind('input', drawRectangleOnTextChange);

    var $radioPoint = $('input[type="radio"][value="point"]'); // id_type_2
    var $radioBox = $('input[type="radio"][value="box"]'); // id_type_1
    // Set initial coverage fields state
    if ($radioBox.is(':checked')) { //box type coverage
        $("#div_id_north").hide();
        $("#div_id_east").hide();
        $("#div_id_elevation").hide();
    }
    if ($radioPoint.is(':checked')) { // point type coverage
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
});

function drawInitialShape() {
    // This field is populated if the page is in view mode
    var shapeType = $("#coverageMap")[0].getAttribute("data-shape-type");

    var resourceType = $("#resource-type").val();
    // Center the map
    if (shapeType || resourceType === "Time Series") {
        leafletMarkers.clearLayers();
        if (shapeType == "point" || (resourceType === "Time Series" && spatial_coverage_type == "point")) {
            var myLatLng;
            if (shapeType == "point") {
                // resource view mode
                myLatLng = {
                    lat: parseFloat($("#cov_north").text()),
                    lng: parseFloat($("#cov_east").text())
                };
            }
            else {
                // time series resource in edit mode
                myLatLng = {
                    lat: parseFloat($("#id_north").val()),
                    lng: parseFloat($("#id_east").val())
                };
                if ($('#id_north').val()) {
                    $("#id_name").prop('readonly', false);
                }
            }

            if (!myLatLng.lat || !myLatLng.lng) {
                return;
            }
            drawMarker(L.latLng(myLatLng.lat, myLatLng.lng));
        }
        else if (shapeType == "box" || (resourceType === "Time Series" && spatial_coverage_type == "box")) {
            var bounds;
            if (shapeType == "box") {
                //resource view mode
                bounds = {
                    north: parseFloat($("#cov_northlimit").text()),
                    south: parseFloat($("#cov_southlimit").text()),
                    east: parseFloat($("#cov_eastlimit").text()),
                    west: parseFloat($("#cov_westlimit").text())
                };
            }
            else {
                // time series resource edit mode
                bounds = {
                    north: parseFloat($("#id_northlimit").val()),
                    south: parseFloat($("#id_southlimit").val()),
                    east: parseFloat($("#id_eastlimit").val()),
                    west: parseFloat($("#id_westlimit").val())
                };
                if ($('#id_northlimit').val()) {
                    $("#id_name").prop('readonly', false);
                }
            }

            if (bounds.north === null || bounds.south === null || bounds.east === null || bounds.west === null) {
                return;
            }
            // Define the rectangle and set its editable property to true.
            drawRectangle(bounds);
        }
    }
    else {
        var $radioBox = $('input[type="radio"][value="box"]'); // id_type_1
        if ($radioBox.is(":checked")) {
            drawRectangleOnTextChange();
        }
        else {
            drawMarkerOnTextChange();
        }
    }
    $("#id-coverage-spatial input:radio").change(function () {
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
        }
        else {
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
    if (sessionStorage.signininfo) {
        $("#sign-in-info").text(sessionStorage.signininfo);
        $("#btn-select-irods-file").show();
    }
}

function initMap() {
    if (coverageMap != undefined) { coverageMap.remove(); }

    // setup a marker group
    leafletMarkers = L.featureGroup();
    coverageMap = L.map('coverageMap', {scrollWheelZoom: false}).setView([41.850033, -87.6500523], 3);

    // https://leaflet.github.io/Leaflet.draw/docs/leaflet-draw-latest.html#l-draw
    
    let terrain = L.tileLayer('https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.jpg', {
        attribution: 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://www.openstreetmap.org/copyright">ODbL</a>.',
        maxZoom: 18,
    });

    let streets = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 18,
    });

    let toner = L.tileLayer('https://stamen-tiles.a.ssl.fastly.net/toner/{z}/{x}/{y}.png', {
        attribution: 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://www.openstreetmap.org/copyright">ODbL</a>.',
        maxZoom: 18,
    });

    var baseMaps = {
        "Terrain": terrain,
        "Streets": streets,
        "Toner": toner
      };

      var overlayMaps = {
        "Spatial Extent": leafletMarkers,
      };

      let layerControl = L.control.layers(baseMaps, overlayMaps);
      layerControl.addTo(coverageMap);

      var drawControl = new L.Control.Draw({
        draw: {
            featureGroup: leafletMarkers,
            polygon: false,
            circle: false,
            circlemarker: false,
            polyline: false
        },
        edit: {
            featureGroup: leafletMarkers,
            remove: false
        }
      });
      if(RESOURCE_MODE === 'Edit'){
        coverageMap.addControl(drawControl);
      }
        coverageMap.on(L.Draw.Event.CREATED, function (e) {
            let coordinates;
            var type = e.layerType,
                layer = e.layer;
            leafletMarkers.addLayer(layer);

            if(type === 'rectangle'){
                coordinates = layer.getBounds();
            }else{
                coordinates = layer.getLatLng();
            }
            processDrawing(coordinates, type);
        });

        coverageMap.on(L.Draw.Event.DRAWSTART, function (e) {
            leafletMarkers.clearLayers();
        });

        coverageMap.on(L.Draw.Event.EDITED, function (e) {
            var layers = e.layers;
            layers.eachLayer(function (layer) {
                let coordinates;
                let type = "rectangle";
                if (layer instanceof L.Marker){
                    coordinates = layer.getLatLng();
                    type = "marker";
                }else{
                    coordinates = layer.getBounds();
                }
                processDrawing(coordinates, type);
            });
            $("#coverage-spatial").find(".btn-primary").not('#btn-update-resource-spatial-coverage').trigger('click');
        });

      L.control.fullscreen({
        position: 'topright',
        title: 'Toggle fullscreen view',
        titleCancel: 'Exit Fullscreen',
        content: `<i class="fa-expand"></i>`
      }).addTo(coverageMap);

      // show the default layers at start
      coverageMap.addLayer(terrain);
      coverageMap.addLayer(leafletMarkers);
      drawInitialShape();
}

function drawMarkerOnTextChange(){
    var latlng = L.latLng(parseFloat($("#id_north").val()), parseFloat($("#id_east").val()));
    var myLatLng = {lat: parseFloat($("#id_north").val()), lng: parseFloat($("#id_east").val())};
    // Delete previous drawings
    leafletMarkers.clearLayers();
    // deleteAllOverlays();

    // Bounds validation
    var badInput = false;
    // Lat
    if (myLatLng.lat > 90 || myLatLng.lat < -90) {
        $("#id_north").addClass("invalid-input");
        badInput = true;
    }
    else {
        $("#id_north").removeClass("invalid-input");
    }
    if (myLatLng.lng > 180 || myLatLng.lng < -180) {
        $("#id_east").addClass("invalid-input");
        badInput = true;
    }
    else {
        $("#id_east").removeClass("invalid-input");
    }
    if (badInput || isNaN(myLatLng.lat) || isNaN(myLatLng.lng)) {
        return;
    }
    // Define the marker.
    drawMarker(latlng);

    // Set onClick event for recenter button
    // $("#coverageMap").on("click", "#resetZoomBtn", function () {
    //     coverageMap.setCenter(marker.getPosition());
    // });
    // allShapes.push(marker);
}

function drawMarker(latLng){
    let marker = L.marker(latLng);
    leafletMarkers.addLayer(marker);
    
    marker.addTo(coverageMap)
        // .bindPopup('TODO: add res link and lat/long');
        // .openPopup();

    // Center map at new marker
    coverageMap.setView(latLng, 3);
}

function drawRectangleOnTextChange(){
    var bounds = {
        north: parseFloat($("#id_northlimit").val()),
        south: parseFloat($("#id_southlimit").val()),
        east: parseFloat($("#id_eastlimit").val()),
        west: parseFloat($("#id_westlimit").val())
    };
    // Delete previous drawings
    leafletMarkers.clearLayers();
    // deleteAllOverlays();
    // Bounds validation
    var badInput = false;
    // North
    if (bounds.north > 90 || bounds.north < -90) {
        $("#id_northlimit").addClass("invalid-input");
        badInput = true;
    }
    else {
        $("#id_northlimit").removeClass("invalid-input");
    }
    // East
    if (bounds.east > 180 || bounds.east < -180) {
        badInput = true;
        $("#id_eastlimit").addClass("invalid-input");
    }
    else {
        $("#id_eastlimit").removeClass("invalid-input");
    }
    // South
    if (bounds.south < -90 || bounds.south > 90) {
        badInput = true;
        $("#id_southlimit").addClass("invalid-input");
    }
    else {
        $("#id_southlimit").removeClass("invalid-input");
    }
    // West
    if (bounds.west < -180 || bounds.west > 180) {
        badInput = true;
        $("#id_westlimit").addClass("invalid-input");
    }
    else {
        $("#id_westlimit").removeClass("invalid-input");
    }
    if (badInput || isNaN(bounds.north) || isNaN(bounds.south) || isNaN(bounds.east) || isNaN(bounds.west)) {
        return;
    }

    // Define the rectangle and set its editable property to true.
    drawRectangle(bounds);
    // var rectangle = new google.maps.Rectangle({
    //     bounds: bounds,
    //     editable: true,
    //     draggable: true
    // });
    // rectangle.setMap(coverageMap);

    // TODO: add an event listener that triggers processing!!!
    // rectangle.addListener('bounds_changed', function () {
    //     var coordinates = (rectangle.getBounds());
    //     processDrawing(coordinates, "rectangle");
    // });

    // zoomCoverageMap(bounds);
    // $("#coverageMap").on("click", "#resetZoomBtn", function () {
    //     zoomCoverageMap(bounds);
    // });
    // allShapes.push(rectangle);
}
function drawRectangle(bounds){
    var rectangle = L.rectangle([[bounds.north, bounds.east], [bounds.south, bounds.west]]);
    leafletMarkers.addLayer(rectangle);

    rectangle.addTo(coverageMap)
        .bindPopup('TODO: add res link and lat/long');
    
    coverageMap.fitBounds(rectangle.getBounds());
}

function processDrawing(coordinates, shape){
    // // Delete previous drawings
    // if (allOverlays.length > 1){
    //     for (var i = 1; i < allOverlays.length; i++){
    //         allOverlays[i-1].overlay.setMap(null);
    //     }
    //     allOverlays.shift();
    // }
    // if (allOverlays.length > 0) {
    //     deleteAllShapes();
    // }
    // Show save changes button
    $("#coverage-spatial").find(".btn-primary").not('#btn-update-resource-spatial-coverage').show();
    if (shape === "rectangle"){
        var $radioBox = $('input[type="radio"][value="box"]'); // id_type_1
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
        var bounds = {
            north: parseFloat(coordinates.getNorthEast().lat),
            south: parseFloat(coordinates.getSouthWest().lat),
            east: parseFloat(coordinates.getNorthEast().lng),
            west: parseFloat(coordinates.getSouthWest().lng)
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
        $("#coverageMap").on("click", "#resetZoomBtn", function () {
            // zoomCoverageMap(bounds);
        });
    }
    else {
        var $radioPoint = $('input[type="radio"][value="point"]'); // id_type_2
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
        // $("#coverageMap").on("click", "#resetZoomBtn", function () {
        //     coverageMap.setCenter(coordinates);
        // });
    }
}