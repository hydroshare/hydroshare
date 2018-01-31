var minFloatingNumber = 0.0001;
var map = null;
var map_default_bounds = null;
var map_default_zoom = 2;
var map_default_center = new google.maps.LatLng(0, 0);
var markers = [];
var raw_results = [];
var markerCluster = null;
var info_window = null;
var shade_rects = [];

var initMap = function(json_results) {
    var $mapDiv = $("#discover-map");
    var mapDim = {
        height: $mapDiv.height(),
        width: $mapDiv.width()
    };

    map = new google.maps.Map($mapDiv[0], {
        zoom: map_default_zoom,
        mapTypeId: google.maps.MapTypeId.TERRAIN
    });

    info_window = new google.maps.InfoWindow();

    setMarkers(json_results);
    var bounds = (markers.length > 0) ? createBoundsForMarkers(markers) : map.setZoom(2);
    if (bounds) {
        var ne = bounds.getNorthEast();
        var sw = bounds.getSouthWest();
        document.getElementById("id_NElat").value = ne.lat();
        document.getElementById("id_NElng").value = ne.lng();
        document.getElementById("id_SWlat").value = sw.lat();
        document.getElementById("id_SWlng").value = sw.lng();
        map_default_bounds = bounds;
        map.fitBounds(map_default_bounds);
        map_default_zoom = getBoundsZoomLevel(map_default_bounds, mapDim);
        map_default_center = map_default_bounds.getCenter();
    }

    var idle_listener = google.maps.event.addListener(map, "idle", function () {
        map.setCenter(map_default_center);
        map.setZoom(map_default_zoom);
        google.maps.event.removeListener(idle_listener);
    });

    var bounds_listener = google.maps.event.addListener(map, 'bounds_changed', function(){
        var bnds = map.getBounds();
        if (bnds) {
            var ne = bnds.getNorthEast();
            var sw = bnds.getSouthWest();
            document.getElementById("id_NElng").value = ne.lng();
            document.getElementById("id_NElat").value = ne.lat();
            document.getElementById("id_SWlng").value = sw.lng();
            document.getElementById("id_SWlat").value = sw.lat();
            setLatLngLabels();
        }
    });

    map.enableKeyDragZoom({
        key: 'shift',
        visualEnabled: true
    });

    var dz = map.getDragZoomObject();

    google.maps.event.addListener(dz, 'dragend', function (bnds) {
        map.setCenter(bnds.getCenter());
        map.setZoom(getBoundsZoomLevel(bnds, mapDim));
        var ne = bnds.getNorthEast();
        var sw = bnds.getSouthWest();
        document.getElementById("id_NElng").value = ne.lng();
        document.getElementById("id_NElat").value = ne.lat();
        document.getElementById("id_SWlng").value = sw.lng();
        document.getElementById("id_SWlat").value = sw.lat();

    });

    var zoom_listener = google.maps.event.addListener(map, 'zoom_changed', function(){
        updateMapView();
    });

    var drag_listener = google.maps.event.addListener(map, 'dragend', function(){
        updateMapView();
    });


    generateLegend();

    var input_address = document.getElementById('geocoder-address');
    var autocomplete = new google.maps.places.Autocomplete(input_address);

    var geocoder = new google.maps.Geocoder();
    document.getElementById('geocoder-submit').addEventListener('click', function() {
        geocodeAddress(geocoder, map, mapDim);
    });

    google.maps.event.addListener(map,'click',function(e){
        var map_items_table = $('#map-items').DataTable();
        map_items_table.clear().draw();
        shade_rects.forEach(function(rect){
            rect.setOptions({fillOpacity: 0});
        });
    });
};


var setMarkers = function(json_results) {
    var modified_points_data = [];
    var modified_boxes_data = [];
    var boxes_data = [];
    for (var i = 0; i < json_results.length; i++ ) {
        if (json_results[i].coverage_type == 'point') {
            checkDuplicatePointResults(modified_points_data, json_results[i]);
        } else if (json_results[i].coverage_type == 'box') {
            checkDuplicateBoxResults(modified_boxes_data, json_results[i]);
            boxes_data.push(json_results[i]);
        }
    }

    modified_points_data.forEach(function(point){
        createPointResourceMarker(point);
    });

    modified_boxes_data.forEach(function(box){
        createBoxResourceMarker (box);
    });

    drawShadeRectangles(boxes_data);

    shade_rects.forEach(function(rect){
        google.maps.event.addListener(rect,'click',function(e){
            highlightOverlapping(e.latLng);
            var map_resources = [];
            buildMapItemsTableData(boxes_data, map_resources, e.latLng);
            var map_items_table = $('#map-items').DataTable();
            map_items_table.clear();
            map_items_table.rows.add(map_resources);
            map_items_table.draw();
        });
    });
    markerCluster = new MarkerClusterer(map, markers, {
        styles:[{
            height: 55,
            width: 56,
            url: '//cdn.rawgit.com/googlemaps/js-marker-clusterer/gh-pages/images/m2.png'
        }]
    });
};

