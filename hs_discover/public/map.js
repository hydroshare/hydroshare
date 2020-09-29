((exports) => {
  const mapDefaultZoom = 4;
  // eslint-disable-next-line no-unused-vars
  let googMarkers = [];
  let pois = [];
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
    const searchBox = new google.maps.places.SearchBox(document.getElementById('map-search')); // eslint-disable-line
    exports.map.controls[google.maps.ControlPosition.TOP_CENTER].push(document.getElementById('map-search')); // eslint-disable-line
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

      const bounds = new google.maps.LatLngBounds(); // eslint-disable-line
      places.forEach((place) => {
        if (!place.geometry) {
          console.log('Returned place contains no geometry');
          return;
        }
        // const icon = {
        //   url: place.icon,
        //   size: new google.maps.Size(71, 71),
        //   origin: new google.maps.Point(0, 0),
        //   anchor: new google.maps.Point(17, 34),
        //   scaledSize: new google.maps.Size(25, 25),
        // };

        markers.push(new google.maps.Marker({ // eslint-disable-line
          map: exports.map,
          // icon,
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

  // eslint-disable-next-line no-unused-vars
  const createLegend = () => {
    const legend = document.getElementById('discover-map-legend');
    exports.map.controls[google.maps.ControlPosition.RIGHT_TOP].push(legend); // eslint-disable-line
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

  const createBatchMarkers = (locations, hsUid, labels) => {
    document.body.style.cursor = 'wait';
    googMarkers = locations.map((location, k) => {
      const marker = new google.maps.Marker({ // eslint-disable-line
        map: exports.map,
        position: location,
        hsUid: hsUid[k % hsUid.length],
        // title: labels[k % labels.length],
      });
      const infowindow = new google.maps.InfoWindow(); // eslint-disable-line
      infowindow.setContent(`<a href="/resource/${hsUid[k % hsUid.length]}" target="_blank">${labels[k % labels.length]}</a>
        lat: ${location.lat.toFixed(2)} lng: ${location.lng.toFixed(2)}`);
      marker.addListener('click', () => {
        infowindow.open(exports.map, marker);
      });
      return marker;
    });
    markerCluster = new MarkerClusterer(exports.map, googMarkers, // eslint-disable-line
      { imagePath: 'https://developers.google.com/maps/documentation/javascript/examples/markerclusterer/m' });
    document.body.style.cursor = 'default';
  };

  const gotoBounds = () => {
    const bounds = new google.maps.LatLngBounds();
    // googMarkers.forEach(marker => console.log(marker));
    googMarkers.forEach(marker => bounds.extend(marker.position));
    exports.map.fitBounds(bounds);
  };

  const highlightMarker = (hsid) => {
    const loc = googMarkers.filter(x => x.hsUid === hsid)[0];
    pois.forEach(x => x.setMap(null));
    pois = [];
    if (loc.position.lat() && loc.position.lng()) {
      const poi = new google.maps.Marker({ // eslint-disable-line
        map: exports.map,
        position: { lat: loc.position.lat(), lng: loc.position.lng() },
      });
      pois.push(poi);
      exports.map.setZoom(7);
      exports.map.panTo(poi.position);
    }
  };

  const toggleMap = () => {
    document.getElementById('map-view').style.display = document.getElementById('map-view').style.display === 'block' ? 'none' : 'block';
  };

  const initMap = () => {
    // eslint-disable-next-line no-param-reassign,no-undef
    exports.map = new google.maps.Map(document.getElementById('map'), {
      center: {
        lat: 42,
        lng: -71,
      },
      zoom: mapDefaultZoom,
      gestureHandling: 'greedy',
      mapTypeId: google.maps.MapTypeId.TERRAIN, // eslint-disable-line
    });
    // https://stackoverflow.com/questions/29869261/google-map-search-box
    // const mapLegend = createLegend();
    // eslint-disable-next-line no-unused-vars
    // const searchBox = createSearcher();
    exports.map.addListener('bounds_changed', () => {
      const visMarkers = [];
      const bounds = exports.map.getBounds();
      googMarkers.forEach((marker) => {
        if (bounds.contains(marker.position)) {
          visMarkers.push(marker.hsUid);
        }
      });
      // console.log(`Pushed ${visMarkers.length} marker hs short ids`);
      this.visMarkers = visMarkers; // window
      // poi = new google.maps.Marker({
      //   map: exports.map,
      // });
      // const mapfilter = document.getElementById('map-filter-button');
      // exports.map.controls[google.maps.ControlPosition.BOTTOM_CENTER].push(mapfilter);
    });
    exports.map.setOptions({ minZoom: 2, maxZoom: 15 });
  };
  exports.initMap = initMap; // eslint-disable-line
  exports.createBatchMarkers = createBatchMarkers; // eslint-disable-line
  exports.toggleMap = toggleMap; // eslint-disable-line
  exports.deleteMarkers = deleteMarkers; // eslint-disable-line
  exports.gotoBounds = gotoBounds; // eslint-disable-line
})(this.window = this.window || {});
