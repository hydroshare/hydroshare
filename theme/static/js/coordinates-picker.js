/**
 * Created by Mauriel on 3/28/2017.
 */

var coordinatesPicker;
var currentInstance;   // Keeps track of the instance to work with
var allOverlaysFileType = [];
var drawingManagerFileType;

(function( $ ){
    $.fn.coordinatesPicker = function () {
        // If component already initiated, return
        if ($(this).hasClass("has-coordinates-picker")) {
            return this;
        }
        var selectedItem = $("#fb-files-container li.ui-selected");
        var logical_type = selectedItem.children('span.fb-logical-file-type').attr("data-logical-file-type");
        initMapFileType();

        var item = $(this);

        // Wrap the element and append a button next to it to trigger the map modal
        // The button adapts to the size of the input (bootstrap classes: input-sm and input-lg)
        if (item.hasClass("input-sm")) {
            item.wrap('<div class="input-group input-group-sm"></div>');
        }
        else if (item.hasClass("input-lg")) {
            item.wrap('<div class="input-group input-group-lg"></div>');
        }
        else {
            item.wrap('<div class="input-group"></div>');
        }

        item.parent().append('<span class="input-group-btn btn-choose-coordinates" title="Choose coordinates">' +
            '<span class="btn btn-default" type="button">' +
            '<i class="fa fa-map-marker" aria-hidden="true"></i>' +
            '</span>' +
            '</span>');

        item.toggleClass("form-control", true);
        // Delete previous drawings
        for (var i = 0; i < allOverlaysFileType.length; i++) {
            allOverlaysFileType[i].overlay.setMap(null);
        }

        allOverlaysFileType = [];

        // Map trigger event handler
        item.parent().find(".btn-choose-coordinates").click(function () {
            var btn_choose_coordinates = $(this);
            currentInstance = item.closest("[data-coordinates-type]");
            var type = currentInstance.attr("data-coordinates-type");
            // Delete previous drawings
            for (var i = 0; i < allShapes.length; i++) {
                allShapes[i].setMap(null);
            }
            allShapes = [];
            for (var i = 0; i < allOverlaysFileType.length; i++) {
                allOverlaysFileType[i].overlay.setMap(null);
            }
            allOverlaysFileType = [];
            // Set the type of controls
            if (type === "point") {
                drawingManagerFileType.drawingControlOptions.drawingModes = [
                    google.maps.drawing.OverlayType.MARKER
                ];
                drawingManagerFileType.drawingMode = null;  // Set the default hand control
                drawingManagerFileType.setMap(coordinatesPicker);
                var lat_field = $(".coord_picker_class").filter("[data-id='north']");
                var lon_field = $(".coord_picker_class").filter("[data-id='east']");
                var myLatLng = {
                    lat: parseFloat(lat_field.val()),
                    lng: parseFloat(lon_field.val())
                };
                if(myLatLng.lat && myLatLng.lng) {
                    // Define the rectangle and set its editable property to true.
                    var marker = new google.maps.Marker({
                        position: myLatLng,
                        map: coordinatesPicker
                    });
                    allShapes.push(marker);
                    var coordinates = (marker.getPosition());
                    marker.setMap(coordinatesPicker);
                    // Set onClick event for recenter button
                    processDrawingFileType(coordinates, "marker");
                    // Center map at new market
                    coordinatesPicker.setCenter(marker.getPosition());
                    $("#resetZoomBtn").click(function () {
                        coordinatesPicker.setCenter(marker.getPosition());
                    });
                }
            }
            else if (type === "rectangle") {
                drawingManagerFileType.drawingControlOptions.drawingModes = [
                    google.maps.drawing.OverlayType.RECTANGLE
                ];
                drawingManagerFileType.drawingMode = null;  // Set the default hand control
                drawingManagerFileType.setMap(coordinatesPicker);
                var bounds = {
                    north: parseFloat($(".coord_picker_class").filter("[data-id='north']").val()),
                    south: parseFloat($(".coord_picker_class").filter("[data-id='south']").val()),
                    east: parseFloat($(".coord_picker_class").filter("[data-id='east']").val()),
                    west: parseFloat($(".coord_picker_class").filter("[data-id='west']").val())
                };
                if (bounds.north && bounds.south && bounds.east && bounds.west) {
                    var rectangle = new google.maps.Rectangle({
                        bounds: bounds,
                        editable: true,
                        draggable: true
                    });
                    rectangle.setMap(coordinatesPicker);
                    rectangle.addListener('bounds_changed', function () {
                        var coordinates = (rectangle.getBounds());
                        processDrawingFileType(coordinates, "rectangle");
                    });
                    allShapes.push(rectangle);
                    zoomCoverageMap(bounds);
                    $("#resetZoomBtn").click(function () {
                        zoomCoverageMap(bounds);
                    });
                }
            }

            // Set default behavior. It is overridden once coordinates are selected.
            $("#btn-confirm-coordinates").unbind("click");
            $("#btn-confirm-coordinates").click(function () {
                $('#coordinates-picker-modal').modal('hide')
            });

            $("#coordinates-picker-modal").modal("show");
        });

        $(this).addClass("has-coordinates-picker");

        return this;
    };
})( jQuery );


