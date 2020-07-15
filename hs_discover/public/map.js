((exports) => {
  const mapDefaultZoom = 4; // TODO set back to 2 to match HydroShare
  // eslint-disable-next-line no-unused-vars
  let infowindow;
  let googMarkers = [];
  let markerCluster;

  const deleteMarkers = () => {
    googMarkers.forEach((marker) => {
      marker.setMap(null);
    });
    googMarkers = [];
  };

  const createSearcher = () => {
    const searchBox = new google.maps.places.SearchBox(document.getElementById('map-search'));
    exports.map.controls[google.maps.ControlPosition.TOP_CENTER].push(document.getElementById('map-search'));
    // Bias the SearchBox results towards current map's viewport.
    exports.map.addListener('bounds_changed', function () {
      searchBox.setBounds(exports.map.getBounds());
    });

    let markers = [];
    // Listen for the event fired when the user selects a prediction and retrieve
    // more details for that place.
    searchBox.addListener('places_changed', function () {
      const places = searchBox.getPlaces();

      if (places.length === 0) {
        return;
      }

      // Clear out the old markers.
      markers.forEach(function (marker) {
        marker.setMap(null);
      });
      markers = [];

      // For each place, get the icon, name and location.
      const bounds = new google.maps.LatLngBounds();
      places.forEach(function (place) {
        if (!place.geometry) {
          console.log('Returned place contains no geometry');
          return;
        }
        const icon = {
          url: place.icon,
          size: new google.maps.Size(71, 71),
          origin: new google.maps.Point(0, 0),
          anchor: new google.maps.Point(17, 34),
          scaledSize: new google.maps.Size(25, 25),
        };

        // Create a marker for each place.
        markers.push(new google.maps.Marker({
          map: exports.map,
          icon: icon,
          title: place.name,
          position: place.geometry.location,
        }));

        if (place.geometry.viewport) {
          // Only geocodes have viewport.
          bounds.union(place.geometry.viewport);
        } else {
          bounds.extend(place.geometry.location);
        }
      });
      exports.map.fitBounds(bounds);
    });
    return searchBox;
  };

  const createLegend = () => {
    const legend = document.getElementById('discover-map-legend');
    exports.map.controls[google.maps.ControlPosition.RIGHT_TOP].push(legend);
    let legendTable = '<table><tbody>';
    legendTable += "<tr><td class='text-center'><img src='/static/img/discover_map_red_marker.png'>"
      + '</td><td>Point Coverage Locations</td></tr>';
    legendTable += "<tr><td class='text-center'><img src='/static/img/discover_map_blue_marker.png'>"
      + '</td><td>Box Coverage Centers</td></tr>';
    legendTable += "<tr><td class='text-center'><img src='/static/img/discover_map_cluster_icon.png'>"
      + '</td><td>Clusters</td></tr></tbody></table>';
    legend.innerHTML = legendTable;
    return legend;
  };

  const createMarker = (loc, title) => {
    const addmarker = new google.maps.Marker({
      // icon: './images/pin.png',
      // zIndex: i,
      map: exports.map,
      position: loc,
    });
    google.maps.event.addListener(addmarker, 'mouseover', function () {
      infowindow.setContent(title);
      infowindow.open(exports.map, this);
    });
    google.maps.event.addListener(addmarker, 'mouseout', function () {
      infowindow.close();
    });
    googMarkers.push(addmarker);
    markerCluster = new MarkerClusterer(exports.map, googMarkers,
      { imagePath: 'https://developers.google.com/maps/documentation/javascript/examples/markerclusterer/m' });
  };

  const toggleMap = () => {
    document.getElementById('map-view').style.display = document.getElementById('map-view').style.display === 'block' ? 'none' : 'block';
  };

  const initMap = () => {
    infowindow = new google.maps.InfoWindow();
    // eslint-disable-next-line no-param-reassign
    exports.map = new google.maps.Map(document.getElementById('map'), {
      center: {
        lat: 42,
        lng: -71,
      },
      zoom: mapDefaultZoom,
      mapTypeId: google.maps.MapTypeId.TERRAIN,
    });
    // https://stackoverflow.com/questions/29869261/google-map-search-box
    const mapLegend = createLegend();
    const searchBox = createSearcher();
    exports.map.addListener('zoom_changed', function() {
      markerCluster = new MarkerClusterer(exports.map, googMarkers,
        { imagePath: 'https://developers.google.com/maps/documentation/javascript/examples/markerclusterer/m' });
    });
  };
  exports.initMap = initMap; // eslint-disable-line
  exports.createMarker = createMarker; // eslint-disable-line
  exports.toggleMap = toggleMap; // eslint-disable-line
  exports.deleteMarkers = deleteMarkers; // eslint-disable-line
})(this.window = this.window || {});
