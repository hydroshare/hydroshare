const minFloatingNumber = 0.0001;
let map = null;
let map_default_bounds = null;
let map_default_zoom = 2;
let map_default_center = new google.maps.LatLng(0, 0);
let markers = [];
let raw_results = [];
let markerCluster = null;
let info_window = null;
let shade_rects = [];

const initMap = function (json_results) {
  const $mapDiv = $('#discover-map');
  const mapDim = {
    height: $mapDiv.height(),
    width: $mapDiv.width(),
  };

  map = new google.maps.Map($mapDiv[0], {
    zoom: map_default_zoom,
    mapTypeId: google.maps.MapTypeId.TERRAIN,
  });

  info_window = new google.maps.InfoWindow();

  setMarkers(json_results);
  const bounds = (markers.length > 0) ? createBoundsForMarkers(markers) : map.setZoom(2);
  if (bounds) {
    const ne = bounds.getNorthEast();
    const sw = bounds.getSouthWest();
    document.getElementById('id_NElat').value = ne.lat();
    document.getElementById('id_NElng').value = ne.lng();
    document.getElementById('id_SWlat').value = sw.lat();
    document.getElementById('id_SWlng').value = sw.lng();
    map_default_bounds = bounds;
    map.fitBounds(map_default_bounds);
    map_default_zoom = getBoundsZoomLevel(map_default_bounds, mapDim);
    map_default_center = map_default_bounds.getCenter();
  }

  var idle_listener = google.maps.event.addListener(map, 'idle', () => {
    map.setCenter(map_default_center);
    map.setZoom(map_default_zoom);
    google.maps.event.removeListener(idle_listener);
  });

  const bounds_listener = google.maps.event.addListener(map, 'bounds_changed', () => {
    const bnds = map.getBounds();
    if (bnds) {
      const ne = bnds.getNorthEast();
      const sw = bnds.getSouthWest();
      document.getElementById('id_NElng').value = ne.lng();
      document.getElementById('id_NElat').value = ne.lat();
      document.getElementById('id_SWlng').value = sw.lng();
      document.getElementById('id_SWlat').value = sw.lat();
      setLatLngLabels();
    }
  });

  map.enableKeyDragZoom({
    key: 'shift',
    visualEnabled: true,
  });

  const dz = map.getDragZoomObject();

  google.maps.event.addListener(dz, 'dragend', (bnds) => {
    map.setCenter(bnds.getCenter());
    map.setZoom(getBoundsZoomLevel(bnds, mapDim));
    const ne = bnds.getNorthEast();
    const sw = bnds.getSouthWest();
    document.getElementById('id_NElng').value = ne.lng();
    document.getElementById('id_NElat').value = ne.lat();
    document.getElementById('id_SWlng').value = sw.lng();
    document.getElementById('id_SWlat').value = sw.lat();
  });

  const zoom_listener = google.maps.event.addListener(map, 'zoom_changed', () => {
    updateMapView();
    const map_items_table = $('#map-items').DataTable();
    map_items_table.clear().draw();
  });

  const drag_listener = google.maps.event.addListener(map, 'dragend', () => {
    updateMapView();
    const map_items_table = $('#map-items').DataTable();
    map_items_table.clear().draw();
  });


  generateLegend();

  const input_address = document.getElementById('geocoder-address');
  const autocomplete = new google.maps.places.Autocomplete(input_address);

  const geocoder = new google.maps.Geocoder();
  document.getElementById('geocoder-submit').addEventListener('click', () => {
    geocodeAddress(geocoder, map, mapDim);
  });

  google.maps.event.addListener(map, 'click', (e) => {
    const map_items_table = $('#map-items').DataTable();
    map_items_table.clear().draw();
    shade_rects.forEach((rect) => {
      rect.setOptions({ fillOpacity: 0 });
    });
  });
};