var highlightOverlapping = function(position) {
    shade_rects.forEach(function(rect){
        var rect_bound = new google.maps.LatLngBounds();
        calShadeRectBounds(rect, rect_bound);
        if (rect_bound.contains(position)) {
            rect.setOptions({fillOpacity: 0.15});
        } else {
            rect.setOptions({fillOpacity: 0});
        }
    });
};

var drawShadeRectangles = function(boxes) {
    for (var i = 0; i < boxes.length; i++) {
        var box = boxes[i];
        var northlimit = parseFloat(box.northlimit);
        var southlimit = parseFloat(box.southlimit);
        var eastlimit = parseFloat(box.eastlimit);
        var westlimit = parseFloat(box.westlimit);

        var box_ne = new google.maps.LatLng(northlimit, eastlimit);
        var box_sw = new google.maps.LatLng(southlimit, westlimit);

        var rectCoords = [
          {lat: northlimit, lng: westlimit},
          {lat: northlimit, lng: eastlimit},
          {lat: southlimit, lng: eastlimit},
          {lat: southlimit, lng: westlimit}
        ];

        shade_rects[i] = new google.maps.Polygon({
            paths: [rectCoords],
            strokeColor: '#FF0000',
            strokeOpacity: 0.15,
            strokeWeight: 2,
            fillColor: '#FF0000',
            fillOpacity: 0
        });

        shade_rects[i].setMap(map);
    }
};


var buildMapItemsTableData = function(box_resources, map_resources, latLng) {
    box_resources.forEach(function(resource) {
        var northlimit = parseFloat(resource.northlimit);
        var southlimit = parseFloat(resource.southlimit);
        var eastlimit = parseFloat(resource.eastlimit);
        var westlimit = parseFloat(resource.westlimit);
        var ne_latlng = new google.maps.LatLng(northlimit, eastlimit);
        var sw_latlng = new google.maps.LatLng(southlimit, westlimit);
        var resource_bound = new google.maps.LatLngBounds(sw_latlng, ne_latlng);
        if (resource_bound.contains(latLng)) {
            var author_name = "";
            if (resource.first_author_url) {
                author_name = '<a target="_blank" href="' + resource.first_author_url + '">' + resource.first_author + '</a>';
            } else {
                author_name = resource.first_author;
            }
            var resource_title = '<a target="_blank" href="' + resource.get_absolute_url + '">' + resource.title + '</a>';
            var map_resource = [resource, resource.resource_type, resource_title, author_name];
            map_resources.push(map_resource);
        }
    });

};

var buildMapItemsTableDataforMarkers = function (resources_list, map_resources) {
    resources_list.forEach(function(resource) {
        var northlimit = parseFloat(resource.northlimit);
        var southlimit = parseFloat(resource.southlimit);
        var eastlimit = parseFloat(resource.eastlimit);
        var westlimit = parseFloat(resource.westlimit);
        var ne_latlng = new google.maps.LatLng(northlimit, eastlimit);
        var sw_latlng = new google.maps.LatLng(southlimit, westlimit);
        var resource_bound = new google.maps.LatLngBounds(sw_latlng, ne_latlng);
        var author_name = "";
        if (resource.first_author_url) {
            author_name = '<a target="_blank" href="' + resource.first_author_url + '">' + resource.first_author + '</a>';
        } else {
            author_name = resource.first_author;
        }
        var resource_title = '<a target="_blank" href="' + resource.get_absolute_url + '">' + resource.title + '</a>';
        var map_resource = [resource, resource.resource_type, resource_title, author_name];
        map_resources.push(map_resource);
    });
};

var setMapItemsList = function(json_results, latLng) {
    var map_resources = [];
    buildMapItemsTableData(json_results, map_resources, latLng);

    var mapItems = $('#map-items').DataTable( {
        data: map_resources,
        "scrollY": "200px",
        "scrollCollapse": true,
        "paging": false,
        "bDestroy": true,
        "language": {
            "emptyTable": "Click on map to explore resource data."
        },
        columns: [
            { title: "Show on Map"},
            { title: "Resource Type" },
            { title: "Title" },
            { title: "First Author" }
        ],
        "columnDefs": [ {
            "targets": [0],
            "width": "90px",
            "data": null,
            "defaultContent": '<a class="btn btn-default" role="button"><span class="glyphicon glyphicon-zoom-in"></span></button>'
        },
        {
           "targets": [1],     // Resource type
            "width": "110px"
        }]
    });
    setMapFunctions(mapItems);
};

