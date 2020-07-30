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
    if (markerCluster) {
      markerCluster.clearMarkers();
    }
  };

  const createSearcher = () => {
    const searchBox = new google.maps.places.SearchBox(document.getElementById('map-search'));
    exports.map.controls[google.maps.ControlPosition.TOP_CENTER].push(document.getElementById('map-search'));
    // Bias the SearchBox results towards current map's viewport.
    exports.map.addListener('bounds_changed', () => {
      searchBox.setBounds(exports.map.getBounds());
    });

    let markers = [];
    searchBox.addListener('places_changed', () => {
      const places = searchBox.getPlaces();

      if (places.length === 0) {
        return;
      }

      markers.forEach((marker) => {
        marker.setMap(null);
      });
      markers = [];

      const bounds = new google.maps.LatLngBounds();
      places.forEach((place) => {
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

        markers.push(new google.maps.Marker({
          map: exports.map,
          icon,
          // title: place.name,
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
    // legendTable += "<tr><td class='text-center'><img src='/static/img/discover_map_blue_marker.png'>"
    //   + '</td><td>Box Coverage Centers</td></tr>';
    legendTable += "<tr><td class='text-center'><img src='/static/img/discover_map_cluster_icon.png'>"
      + '</td><td>Clusters</td></tr></tbody></table>';
    legend.innerHTML = legendTable;
    return legend;
  };

  const createBatchMarkers = (locations, links, labels) => {
    document.body.style.cursor = 'wait';
    googMarkers = locations.map(function (location, k) {
      const marker = new google.maps.Marker({
        map: exports.map,
        position: location,
        // title: labels[k % labels.length],
      });
      const _infowindow = new google.maps.InfoWindow();
      _infowindow.setContent(`<a href="${links[k % links.length]}" target="_blank">${labels[k % labels.length]}</a>`);
      marker.addListener('click', () => {
        _infowindow.open(exports.map, marker);
      });
      return marker;
    });
    markerCluster = new MarkerClusterer(exports.map, googMarkers,
      { imagePath: 'https://developers.google.com/maps/documentation/javascript/examples/markerclusterer/m' });
    document.body.style.cursor = 'default';
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
    google.maps.event.addListener(addmarker, 'mouseout', () => {
      infowindow.close();
    });
    googMarkers.push(addmarker);
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
    // const mapLegend = createLegend();
    const searchBox = createSearcher();

//     for(var i = 0; i < markers.length; i++){ // looping through my Markers Collection
// if(bounds.contains(markers[i].position))
//  console.log("Marker"+ i +" - matched");
// }
  };
  exports.initMap = initMap; // eslint-disable-line
  exports.createBatchMarkers = createBatchMarkers; // eslint-disable-line
  exports.toggleMap = toggleMap; // eslint-disable-line
  exports.deleteMarkers = deleteMarkers; // eslint-disable-line
})(this.window = this.window || {});