var setMarkers = function (json_results) {
  const modified_points_data = [];
  const modified_boxes_data = [];
  const boxes_data = [];
  for (let i = 0; i < json_results.length; i++) {
    if (json_results[i].coverage_type == 'point') {
      checkDuplicatePointResults(modified_points_data, json_results[i]);
    } else if (json_results[i].coverage_type == 'box') {
      checkDuplicateBoxResults(modified_boxes_data, json_results[i]);
      boxes_data.push(json_results[i]);
    }
  }

  modified_points_data.forEach((point) => {
    createPointResourceMarker(point);
  });

  modified_boxes_data.forEach((box) => {
    createBoxResourceMarker(box);
  });

  drawShadeRectangles(boxes_data);

  shade_rects.forEach((rect) => {
    google.maps.event.addListener(rect, 'click', (e) => {
      highlightOverlapping(e.latLng);
      const map_resources = [];
      buildMapItemsTableData(boxes_data, map_resources, e.latLng);
      const map_items_table = $('#map-items').DataTable();
      map_items_table.clear();
      map_items_table.rows.add(map_resources);
      map_items_table.draw();
    });
  });
  markerCluster = new MarkerClusterer(map, markers, {
    styles: [{
      height: 55,
      width: 56,
      url: '/static/img/m2.png',
    }],
  });
};

var highlightOverlapping = function (position) {
  shade_rects.forEach((rect) => {
    const rect_bound = new google.maps.LatLngBounds();
    calShadeRectBounds(rect, rect_bound);
    if (rect_bound.contains(position)) {
      rect.setOptions({ fillOpacity: 0.15 });
    } else {
      rect.setOptions({ fillOpacity: 0 });
    }
  });
};

var drawShadeRectangles = function (boxes) {
  for (let i = 0; i < boxes.length; i++) {
    const box = boxes[i];
    const northlimit = parseFloat(box.northlimit);
    const southlimit = parseFloat(box.southlimit);
    const eastlimit = parseFloat(box.eastlimit);
    const westlimit = parseFloat(box.westlimit);

    const rectCoords = [
      { lat: northlimit, lng: westlimit },
      { lat: northlimit, lng: (westlimit + eastlimit) / 2 },
      { lat: northlimit, lng: eastlimit },
      { lat: southlimit, lng: eastlimit },
      { lat: southlimit, lng: (westlimit + eastlimit) / 2 },
      { lat: southlimit, lng: westlimit },
    ];

    shade_rects[i] = new google.maps.Polygon({
      paths: [rectCoords],
      strokeColor: '#FF0000',
      strokeOpacity: 0.15,
      strokeWeight: 2,
      fillColor: '#FF0000',
      fillOpacity: 0,
    });

    shade_rects[i].setMap(map);
  }
};


var buildMapItemsTableData = function (box_resources, map_resources, latLng) {
  box_resources.forEach((resource) => {
    const northlimit = parseFloat(resource.northlimit);
    const southlimit = parseFloat(resource.southlimit);
    const eastlimit = parseFloat(resource.eastlimit);
    const westlimit = parseFloat(resource.westlimit);
    const ne_latlng = new google.maps.LatLng(northlimit, eastlimit);
    const sw_latlng = new google.maps.LatLng(southlimit, westlimit);
    const resource_bound = new google.maps.LatLngBounds(sw_latlng, ne_latlng);
    if (resource_bound.contains(latLng)) {
      let author_name = '';
      if (resource.first_author_url) {
        author_name = `<a target="_blank" href="${resource.first_author_url}">${resource.first_author}</a>`;
      } else {
        author_name = resource.first_author;
      }
      const resource_title = `<a target="_blank" href="${resource.get_absolute_url}">${resource.title}</a>`;
      const map_resource = [resource, resource.resource_type, resource_title, author_name];
      map_resources.push(map_resource);
    }
  });
};

const buildMapItemsTableDataforMarkers = function (resources_list, map_resources) {
  resources_list.forEach((resource) => {
    const northlimit = parseFloat(resource.northlimit);
    const southlimit = parseFloat(resource.southlimit);
    const eastlimit = parseFloat(resource.eastlimit);
    const westlimit = parseFloat(resource.westlimit);
    const ne_latlng = new google.maps.LatLng(northlimit, eastlimit);
    const sw_latlng = new google.maps.LatLng(southlimit, westlimit);
    const resource_bound = new google.maps.LatLngBounds(sw_latlng, ne_latlng);
    let author_name = '';
    if (resource.first_author_url) {
      author_name = `<a target="_blank" href="${resource.first_author_url}">${resource.first_author}</a>`;
    } else {
      author_name = resource.first_author;
    }
    const resource_title = `<a target="_blank" href="${resource.get_absolute_url}">${resource.title}</a>`;
    const map_resource = [resource, resource.resource_type, resource_title, author_name];
    map_resources.push(map_resource);
  });
};

