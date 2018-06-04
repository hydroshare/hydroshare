/**
 * Created by Mauriel on 2/9/2016.
 */
// Map js
var coverageMap;
var allOverlays = [];
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


    // Set initial coverage fields state
    if ($("#id_type_1").is(':checked')) { //box type coverage
        $("#div_id_north").hide();
        $("#div_id_east").hide();
        $("#div_id_elevation").hide();
    }
    if ($("#id_type_2").is(':checked')) { // point type coverage
        $("#div_id_northlimit").hide();
        $("#div_id_eastlimit").hide();
        $("#div_id_southlimit").hide();
        $("#div_id_westlimit").hide();
        $("#div_id_uplimit").hide();
        $("#div_id_downlimit").hide();
    }

    if ($("#coverageMap").length) {
        google.maps.event.addDomListener(window, "load", initMap);
    }
});

function drawInitialShape() {
    // This field is populated if the page is in view mode
    var shapeType = $("#coverageMap")[0].getAttribute("data-shape-type");

    var resourceType = $("#resource-type").val();
    var spatialCoverageType = $("#spatial-coverage-type").val();
    // Center the map
    if (shapeType || resourceType === "Time Series") {
        deleteAllShapes();
        if (shapeType == "point" || (resourceType === "Time Series" && spatialCoverageType == "point")) {
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
            // Define the rectangle and set its editable property to true.
            var marker = new google.maps.Marker({
                position: myLatLng,
                map: coverageMap
            });
            allShapes.push(marker);
            // Center map at new market
            coverageMap.setCenter(marker.getPosition());
            $("#resetZoomBtn").click(function () {
                coverageMap.setCenter(marker.getPosition());
            });
        }
        else if (shapeType == "box" || (resourceType === "Time Series" && spatialCoverageType == "box")) {
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

            if (!bounds.north || !bounds.south || !bounds.east || !bounds.west) {
                return;
            }
            // Define the rectangle and set its editable property to true.
            var rectangle = new google.maps.Rectangle({
                bounds: bounds,
                editable: false,
                draggable: false
            });
            rectangle.setMap(coverageMap);
            allShapes.push(rectangle);
            zoomCoverageMap(bounds);
            $("#resetZoomBtn").click(function () {
                zoomCoverageMap(bounds);
            });
        }
    }
    else {
        if ($("#id_type_1").is(":checked")) {
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
            drawingManager.setDrawingMode(google.maps.drawing.OverlayType.MARKER);
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
            drawingManager.setDrawingMode(google.maps.drawing.OverlayType.RECTANGLE);
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
    var shapeType;
    var resourceType;
    if ($("#coverageMap")[0]) {
        // data-shape-type is set to have a value only in resource view mode
        shapeType = $("#coverageMap")[0].getAttribute("data-shape-type");
        resourceType = $("#resource-type").val();
        if (resourceType === "Time Series"){
            // set to view mode
            shapeType = " ";
        }
    }
    coverageMap = new google.maps.Map(document.getElementById('coverageMap'), {
        color:"#DDD",
        zoom: 3,
        streetViewControl: false,
        scrollwheel: false,
        center: {lat: 41.850033, lng: -87.6500523}, // Default center
        mapTypeControl: true,
        mapTypeControlOptions: {
            style: google.maps.MapTypeControlStyle.DROPDOWN_MENU,
            mapTypeIds: [
                google.maps.MapTypeId.ROADMAP,
                google.maps.MapTypeId.SATELLITE
            ],
            position: google.maps.ControlPosition.TOP_RIGHT
        }
    });

    drawInitialShape();
    if (!shapeType) {
        drawingManager = new google.maps.drawing.DrawingManager({
            drawingControl: true,
            drawingControlOptions: {
                position: google.maps.ControlPosition.TOP_CENTER,
                drawingModes: [
                    google.maps.drawing.OverlayType.MARKER,
                    google.maps.drawing.OverlayType.RECTANGLE
                ]
            },
            rectangleOptions: {
                editable: true,
                draggable: true
            }
        });
        drawingManager.setMap(coverageMap);
        google.maps.event.addListener(drawingManager, 'rectanglecomplete', function (rectangle) {
            var coordinates = (rectangle.getBounds());
            processDrawing(coordinates, "rectangle");
            rectangle.addListener('bounds_changed', function () {
                var coordinates = (rectangle.getBounds());
                processDrawing(coordinates, "rectangle");
            });
        });
        google.maps.event.addListener(drawingManager, 'markercomplete', function (marker) {
            var coordinates = (marker.getPosition());
            // Set onClick event for recenter button
            processDrawing(coordinates, "marker");
        });
        google.maps.event.addListener(drawingManager, 'overlaycomplete', function (e) {
            allOverlays.push(e);
        });
    }
}

function drawMarkerOnTextChange(){
    var myLatLng = {lat: parseFloat($("#id_north").val()), lng: parseFloat($("#id_east").val())};
    // Delete previous drawings
    deleteAllShapes();
    deleteAllOverlays();
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
    // Define the rectangle and set its editable property to true.
    var marker = new google.maps.Marker({
        position: myLatLng,
        map: coverageMap
    });
    // Center map at new market
    coverageMap.setCenter(marker.getPosition());
    // Set onClick event for recenter button
    $("#resetZoomBtn").click(function(){
        coverageMap.setCenter(marker.getPosition());
    });
    allShapes.push(marker);
}

function drawRectangleOnTextChange(){
    var bounds = {
        north: parseFloat($("#id_northlimit").val()),
        south: parseFloat($("#id_southlimit").val()),
        east: parseFloat($("#id_eastlimit").val()),
        west: parseFloat($("#id_westlimit").val())
    };
    // Delete previous drawings
    deleteAllShapes();
    deleteAllOverlays();
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
    var rectangle = new google.maps.Rectangle({
        bounds: bounds,
        editable: true,
        draggable: true
    });
    rectangle.setMap(coverageMap);
    rectangle.addListener('bounds_changed', function () {
        var coordinates = (rectangle.getBounds());
        processDrawing(coordinates, "rectangle");
    });
    zoomCoverageMap(bounds);
    $("#resetZoomBtn").click(function(){
        zoomCoverageMap(bounds);
    });
    allShapes.push(rectangle);
}

function processDrawing (coordinates, shape) {
    // Delete previous drawings
    if (allOverlays.length > 1){
        for (var i = 1; i < allOverlays.length; i++){
            allOverlays[i-1].overlay.setMap(null);
        }
        allOverlays.shift();
    }
    if (allOverlays.length > 0) {
        deleteAllShapes();
    }
    // Show save changes button
    $("#coverage-spatial").find(".btn-primary").not('#btn-update-resource-spatial-coverage').show();
    if (shape == "rectangle"){
        document.getElementById("id_type_1").checked = true;
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
            north: parseFloat(coordinates.getNorthEast().lat()),
            south: parseFloat(coordinates.getSouthWest().lat()),
            east: parseFloat(coordinates.getNorthEast().lng()),
            west: parseFloat(coordinates.getSouthWest().lng())
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
        $("#resetZoomBtn").click(function(){
            zoomCoverageMap(bounds);
        });
    }
    else {
        document.getElementById("id_type_2").checked = true;
        $("#div_id_north").show();
        $("#div_id_east").show();
        $("#div_id_elevation").show();
        $("#div_id_northlimit").hide();
        $("#div_id_eastlimit").hide();
        $("#div_id_southlimit").hide();
        $("#div_id_westlimit").hide();
        $("#div_id_uplimit").hide();
        $("#div_id_downlimit").hide();
        $("#id_east").val(coordinates.lng().toFixed(4));
        $("#id_north").val(coordinates.lat().toFixed(4));
        // Remove red borders
        $("#id_east").removeClass("invalid-input");
        $("#id_north").removeClass("invalid-input");
        $("#resetZoomBtn").click(function () {
            coverageMap.setCenter(coordinates);
        });
    }
}

function deleteAllOverlays() {
    for (var i = 0; i < allOverlays.length; i++) {
        allOverlays[i].overlay.setMap(null);
    }
    allOverlays = [];
}

function deleteAllShapes(){
    for (var i = 0; i < allShapes.length; i++) {
        allShapes[i].setMap(null);
    }
    allShapes = [];
}

function zoomCoverageMap(bounds) {
    // Zoom in on the shape
    var GLOBE_WIDTH = 256; // a constant in Google maps projection
    var c_west = bounds.west * 8;    // Zooms out on the shape a little so that we can see it
    var c_east = bounds.east * 8;
    var angle = c_east - c_west;
    var pixelWidth = parseInt($("#coverageMap").width());
    if (angle < 0) {
        angle += 360;
    }
    var zoom = Math.round(Math.log(pixelWidth * 360 / angle / GLOBE_WIDTH) / Math.LN2);
    if (!isNaN(zoom)){
        coverageMap.setZoom(Math.max(3, zoom)); // Allow minumum zoom level of 3
    }
    else{
        return;
    }
    // Center map at new rectangle
    var latCenter = (bounds.north + bounds.south) / 2;
    var lngCenter = (bounds.west + bounds.east) / 2;
    coverageMap.setCenter(new google.maps.LatLng(latCenter, lngCenter));
}