var setMapFunctions = function (datatable) {
    $('#map-items tbody').on('click', '[role="button"]', function () {
        var data = datatable.row($(this).parents('tr')).data();
        showBoxMarker(data[0], true);
    });
    $('#map-items tbody').on('hover', 'tr', function () {
        var data = datatable.row(this).data();
        if (data) {
            showBoxMarker(data[0], false);
        }
    });
};

var showBoxMarker = function(box, zoom_on_map) {
    var northlimit = parseFloat(box.northlimit);
    var southlimit = parseFloat(box.southlimit);
    var eastlimit = parseFloat(box.eastlimit);
    var westlimit = parseFloat(box.westlimit);

    var rectBounds = new google.maps.LatLngBounds(
            new google.maps.LatLng(southlimit, westlimit),
            new google.maps.LatLng(northlimit, eastlimit)
    );

    if (zoom_on_map) {
        map.fitBounds(rectBounds);
        updateMapView();
    }
    findShadeRect(rectBounds);
};

var clientUpdateMarkers = function(filtered_results) {
    removeMarkers();
    var bnds = map.getBounds();
    if (bnds) {
        for (var  i = 0; i < raw_results.length; i++ ) {
            if (raw_results[i].coverage_type == 'point') {
                var data_lat = parseFloat(raw_results[i].north);
                var data_lng = parseFloat(raw_results[i].east);
                var latlng = new google.maps.LatLng(data_lat, data_lng);
                if (bnds.contains(latlng)) {
                    filtered_results.push(raw_results[i]);
                }
            } else if (raw_results[i].coverage_type == 'box') {
                var northlimit = parseFloat(raw_results[i].northlimit);
                var southlimit =  parseFloat(raw_results[i].southlimit);
                var eastlimit = parseFloat(raw_results[i].eastlimit);
                var westlimit = parseFloat(raw_results[i].westlimit);
                var ne_latlng = new google.maps.LatLng(northlimit, eastlimit);
                var sw_latlng = new google.maps.LatLng(southlimit, westlimit);
                var box_bound = new google.maps.LatLngBounds(sw_latlng, ne_latlng);
                if (bnds.intersects(box_bound)) {
                    filtered_results.push(raw_results[i]);
                }
            }
        }
    }
};

var removeMarkers = function() {
    for (var n = 0; n < shade_rects.length; n++) {
        if (shade_rects[n].getMap() != null) {
            shade_rects[n].setMap(null);
        }
    }
    shade_rects = [];

    if (markerCluster) {
        markerCluster.clearMarkers(markers);
    }
    for (var i = 0; i < markers.length; i++) {
        if (markers[i].getMap() != null) {
            markers[i].setMap(null);
        }
    }
    markers = [];
};

var checkDuplicatePointResults = function (modified_points_data, test){
    var test_lat = parseFloat(test.north);
    var test_lng = parseFloat(test.east);
    var existed = false;
    modified_points_data.forEach(function(item) {
        var item_lat = parseFloat(item.north);
        var item_lng = parseFloat(item.east);

        var lat_diff = Math.abs(test_lat - item_lat);
        var lng_diff = Math.abs(test_lng - item_lng);
        if (lat_diff < minFloatingNumber && lng_diff < minFloatingNumber) {
            item.info_link = item.info_link + '<br />' + '<a href="' + test.get_absolute_url + '">' + test.title +'</a>';
            item.counter++;
            item.resources_list.push(test);
            existed = true;
        }
    });
    if (!existed) {
        test.resources_list = [];
        test.resources_list.push(test);
        test.info_link = '<a href="' + test.get_absolute_url + '">' + test.title + '</a>';
        test.counter = 1;
        modified_points_data.push(test);
    }
};

var checkDuplicateBoxResults = function (modified_boxes_data, test){
    var test_lat = (parseFloat(test.northlimit) + parseFloat(test.southlimit)) / 2;
    var test_lng = (parseFloat(test.eastlimit) + parseFloat(test.westlimit)) / 2;
    var existed = false;
    modified_boxes_data.forEach(function(item){
        var item_lat = (parseFloat(item.northlimit) + parseFloat(item.southlimit)) / 2;
        var item_lng = (parseFloat(item.eastlimit) + parseFloat(item.westlimit)) / 2;

        var lat_diff = Math.abs(test_lat - item_lat);
        var lng_diff = Math.abs(test_lng - item_lng);

        if (lat_diff < minFloatingNumber && lng_diff < minFloatingNumber) {
            item.info_link = item.info_link + '<br />' + '<a href="' + test.get_absolute_url + '">' + test.title + '</a>';
            item.counter++;
            item.resources_list.push(test);
            existed = true;
        }
    });
    if (!existed) {
        test.resources_list = [];
        test.resources_list.push(test);
        test.info_link = '<a href="' + test.get_absolute_url + '">' + test.title + '</a>';
        test.counter = 1;
        modified_boxes_data.push(test);
    }
};