const setMapItemsList = function (json_results, latLng) {
  const map_resources = [];
  buildMapItemsTableData(json_results, map_resources, latLng);

  const mapItems = $('#map-items').DataTable({
    data: map_resources,
    scrollY: '200px',
    scrollCollapse: true,
    paging: false,
    bDestroy: true,
    language: {
      emptyTable: 'Click on map to explore resource data.',
    },
    columns: [
      { title: 'Show on Map' },
      { title: 'Resource Type' },
      { title: 'Title' },
      { title: 'First Author' },
    ],
    columnDefs: [{
      targets: [0],
      width: '90px',
      data: null,
      defaultContent: '<a class="btn btn-default" role="button"><span class="glyphicon glyphicon-zoom-in"></span></button>',
    },
    {
      targets: [1], // Resource type
      width: '110px',
    }],
  });
  setMapFunctions(mapItems);
};

var setMapFunctions = function (datatable) {
  $('#map-items tbody').on('click', '[role="button"]', function () {
    const data = datatable.row($(this).parents('tr')).data();
    showBoxMarker(data[0], true);
  });
  $('#map-items tbody').on('hover', 'tr', function () {
    const data = datatable.row(this).data();
    if (data) {
      showBoxMarker(data[0], false);
    }
  });
};

var showBoxMarker = function (box, zoom_on_map) {
  const northlimit = parseFloat(box.northlimit);
  const southlimit = parseFloat(box.southlimit);
  const eastlimit = parseFloat(box.eastlimit);
  const westlimit = parseFloat(box.westlimit);

  const rectBounds = new google.maps.LatLngBounds(
    new google.maps.LatLng(southlimit, westlimit),
    new google.maps.LatLng(northlimit, eastlimit),
  );

  if (zoom_on_map) {
    map.fitBounds(rectBounds);
    updateMapView();
    let author_name = '';
    if (box.first_author_url) {
      author_name = `<a target="_blank" href="${box.first_author_url}">${box.first_author}</a>`;
    } else {
      author_name = box.first_author;
    }
    const resource_title = `<a target="_blank" href="${box.get_absolute_url}">${box.title}</a>`;
    const map_resource = [box, box.resource_type, resource_title, author_name];
    const map_items_table = $('#map-items').DataTable();
    map_items_table.row.add(map_resource).draw();
  }
  findShadeRect(rectBounds);
};

const clientUpdateMarkers = function (filtered_results) {
  removeMarkers();
  const bnds = map.getBounds();
  if (bnds) {
    for (let i = 0; i < raw_results.length; i++) {
      if (raw_results[i].coverage_type == 'point') {
        const data_lat = parseFloat(raw_results[i].north);
        const data_lng = parseFloat(raw_results[i].east);
        const latlng = new google.maps.LatLng(data_lat, data_lng);
        if (bnds.contains(latlng)) {
          filtered_results.push(raw_results[i]);
        }
      } else if (raw_results[i].coverage_type == 'box') {
        const northlimit = parseFloat(raw_results[i].northlimit);
        const southlimit = parseFloat(raw_results[i].southlimit);
        const eastlimit = parseFloat(raw_results[i].eastlimit);
        const westlimit = parseFloat(raw_results[i].westlimit);
        const ne_latlng = new google.maps.LatLng(northlimit, eastlimit);
        const sw_latlng = new google.maps.LatLng(southlimit, westlimit);
        const box_bound = new google.maps.LatLngBounds(sw_latlng, ne_latlng);
        if (bnds.intersects(box_bound)) {
          filtered_results.push(raw_results[i]);
        }
      }
    }
  }
};

var removeMarkers = function () {
  for (let n = 0; n < shade_rects.length; n++) {
    if (shade_rects[n].getMap() != null) {
      shade_rects[n].setMap(null);
    }
  }
  shade_rects = [];

  if (markerCluster) {
    markerCluster.clearMarkers(markers);
  }
  for (let i = 0; i < markers.length; i++) {
    if (markers[i].getMap() != null) {
      markers[i].setMap(null);
    }
  }
  markers = [];
};

