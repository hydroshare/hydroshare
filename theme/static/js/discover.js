var minFloatingNumber = 0.0001;
var maps = {};
maps["point_map"] = null;
maps["area_map"] = null;
var map_set = false;
var map_default_bounds = null;
var map_default_zoom = 2;
var map_default_center = new google.maps.LatLng(0, 0);
var current_map_bounds = null;
var current_map_zoom = 2;
var current_map_center = new google.maps.LatLng(0, 0);
var markers = [];
var box_centers = [];
var small_box_markers = [];
var raw_box_results = [];
var raw_point_results = [];
var markers_cluster = null;
var box_centers_cluster = null;
var info_window = null;
var shade_rects = [];

var initMap = function(json_results, view_type) {
    var map_view_option = "";
    var geocoder_address_id = "";
    var geocoder_submit_id = "";
    if (view_type == "point_map") {
        map_view_option = "#discover-point-map";
        geocoder_address_id = "point-geocoder-address";
        geocoder_submit_id = "point-geocoder-submit";
    } else {
        map_view_option = "#discover-area-map";
        geocoder_address_id = "area-geocoder-address";
        geocoder_submit_id = "area-geocoder-submit";
    }
    var $mapDiv = $(map_view_option);
    var mapDim = {
        height: $mapDiv.height(),
        width: $mapDiv.width()
    };

    maps[view_type] = new google.maps.Map($mapDiv[0], {
        zoom: map_default_zoom,
        mapTypeId: google.maps.MapTypeId.TERRAIN
    });

    info_window = new google.maps.InfoWindow();
    if (view_type == "point_map") {
        setMarkers(json_results);
    } else {
        setBoxes(json_results);
    }
    if (map_set) {
        maps[view_type].fitBounds(current_map_bounds);
        maps[view_type].setCenter(current_map_center);
        maps[view_type].setZoom(current_map_zoom);
    } else {
        var bounds = null;
        if (view_type == "point_map") {
            bounds = (markers.length > 0) ? createBoundsForMarkers(markers, view_type) : maps[view_type].setZoom(2);
        } else {
            bounds = (box_centers.length > 0) ? createBoundsForMarkers(box_centers, view_type) : maps[view_type].setZoom(2);
        }

        if (bounds) {
            var ne = bounds.getNorthEast();
            var sw = bounds.getSouthWest();
            document.getElementById("id_NElat").value = ne.lat();
            document.getElementById("id_NElng").value = ne.lng();
            document.getElementById("id_SWlat").value = sw.lat();
            document.getElementById("id_SWlng").value = sw.lng();
            map_default_bounds = bounds;
            current_map_bounds = map_default_bounds;
            maps[view_type].fitBounds(map_default_bounds);
            map_default_zoom = getBoundsZoomLevel(map_default_bounds, mapDim);
            current_map_zoom = map_default_zoom;
            map_default_center = map_default_bounds.getCenter();
            current_map_center = map_default_center;

        }
    }

    var idle_listener = google.maps.event.addListener(maps[view_type], "idle", function () {
        maps[view_type].setCenter(current_map_center);
        maps[view_type].setZoom(current_map_zoom);
        google.maps.event.removeListener(idle_listener);

    });

    var bounds_listener = google.maps.event.addListener(maps[view_type], 'bounds_changed', function(){
        var bnds = maps[view_type].getBounds();
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

    maps[view_type].enableKeyDragZoom({
        key: 'shift',
        visualEnabled: true
    });

    var dz = maps[view_type].getDragZoomObject();

    google.maps.event.addListener(dz, 'dragend', function (bnds) {
        maps[view_type].setCenter(bnds.getCenter());
        maps[view_type].setZoom(getBoundsZoomLevel(bnds, mapDim));
        var ne = bnds.getNorthEast();
        var sw = bnds.getSouthWest();
        document.getElementById("id_NElng").value = ne.lng();
        document.getElementById("id_NElat").value = ne.lat();
        document.getElementById("id_SWlng").value = sw.lng();
        document.getElementById("id_SWlat").value = sw.lat();

    });

    var zoom_listener = google.maps.event.addListener(maps[view_type], 'zoom_changed', function(){
        updateMapView(view_type);
    });

    var drag_listener = google.maps.event.addListener(maps[view_type], 'dragend', function(){
        updateMapView(view_type);
    });


    generateLegend(view_type);

    var input_address = document.getElementById(geocoder_address_id);
    var autocomplete = new google.maps.places.Autocomplete(input_address);

    var geocoder = new google.maps.Geocoder();
    document.getElementById(geocoder_submit_id).addEventListener('click', function() {
        geocodeAddress(geocoder, maps[view_type], mapDim, view_type);
    });
};

var setMarkers = function(json_results) {
    var modified_points_data = [];
    for (var i = 0; i < json_results.length; i++ ) {
        if (json_results[i].coverage_type == 'point') {
            checkDuplicatePointResults(modified_points_data, json_results[i]);
        }
    }
    modified_points_data.forEach(function(point){
        createPointResourceMarker(point);
    });
    markers_cluster = new MarkerClusterer(maps["point_map"], markers, {
        styles:[{
            height: 55,
            width: 56,
            url: '//cdn.rawgit.com/googlemaps/js-marker-clusterer/gh-pages/images/m2.png'
        }]
    });
};

var setBoxes = function(json_results) {

    var modified_boxes_data = [];
    var boxes_data = [];
    for (var i = 0; i < json_results.length; i++ ) {
        if (json_results[i].coverage_type == 'box') {
            checkDuplicateBoxResults(modified_boxes_data, json_results[i]);
            boxes_data.push(json_results[i]);
        }
    }

    modified_boxes_data.forEach(function(box){
        createBoxResourceMarker (box);
    });
    drawShadeRectangles(boxes_data);

    box_centers_cluster = new MarkerClusterer(maps["area_map"], box_centers, {
        styles:[{
            height: 55,
            width: 56,
            url: '//cdn.rawgit.com/googlemaps/js-marker-clusterer/gh-pages/images/m2.png'
        }]
    });
};

var drawShadeRectangles = function(boxes) {
    for (var i = 0; i < boxes.length; i++) {
        var box = boxes[i];
        var northlimit = parseFloat(box.northlimit);
        var southlimit = parseFloat(box.southlimit);
        var eastlimit = parseFloat(box.eastlimit);
        var westlimit = parseFloat(box.westlimit);

        var rectCoords = [
            {lat: northlimit, lng: westlimit},
            {lat: northlimit, lng: (westlimit + eastlimit)/2},
            {lat: northlimit, lng: eastlimit},
            {lat: southlimit, lng: eastlimit},
            {lat: southlimit, lng: (westlimit + eastlimit)/2},
            {lat: southlimit, lng: westlimit}
        ];

        shade_rects[i] = {
            rect: new google.maps.Polygon({
                    paths: [rectCoords],
                    strokeColor: '#FF0000',
                    strokeOpacity: 0.35,
                    strokeWeight: 2,
                    fillColor: '#FF0000',
                    fillOpacity: 0,
                    clickable: false
                    }),
            checked: false,
            rect_id: box.short_id
        };

        shade_rects[i].rect.setMap(maps["area_map"]);

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

        if (latLng == null || resource_bound.contains(latLng)) {
            var author_name = "";
            if (resource.first_author_description) {
                author_name = '<a target="_blank" href="' + resource.first_author_description + '">' + resource.first_author + '</a>';
            } else {
                author_name = resource.first_author;
            }
            var resource_title = '<a target="_blank" href="' + resource.get_absolute_url + '">' + resource.title + '</a>';
            var map_resource = [resource.short_id, resource, resource.resource_type, resource_title, author_name];
            map_resources.push(map_resource);
        }
    });

};

var buildMapItemsTableDataforMarkers = function (resources_list, map_resources) {
    resources_list.forEach(function(resource) {
        var author_name = "";
        if (resource.first_author_description) {
            author_name = '<a target="_blank" href="' + resource.first_author_description + '">' + resource.first_author + '</a>';
        } else {
            author_name = resource.first_author;
        }
        var resource_title = '<a target="_blank" href="' + resource.get_absolute_url + '">' + resource.title + '</a>';
        var map_resource = [resource.short_id, resource, resource.resource_type, resource_title, author_name];
        map_resources.push(map_resource);
    });
};


var setMapItemsList = function(json_results, view_type, latLng) {
    var map_resources = [];
    var map_item_id = "";
    if (view_type == "area_map") {
        map_item_id = "#area-map-items";
        buildMapItemsTableData(json_results, map_resources, latLng);
    } else {
        map_item_id = "#point-map-items";
        buildMapItemsTableDataforMarkers(json_results, map_resources, latLng);
    }
    var mapItems = $(map_item_id).DataTable( {
        data: map_resources,
        "scrollY": "200px",
        "scrollCollapse": true,
        "paging": false,
        "bDestroy": true,
        "language": {
            "emptyTable": "Click on map to explore resource data."
        },
        "columnDefs": [
        {
            'targets': [0],
            'searchable':false,
            'orderable':false,
            'width':"1%",
            'data': null,
            'className': "dt-body-center",
            'render': function (data, type, full, meta){
                return '<input type="checkbox">';
            }
        },
        {
            "targets": [1],
            "width": "60px",
            "data": null,
            "defaultContent": '<a class="btn btn-default" role="button"><span class="glyphicon glyphicon-zoom-in"></span></button>'
        },
        {
           "targets": [2],     // Resource type
            "width": "60px"
        },
        {
           "targets": [4],     // First author
            "width": "70px"
        }]
    });
    if (view_type == "area_map") {
        setMapFunctions(mapItems, "area_map");
    } else {
        setMapFunctions(mapItems, "point_map");
    }
};

var setMapFunctions = function (datatable, view_type) {
    if (view_type == "area_map") {
        $('#area-map-items tbody').on('click', '[role="button"]', function () {
            var data = datatable.row($(this).parents('tr')).data();
            showBoxOnMap(data[1], true);
        });
        $('#area-map-items tbody').on('hover', 'tr', function () {
            var data = datatable.row(this).data();
            if (data) {
                showBoxOnMap(data[1], false);
            }
        });

        $('#area-map-items tbody').on('change', 'input[type="checkbox"]', function(e){
            var $row = $(this).closest('tr');
            var data = datatable.row($row).data();
            //console.log(datatable.row($row).index());
            if (this.checked) {
                highlightOrHideBox(data[1], 0);
                //datatable.row(datatable.row($row).index()).scrollTo();
            } else {
                highlightOrHideBox(data[1], 1);
            }
            // Update state of "Select all" control
            updateDataTableSelectAllCtrl(datatable, view_type);
        });

        // Handle click on "Select all" control
        $('thead input[name="select_all"]', datatable.table().container()).on('click', function(e){
            if(this.checked){
                $('#area-map-items tbody input[type="checkbox"]:not(:checked)').trigger('click');
            } else {
                $('#area-map-items tbody input[type="checkbox"]:checked').trigger('click');
            }
            updateDataTableSelectAllCtrl(datatable, view_type);
        });

    } else {
        $('#point-map-items tbody').on('click', '[role="button"]', function () {
            var data = datatable.row($(this).parents('tr')).data();
            showPointMarker(data[1]);
        });
        // Handle click on checkbox
        $('#point-map-items tbody').on('change', 'input[type="checkbox"]', function(e){
            var $row = $(this).closest('tr');

            var data = datatable.row($row).data();
            if (this.checked) {
                popMarkerWindow(data[0], 0);
            } else {
                popMarkerWindow(data[0], 1);
            }
            // Update state of "Select all" control
            updateDataTableSelectAllCtrl(datatable, view_type);

        });

        // Handle click on table cells with checkboxes


        // Handle click on "Select all" control
        $('thead input[name="select_all"]', datatable.table().container()).on('click', function(e){
            if(this.checked){
                $('#point-map-items tbody input[type="checkbox"]:not(:checked)').trigger('click');
            } else {
                $('#point-map-items tbody input[type="checkbox"]:checked').trigger('click');
            }
            updateDataTableSelectAllCtrl(datatable, view_type);
        });

    }

};

var updateDataTableSelectAllCtrl = function(table, view_type) {
    var $table             = table.table().node();
    var $chkbox_all        = $('tbody input[type="checkbox"]', $table);
    var $chkbox_checked    = $('tbody input[type="checkbox"]:checked', $table);

    var select_all_id = "";
    if (view_type == "point_map") {
        select_all_id = "#point_select_all";
    } else {
        select_all_id = "#area_select_all";
    }

    var chkbox_select_all = $(select_all_id)[0];
    if($chkbox_checked.length === 0){
        chkbox_select_all.checked = false;
        if('indeterminate' in chkbox_select_all){
            chkbox_select_all.indeterminate = false;
        }

    // If all of the checkboxes are checked
    } else if ($chkbox_checked.length === $chkbox_all.length){
        chkbox_select_all.checked = true;
        if('indeterminate' in chkbox_select_all){
            chkbox_select_all.indeterminate = false;
        }

    // If some of the checkboxes are checked
    } else {
        chkbox_select_all.checked = true;
        if('indeterminate' in chkbox_select_all){
            chkbox_select_all.indeterminate = true;
        }
    }
};

var highlightOrHideBox = function(target, option) {
    shade_rects.forEach(function(box) {
        var rect = box.rect;
        if (box.rect_id == target.short_id) {
            if (option == 0) {
                rect.setOptions({fillOpacity: 0.15});
                box.checked = true;
            } else {
                rect.setOptions({fillOpacity: 0});
                box.checked = false;
            }
        }
    });
};

var popMarkerWindow = function(point_id, option) {
    for(var i = 0; i < markers.length; i++){
        if(markers[i].short_id == point_id) {
            if (option == 0){
                markers[i].info_window.open(maps["point_map"], markers[i]);
            } else {
                markers[i].info_window.close();
            }
            break;
        }
    }
}

var showBoxOnMap = function(box, zoom_on_map) {
    var northlimit = parseFloat(box.northlimit);
    var southlimit = parseFloat(box.southlimit);
    var eastlimit = parseFloat(box.eastlimit);
    var westlimit = parseFloat(box.westlimit);
    var view_type = "area_map";
    var rectBounds = new google.maps.LatLngBounds(
            new google.maps.LatLng(southlimit, westlimit),
            new google.maps.LatLng(northlimit, eastlimit)
    );

    if (zoom_on_map) {
        maps["area_map"].fitBounds(rectBounds);
        updateMapView(view_type);

        var map_items_table = $('#area-map-items').DataTable();
        map_items_table.rows().every( function (rowIdx, tableLoop, rowLoop ) {
            var data = this.data();
            var resource_id = data[0];
            var node_data = this.node();
            if (box.short_id == resource_id) {
                $(node_data).find("input[type=checkbox]:not(:checked)").trigger("click");
            }

        });
    } else {

        findShadeRectById(box);
    }
};

var showPointMarker = function(point) {
    var bounds = new google.maps.LatLngBounds();
    var north = parseFloat(point.north);
    var east = parseFloat(point.east);
    var lat_lng = new google.maps.LatLng(north, east);
    bounds.extend(lat_lng);
    maps["point_map"].fitBounds(bounds);
}

var clientUpdateMarkers = function(filtered_results, view_type) {
    var coverage_type = "";
    if (view_type == "point_map") {
        removeMarkers();
        coverage_type = "point";
    } else {
        removeBoxes();
        coverage_type = "box";
    }
    var bnds = maps[view_type].getBounds();
    if (bnds) {
        if (coverage_type == "point") {
            for (var  i = 0; i < raw_point_results.length; i++ ) {
                var data_lat = parseFloat(raw_point_results[i].north);
                var data_lng = parseFloat(raw_point_results[i].east);
                var latlng = new google.maps.LatLng(data_lat, data_lng);
                if (bnds.contains(latlng)) {
                    filtered_results.push(raw_point_results[i]);
                }
            }
        } else {
            for (var  i = 0; i < raw_box_results.length; i++ ) {
                var northlimit = parseFloat(raw_box_results[i].northlimit);
                var southlimit =  parseFloat(raw_box_results[i].southlimit);
                var eastlimit = parseFloat(raw_box_results[i].eastlimit);
                var westlimit = parseFloat(raw_box_results[i].westlimit);
                var ne_latlng = new google.maps.LatLng(northlimit, eastlimit);
                var sw_latlng = new google.maps.LatLng(southlimit, westlimit);
                var box_bound = new google.maps.LatLngBounds(sw_latlng, ne_latlng);
                if (bnds.intersects(box_bound)) {
                    filtered_results.push(raw_box_results[i]);
                }
            }
        }
    }
};


var removeBoxes = function() {
    if (box_centers_cluster) {
        box_centers_cluster.clearMarkers(box_centers);
    }
    for (var i = 0; i < box_centers.length; i++) {
        if (box_centers[i].getMap() != null) {
            box_centers[i].setMap(null);
        }
    }

    box_centers = [];

    for (var n = 0; n < shade_rects.length; n++) {
        if (shade_rects[n].rect.getMap() != null) {
            shade_rects[n].rect.setMap(null);
        }
        shade_rects[n].checked = false;
    }
    shade_rects = [];

}

var removeMarkers = function() {

    if (markers_cluster) {
        markers_cluster.clearMarkers(markers);
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
            item.info_link = item.info_link + '<br />' + '<a target="_blank" href="' + test.get_absolute_url + '">' + test.title +'</a>';
            item.counter++;
            item.resources_list.push(test);
            existed = true;
        }
    });
    if (!existed) {
        test.resources_list = [];
        test.resources_list.push(test);
        test.info_link = '<a target="_blank" href="' + test.get_absolute_url + '">' + test.title + '</a>';
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
            item.info_link = item.info_link + '<br />' + '<a target="_blank" href="' + test.get_absolute_url + '">' + test.title + '</a>';
            item.counter++;
            item.resources_list.push(test);
            existed = true;
        }
    });
    if (!existed) {
        test.resources_list = [];
        test.resources_list.push(test);
        test.info_link = '<a target="_blank" href="' + test.get_absolute_url + '">' + test.title + '</a>';
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
    var marker =  new google.maps.Marker({
        map: maps["point_map"],
        icon: '//cdn.rawgit.com/Concept211/Google-Maps-Markers/master/images/marker_blue' + counter + '.png',
        position: latlng,
        short_id: point.short_id
    });

    marker.info_window = new google.maps.InfoWindow({
        content: info_content
    });

    markers.push(marker);

    var map_items_table = $('#point-map-items').DataTable();
    google.maps.event.addListener(marker, 'click', function() {
        marker.info_window.open(maps["point_map"], marker);

        map_items_table.rows().every( function (rowIdx, tableLoop, rowLoop ) {
            var data = this.data();
            var resource_id = data[0];
            var node_data = this.node();
            if (resource_id == marker.short_id) {
                $(node_data).find("input[type=checkbox]:not(:checked)").trigger("click");
            }

        });


    });

    google.maps.event.addListener(marker.info_window,'closeclick',function(){

        map_items_table.rows().every( function (rowIdx, tableLoop, rowLoop ) {
            var data = this.data();
            var resource_id = data[0];
            var node_data = this.node();
            if (resource_id == marker.short_id) {
                $(node_data).find("input[type=checkbox]:checked").trigger("click");
            }

        });
    });
};