var createPointResourceMarker = function (point) {
    var info_content = point.info_link;
    var lat = parseFloat(point.north);
    var lng = parseFloat(point.east);
    var counter = point.counter.toString();
    var latlng = new google.maps.LatLng(lat, lng);
    var marker = new google.maps.Marker({
        map: map,
        icon: '//cdn.rawgit.com/Concept211/Google-Maps-Markers/master/images/marker_red' + counter + '.png',
        position: latlng
    });
    markers.push(marker);
    google.maps.event.addListener(marker, 'click', function() {
        var map_resources = [];
        buildMapItemsTableDataforMarkers(point.resources_list, map_resources);
        var map_items_table = $('#map-items').DataTable();
        map_items_table.clear();
        map_items_table.rows.add(map_resources);
        map_items_table.draw();
        info_window.setContent(info_content);
        info_window.open(map, marker);

    });
};

var createBoxResourceMarker = function (box) {
    var info_content = box.info_link;
    var northlimit = parseFloat(box.northlimit);
    var southlimit = parseFloat(box.southlimit);
    var eastlimit = parseFloat(box.eastlimit);
    var westlimit = parseFloat(box.westlimit);
    var counter = box.counter.toString();
    var lat = (parseFloat(northlimit) + parseFloat(southlimit)) / 2;
    var lng = (parseFloat(eastlimit) + parseFloat(westlimit)) / 2;
    var latlng = new google.maps.LatLng(lat, lng);

    var marker = new google.maps.Marker({
        map: map,
        icon: '//cdn.rawgit.com/Concept211/Google-Maps-Markers/master/images/marker_blue' + counter + '.png',
        position: latlng
    });
    markers.push(marker);

    google.maps.event.addListener(marker, 'click', function() {
        var map_resources = [];
        buildMapItemsTableDataforMarkers(box.resources_list, map_resources);
        var map_items_table = $('#map-items').DataTable();
        map_items_table.clear();
        map_items_table.rows.add(map_resources);
        map_items_table.draw();
        info_window.setContent(info_content);
        info_window.open(map, marker);
        var rectBounds = new google.maps.LatLngBounds(
                new google.maps.LatLng(southlimit, westlimit),
                new google.maps.LatLng(northlimit, eastlimit)
        );
        findShadeRect(rectBounds);
    });
};

var createBoundsForMarkers = function(markers) {
    var bounds = new google.maps.LatLngBounds();
    $.each(markers, function() {
        bounds.extend(this.getPosition());
    });
    return bounds;
};

var getBoundsZoomLevel = function (bounds, mapDim) {
    var WORLD_DIM = {height: 256, width: 256};
    var ZOOM_MAX = 21;

    function latRad(lat) {
        var sin = Math.sin(lat * Math.PI / 180);
        var radX2 = Math.log((1 + sin) / (1 - sin)) / 2;
        return Math.max(Math.min(radX2, Math.PI), -Math.PI) / 2;
    }

    function zoom(mapPx, worldPx, fraction) {
        return Math.floor(Math.log(mapPx / worldPx / fraction) / Math.LN2);
    }

    var ne = bounds.getNorthEast();
    var sw = bounds.getSouthWest();

    var latFraction = (latRad(ne.lat()) - latRad(sw.lat())) / Math.PI;

    var lngDiff = ne.lng() - sw.lng();
    var lngFraction = ((lngDiff < 0) ? (lngDiff + 360) : lngDiff) / 360;

    var latZoom = zoom(mapDim.height, WORLD_DIM.height, latFraction);
    var lngZoom = zoom(mapDim.width, WORLD_DIM.width, lngFraction);

    return Math.min(latZoom, lngZoom, ZOOM_MAX);
};