var checkDuplicatePointResults = function (modified_points_data, test) {
  const test_lat = parseFloat(test.north);
  const test_lng = parseFloat(test.east);
  let existed = false;
  modified_points_data.forEach((item) => {
    const item_lat = parseFloat(item.north);
    const item_lng = parseFloat(item.east);

    const lat_diff = Math.abs(test_lat - item_lat);
    const lng_diff = Math.abs(test_lng - item_lng);
    if (lat_diff < minFloatingNumber && lng_diff < minFloatingNumber) {
      item.info_link = `${item.info_link}<br />` + `<a href="${test.get_absolute_url}">${test.title}</a>`;
      item.counter++;
      item.resources_list.push(test);
      existed = true;
    }
  });
  if (!existed) {
    test.resources_list = [];
    test.resources_list.push(test);
    test.info_link = `<a href="${test.get_absolute_url}">${test.title}</a>`;
    test.counter = 1;
    modified_points_data.push(test);
  }
};

var checkDuplicateBoxResults = function (modified_boxes_data, test) {
  const test_lat = (parseFloat(test.northlimit) + parseFloat(test.southlimit)) / 2;
  const test_lng = (parseFloat(test.eastlimit) + parseFloat(test.westlimit)) / 2;
  let existed = false;
  modified_boxes_data.forEach((item) => {
    const item_lat = (parseFloat(item.northlimit) + parseFloat(item.southlimit)) / 2;
    const item_lng = (parseFloat(item.eastlimit) + parseFloat(item.westlimit)) / 2;

    const lat_diff = Math.abs(test_lat - item_lat);
    const lng_diff = Math.abs(test_lng - item_lng);

    if (lat_diff < minFloatingNumber && lng_diff < minFloatingNumber) {
      item.info_link = `${item.info_link}<br />` + `<a href="${test.get_absolute_url}">${test.title}</a>`;
      item.counter++;
      item.resources_list.push(test);
      existed = true;
    }
  });
  if (!existed) {
    test.resources_list = [];
    test.resources_list.push(test);
    test.info_link = `<a href="${test.get_absolute_url}">${test.title}</a>`;
    test.counter = 1;
    modified_boxes_data.push(test);
  }
};

var createPointResourceMarker = function (point) {
  const info_content = point.info_link;
  const lat = parseFloat(point.north);
  const lng = parseFloat(point.east);
  const counter = point.counter.toString();
  const latlng = new google.maps.LatLng(lat, lng);
  const marker = new google.maps.Marker({
    map,
    icon: `//raw.githubusercontent.com/Concept211/Google-Maps-Markers/master/images/marker_red${counter}.png`,
    position: latlng,
  });
  markers.push(marker);
  google.maps.event.addListener(marker, 'click', () => {
    const map_resources = [];
    buildMapItemsTableDataforMarkers(point.resources_list, map_resources);
    const map_items_table = $('#map-items').DataTable();
    map_items_table.clear();
    map_items_table.rows.add(map_resources);
    map_items_table.draw();
    info_window.setContent(info_content);
    info_window.open(map, marker);
  });
};

var createBoxResourceMarker = function (box) {
  const info_content = box.info_link;
  const northlimit = parseFloat(box.northlimit);
  const southlimit = parseFloat(box.southlimit);
  const eastlimit = parseFloat(box.eastlimit);
  const westlimit = parseFloat(box.westlimit);
  const counter = box.counter.toString();
  const lat = (parseFloat(northlimit) + parseFloat(southlimit)) / 2;
  const lng = (parseFloat(eastlimit) + parseFloat(westlimit)) / 2;
  const latlng = new google.maps.LatLng(lat, lng);

  const marker = new google.maps.Marker({
    map,
    icon: `//raw.githubusercontent.com/Concept211/Google-Maps-Markers/master/images/marker_blue${counter}.png`,
    position: latlng,
  });
  markers.push(marker);

  google.maps.event.addListener(marker, 'click', () => {
    const map_resources = [];
    buildMapItemsTableDataforMarkers(box.resources_list, map_resources);
    const map_items_table = $('#map-items').DataTable();
    map_items_table.clear();
    map_items_table.rows.add(map_resources);
    map_items_table.draw();
    info_window.setContent(info_content);
    info_window.open(map, marker);
    const rectBounds = new google.maps.LatLngBounds(
      new google.maps.LatLng(southlimit, westlimit),
      new google.maps.LatLng(northlimit, eastlimit),
    );
    findShadeRect(rectBounds);
  });
};