var createBoxResourceMarker = function(box) {

    var info_content = box.info_link;
    var northlimit = parseFloat(box.northlimit);
    var southlimit = parseFloat(box.southlimit);
    var eastlimit = parseFloat(box.eastlimit);
    var westlimit = parseFloat(box.westlimit);
    var counter = box.counter.toString();
    var lat = (parseFloat(northlimit) + parseFloat(southlimit)) / 2;
    var lng = (parseFloat(eastlimit) + parseFloat(westlimit)) / 2;
    var latlng = new google.maps.LatLng(lat, lng);
    var resources_ids = [];
    box.resources_list.forEach(function(resource){
        resources_ids.push(resource.short_id);
    });


    var box_center = new google.maps.Marker({
        map: maps["area_map"],
        icon: '//cdn.rawgit.com/Concept211/Google-Maps-Markers/master/images/marker_red' + counter + '.png',
        position: latlng
    });

    box_center.info_window = new google.maps.InfoWindow({
        content: info_content
    });

    box_centers.push(box_center);

    var map_items_table = $('#area-map-items').DataTable();

    google.maps.event.addListener(box_center, 'click', function() {
        createBoundsForResources(box.resources_list);
        updateMapView("area_map");

        box_center.info_window.open(maps["area_map"], box_center);
        map_items_table.rows().every( function (rowIdx, tableLoop, rowLoop ) {
            var data = this.data();
            var resource_id = data[0];
            var node_data = this.node();
            if (resources_ids.indexOf(resource_id) > -1) {
                $(node_data).find("input[type=checkbox]:not(:checked)").trigger("click");
            }

        });

    });

    google.maps.event.addListener(box_center.info_window,'closeclick',function(){
        map_items_table.rows().every( function (rowIdx, tableLoop, rowLoop ) {
            var data = this.data();
            var resource_id = data[0];
            var node_data = this.node();
            if (resources_ids.indexOf(resource_id) > -1) {
                $(node_data).find("input[type=checkbox]:checked").trigger("click");
            }

        });
    });


};