var generateLegend = function() {
    var map_legend = document.getElementById('discover-map-legend');
    var geo_coder = document.getElementById('geocoder-panel');
    var reset_zoom_button = document.getElementById('resetZoom');
    map.controls[google.maps.ControlPosition.RIGHT_TOP].push(map_legend);
    map.controls[google.maps.ControlPosition.LEFT_BOTTOM].push(geo_coder);
    map.controls[google.maps.ControlPosition.RIGHT_BOTTOM].push(reset_zoom_button);
    var geocoder_content = [];
    var resetButton_content = [];
    var legend_table = "<table><tbody>";
    legend_table += "<tr><td class='text-center'><img src='/static/img/discover_map_red_marker.png'></td><td>Point Coverage Locations</td></tr>";
    legend_table += "<tr><td class='text-center'><img src='/static/img/discover_map_blue_marker.png'></td><td>Box Coverage Centers</td></tr>";
    legend_table += "<tr><td class='text-center'><img src='/static/img/discover_map_cluster_icon.png'></td><td>Clusters</td></tr></tbody></table>";
    geocoder_content.push("<input id='geocoder-address' type='textbox' placeholder='Search Locations...'>");
    geocoder_content.push("<a id='geocoder-submit' style='margin-left:10px' class='btn btn-default' role='button'><span class='glyphicon glyphicon-zoom-in'></span> Go </a>");
    resetButton_content.push("<a id='reset-zoom-btn' data-toggle='tooltip' title='Reset Zoom' class='btn btn-default btn-sm' onclick='resetMapZoom()'>");
    resetButton_content.push("<span class='glyphicon glyphicon-fullscreen'></span></a>");
    map_legend.innerHTML = legend_table;
    geo_coder.innerHTML = geocoder_content.join('');
    reset_zoom_button.innerHTML = resetButton_content.join('');
};

var geocodeAddress = function(geocoder, resultsMap, mapDim) {
    var address = document.getElementById('geocoder-address').value;
    geocoder.geocode({'address': address}, function(results, status) {
        if (status === google.maps.GeocoderStatus.OK) {
            resultsMap.setCenter(results[0].geometry.location);
            resultsMap.setZoom(getBoundsZoomLevel(results[0].geometry.bounds, mapDim));
            updateMapView();
        } else {
            alert('Geocode was not successful for the following reason: ' + status);
        }
    });
};

var resetMapZoom = function() {
    removeMarkers();
    setMarkers(raw_results);
    var map_items_table = $('#map-items').DataTable();
    map_items_table.clear().draw();
    var $mapDiv = $("#discover-map");
    var mapDim = {
        height: $mapDiv.height(),
        width: $mapDiv.width()
    };

    var bounds = (markers.length > 0) ? createBoundsForMarkers(markers) : map.setZoom(2);
    map.fitBounds(bounds);
    var zoom_level = getBoundsZoomLevel(bounds, mapDim);
    var reset_center = bounds.getCenter();
    if (bounds) {
        map.fitBounds(bounds);
        var listener = google.maps.event.addListener(map, "idle", function () {
            map.setZoom(zoom_level);
            map.setCenter(reset_center);
            google.maps.event.removeListener(listener);
        });
    } else {
        map.setZoom(map_default_zoom);
    }
};

var updateMapView = function() {
    var filtered_results = [];
    clientUpdateMarkers(filtered_results);
    setMarkers(filtered_results);
};

// var updateListView = function (data) {
//     var requestURL = "/search/";
// 
//     if (window.location.search.length == 0) {
//         requestURL += "?q=";
//     } else {
//         var textSearch = $("#id_q").val();
//         var searchURL = "?q=" + textSearch;
//         requestURL += searchURL;
//         requestURL += buildURLOnCheckboxes();
//     }
//     $("#discover-list-loading-spinner").show();
//     $.ajax({
//         type: "GET",
//         url: requestURL,
//         data: data,
//         dataType: 'html',
//         success: function (data) {
//             $('#items-discovered_wrapper').empty();
//             $("#discover-page-options").empty();
//             var tableDiv = $("#items-discovered", data);
//             $("#items-discovered_wrapper").html(tableDiv);
//             var pageOptionDiv = $("#discover-page-options", data);
//             $("#discover-page-options").html(pageOptionDiv);
// 
//             initializeTable();
//             $("#discover-list-loading-spinner").hide();
//         },
//         failure: function (data) {
//             console.error("Ajax call for updating list-view data failed");
//             $("#discover-list-loading-spinner").hide();
//         }
//     });
// };

var updateListItems = function (request_url) {
    // TODO: not sure why we need list spinner when map is visible?
    $("#discover-list-loading-spinner").show();
    if (map != null) {
        $("#discover-map-loading-spinner").show();
        $.when(updateMapFaceting(), updateListFaceting(request_url)).done(function(){
            $("#discover-list-loading-spinner").hide();
            $("#discover-map-loading-spinner").hide();
        });
    } else {
        $.when(updateListFaceting(request_url)).done(function(){
            $("#discover-list-loading-spinner").hide();
        });
    }
};

