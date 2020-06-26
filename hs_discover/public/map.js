(function (exports) {
  const mapDefaultZoom = 2;

  const initMap = () => {
    // eslint-disable-next-line no-param-reassign
    exports.map = new google.maps.Map(document.getElementById('map'), {
      center: {
        lat: 0,
        lng: 0,
      },
      zoom: mapDefaultZoom,
      mapTypeId: google.maps.MapTypeId.TERRAIN,
    });
    const mapLegend = document.getElementById('discover-map-legend');
    const geoCoder = document.getElementById('geocoder-panel');
    const resetZoomButton = document.getElementById('reset-zoom');
    const geoCoderContent = [];
    const resetButtonContent = [];
    exports.map.controls[google.maps.ControlPosition.RIGHT_TOP].push(mapLegend);
    exports.map.controls[google.maps.ControlPosition.LEFT_BOTTOM].push(geoCoder);
    exports.map.controls[google.maps.ControlPosition.RIGHT_BOTTOM].push(resetZoomButton);
    let legendTable = '<table><tbody>';
    legendTable += "<tr><td class='text-center'><img src='/static/img/discover_map_red_marker.png'></td><td>Point Coverage Locations</td></tr>";
    legendTable += "<tr><td class='text-center'><img src='/static/img/discover_map_blue_marker.png'></td><td>Box Coverage Centers</td></tr>";
    legendTable += "<tr><td class='text-center'><img src='/static/img/discover_map_cluster_icon.png'></td><td>Clusters</td></tr></tbody></table>";
    geoCoderContent.push("<input id='geocoder-address' type='textbox' placeholder='Search Locations...'>");
    geoCoderContent.push("<a id='geocoder-submit' style='margin-left:10px' class='btn btn-default' role='button'><span class='glyphicon glyphicon-zoom-in'></span> Go </a>");
    resetButtonContent.push("<a id='reset-zoom-btn' data-toggle='tooltip' title='Reset Zoom' class='btn btn-default btn-sm' onclick='resetMapZoom()'>");
    resetButtonContent.push("<span class='glyphicon glyphicon-fullscreen'></span></a>");
    mapLegend.innerHTML = legendTable;
    geoCoder.innerHTML = geoCoderContent.join('');
    resetZoomButton.innerHTML = resetButtonContent.join('');
    const setMarkers = function(jsonResults) {
      let modifiedPointsData = [];
      let modifiedBoxesData = [];
      let boxesData = [];
      jsonResults.forEach((x) => {
        console.log(x);
      });

      modifiedPointsData.forEach(function(point) {
        createPointResourceMarker(point);
      });

      modifiedBoxesData.forEach(function(box) {
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
              url: '/static/img/m2.png'
          }]
      });
  };
  };

  exports.initMap = initMap; // eslint-disable-line
}((this.window = this.window || {})));
