((exports) => {
  const mapDefaultZoom = 4;
  const mapCenter = { lat: 42, lng: -71 };
  // eslint-disable-next-line no-unused-vars
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

  const recenterMap = () => {
    exports.map.panTo(mapCenter);
  };

  const createBatchMarkers = (locations, hsUid, labels) => {
    document.body.style.cursor = 'wait';
    const minClusterZoom = 14;
    const oms = new OverlappingMarkerSpiderfier(exports.map, {
      // https://github.com/nmccready/OverlappingMarkerSpiderfier#construction
      markersWontMove: true,
      markersWontHide: true,
      basicFormatEvents: true,
      minZoomLevel: minClusterZoom,
      keepSpiderfied: true,
      legWeight: 5,
      circleSpiralSwitchover: 0,
      // nearbyDistance
    });

    googMarkers = locations.map((location, k) => {
      const marker = new google.maps.Marker({ // eslint-disable-line
        map: exports.map,
        position: location,
        hsUid: hsUid[k % hsUid.length],
      });
      const infowindow = new google.maps.InfoWindow(); // eslint-disable-line
      infowindow.setContent(`<a href="/resource/${hsUid[k % hsUid.length]}" target="_blank">${labels[k % labels.length]}</a>
        lat: ${location.lat.toFixed(2)} lng: ${location.lng.toFixed(2)}`);
      oms.addListener('spiderfy', ()=> {
        infowindow.close();
      });
      oms.addListener('unspiderfy', ()=> {
        infowindow.close();
      });
      marker.addListener('click', () => {
        infowindow.close();
      });

      google.maps.event.addListener(marker, 'spider_click', function(e) {  // 'spider_click', not plain 'click'
        infowindow.close();
        infowindow.open(exports.map, marker);
      });
      oms.addMarker(marker);  // adds the marker to the spiderfier _and_ the map
      return marker;
    });
    const algorithm = new markerClusterer.SuperClusterAlgorithm({ maxZoom: minClusterZoom, zoomOnClick: false })
    const markerCluster = new markerClusterer.MarkerClusterer({ markers:googMarkers, map:exports.map, algorithm:algorithm });

    // Optional: prevent overzooming
    // google.maps.event.addListener(markerCluster, 'clusterclick', function(cluster) {
    //   map.fitBounds(cluster.getBounds()); // Fit the bounds of the cluster clicked on
    //   if( map.getZoom() > minClusterZoom+1 ) // If zoomed in past first level without clustering, zoom out to that level
    //       map.setZoom(minClusterZoom+1);
    // });
    document.body.style.cursor = 'default';
  };

  const gotoBounds = () => {
    const bounds = new google.maps.LatLngBounds();
    googMarkers.forEach(marker => bounds.extend(marker.position));
    exports.map.fitBounds(bounds);
  };

  const toggleMap = () => {
    document.getElementById('map-view').style.display = document.getElementById('map-view').style.display === 'block' ? 'none' : 'block';
  };

  const initMap = () => {
    // eslint-disable-next-line no-param-reassign,no-undef
    exports.map = new google.maps.Map(document.getElementById('map'), {
      center: mapCenter,
      zoom: mapDefaultZoom,
      gestureHandling: 'greedy',
      mapTypeId: google.maps.MapTypeId.TERRAIN, // eslint-disable-line
    });

    exports.map.addListener('bounds_changed', () => {
      const visMarkers = [];
      const bounds = exports.map.getBounds();
      googMarkers.forEach((marker) => {
        if (bounds.contains(marker.position)) {
          visMarkers.push(marker.hsUid);
        }
      });
      this.visMarkers = visMarkers; // window
    });
    exports.map.setOptions({ minZoom: 2, maxZoom: 15 });
  };
  exports.initMap = initMap; // eslint-disable-line
  exports.createBatchMarkers = createBatchMarkers; // eslint-disable-line
  exports.toggleMap = toggleMap; // eslint-disable-line
  exports.deleteMarkers = deleteMarkers; // eslint-disable-line
  exports.gotoBounds = gotoBounds; // eslint-disable-line
  exports.recenterMap = recenterMap; //eslint-disable-line
})(this.window = this.window || {});