var updateListFaceting = function (request_url) {
    return $.ajax({
        type: "GET",
        url: request_url,
        dataType: 'html',
        success: function (data) {
            $('#items-discovered_wrapper').empty();
            $("#discover-page-options-1").empty();
            $("#discover-page-options-2").empty();
            var tableDiv = $("#items-discovered", data);
            $("#items-discovered_wrapper").html(tableDiv);
            var pageOptionDiv1 = $("#discover-page-options-1", data);
            $("#discover-page-options-1").html(pageOptionDiv1);
            var pageOptionDiv2 = $("#discover-page-options-2", data);
            $("#discover-page-options-2").html(pageOptionDiv2);
            initializeTable();
        },
        failure: function (data) {
            console.error("Ajax call for updating list-view data failed");
        }
    });
};

var updateMapFaceting = function (){
    var map_update_url = "/searchjson/";
    var textSearch = $("#id_q").val();
    var searchURL = "?q=" + textSearch;
    map_update_url += searchURL;
    map_update_url += buildURLOnCheckboxes();
    var start_date = $("#id_start_date").val();
    var end_date = $("#id_end_date").val();
    removeMarkers();
    return $.ajax({
        type: "GET",
        url: map_update_url,
        data: {
            NElat: '',
            NElng: '',
            SWlat: '',
            SWlng: '',
            start_date: start_date,
            end_date: end_date
        },
        dataType: 'json',
        success: function (data) {
            raw_results = [];
            for (var j = 0; j < data.length; j++) {
                var item = $.parseJSON(data[j]);
                raw_results.push(item);
            }

            updateMapView();
        },
        failure: function(data) {
            console.error("Ajax call for getting map data failed");
        }
    });
};

var calShadeRectBounds = function (rect, shade_rect_bound) {
    rect.getPaths().getArray().forEach(function(path){
        path.getArray().forEach(function(latlng){
            shade_rect_bound.extend(latlng);
        });
    });
};

var findShadeRect = function(rectBounds) {
    var found = 0;
    shade_rects.forEach(function(rect){
        var shade_rect_bound = new google.maps.LatLngBounds();
        calShadeRectBounds(rect, shade_rect_bound);
        if (rectBounds.equals(shade_rect_bound) && found == 0) {
            rect.setOptions({fillOpacity: 0.35});
            found = 1;
        } else {
            rect.setOptions({fillOpacity: 0});
        }
    });
};

var setLatLngLabels = function() {
    var ne_lat = parseFloat(document.getElementById("id_NElat").value).toFixed(3) + '°';
    var ne_lng = parseFloat(document.getElementById("id_NElng").value).toFixed(3) + '°';
    var sw_lat = parseFloat(document.getElementById("id_SWlat").value).toFixed(3) + '°';
    var sw_lng = parseFloat(document.getElementById("id_SWlng").value).toFixed(3) + '°';
    jQuery("label[for='ne-lat-value']").html(ne_lat);
    jQuery("label[for='ne-lng-value']").html(ne_lng);
    jQuery("label[for='sw-lat-value']").html(sw_lat);
    jQuery("label[for='sw-lng-value']").html(sw_lng);
};

var reorderDivs = function() {
    var faceted_fields = ['creator', 'contributor', 'owner', 
        'resource_type', 'subject', 'availability'];
    var div_ordering = [];
    faceted_fields.forEach(function(field) {
        var faceting_div = "faceting-"+field;
        div_ordering.push(faceting_div);
    });
    var i;
    for (i = 1; i < div_ordering.length; i++) {
        var div0 = "#" + div_ordering[i-1];
        var div1 = "#" + div_ordering[i];
        $(div1).insertAfter(div0);
    }
};

var formGeoParameters = function() {
    var selected_results = $('input[name=results-selection]:checked').val();
    var geoSearchParams = "&NElat=&NElng=&SWlat=&SWlng=";
    return geoSearchParams;
};

var formDateParameters = function() {
    var start_date = $("#id_start_date").val();
    var end_date = $("#id_end_date").val();
    // if (start_date <= end_date or not start_date or not end_date) {  
    return "&start_date="+start_date+"&end_date="+end_date;
    // }
};

var formOrderParameters = function() {
    var sort_order = $("#id_sort_order").val();
    var sort_direction = $("#id_sort_direction").val();
    return "&sort_order="+sort_order+"&sort_direction="+sort_direction;
};

var buildURLOnCheckboxes = function () {
    var requestURL = '';
    $(".faceted-selections").each(function () {
        var checkboxId = $(this).attr("id");
        var sessionStorageCheckboxId = 'search-' + checkboxId;
        if(document.getElementById(checkboxId).checked){
            var arr = $(this).val().split(",");
            var key = arr[0];
            var value = arr[1];
            requestURL += "&selected_facets="+key+"_exact:"+value;
        }
    });
    return requestURL;
};