var createBoundsForMarkers = function (markers) {
  const bounds = new google.maps.LatLngBounds();
  $.each(markers, function () {
    bounds.extend(this.getPosition());
  });
  return bounds;
};

var getBoundsZoomLevel = function (bounds, mapDim) {
  const WORLD_DIM = { height: 256, width: 256 };
  const ZOOM_MAX = 21;

  function latRad(lat) {
    const sin = Math.sin(lat * Math.PI / 180);
    const radX2 = Math.log((1 + sin) / (1 - sin)) / 2;
    return Math.max(Math.min(radX2, Math.PI), -Math.PI) / 2;
  }

  function zoom(mapPx, worldPx, fraction) {
    return Math.floor(Math.log(mapPx / worldPx / fraction) / Math.LN2);
  }

  const ne = bounds.getNorthEast();
  const sw = bounds.getSouthWest();

  const latFraction = (latRad(ne.lat()) - latRad(sw.lat())) / Math.PI;

  const lngDiff = ne.lng() - sw.lng();
  const lngFraction = ((lngDiff < 0) ? (lngDiff + 360) : lngDiff) / 360;

  const latZoom = zoom(mapDim.height, WORLD_DIM.height, latFraction);
  const lngZoom = zoom(mapDim.width, WORLD_DIM.width, lngFraction);

  return Math.min(latZoom, lngZoom, ZOOM_MAX);
};

