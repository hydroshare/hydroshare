/**
 * Created by Mauriel on 3/28/2017.
 */

var coordinatesPicker;
var currentInstance;   // Keeps track of the instance to work with
var allOverlays = [];
var drawingManager;

(function( $ ){
    $.fn.coordinatesPicker = function () {
        // If component already initiated, return
        if ($(this).hasClass("has-coordinates-picker")) {
            return this;
        }

        var items = $(this).find("input[data-map-item]");

        items.each(function () {
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

            // Map trigger event handler
            item.parent().find(".btn-choose-coordinates").click(function () {
                currentInstance = item.closest("[data-coordinates-type]");
                var type = currentInstance.attr("data-coordinates-type");

                // Set the type of controls
                if (type == "point") {
                    drawingManager.drawingControlOptions.drawingModes = [
                        google.maps.drawing.OverlayType.MARKER
                    ];
                    drawingManager.drawingMode = null;  // Set the default hand control
                    drawingManager.setMap(coordinatesPicker);
                }
                else if (type == "rectangle") {
                    drawingManager.drawingControlOptions.drawingModes = [
                        google.maps.drawing.OverlayType.RECTANGLE
                    ];
                    drawingManager.drawingMode = null;  // Set the default hand control
                    drawingManager.setMap(coordinatesPicker);
                }

                // Delete previous drawings
                for (var i = 0; i < allOverlays.length; i++) {
                    allOverlays[i].overlay.setMap(null);
                }

                allOverlays = [];

                // Set default behavior. It is overridden once coordinates are selected.
                $("#btn-confirm-coordinates").unbind("click");
                $("#btn-confirm-coordinates").click(function () {
                    $('#coordinates-picker-modal').modal('hide')
                });

                $("#coordinates-picker-modal").modal("show");
            });
        });

        $(this).addClass("has-coordinates-picker");

        return this;
    };
})( jQuery );

$(document).ready(function () {
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

    drawingManager = new google.maps.drawing.DrawingManager({
        drawingControl: true,
        drawingControlOptions: {
            position: google.maps.ControlPosition.TOP_CENTER,
        },
        rectangleOptions: {
            editable: true,
            draggable: true
        }
    });

    drawingManager.setMap(coordinatesPicker);

    // When a rectangle is drawn
    google.maps.event.addListener(drawingManager, 'rectanglecomplete', function (rectangle) {
        var coordinates = (rectangle.getBounds());
        processDrawing(coordinates, "rectangle");

        // When this rectangle is modified
        rectangle.addListener('bounds_changed', function () {
            var coordinates = (rectangle.getBounds());
            processDrawing(coordinates, "rectangle");
        });
    });

    // When a point is selected
    google.maps.event.addListener(drawingManager, 'markercomplete', function (marker) {
        var coordinates = (marker.getPosition());
            processDrawing(coordinates, "marker");
    });

    google.maps.event.addListener(drawingManager, 'overlaycomplete', function (e) {
        allOverlays.push(e);
    });

    function processDrawing(coordinates, shape) {
        // Delete previous drawings
        if (allOverlays.length > 1) {
            for (var i = 1; i < allOverlays.length; i++) {
                allOverlays[i - 1].overlay.setMap(null);
            }
            allOverlays.shift();
        }

        if (shape == "rectangle") {
            var bounds = {
                north: parseFloat(coordinates.getNorthEast().lat()),
                south: parseFloat(coordinates.getSouthWest().lat()),
                east: parseFloat(coordinates.getNorthEast().lng()),
                west: parseFloat(coordinates.getSouthWest().lng())
            };

            $("#btn-confirm-coordinates").unbind("click");
            $("#btn-confirm-coordinates").click(function () {
                currentInstance.find("input[data-map-item='northlimit']").val(bounds.north.toFixed(4));
                currentInstance.find("input[data-map-item='eastlimit']").val(bounds.east.toFixed(4));
                currentInstance.find("input[data-map-item='southlimit']").val(bounds.south.toFixed(4));
                currentInstance.find("input[data-map-item='westlimit']").val(bounds.west.toFixed(4));

                // Issue a text change
                currentInstance.find("input[data-map-item='northlimit']").trigger("change");
                currentInstance.find("input[data-map-item='eastlimit']").trigger("change");
                currentInstance.find("input[data-map-item='southlimit']").trigger("change");
                currentInstance.find("input[data-map-item='westlimit']").trigger("change");

                $('#coordinates-picker-modal').modal('hide')
            });
        }
        else {
            $("#btn-confirm-coordinates").unbind("click");
            $("#btn-confirm-coordinates").click(function () {
                currentInstance.find("input[data-map-item='longitude']").val(coordinates.lng().toFixed(4));
                currentInstance.find("input[data-map-item='latitude']").val(coordinates.lat().toFixed(4));

                // Issue a text change
                currentInstance.find("input[data-map-item='longitude']").trigger("change");
                currentInstance.find("input[data-map-item='latitude']").trigger("change");

                $('#coordinates-picker-modal').modal('hide')
            });
        }
    }

    $(".hs-coordinates-picker").each(function() {
        const instance = $(this);
        instance.coordinatesPicker();
    })
});