var popCheckboxes = function() {
    $(".faceted-selections").each(function () {
        var checkboxId = $(this).attr("id");
        var sessionStorageCheckboxId = 'search-' + checkboxId;
        var val = sessionStorage[sessionStorageCheckboxId];
        var isChecked = val !== undefined ? val == 'true' : false;
        $(this).prop("checked", isChecked);
    });
};

var clearCheckboxes = function() {
    $(".faceted-selections").each(function () {
        var checkboxId = $(this).attr("id");
        var sessionStorageCheckboxId = 'search-' + checkboxId;
        sessionStorage[sessionStorageCheckboxId] = 'false';
        sessionStorage.removeItem(sessionStorageCheckboxId);
    });
};

var clearAllFaceted = function() {
    clearCheckboxes();
    var clearURL = "/search/";
    window.location = clearURL;
};

var clearDates = function() {
    var textSearch = $("#id_q").val();
    var searchURL = "?q=" + textSearch;
    var geoSearchParams = formGeoParameters();
    var facetingParams = buildURLOnCheckboxes();
    var dateSearchParams = "&start_date=&end_date=";
    var sortOrderParams = formOrderParameters();
    var windowPath = window.location.pathname;
    var requestURL =  windowPath + searchURL + facetingParams + geoSearchParams 
        + dateSearchParams + sortOrderParams;
    if (window.location.hash) {
        requestURL = requestURL + window.location.hash;
    }
    window.location = requestURL;
};

function initializeTable() {
    var RESOURCE_TYPE_COL = 0;
    var TITLE_COL = 1;
    var OWNER_COL = 2;
    var DATE_CREATED_COL = 3;
    var LAST_MODIFIED_COL = 4;

    var colDefs = [
        {
            "targets": [RESOURCE_TYPE_COL],     // Resource type
            "width": "110px"
        },
        {
            "targets": [DATE_CREATED_COL]     // Date created
        },
        {
            "targets": [LAST_MODIFIED_COL]     // Last modified
        },
    ];

    $('#items-discovered').DataTable({
        "paging": false,
        "searching": false,
        "info": false,
        "ordering": false,
        // "order": [[TITLE_COL, "asc"]],
        "columnDefs": colDefs
    });
}