var createBoundsForResources = function (resources_list) {
    var bounds = new google.maps.LatLngBounds();

    resources_list.forEach(function(resource){
        var northlimit = parseFloat(resource.northlimit);
        var southlimit = parseFloat(resource.southlimit);
        var eastlimit = parseFloat(resource.eastlimit);
        var westlimit = parseFloat(resource.westlimit);
        var rectBounds = new google.maps.LatLngBounds(
            new google.maps.LatLng(southlimit, westlimit),
            new google.maps.LatLng(northlimit, eastlimit)
        );
        bounds.union(rectBounds);

    });
    maps["area_map"].fitBounds(bounds);
};

var createBoundsForMarkers = function(markers, view_type) {
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

var generateLegend = function(view_type) {
    var map_legends = document.getElementsByClassName('discover-map-legend');
    var geo_coder = "";
    var reset_zoom_buttons = document.getElementsByClassName('resetZoom');

    if (view_type == "point_map") {
        maps[view_type].controls[google.maps.ControlPosition.RIGHT_TOP].push(map_legends[0]);
        maps[view_type].controls[google.maps.ControlPosition.RIGHT_BOTTOM].push(reset_zoom_buttons[0]);
        geo_coder = document.getElementById('point-geocoder-panel');

    } else {
        maps[view_type].controls[google.maps.ControlPosition.RIGHT_TOP].push(map_legends[1]);
        maps[view_type].controls[google.maps.ControlPosition.RIGHT_BOTTOM].push(reset_zoom_buttons[1]);
        geo_coder = document.getElementById('area-geocoder-panel');

    }
    maps[view_type].controls[google.maps.ControlPosition.LEFT_BOTTOM].push(geo_coder);
    var point_geocoder_content = [];
    var area_geocoder_content = [];
    var point_resetButton_content = [];
    var area_resetButton_content = [];
    var legend_table = "<table><tbody>";
    legend_table += "<tr><td class='text-center'><img src='/static/img/discover_map_blue_marker.png'></td><td>Point Coverage Locations</td></tr>";
    legend_table += "<tr><td class='text-center'><img src='/static/img/discover_map_red_marker.png'></td><td>Box Coverage Centers</td></tr>";
    legend_table += "<tr><td class='text-center'><img src='/static/img/discover_map_cluster_icon.png'></td><td>Clusters</td></tr></tbody></table>";

    point_geocoder_content.push("<input id='point-geocoder-address' type='textbox' placeholder='Search Locations...'>");
    point_geocoder_content.push("<a id='point-geocoder-submit' style='margin-left:10px' class='btn btn-default' role='button'><span class='glyphicon glyphicon-zoom-in'></span> Go </a>");

    area_geocoder_content.push("<input id='area-geocoder-address' type='textbox' placeholder='Search Locations...'>");
    area_geocoder_content.push("<a id='area-geocoder-submit' style='margin-left:10px' class='btn btn-default' role='button'><span class='glyphicon glyphicon-zoom-in'></span> Go </a>");

    point_resetButton_content.push("<a data-toggle='tooltip' title='Reset Zoom' class='btn btn-default btn-sm' onclick='resetMapZoom(0)'>");
    point_resetButton_content.push("<span class='glyphicon glyphicon-fullscreen'></span></a>");

    area_resetButton_content.push("<a data-toggle='tooltip' title='Reset Zoom' class='btn btn-default btn-sm' onclick='resetMapZoom(1)'>");
    area_resetButton_content.push("<span class='glyphicon glyphicon-fullscreen'></span></a>");

    if (view_type == "point_map") {
        map_legends[0].innerHTML = legend_table;
        reset_zoom_buttons[0].innerHTML = point_resetButton_content.join('');
        geo_coder.innerHTML = point_geocoder_content.join('');
    } else {
        map_legends[1].innerHTML = legend_table;
        reset_zoom_buttons[1].innerHTML = area_resetButton_content.join('');
        geo_coder.innerHTML = area_geocoder_content.join('');
    }
};

var geocodeAddress = function(geocoder, resultsMap, mapDim, view_type) {
    var geocoder_address_input = "";
    if (view_type == "point_map") {
        geocoder_address_input = "point-geocoder-address";
    } else {
        geocoder_address_input = "area-geocoder-address";
    }
    var address = document.getElementById(geocoder_address_input).value;
    geocoder.geocode({'address': address}, function(results, status) {
        if (status === google.maps.GeocoderStatus.OK) {
            resultsMap.setCenter(results[0].geometry.location);
            resultsMap.setZoom(getBoundsZoomLevel(results[0].geometry.bounds, mapDim));
            updateMapView(view_type);
        } else {
            alert('Geocode was not successful for the following reason: ' + status);
        }
    });
};

var resetMapZoom = function(option) {
    var view_type = "";
    var datatableId = "";
    var map_view_option = "";
    var map_resources = [];
    if (option == 0) {
        view_type = "point_map";
        datatableId = "#point-map-items";
        map_view_option = "#discover-point-map";
        removeMarkers();
        setMarkers(raw_point_results);
        buildMapItemsTableDataforMarkers(raw_point_results, map_resources, null);

    } else {
        view_type = "area_map";
        datatableId = "#area-map-items";
        map_view_option = "#discover-area-map";
        removeBoxes();
        setBoxes(raw_box_results);
        buildMapItemsTableData(raw_box_results, map_resources, null);
    }



    var map_items_table = $(datatableId).DataTable();
    map_items_table.clear();
    map_items_table.rows.add(map_resources);
    map_items_table.draw();

    var $mapDiv = $(map_view_option);
    var mapDim = {
        height: $mapDiv.height(),
        width: $mapDiv.width()
    };

    var bounds = null;
    if (view_type == "point_map") {
        bounds = (markers.length > 0) ? createBoundsForMarkers(markers, view_type) : maps[view_type].setZoom(2);
    } else {
        bounds = (box_centers.length > 0) ? createBoundsForMarkers(box_centers, view_type) : maps[view_type].setZoom(2);
    }
    maps[view_type].fitBounds(bounds);
    var zoom_level = getBoundsZoomLevel(bounds, mapDim);
    var reset_center = bounds.getCenter();
    if (bounds) {
        maps[view_type].fitBounds(bounds);
        var listener = google.maps.event.addListener(maps[view_type], "idle", function () {
            maps[view_type].setZoom(zoom_level);
            maps[view_type].setCenter(reset_center);
            google.maps.event.removeListener(listener);
        });
    } else {
        maps[view_type].setZoom(map_default_zoom);
    }
};


var updateMapView = function(view_type) {
    var filtered_results = [];
    clientUpdateMarkers(filtered_results, view_type);
    var map_resources = [];
    if (view_type == "point_map") {
        setMarkers(filtered_results);
        buildMapItemsTableDataforMarkers(filtered_results, map_resources, null);
        var map_items_table = $('#point-map-items').DataTable();
        map_items_table.clear();
        map_items_table.rows.add(map_resources);
        map_items_table.draw();
        select_all_id = "#point_select_all";
    } else {
        setBoxes(filtered_results);
        buildMapItemsTableData(filtered_results, map_resources, null);
        var map_items_table = $('#area-map-items').DataTable();
        map_items_table.clear();
        map_items_table.rows.add(map_resources);
        map_items_table.draw();
        select_all_id = "#area_select_all";
    }

    var chkbox_select_all = $(select_all_id)[0];
    chkbox_select_all.checked = false;
    chkbox_select_all.indeterminate = false;

    current_map_bounds = maps[view_type].getBounds();
    current_map_center = maps[view_type].getCenter();
    current_map_zoom = maps[view_type].getZoom();
    map_set = true;
};

var updateListView = function (data) {
    var requestURL = "/search/";

    if (window.location.search.length == 0) {
        requestURL += "?q=";
    } else {
        var textSearch = $("#id_q").val();
        var searchURL = "?q=" + textSearch;
        requestURL += searchURL;
        requestURL += buildURLOnCheckboxes();
    }
    $("#discover-list-loading-spinner").show();
    $.ajax({
        type: "GET",
        url: requestURL,
        data: data,
        dataType: 'html',
        success: function (data) {
            $('#items-discovered_wrapper').empty();
            $("#discover-page-options").empty();
            var tableDiv = $("#items-discovered", data);
            $("#items-discovered_wrapper").html(tableDiv);
            var pageOptionDiv = $("#discover-page-options", data);
            $("#discover-page-options").html(pageOptionDiv);

            initializeTable();
            $("#discover-list-loading-spinner").hide();
        },
        failure: function (data) {
            console.error("Ajax call for updating list-view data failed");
            $("#discover-list-loading-spinner").hide();
        }
    });
};

var updateFacetingItems = function (request_url) {
    $("#discover-list-loading-spinner").show();
    if (maps["area_map"] != null) {
        $("#discover-area-map-loading-spinner").show();
        $.when(updateMapFaceting("area_map")).done(function(){
            $("#discover-area-map-loading-spinner").hide();
        });
    }

    if (maps["point_map"] != null) {
        $("#discover-point-map-loading-spinner").show();
        $.when(updateMapFaceting("point_map")).done(function(){
            $("#discover-point-map-loading-spinner").hide();
        });
    }

    $.when(updateListFaceting(request_url)).done(function(){
        $("#discover-list-loading-spinner").hide();
    });
};

var updateListFaceting = function (request_url) {
    return $.ajax({
        type: "GET",
        url: request_url,
        dataType: 'html',
        success: function (data) {
            $('#items-discovered_wrapper').empty();
            $("#discover-page-options").empty();
            var tableDiv = $("#items-discovered", data);
            $("#items-discovered_wrapper").html(tableDiv);
            var pageOptionDiv = $("#discover-page-options", data);
            $("#discover-page-options").html(pageOptionDiv);
            initializeTable();
        },
        failure: function (data) {
            console.error("Ajax call for updating list-view data failed");
        }
    });
};

var updateMapFaceting = function (view_type){
    var map_update_url = "/searchjson/";
    var textSearch = $("#id_q").val();
    var searchURL = "?q=" + textSearch;
    map_update_url += searchURL;
    map_update_url += buildURLOnCheckboxes();
    var start_date = $("#id_start_date").val();
    var end_date = $("#id_end_date").val();
    var coverage_type = "";
    if (view_type == "point_map") {
        removeMarkers();
        coverage_type = "point";
    } else {
        removeBoxes();
        coverage_type = "box";
    }
    return $.ajax({
        type: "GET",
        url: map_update_url,
        data: {
            NElat: '',
            NElng: '',
            SWlat: '',
            SWlng: '',
            start_date: start_date,
            end_date: end_date,
            coverage_type: coverage_type
        },
        dataType: 'json',
        success: function (data) {
            if (view_type == "point") {
                raw_point_results = [];
                for (var j = 0; j < data.length; j++) {
                    var item = $.parseJSON(data[j]);
                    raw_point_results.push(item);
                }
            } else {
                raw_box_results = [];
                for (var j = 0; j < data.length; j++) {
                    var item = $.parseJSON(data[j]);
                    raw_box_results.push(item);
                }
            }
            updateMapView(view_type);


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

var findShadeRectById = function(target) {
    shade_rects.forEach(function(box) {
        var rect = box.rect;
        if (box.rect_id == target.short_id) {
            rect.setOptions({fillOpacity: 0.15});
        } else if (!box.checked) {
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
    var faceted_fields = ['creators', 'subjects', 'resource_type', 'owners_names',
        'variable_names', 'sample_mediums', 'units_names', 'availability'];
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
    return "&start_date="+start_date+"&end_date="+end_date;
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
    var windowPath = window.location.pathname;
    var requestURL =  windowPath + searchURL + facetingParams + geoSearchParams + dateSearchParams;
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
    var DATE_CREATED_SORT_COL = 4;
    var LAST_MODIFIED_COL = 5;
    var LAST_MODIF_SORT_COL = 6;

    var colDefs = [
        {
            "targets": [RESOURCE_TYPE_COL],     // Resource type
            "width": "110px"
        },
        {
            "targets": [DATE_CREATED_COL],     // Date created
            "iDataSort": DATE_CREATED_SORT_COL
        },
        {
            "targets": [LAST_MODIFIED_COL],     // Last modified
            "iDataSort": LAST_MODIF_SORT_COL
        },
        {
            "targets": [LAST_MODIF_SORT_COL],     // Last modified (for sorting)
            "visible": false
        },
        {
            "targets": [DATE_CREATED_SORT_COL],     // Last modified (for sorting)
            "visible": false
        }
    ];

    $('#items-discovered').DataTable({
        "paging": false,
        "searching": false,
        "info": false,
        "order": [[TITLE_COL, "asc"]],
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
            var windowPath = window.location.pathname;
            var requestURL =  windowPath + searchURL + geoSearchParams + dateSearchParams;
            window.location = requestURL;
        }
    });

    $("#covereage-search-fields input, #date-search-fields input, #id_q").addClass("form-control");

    $("title").text("Discover | HydroShare");   // Set browser tab title

    initializeTable();
    popCheckboxes();

    $("ul.nav-tabs > li > a").on("shown.bs.tab", function (e) {
        var tabId = $(e.target).attr("href").substr(1);
        window.location.hash = tabId;
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
        if (tabId == "map-area-view") {
            if(maps["area_map"] == null){
                $("#discover-area-map-loading-spinner").show();
                $.ajax({
                    type: "GET",
                    url: requestURL,
                    data: {
                        NElat: "",
                        NElng: "",
                        SWlat: "",
                        SWlng: "",
                        start_date: start_date,
                        end_date: end_date,
                        coverage_type: "box"
                    },
                    dataType: 'json',
                    success: function (data) {
                        var json_box_results = [];
                        for (var j = 0; j < data.length; j++) {
                            var item = $.parseJSON(data[j]);
                            json_box_results.push(item);
                            raw_box_results.push(item);
                        }
                        initMap(json_box_results, "area_map");
                        setMapItemsList(json_box_results, "area_map",null);
                        $("#resource-search").show();
                        $("#discover-area-map-loading-spinner").hide();
                        if (maps["point_map"] == null) {
                            map_set = true;
                        }
                    },
                    failure: function(data) {
                        $("#discover-area-map-loading-spinner").hide();
                        console.error("Ajax call for getting map data failed");
                    }
                });
            } else {
                if (maps["point_map"] != null && map_set) {
                    var current_map_bounds1 = maps["point_map"].getBounds();
                    var current_map_center1 = maps["point_map"].getCenter();
                    var current_map_zoom1 = maps["point_map"].getZoom();
                    maps["area_map"].fitBounds(current_map_bounds1);
                    maps["area_map"].setCenter(current_map_center1);
                    maps["area_map"].setZoom(current_map_zoom1);
                    map_set = false;
                }
            }
        } else if (tabId == "map-point-view") {
            if (maps["point_map"] == null) {
                $("#discover-point-map-loading-spinner").show();
                $.ajax({
                    type: "GET",
                    url: requestURL,
                    data: {
                        NElat: "",
                        NElng: "",
                        SWlat: "",
                        SWlng: "",
                        start_date: start_date,
                        end_date: end_date,
                        coverage_type: "point"
                    },
                    dataType: 'json',
                    success: function (data) {
                        var json_point_results = [];
                        for (var j = 0; j < data.length; j++) {
                            var item = $.parseJSON(data[j]);
                            json_point_results.push(item);
                            raw_point_results.push(item);
                        }
                        initMap(json_point_results, "point_map");
                        setMapItemsList(json_point_results, "point_map", null);
                        $("#discover-point-map-loading-spinner").hide();
                        if (maps["area_map"] == null) {
                            map_set = true;
                        }
                    },
                    failure: function(data) {
                        $("#discover-point-map-loading-spinner").hide();
                        console.error("Ajax call for getting map data failed");
                    }
                });
            } else {
                if (maps["area_map"] != null && map_set) {
                    var current_map_bounds2 = maps["area_map"].getBounds();
                    var current_map_center2 = maps["area_map"].getCenter();
                    var current_map_zoom2 = maps["area_map"].getZoom();
                    maps["point_map"].fitBounds(current_map_bounds2);
                    maps["point_map"].setCenter(current_map_center2);
                    maps["point_map"].setZoom(current_map_zoom2);
                    map_set = false;
                }
            }
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

    function updateResults () {
        var textSearch = $("#id_q").val();
        var searchURL = "?q=" + textSearch;
        searchURL += buildURLOnCheckboxes();
        var geoSearchParams = formGeoParameters();
        var dateSearchParams = formDateParameters();
        var windowPath = window.location.pathname;
        var requestURL = windowPath + searchURL + geoSearchParams + dateSearchParams;
        if (window.location.hash) {
            requestURL = requestURL + window.location.hash;
        }
        window.location = requestURL;
    }

    $("#date-search-fields input").change(function () {
        updateResults();
    });

    $(".faceted-selections").click(function () {
        var textSearch = $("#id_q").val();
        var searchURL = "?q=" + textSearch;
        var geoSearchParams = formGeoParameters();
        var dateSearchParams = formDateParameters();
        var windowPath = window.location.pathname;
        var requestURL =  windowPath + searchURL;
        if($(this).is(":checked")) {
            requestURL += buildURLOnCheckboxes();
            var checkboxId = $(this).attr("id");
            var sessionStorageCheckboxId = 'search-' + checkboxId;
            sessionStorage[sessionStorageCheckboxId] = 'true';
            requestURL = requestURL + geoSearchParams + dateSearchParams;
            updateFacetingItems(requestURL);
        }
        else {
            var checkboxId = $(this).attr("id");
            var sessionStorageCheckboxId = 'search-' + checkboxId;
            sessionStorage.removeItem(sessionStorageCheckboxId);
            var updateURL =  windowPath + searchURL + buildURLOnCheckboxes() + geoSearchParams + dateSearchParams;
            updateFacetingItems(updateURL);
        }
    });


    $("#solr-help-info").popover({
        html: true,
        container: '#body',
        content: '<p>Search here to find all public and discoverable resources. This search box supports <a href="https://cwiki.apache.org/confluence/display/solr/Searching" target="_blank">SOLR Query syntax</a>.</p>',
        trigger: 'click'
    });

    $("#btn-show-all").click(clearAllFaceted);
    $("#clear-dates-options").click(clearDates);
});