var generateLegend = function () {
  const map_legend = document.getElementById('discover-map-legend');
  const geo_coder = document.getElementById('geocoder-panel');
  const reset_zoom_button = document.getElementById('resetZoom');
  map.controls[google.maps.ControlPosition.RIGHT_TOP].push(map_legend);
  map.controls[google.maps.ControlPosition.LEFT_BOTTOM].push(geo_coder);
  map.controls[google.maps.ControlPosition.RIGHT_BOTTOM].push(reset_zoom_button);
  const geocoder_content = [];
  const resetButton_content = [];
  let legend_table = '<table><tbody>';
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

var geocodeAddress = function (geocoder, resultsMap, mapDim) {
  const address = document.getElementById('geocoder-address').value;
  geocoder.geocode({ address }, (results, status) => {
    if (status === google.maps.GeocoderStatus.OK) {
      resultsMap.setCenter(results[0].geometry.location);
      resultsMap.setZoom(getBoundsZoomLevel(results[0].geometry.bounds, mapDim));
      updateMapView();
      const map_items_table = $('#map-items').DataTable();
      map_items_table.clear().draw();
    } else {
      alert(`Geocode was not successful for the following reason: ${status}`);
    }
  });
};

const resetMapZoom = function () {
  removeMarkers();
  setMarkers(raw_results);
  const map_items_table = $('#map-items').DataTable();
  map_items_table.clear().draw();
  const $mapDiv = $('#discover-map');
  const mapDim = {
    height: $mapDiv.height(),
    width: $mapDiv.width(),
  };

  const bounds = (markers.length > 0) ? createBoundsForMarkers(markers) : map.setZoom(2);
  map.fitBounds(bounds);
  const zoom_level = getBoundsZoomLevel(bounds, mapDim);
  const reset_center = bounds.getCenter();
  if (bounds) {
    map.fitBounds(bounds);
    var listener = google.maps.event.addListener(map, 'idle', () => {
      map.setZoom(zoom_level);
      map.setCenter(reset_center);
      google.maps.event.removeListener(listener);
    });
  } else {
    map.setZoom(map_default_zoom);
  }
};

var updateMapView = function () {
  const filtered_results = [];
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

const updateListItems = function (request_url) {
  // TODO: not sure why we need list spinner when map is visible?
  // From Alva: Sometimes this loading can take a while.
  $('#discover-list-loading-spinner').show();
  if (map != null) {
    $('#discover-map-loading-spinner').show();
    $.when(updateMapFaceting(), updateListFaceting(request_url)).done(() => {
      $('#discover-list-loading-spinner').hide();
      $('#discover-map-loading-spinner').hide();
    });
  } else {
    $.when(updateListFaceting(request_url)).done(() => {
      $('#discover-list-loading-spinner').hide();
    });
  }
};

var updateListFaceting = function (request_url) {
  return $.ajax({
    type: 'GET',
    url: request_url,
    dataType: 'html',
    success(data) {
      $('#items-discovered_wrapper').empty();
      $('#discover-page-options-1').empty();
      $('#discover-page-options-2').empty();
      const tableDiv = $('#items-discovered', data);
      $('#items-discovered_wrapper').html(tableDiv);
      const pageOptionDiv1 = $('#discover-page-options-1', data);
      $('#discover-page-options-1').html(pageOptionDiv1);
      const pageOptionDiv2 = $('#discover-page-options-2', data);
      $('#discover-page-options-2').html(pageOptionDiv2);
      initializeTable();
    },
    failure(data) {
      console.error('Ajax call for updating list-view data failed');
    },
  });
};

var updateMapFaceting = function () {
  let map_update_url = '/searchjson/';
  const textSearch = $('#id_q').val();
  const searchURL = `?q=${textSearch}`;
  map_update_url += searchURL;
  map_update_url += buildURLOnCheckboxes();
  const start_date = $('#id_start_date').val();
  const end_date = $('#id_end_date').val();
  removeMarkers();
  return $.ajax({
    type: 'GET',
    url: map_update_url,
    data: {
      NElat: '',
      NElng: '',
      SWlat: '',
      SWlng: '',
      start_date,
      end_date,
    },
    dataType: 'json',
    success(data) {
      raw_results = [];
      for (let j = 0; j < data.length; j++) {
        const item = $.parseJSON(data[j]);
        raw_results.push(item);
      }

      updateMapView();
      const map_items_table = $('#map-items').DataTable();
      map_items_table.clear().draw();
    },
    failure(data) {
      console.error('Ajax call for getting map data failed');
    },
  });
};

var calShadeRectBounds = function (rect, shade_rect_bound) {
  rect.getPaths().getArray().forEach((path) => {
    path.getArray().forEach((latlng) => {
      shade_rect_bound.extend(latlng);
    });
  });
};

var findShadeRect = function (rectBounds) {
  let found = 0;
  shade_rects.forEach((rect) => {
    const shade_rect_bound = new google.maps.LatLngBounds();
    calShadeRectBounds(rect, shade_rect_bound);
    if (rectBounds.equals(shade_rect_bound) && found == 0) {
      rect.setOptions({ fillOpacity: 0.35 });
      found = 1;
    } else {
      rect.setOptions({ fillOpacity: 0 });
    }
  });
};

var setLatLngLabels = function () {
  const ne_lat = `${parseFloat(document.getElementById('id_NElat').value).toFixed(3)}°`;
  const ne_lng = `${parseFloat(document.getElementById('id_NElng').value).toFixed(3)}°`;
  const sw_lat = `${parseFloat(document.getElementById('id_SWlat').value).toFixed(3)}°`;
  const sw_lng = `${parseFloat(document.getElementById('id_SWlng').value).toFixed(3)}°`;
  jQuery("label[for='ne-lat-value']").html(ne_lat);
  jQuery("label[for='ne-lng-value']").html(ne_lng);
  jQuery("label[for='sw-lat-value']").html(sw_lat);
  jQuery("label[for='sw-lng-value']").html(sw_lng);
};

const reorderDivs = function () {
  const faceted_fields = ['creator', 'contributor', 'owner',
    'resource_type', 'subject', 'availability'];
  const div_ordering = [];
  faceted_fields.forEach((field) => {
    const faceting_div = `faceting-${field}`;
    div_ordering.push(faceting_div);
  });
  let i;
  for (i = 1; i < div_ordering.length; i++) {
    const div0 = `#${div_ordering[i - 1]}`;
    const div1 = `#${div_ordering[i]}`;
    $(div1).insertAfter(div0);
  }
};

const formGeoParameters = function () {
  const selected_results = $('input[name=results-selection]:checked').val();
  const geoSearchParams = '&NElat=&NElng=&SWlat=&SWlng=';
  return geoSearchParams;
};

const formDateParameters = function () {
  const start_date = $('#id_start_date').val();
  const end_date = $('#id_end_date').val();
  // if (start_date <= end_date or not start_date or not end_date) {
  return `&start_date=${start_date}&end_date=${end_date}`;
  // }
};

const formOrderParameters = function () {
  const sort_order = $('#id_sort_order').val();
  const sort_direction = $('#id_sort_direction').val();
  return `&sort_order=${sort_order}&sort_direction=${sort_direction}`;
};

var buildURLOnCheckboxes = function () {
  let requestURL = '';
  $('.faceted-selections').each(function () {
    const checkboxId = $(this).attr('id');
    const sessionStorageCheckboxId = `search-${checkboxId}`;
    if (document.getElementById(checkboxId).checked) {
      const arr = $(this).val().split(',');
      const key = arr[0];
      const value = arr[1];
      requestURL += `&selected_facets=${key}_exact:${value}`;
    }
  });
  return requestURL;
};

const popCheckboxes = function () {
  $('.faceted-selections').each(function () {
    const checkboxId = $(this).attr('id');
    const sessionStorageCheckboxId = `search-${checkboxId}`;
    const val = sessionStorage[sessionStorageCheckboxId];
    const isChecked = val !== undefined ? val == 'true' : false;
    $(this).prop('checked', isChecked);
  });
};

const clearCheckboxes = function () {
  $('.faceted-selections').each(function () {
    const checkboxId = $(this).attr('id');
    const sessionStorageCheckboxId = `search-${checkboxId}`;
    sessionStorage[sessionStorageCheckboxId] = 'false';
    sessionStorage.removeItem(sessionStorageCheckboxId);
  });
};

const clearAllFaceted = function () {
  clearCheckboxes();
  const clearURL = '/search/';
  window.location = clearURL;
};

const clearDates = function () {
  const textSearch = $('#id_q').val();
  const searchURL = `?q=${textSearch}`;
  const geoSearchParams = formGeoParameters();
  const facetingParams = buildURLOnCheckboxes();
  const dateSearchParams = '&start_date=&end_date=';
  const sortOrderParams = formOrderParameters();
  const windowPath = window.location.pathname;
  let requestURL = windowPath + searchURL + facetingParams + geoSearchParams
        + dateSearchParams + sortOrderParams;
  if (window.location.hash) {
    requestURL += window.location.hash;
  }
  window.location = requestURL;
};

function initializeTable() {
  const RESOURCE_TYPE_COL = 0;
  const TITLE_COL = 1;
  const OWNER_COL = 2;
  const DATE_CREATED_COL = 3;
  const LAST_MODIFIED_COL = 4;

  const colDefs = [
    {
      targets: [RESOURCE_TYPE_COL], // Resource type
      width: '110px',
    },
    {
      targets: [DATE_CREATED_COL], // Date created
    },
    {
      targets: [LAST_MODIFIED_COL], // Last modified
    },
  ];

  $('#items-discovered').DataTable({
    paging: false,
    searching: false,
    info: false,
    ordering: false,
    // "order": [[TITLE_COL, "asc"]],
    columnDefs: colDefs,
  });
}

$(document).ready(() => {
  $('#id_start_date').datepicker({
    dateFormat: 'mm/dd/yy',
    changeMonth: true,
    changeYear: true,
    yearRange: '1950:',
  });
  $('#id_end_date').datepicker({
    dateFormat: 'mm/dd/yy',
    changeMonth: true,
    changeYear: true,
    yearRange: '1950:',
  });

  if (window.location.search.length == 0) {
    clearCheckboxes();
  }
  $('.search-field').keypress((event) => {
    if (event.which == 13) {
      event.preventDefault();
      clearCheckboxes();
      const textSearch = $('#id_q').val();
      const searchURL = `?q=${textSearch}`;
      const geoSearchParams = formGeoParameters();
      const dateSearchParams = formDateParameters();
      const sortOrderParams = formOrderParameters();
      const windowPath = window.location.pathname;
      const requestURL = windowPath + searchURL + geoSearchParams
                + dateSearchParams + sortOrderParams;
      window.location = requestURL;
    }
  });

  $('#covereage-search-fields input, #date-search-fields input, #id_q').addClass('form-control');
  $('#search-order-fields select').addClass('form-control');

  initializeTable();
  popCheckboxes();

  $('ul.nav-tabs > li > a').on('shown.bs.tab', (e) => {
    const tabId = $(e.target).attr('href').substr(1);
    window.location.hash = tabId;
    if (tabId == 'map-view' && map == null) {
      let requestURL = '/searchjson/';
      const textSearch = $('#id_q').val();
      const searchURL = `?q=${textSearch}`;
      requestURL += searchURL;
      requestURL += buildURLOnCheckboxes();
      const ne_lat = document.getElementById('id_NElat').value;
      const ne_lng = document.getElementById('id_NElng').value;
      const sw_lat = document.getElementById('id_SWlat').value;
      const sw_lng = document.getElementById('id_SWlng').value;
      const start_date = $('#id_start_date').val();
      const end_date = $('#id_end_date').val();
      $('#discover-map-loading-spinner').show();
      $.ajax({
        type: 'GET',
        url: requestURL,
        data: {
          NElat: ne_lat,
          NElng: ne_lng,
          SWlat: sw_lat,
          SWlng: sw_lng,
          start_date,
          end_date,
        },
        dataType: 'json',
        success(data) {
          const json_results = [];
          for (let j = 0; j < data.length; j++) {
            const item = $.parseJSON(data[j]);
            json_results.push(item);
            raw_results.push(item);
          }
          initMap(json_results);
          setMapItemsList([], null);
          $('#resource-search').show();
          $('#discover-map-loading-spinner').hide();
        },
        failure(data) {
          $('#discover-map-loading-spinner').hide();
          console.error('Ajax call for getting map data failed');
        },
      });
    }
  });

  $('.nav-tabs a').click(function () {
    $(this).tab('show');
  });

  // on load of the page: switch to the currently selected tab
  const { hash } = window.location;
  $(`#switch-view a[href="${hash}"]`).tab('show');

  $('#id_q').attr('placeholder', 'Search All Public and Discoverable Resources');
  reorderDivs();

  $('.collapse').on('shown.bs.collapse', function () {
    $(this).parent().find('.glyphicon-plus').removeClass('glyphicon-plus')
      .addClass('glyphicon-minus');
  }).on('hidden.bs.collapse', function () {
    $(this).parent().find('.glyphicon-minus').removeClass('glyphicon-minus')
      .addClass('glyphicon-plus');
  });

  // This forces a page reload and should only be done when updating queries
  function updateResults() {
    const textSearch = $('#id_q').val();
    let searchURL = `?q=${textSearch}`;
    searchURL += buildURLOnCheckboxes();
    const geoSearchParams = formGeoParameters();
    const dateSearchParams = formDateParameters();
    const sortOrderParams = formOrderParameters();
    const windowPath = window.location.pathname;
    let requestURL = windowPath + searchURL + geoSearchParams + dateSearchParams
            + sortOrderParams;
    if (window.location.hash) {
      requestURL += window.location.hash;
    }
    window.location = requestURL;
  }

  $('#date-search-fields input').change(() => {
    const textSearch = $('#id_q').val();
    const searchURL = `?q=${textSearch}`;
    const geoSearchParams = formGeoParameters();
    const dateSearchParams = formDateParameters();
    const sortOrderParams = formOrderParameters();
    const windowPath = window.location.pathname;
    let requestURL = windowPath + searchURL;
    requestURL = requestURL + geoSearchParams + dateSearchParams + sortOrderParams;
    updateListItems(requestURL);
  });

  $('#search-order-fields select').change(() => {
    const textSearch = $('#id_q').val();
    const searchURL = `?q=${textSearch}`;
    const geoSearchParams = formGeoParameters();
    const dateSearchParams = formDateParameters();
    const sortOrderParams = formOrderParameters();
    const windowPath = window.location.pathname;
    let requestURL = windowPath + searchURL;
    requestURL = requestURL + geoSearchParams + dateSearchParams + sortOrderParams;
    updateListItems(requestURL);
  });
});