$(document).ready(function () {
    $("#id_start_date").datepicker({
        dateFormat: 'mm/dd/yy',
        changeMonth: true,
        changeYear: true,
        yearRange: '1950:'
    });
    $("#id_end_date").datepicker({
        dateFormat: 'mm/dd/yy',
        changeMonth: true,
        changeYear: true,
        yearRange: '1950:'
    });

    if (window.location.search.length == 0) {
        clearCheckboxes();
    }
    $(".search-field").keypress(function(event) {
        if (event.which == 13) {
            event.preventDefault();
            clearCheckboxes();
            var textSearch = $("#id_q").val();
            var searchURL = "?q=" + textSearch;
            var geoSearchParams = formGeoParameters();
            var dateSearchParams = formDateParameters();
            var sortOrderParams = formOrderParameters();
            var windowPath = window.location.pathname;
            var requestURL =  windowPath + searchURL + geoSearchParams 
                + dateSearchParams + sortOrderParams;
            window.location = requestURL;
        }
    });

    $("#covereage-search-fields input, #date-search-fields input, #id_q").addClass("form-control");
    $("#search-order-fields select").addClass("form-control");

    $("title").text("Discover | HydroShare");   // Set browser tab title

    initializeTable(); 
    popCheckboxes();

    $("ul.nav-tabs > li > a").on("shown.bs.tab", function (e) {
        var tabId = $(e.target).attr("href").substr(1);
        window.location.hash = tabId;
        if (tabId == "map-view" && map == null) {
            var requestURL = "/searchjson/";
            var textSearch = $("#id_q").val();
            var searchURL = "?q=" + textSearch;
            requestURL += searchURL;
            requestURL += buildURLOnCheckboxes();
            var ne_lat = document.getElementById("id_NElat").value;
            var ne_lng = document.getElementById("id_NElng").value;
            var sw_lat = document.getElementById("id_SWlat").value;
            var sw_lng = document.getElementById("id_SWlng").value;
            var start_date = $("#id_start_date").val();
            var end_date = $("#id_end_date").val();
            $("#discover-map-loading-spinner").show();
            $.ajax({
                type: "GET",
                url: requestURL,
                data: {
                    NElat: ne_lat,
                    NElng: ne_lng,
                    SWlat: sw_lat,
                    SWlng: sw_lng,
                    start_date: start_date,
                    end_date: end_date
                },
                dataType: 'json',
                success: function (data) {
                    var json_results = [];
                    for (var j = 0; j < data.length; j++) {
                        var item = $.parseJSON(data[j]);
                        json_results.push(item);
                        raw_results.push(item);
                    }
                    initMap(json_results);
                    setMapItemsList([], null);
                    $("#resource-search").show();
                    $("#discover-map-loading-spinner").hide();
                },
                failure: function(data) {
                    $("#discover-map-loading-spinner").hide();
                    console.error("Ajax call for getting map data failed");
                }
            });
        }
    });

    $(".nav-tabs a").click(function() {
        $(this).tab('show');
    });

    // on load of the page: switch to the currently selected tab
    var hash = window.location.hash;
    $('#switch-view a[href="' + hash + '"]').tab('show');

    $("#id_q").attr('placeholder', 'Search All Public and Discoverable Resources');
    reorderDivs();

    $('.collapse').on('shown.bs.collapse', function() {
        $(this).parent().find(".glyphicon-plus").removeClass("glyphicon-plus").addClass("glyphicon-minus");
    }).on('hidden.bs.collapse', function() {
        $(this).parent().find(".glyphicon-minus").removeClass("glyphicon-minus").addClass("glyphicon-plus");
    });

    // This forces a page reload and should only be done when updating queries
    function updateResults () {
        var textSearch = $("#id_q").val();
        var searchURL = "?q=" + textSearch;
        searchURL += buildURLOnCheckboxes();
        var geoSearchParams = formGeoParameters();
        var dateSearchParams = formDateParameters();
        var sortOrderParams = formOrderParameters(); 
        var windowPath = window.location.pathname;
        var requestURL = windowPath + searchURL + geoSearchParams + dateSearchParams 
            + sortOrderParams;
        if (window.location.hash) {
            requestURL = requestURL + window.location.hash;
        }
        window.location = requestURL;
    }

    $("#date-search-fields input").change(function () { 
        var textSearch = $("#id_q").val();
        var searchURL = "?q=" + textSearch;
        var geoSearchParams = formGeoParameters();
        var dateSearchParams = formDateParameters();
        var sortOrderParams = formOrderParameters();
        var windowPath = window.location.pathname;
        var requestURL =  windowPath + searchURL;
        requestURL = requestURL + geoSearchParams + dateSearchParams + sortOrderParams;
        updateListItems(requestURL);
    });

    $("#search-order-fields select").change(function () {
        var textSearch = $("#id_q").val();
        var searchURL = "?q=" + textSearch;
        var geoSearchParams = formGeoParameters();
        var dateSearchParams = formDateParameters();
        var sortOrderParams = formOrderParameters();
        var windowPath = window.location.pathname;
        var requestURL =  windowPath + searchURL;
        requestURL = requestURL + geoSearchParams + dateSearchParams + sortOrderParams;
        updateListItems(requestURL);
    });

    $(".faceted-selections").click(function () {
        var textSearch = $("#id_q").val();
        var searchURL = "?q=" + textSearch;
        var geoSearchParams = formGeoParameters();
        var dateSearchParams = formDateParameters();
        var sortOrderParams = formOrderParameters();
        var windowPath = window.location.pathname;
        var requestURL =  windowPath + searchURL;
        if($(this).is(":checked")) {
            requestURL += buildURLOnCheckboxes();
            var checkboxId = $(this).attr("id");
            var sessionStorageCheckboxId = 'search-' + checkboxId;
            sessionStorage[sessionStorageCheckboxId] = 'true';
            requestURL = requestURL + geoSearchParams + dateSearchParams + sortOrderParams;
            updateListItems(requestURL);
        }
        else {
            var checkboxId = $(this).attr("id");
            var sessionStorageCheckboxId = 'search-' + checkboxId;
            sessionStorage.removeItem(sessionStorageCheckboxId);
            var updateURL =  windowPath + searchURL + buildURLOnCheckboxes() + geoSearchParams 
                + dateSearchParams + sortOrderParams;
            updateListItems(updateURL);
        }
    });

    $("#solr-help-info").popover({
        html: true,
        container: '#body',
        content: '<p>Type a word to search for all variations of the word. Place a word within double-quotes (e.g.,"word") to search for an exact spelling. Type a "word phrase" in double quotes to search for a phrase. Adding a field name limits search to a specific metadata field, e.g., person:Couch, subject:water, resource_type:Composite, and others. </p>',

        trigger: 'click'
    });

    $("#btn-show-all").click(clearAllFaceted);
    $("#clear-dates-options").click(clearDates);

});

