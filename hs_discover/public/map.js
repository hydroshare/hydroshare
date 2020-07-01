((exports) => {
  const mapDefaultZoom = 4; // TODO set back to 2 to match HydroShare
  const point = { info_link: '', lat: 42, lng: -71 };
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

  const locations = [{ lat: 39, lng: -75 }, { lat: 42, lng: -71 }];

  // const markers = locations.map((location, i) => {
  //   return new google.maps.Marker({
  //     // icon: './images/pin.svg',
  //     position: location,
  //     zIndex: i,
  //     map: exports.map,
  //   });
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
  // });

  const createSearcher = () => {
    const searchBox = new google.maps.places.SearchBox(document.getElementById('map-search'));
    exports.map.controls[google.maps.ControlPosition.TOP_CENTER].push(document.getElementById('map-search'));
    // Bias the SearchBox results towards current map's viewport.
    exports.map.addListener('bounds_changed', function() {
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
    // legendTable += "<tr><td class='text-center'>
    // <img src='/static/img/discover_map_blue_marker.png'>
    // </td><td>Box Coverage Centers</td></tr>";
    // legendTable += "<tr><td class='text-center'>
    // <img src='/static/img/discover_map_cluster_icon.png'>
    // </td><td>Clusters</td></tr></tbody></table>";
    legend.innerHTML = legendTable;
    return legend;
  };

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
    const mapLegend = createLegend();
    const searchBox = createSearcher();
    const request = {
      query: 'Atlanta georgia',
      fields: ['name', 'geometry'],
    };

    axios.get('/searchjson/', { params: { data: {} } })
      .then((response) => {
        console.log(response);
      })
      .catch((error) => {
        console.error(error); // eslint-disable-line
      });
  };
  exports.initMap = initMap; // eslint-disable-line
})(this.window = this.window || {});
