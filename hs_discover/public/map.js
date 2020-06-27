((exports) => {
  const mapDefaultZoom = 4; // TODO set back to 2 to match HydroShare
  const point = { info_link: '', lat: 42, lng: -71 };
  let service;
  let infowindow;

  function createMarker(place) {
    const marker = new google.maps.Marker({
      map: exports.map,
      position: place.geometry.location,
    });

    google.maps.event.addListener(marker, 'click', function() {
      infowindow.setContent(place.name);
      infowindow.open(exports.map, this);
    });
  }

  const initMap = () => {
    infowindow = new google.maps.InfoWindow();
    // eslint-disable-next-line no-param-reassign
    exports.map = new google.maps.Map(document.getElementById('map'), {
      center: {
        lat: point.lat,
        lng: point.lng,
      },
      zoom: mapDefaultZoom,
      mapTypeId: google.maps.MapTypeId.TERRAIN,
    });
    // https://stackoverflow.com/questions/29869261/google-map-search-box
    const mapLegend = document.getElementById('discover-map-legend');
    // const geoCoder = document.getElementById('geocoder-panel');
    const resetZoomButton = document.getElementById('reset-zoom');
    // const geoCoderContent = [];
    const resetButtonContent = [];
    const searchBox = new google.maps.places.SearchBox(document.getElementById('map-search'));
    exports.map.controls[google.maps.ControlPosition.TOP_CENTER].push(document.getElementById('map-search'));
    exports.map.controls[google.maps.ControlPosition.RIGHT_TOP].push(mapLegend);
    // exports.map.controls[google.maps.ControlPosition.LEFT_BOTTOM].push(geoCoder);
    exports.map.controls[google.maps.ControlPosition.RIGHT_BOTTOM].push(resetZoomButton);
    let legendTable = '<table><tbody>';
    legendTable += "<tr><td class='text-center'><img src='/static/img/discover_map_red_marker.png'></td><td>Point Coverage Locations</td></tr>";
    // legendTable += "<tr><td class='text-center'><img src='/static/img/discover_map_blue_marker.png'></td><td>Box Coverage Centers</td></tr>";
    // legendTable += "<tr><td class='text-center'><img src='/static/img/discover_map_cluster_icon.png'></td><td>Clusters</td></tr></tbody></table>";
    // geoCoderContent.push("<input id='geocoder-address' type='textbox' placeholder='Search Locations...'>");
    // geoCoderContent.push("<a id='geocoder-submit' style='margin-left:10px' class='btn btn-default' role='button'><span class='glyphicon glyphicon-zoom-in'></span> Go </a>");
    resetButtonContent.push("<a id='reset-zoom-btn' data-toggle='tooltip' title='Reset Zoom' class='btn btn-default btn-sm' onclick='resetMapZoom()'>");
    resetButtonContent.push("<span class='glyphicon glyphicon-fullscreen'></span></a>");
    mapLegend.innerHTML = legendTable;
    // geoCoder.innerHTML = geoCoderContent.join('');
    resetZoomButton.innerHTML = resetButtonContent.join('');

    const locations = [{ lat: 39, lng: -75 }, { lat: 42, lng: -71 }];

    const markers = locations.map((location, i) => {
      return new google.maps.Marker({
        // icon: './images/pin.svg',
        position: location,
        zIndex: i,
        map: exports.map,
      });
    });

    // axios.get('/discoverapi/', { params: { searchtext: 'abc' } })
    //   .then((response) => {
    //     console.log(JSON.parse(response.data.resources));
    //   })
    //   .catch((error) => {
    //     console.error(error); // eslint-disable-line
    //   });

    const request = {
      query: 'Atlanta georgia',
      fields: ['name', 'geometry'],
    };

    service = new google.maps.places.PlacesService(exports.map);

    service.findPlaceFromQuery(request, (results, status) => {
      if (status === google.maps.places.PlacesServiceStatus.OK) {
        for (let i = 0; i < results.length; i++) {
          createMarker(results[i]);
        }
        exports.map.setCenter(results[0].geometry.location);
      } else {
        console.log(status);
      }
    });

    // Add event listeners to the markers
    // eslint-disable-next-line array-callback-return,no-unused-vars
    // markers.map((marker, i) => {
    //   marker.addListener('mouseover', () => {
    //     toggleIcon(marker, true);
    //   });
    //   marker.addListener('mouseout', () => {
    //     toggleIcon(marker, false);
    //   });
    // });
    axios.get('/discoverapi/', { params: { searchtext: 'good' } })
      .then((response) => {
        console.log(JSON.parse(response.data.resources));
      })
      .catch((error) => {
        console.error(error); // eslint-disable-line
      });

    const setMarkers = function(jsonResults) {
      let modifiedPointsData = [];
      let modifiedBoxesData = [];
      let boxesData = [];
      jsonResults.forEach((x) => {
        console.log(x);
      });
      // shade_rects.forEach(function(rect){
      //     google.maps.event.addListener(rect,'click',function(e){
      //         highlightOverlapping(e.latLng);
      //         var map_resources = [];
      //         buildMapItemsTableData(boxes_data, map_resources, e.latLng);
      //         var map_items_table = $('#map-items').DataTable();
      //         map_items_table.clear();
      //         map_items_table.rows.add(map_resources);
      //         map_items_table.draw();
      //     });
      // });
    };

    // Create Resource Point marker function

    // const latlng = new google.maps.LatLng(point.lat, point.lng);
    // const counter = 0;
    //
    // const marker = new google.maps.Marker({
    //   position: latlng,
    //   map: exports.map,
    //   title: 'Hello World!',
    // });

    // const marker = new google.maps.Marker({
    //   map: exports.map,
    //   icon: '//raw.githubusercontent.com/Concept211/Google-Maps-Markers/master/images/marker_red' + counter + '.png',
    //   position: latlng,
    // });

    // google.maps.event.addListener(marker, 'click', function() {
    //     var map_resources = [];
    //     buildMapItemsTableDataforMarkers(point.resources_list, map_resources);
    //     var map_items_table = $('#map-items').DataTable();
    //     map_items_table.clear();
    //     map_items_table.rows.add(map_resources);
    //     map_items_table.draw();
    //     info_window.setContent(info_content);
    //     info_window.open(map, marker);
    // });
  //     const markerCluster = new MarkerClusterer(exports.map, markers, {
  //         styles: [{
  //             height: 55,
  //             width: 56,
  //             url: '/static/img/m2.png'
  //         }]
  //     });
  // };
  };
  console.log('routine end');
  exports.initMap = initMap; // eslint-disable-line
})(this.window = this.window || {});
