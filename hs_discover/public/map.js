(function (exports) {
  const minFloatingNumber = 0.0001;
  const mapDefaultZoom = 2;

  function initMap() {
    // eslint-disable-next-line no-param-reassign
    exports.map = new google.maps.Map(document.getElementById('map'), {
      center: {
        lat: 0,
        lng: 0,
      },
      zoom: mapDefaultZoom,
      mapTypeId: google.maps.MapTypeId.TERRAIN
    });
    const infoWindow = new google.maps.InfoWindow();
  }

  // eslint-disable-next-line no-param-reassign
  exports.initMap = initMap;
  console.log('main exit'); // eslint-disable-line
}((this.window = this.window || {})));