function initMapFileType() {
    $('#coordinates-picker-modal').on('shown.bs.modal', function () {
        google.maps.event.trigger(coordinatesPicker, 'resize');
    });

    // Initialize Map
    coordinatesPicker = new google.maps.Map(document.getElementById('picker-map-container'), {
        zoom: 3,
        streetViewControl: false,
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

    drawingManagerFileType = new google.maps.drawing.DrawingManager({
        drawingControl: true,
        drawingControlOptions: {
            position: google.maps.ControlPosition.TOP_CENTER
        },
        rectangleOptions: {
            editable: true,
            draggable: true
        }
    });

    drawingManagerFileType.setMap(coordinatesPicker);

    // When a rectangle is drawn
    google.maps.event.addListener(drawingManagerFileType, 'rectanglecomplete', function (rectangle) {
        var coordinates = (rectangle.getBounds());
        processDrawingFileType(coordinates, "rectangle");

        // When this rectangle is modified
        rectangle.addListener('bounds_changed', function () {
            var coordinates = (rectangle.getBounds());
            processDrawingFileType(coordinates, "rectangle");
        });
    });

    // When a point is selected
    google.maps.event.addListener(drawingManagerFileType, 'markercomplete', function (marker) {
        var coordinates = (marker.getPosition());
            processDrawingFileType(coordinates, "marker");
    });

    google.maps.event.addListener(drawingManagerFileType, 'overlaycomplete', function (e) {
        allOverlaysFileType.push(e);
    });


    $(".has-coordinates-picker").each(function() {
        const instance = $(this);
        instance.coordinatesPicker();
    })
}

function processDrawingFileType(coordinates, shape) {
    // Delete previous drawings
    if (allOverlaysFileType.length > 1) {
        for (var i = 1; i < allOverlaysFileType.length; i++) {
            allOverlaysFileType[i - 1].overlay.setMap(null);
        }
        allOverlaysFileType.shift();
    }
    if (allOverlaysFileType.length > 0) {
        for (var i = 0; i < allShapes.length; i++) {
            allShapes[i].setMap(null);
        }
        allShapes = [];
    }

    if (shape === "rectangle") {
        var bounds = {
            north: parseFloat(coordinates.getNorthEast().lat()),
            south: parseFloat(coordinates.getSouthWest().lat()),
            east: parseFloat(coordinates.getNorthEast().lng()),
            west: parseFloat(coordinates.getSouthWest().lng())
        };

        $("#btn-confirm-coordinates").unbind("click");
        $("#btn-confirm-coordinates").click(function () {
            currentInstance.filter("[data-id='north']").val(bounds.north.toFixed(4));
            currentInstance.filter("[data-id='east']").val(bounds.east.toFixed(4));
            currentInstance.filter("[data-id='south']").val(bounds.south.toFixed(4));
            currentInstance.filter("[data-id='west']").val(bounds.west.toFixed(4));

            $('#metadata_schema_save_info').hide();
            $('#metadata_schema_value_submit').show();

            $('#coordinates-picker-modal').modal('hide')
        });
    }
    else {
        $("#btn-confirm-coordinates").unbind("click");
        $("#btn-confirm-coordinates").click(function () {
            currentInstance.filter("[data-id='east']").val(coordinates.lng().toFixed(4));
            currentInstance.filter("[data-id='north']").val(coordinates.lat().toFixed(4));

            $('#metadata_schema_save_info').hide();
            $.find('#metadata_schema_value_submit').show();

            $('#coordinates-picker-modal').modal('hide')
        });
    }
}
