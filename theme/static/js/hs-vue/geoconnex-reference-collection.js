let counter = 0;
// TODO: would it be faster to add each geoconnex collection to a geojson group and then use that to conduct a single turf.js query for each collection
// instead of one for every item?
// Okay, so we want to do the bulk load, but we want to give some feedback...can we do bulk by collection and provide feedback for that?
let geoconnexApp = new Vue({
    el: '#app-geoconnex',
    delimiters: ['${', '}'],
    vuetify: new Vuetify(),
    data() {
        return{
            relations: RELATIONS,
            debug: false,
            resMode: RESOURCE_MODE,
            resSpatialType: null,
            items: [],
            unfilteredItems: [],
            hasFilteredItems: false,
            collections: null,
            values: [],
            loading: true,
            currentLoading: "",
            errorMsg: "",
            errored: false,
            geoconnexUrl: "https://reference.geoconnex.us/collections",
            apiQueryNoGeo: "items?f=json&lang=en-US&skipGeometry=true",
            apiQueryYesGeo: "items?f=json&lang=en-US&skipGeometry=false",
            cacheName: "geoconnexCache",
            geoCache: null,
            resShortId: SHORT_ID,
            cacheDuration: 1000 * 60 * 60 * 24 * 7, // one week in milliseconds
            cacheDuration: 0,
            search: null,
            rules: null,
            showMap: false,
            map: null,
            layerControl: null,
            selectedItemLayers: {},
            selectedFeatureGroup: null,
            hasSearches: false,
            hasExtentSearch: false,
            geometriesAreLoaded: false,
            searchFeatureGroup: null,
            layerGroupDictionary: {},
            searchRadius: 1,
            maxAreaToReturn: 1e12,
            pointLat: 0,
            pointLong: 0,
            northLat: null,
            eastLong: null,
            southLat: null,
            westLong: null,
            searchColor: 'orange',
            selectColor: 'purple'
        }
    },
    watch: {
      values(newValue, oldValue){
        let vue = this;
        vue.errorMsg = "";
        if (newValue.length > oldValue.length){
          vue.addSelectedItem(newValue.pop());
        }else if (newValue.length < oldValue.length){
          let remove = oldValue.filter(obj => newValue.every(s => s.id !== obj.id));
          try{
            vue.selectedFeatureGroup.removeLayer(vue.selectedItemLayers[remove[0].value]);
            vue.map.fitBounds(vue.selectedFeatureGroup.getBounds());
          }catch(e){
            console.log(e.message);
          }
          vue.removeMetadata(remove);

          // re-enable the item for selection
          vue.items.forEach(it =>{
            if(remove[0].value === it.uri){
              it.disabled = false;
            }
          });
        }
      }
    },
    methods: {
      resetItems(){
        let vue = this;
        vue.items = vue.unfilteredItems;
        vue.hasFilteredItems = false;
      },
      filterItemsBySearch(){
        let vue = this;
        vue.loading = true;
        vue.hasFilteredItems = true;
        // save a copy of the items
        vue.unfilteredItems = vue.items;

        // first remove any unused collections -- this has been removed because it is plenty fast just to use "filter"
        // vue.items = vue.items.filter(s => Object.keys(vue.layerGroupDictionary).includes(s.collection));

        // remove all items currently not in the map search
        let keep = [];
        for(const val of Object.values(vue.layerGroupDictionary)){
          if (!val.uris.includes(undefined)){
            keep = keep.concat(val.uris);
          }
        }
        vue.items = vue.items.filter(s => keep.includes(s.uri));
        // vue.items = vue.items.map(function(s){
        //   if(!keep.includes(s.uri)){
        //     s.disabled = true;
        //   }
        //   return s;
        // });
        vue.loading = false;
      },
      addSelectedItem(selected){
        let vue = this;
        vue.fetchSingleGeometry(selected).then(geometry =>{
          selected.geometry = geometry.geometry;
          vue.addToMap(selected, true);
        });
        vue.addMetadata(selected);
        
        // disable so that it can't be duplicated
        vue.items.forEach(it =>{
          if(selected.uri === it.uri){
            it.disabled = true;
          }
        });
      },
      async fetchSingleGeometry(geoconnexObj, refresh=false){
        let vue = this;
        let response = {};
        if(refresh || !geoconnexObj.geometry){
          let query = `${vue.geoconnexUrl}/${geoconnexObj.collection}/items/${geoconnexObj.id}?f=json`;
          response = await vue.getFromCacheOrFetch(query);
        }else{
          response.geometry = geoconnexObj.geometry;
        }
        return response;
      },
      async fetchAllGeometries(){
        let vue = this;
        let itemsWithGeo = [];
        for (let collection of vue.collections){
          console.log(`Loading geometry for ${collection.id}`);
          const url = `${vue.geoconnexUrl}/${collection.id}/${vue.apiQueryYesGeo}`;
          let response = await vue.getFromCacheOrFetch(url);
          for (let feature of response.features){
            itemsWithGeo.push(vue.getFeatureProperties(feature));
          }
        }
        // overwrite now that we have the geometries
        vue.items = itemsWithGeo;
        vue.geometriesAreLoaded = true;
      },
      async fetchReferenceItem(uri){
        let vue = this;
        let relative_id = uri.split('ref/').pop();
        let collection = relative_id.split('/')[0];
        let id = relative_id.split('/')[1];
        let query = `${vue.geoconnexUrl}/${collection}/items/${id}?f=json`;
        let response = await vue.getFromCacheOrFetch(query);
        return response;
      },
      createMap(){
        let vue = this;
        vue.map = L.map('geo-leaflet');

        let terrain = L.tileLayer('https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.jpg', {
          attribution: 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://www.openstreetmap.org/copyright">ODbL</a>.',
          maxZoom: 18,
        });

        let streets = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 18,
        });

        let toner = L.tileLayer('https://stamen-tiles.a.ssl.fastly.net/toner/{z}/{x}/{y}.png', {
          attribution: 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://www.openstreetmap.org/copyright">ODbL</a>.',
          maxZoom: 18,
        });

        var baseMaps = {
          "Terrain": terrain,
          "Streets": streets,
          "Toner": toner
        };

        vue.selectedFeatureGroup =  L.featureGroup();
        vue.searchFeatureGroup =  L.featureGroup();

        var overlayMaps = {
          "Selected Collection Items": vue.selectedFeatureGroup
        };
        if(vue.resMode == "Edit"){
          overlayMaps["Search (all items)"] = vue.searchFeatureGroup;
          vue.map.addLayer(vue.searchFeatureGroup);
        }

        vue.layerControl = L.control.layers(baseMaps, overlayMaps);
        vue.layerControl.addTo(vue.map);

        L.control.fullscreen({
          position: 'topleft',
          title: 'Enter fullscreen',
          titleCancel: 'Exit Fullscreen',
          content: `<i class="fa-expand"></i>`
        }).addTo(vue.map);

        // show the default layers at start
        vue.map.addLayer(terrain);
        vue.map.addLayer(vue.selectedFeatureGroup);
        vue.map.setView([30, 0], 1);
        vue.setMapEvents();
      },
      async addToMap(geojson, zoom=false, style={color: this.selectColor, radius: 5}, group=null){
        let vue = this;
        try {
           let leafletLayer = L.geoJSON(geojson,{
            onEachFeature: function (feature, layer) {
              var popupText = `<h4>${feature.text}</h4>`
              for (var k in feature.properties) {
                  popupText += '<b>'+k+'</b>: ';
                  if(k==="uri"){
                    popupText += `<a href=${feature.properties[k]}>${feature.properties[k]}</a></br>`
                  }
                  else{
                    popupText += feature.properties[k]+'</br>'
                  }
              }
              let hide = ['properties', 'text', 'geometry', 'relative_id', 'type', 'links', 'disabled'];
              for (var k in feature) {
                if(hide.includes(k) | k in feature.properties){
                  continue
                }
                popupText += '<b>'+k+'</b>: ';
                popupText += feature[k]+'</br>'
              }
              if(vue.resMode == "Edit" && style.color == vue.searchColor){
                popupText += `<button type="button" class="btn btn-success map-add-geoconnex" data='${JSON.stringify(feature)}'>Add this feature to your resource metadata</button>`
              }else if(vue.resMode == "Edit" && style.color == vue.selectColor){
                popupText += `<button type="button" class="btn btn-success map-remove-geoconnex" data='${JSON.stringify(feature)}'>Remove this feature from your resource metadata</button>`
              }
              layer.bindPopup(popupText);
            },
            pointToLayer: function (feature, latlng) {
              return L.circleMarker(latlng, style);
            }
          }
          );
          leafletLayer.setStyle(style);
          if(geojson.uri){
            vue.selectedItemLayers[geojson.uri] = leafletLayer;
          }
          if(group){
            group.addLayer(leafletLayer);
          }else{
            vue.selectedFeatureGroup.addLayer(leafletLayer);
          }
          if(group===vue.searchFeatureGroup){
            if(!geojson.collection){
              geojson.collection = "Search Bounds"
            }
            // check if layergroup exists in the "dictionary"
            if(!vue.layerGroupDictionary || vue.layerGroupDictionary[geojson.collection] == undefined){
              vue.layerGroupDictionary[geojson.collection] = L.layerGroup();
              vue.layerGroupDictionary[geojson.collection].uris = [];
              vue.layerControl.addOverlay(vue.layerGroupDictionary[geojson.collection], geojson.collection)
              vue.layerControl.expand();
            }
            vue.map.addLayer(vue.layerGroupDictionary[geojson.collection]);
            vue.layerGroupDictionary[geojson.collection].addLayer(leafletLayer);
            vue.layerGroupDictionary[geojson.collection].uris.push(geojson.uri);
          }

          // handle zooming
          if(zoom){
            vue.map.flyToBounds(leafletLayer.getBounds());
          }else{
            if(group){
              vue.map.fitBounds(group.getBounds());
            }else{
              vue.map.fitBounds(vue.selectedFeatureGroup.getBounds());
            }
          }

        } catch (e) {
          console.log(e.message);
        }
        vue.showMap = true;
      },
      setRules(){
        let vue = this;
        vue.rules = [
          function(v){
            let invalid = [];
            for (let item of v){
              try {
                url = new URL(item.value);
              } catch (_) {
                invalid.push(item.text);  
              }
            }
            if(invalid.length === 1){
              return `"${invalid}" is not a valid URI. We recommend that your custom feature be linkable`;
            }
            if (invalid.length === 2){
              return `"${invalid.join('" and "')}" are not a valid URIs. We recommend that custom features be linkable.`;
            }
            if (invalid.length > 2){
              return `"${invalid.join('", "').replace(/, ([^,]*)$/, ' and $1')}" are not a valid URIs. We recommend that custom features be linkable`;
            }
            return true;
          }
        ];
      },
      async getCollections(){
          let vue = this;
          const collectionsUrl=`${vue.geoconnexUrl}?f=json&lang=en-US`;
          try{
            let response = await vue.getFromCacheOrFetch(collectionsUrl);
            return response;
          }catch(e){
            console.log(e.message)
            vue.errored = true;
          }
        },
      async getAllItems(){
        let vue = this;
        let collections = await vue.getCollections();
        vue.collections = collections.collections;
        for (let col of vue.collections){
          vue.currentLoading = col.description;
          let header = { 
            header: `${col.description} (${col.id})`,
            text: `${col.description} (${col.id})`
          }
          vue.items.push(header);
          let resp = await vue.getItemsIn(col.id);
          for (let feature of resp.features){
            vue.items.push(vue.getFeatureProperties(feature));
          }
        }
      },
      getFeatureProperties(feature){
        feature.relative_id = feature.properties.uri.split('ref/').pop();
        feature.collection = feature.relative_id.split('/')[0];
        feature.uri = feature.properties.uri;
        feature.NAME = feature.properties.NAME;
        if(feature.properties.AQ_NAME){
          feature.NAME = feature.properties.AQ_NAME;
        }
        if(feature.properties.name){
          feature.NAME = feature.properties.name;
        }
        if(feature.properties.name_at_outlet){
          feature.NAME = feature.properties.name_at_outlet;
        }
        if(feature.properties.SHR){
          feature.NAME = feature.properties.SHR;
        }
        if(feature.properties.NAME10){
          feature.NAME = feature.properties.NAME10;
        }
        feature.text = `${feature.NAME} [${feature.relative_id}]`;
        return feature;
      },
      async getOnlyRelationItems(){
        let vue = this;
        for (let relation of vue.relations){
          let feature = await vue.fetchReferenceItem(relation.value);
          vue.items.push(vue.getFeatureProperties(feature));
        }
      },
      async getItemsIn(collectionId){
        let vue = this;
        const url = `${vue.geoconnexUrl}/${collectionId}/${vue.apiQueryNoGeo}`;
        let response = await vue.getFromCacheOrFetch(url);
        return response;
      },
      async getFromCacheOrFetch(url){
        let vue = this;
        let data = {};
        if (!('caches' in window)){
          let fetch_resp = await fetch(url);
          console.log("Cache API not available. Fetching geoconnex data from:\n" + url);
          data = await fetch_resp.json();
        }else{
          let cache_resp = await vue.geoCache.match(url);
          if(vue.isCacheValid(cache_resp)){
            console.log("Geoconnex data used from cache for:\n" + url);
            data = await cache_resp.json();
          }else{
            console.log("Fetching + adding to cache, geoconnex data from:\n" + url);
            try{
              let fetch_resp = await fetch(url);
              let copy = fetch_resp.clone();
              let headers = new Headers(copy.headers);
              headers.append('fetched-on', new Date().getTime());
              let body = await copy.blob();
              vue.geoCache.put(url, new Response(body, {
                status: copy.status,
                statusText: copy.statusText,
                headers: headers
              }));
              data = await fetch_resp.json();
            }catch(e){
              console.log(e.message)
              vue.geoCache.match(url).then(function (response) {
                console.log("Geoconnex API fetch error. Falling back to old cached version.")
                return response.data;
              }).catch(function (e){
                console.log(e.message);
                vue.errored = true;
              })
            }
          }
        }
        return data;
      },
      isCacheValid(response) {
        let vue = this;
        if (!response) return false;
        var fetched = response.headers.get('fetched-on');
        if (fetched && (parseFloat(fetched) + vue.cacheDuration) > new Date().getTime()) return true;
        console.log("Cached data not valid.");
        return false;
      },
      isUrl(stringToTest){
        try {
          new URL(stringToTest);
        } catch (_) {
          return false;
        }
        return true;
      },
      async loadRelations(){
        let vue = this;
        for (relation of vue.relations){
          if (relation.type === "relation"){
            let item;
            try {
              new URL(relation.value);
              item = vue.items.find(obj => {
                return obj.uri === relation.value;
              });
            } catch (_) {
              item = null;
            }
            let data = {
              "id": relation.id,
              "text": item ? item.text : relation.value,
              "value": relation.value,
            };
            vue.values.push(data);

            // disable already selected items
            vue.items.forEach(it =>{
              if(item && item.uri === it.uri){
                it.disabled = true;
              }
            });

            if (item){
              vue.fetchSingleGeometry(item).then(geometry =>{
                item.geometry = geometry.geometry;
                vue.addToMap(item, false);
              });
            }
          }
        }
      },
      addMetadata(selected){
        let vue = this;
        let url = `/hsapi/_internal/${vue.resShortId}/relation/add-metadata/`;
        let data = {
          "type": 'relation',
          "value": selected.uri ? selected.uri : selected
        }
        $.ajax({
          type: "POST",
          url: url,
          data: data,
          success: function (result) {
            console.log(`Added ${selected.text ? selected.text : selected} to resource metadata`)
            vue.values.push({
              "id":result.element_id,
              "value": selected.uri ? selected.uri : selected,
              "text": selected.text ? selected.text : selected
            });
          },
          error: function (request, status, error) {
            vue.errorMsg = `${error} while attempting to add related feature.`;
            console.log(request.responseText);
          }
        });
      },
      removeMetadata(relations){
        let vue = this;
        for (let relation of relations){
          if (relation.id){
            let url = `/hsapi/_internal/${vue.resShortId}/relation/${relation.id}/delete-metadata/`;
            $.ajax({
              type: "POST",
              url: url,
              success: function () {
              },
              error: function (request, status, error) {
                vue.errorMsg = `${error} while attempting to remove related feature.`;
                console.log(request.responseText);
              }
            });
          }
        }
      },
      getGeoItemsFromDebug(){
        let vue = this;
        if(vue.resSpatialType == 'point'){
          vue.getGeoItemsRadius(vue.pointLat, vue.pointLong);
        }else if(vue.resSpatialType == 'box'){
          let bbox = [vue.eastLong, vue.southLat, vue.westLong, vue.northLat];
          var polygon = turf.bboxPolygon(bbox);
          polygon.text = "Search bounds";
          vue.getGeoItemsInPoly(polygon);
        }else{
          alert("Spatial extent isn't set?....")
        }
      },
      async getGeoItemsFromExtent(){
        let vue = this;
        if(vue.resSpatialType == 'point'){
          await vue.getGeoItemsContainingPoint(vue.pointLat, vue.pointLong);
        }else if(vue.resSpatialType == 'box'){
          let bbox = [vue.eastLong, vue.southLat, vue.westLong, vue.northLat];
          var polygon = turf.bboxPolygon(bbox);
          polygon.text = "Search bounds";
          await vue.getGeoItemsInPoly(polygon);
        }else{
          alert("Spatial extent isn't set?....")
        }
        vue.hasExtentSearch = true;
      },
      getGeoItemsRadius(lat=null, long=null){
        let vue=this;
        long = typeof(long) == 'number' ? long : vue.pointLong;
        lat = typeof(lat) == 'number' ? lat : vue.pointLat;
        let center = turf.point([long, lat]);
        let sides = vue.searchRadius / 100;
        var options = {
          steps: sides < 25 ? 25 : sides,
          units: 'kilometers', 
          properties: {
            Radius: `${vue.searchRadius} kilometers`
          }
        };
        var polygon = turf.circle(center, vue.searchRadius, options);
        polygon.text = "Search bounds";
        vue.getGeoItemsInPoly(polygon);
      },
      async getGeoItemsContainingPoint(lat=null, long=null){
        // https://turfjs.org/docs/#booleanPointInPolygon
        let vue=this;
        long = typeof(long) == 'number' ? long : vue.pointLong;
        lat = typeof(lat) == 'number' ? lat : vue.pointLat;
        let center = turf.point([long, lat]);
        center.text = "Search point";
        vue.loading = true;
        vue.map.closePopup();

        vue.addToMap(center, false, {color:'red', fillColor: 'red', fillOpacity: 0.1, radius: 1}, group=vue.searchFeatureGroup);

        for (let item of vue.items){
          try{
            vue.currentLoading = item.collection;
            let geometry = await vue.fetchSingleGeometry(item);
            item.geometry = geometry.geometry;
            if (turf.area(item) < vue.maxAreaToReturn*1e6){
              if(turf.booleanPointInPolygon(center, item)){
                if(item.geometry.type.includes("Point")){
                  await vue.addToMap(item, false, {color: vue.searchColor, radius: 5, fillColor: 'yellow', fillOpacity: 0.8}, group=vue.searchFeatureGroup);
                }else{
                  await vue.addToMap(item, false, {color: vue.searchColor}, group=vue.searchFeatureGroup);
                }
              }
            }
          }catch(e){
            console.log(`Error while attempting to load ${item.text}: ${e.message}`);
          }
        }
        vue.loading = false;
        vue.hasSearches = true;
      },
      async getGeoItemsInPoly(polygon=null){
        // https://turfjs.org/docs/#intersects
        // https://turfjs.org/docs/#booleanIntersects
        // https://turfjs.org/docs/#booleanContains
        let vue=this;
        vue.loading = true;
        vue.map.closePopup();

        vue.addToMap(polygon, false, {color:'red', fillColor: 'red', fillOpacity: 0.1}, group=vue.searchFeatureGroup);

        for (let item of vue.items){
          try{
            vue.currentLoading = item.collection;
            let geometry = await vue.fetchSingleGeometry(item);
            item.geometry = geometry.geometry;
            if (turf.area(item) < vue.maxAreaToReturn*1e6){
              if(turf.booleanIntersects(polygon, item)){
                if(item.geometry.type.includes("Point")){
                  await vue.addToMap(item, false, {color: vue.searchColor, radius: 5, fillColor: 'yellow', fillOpacity: 0.8}, group=vue.searchFeatureGroup);
                }else{
                  await vue.addToMap(item, false, {color: vue.searchColor}, group=vue.searchFeatureGroup);
                }
              }
            }
          }catch(e){
            console.log(`Error while attempting to find intersecting geometries: ${e.message}`);
          }
        }
        vue.loading = false;
        vue.hasSearches = true;
      },
      clearMappedSearches(){
        let vue = this;
        vue.searchFeatureGroup.clearLayers();
        for (let key in vue.layerGroupDictionary){
          vue.layerControl.removeLayer(vue.layerGroupDictionary[key]);
          delete vue.layerGroupDictionary[key];
        }
        // vue.layerControl.removeLayer(vue.searchFeatureGroup);
        // vue.map.removeLayer(vue.searchFeatureGroup);

        vue.hasSearches = false;
        vue.hasExtentSearch = false;
      },
      searchUsingSpatialExtent(){
        let vue = this;
        vue.fillFromExtent();
        vue.getGeoItemsFromExtent();
      },
      updateSpatialExtentType(){
        let vue = this;
        let checked = $("#div_id_type input:checked").val();
        vue.resSpatialType = checked;
      },
      fillFromExtent(){
        let vue = this;
        if(vue.resSpatialType == 'point'){
          vue.fillFromPointExtent();
        }else if(vue.resSpatialType == 'box'){
          vue.fillFromBoxExtent();
        }else{
          alert("Spatial extent isn't set?....")
        }
      },
      fillFromPointExtent(){
        let vue = this;
          vue.pointLat = $('#id_north').val();
          vue.pointLong = $('#id_east').val();
      },
      fillFromBoxExtent(){
        let vue = this;
          vue.northLat = $('#id_northlimit').val();
          vue.eastLong = $('#id_eastlimit').val();
          vue.southLat = $('#id_southlimit').val();
          vue.westLong = $('#id_westlimit').val();
      },
      fillFromCoords(lat, long){
        let vue = this;
          vue.pointLat = lat;
          vue.pointLong = long;
      },
      setMapEvents(){
        let vue = this;
        var popup = L.popup();

        function onMapClick(e) {
          let loc = {lat: e.latlng.lat, long: e.latlng.lng};
          if(vue.geometriesAreLoaded){
            let content = `<button type="button" class="btn btn-success leaflet-point-search" data='${JSON.stringify(loc)}'>Search for Geoconnex items containing this location</button>`
            popup
                .setLatLng(e.latlng)
                .setContent(content)
                .openOn(vue.map);
          }
        }

        if(vue.resMode === 'Edit'){
          vue.map.on('click', onMapClick);
          
          $("div").on("click", 'button.leaflet-point-search', function (e) {
            e.stopPropagation();
            var loc = JSON.parse($(this).attr("data"));
            vue.fillFromCoords(loc.lat, loc.long);
            vue.getGeoItemsContainingPoint(loc.lat, loc.long);
          });

          $("div").on("click", 'button.map-add-geoconnex', function (e) {
            e.stopPropagation();
            let data = JSON.parse($(this).attr("data"));
            vue.addSelectedItem(data);
            vue.map.closePopup();
          });
  
          $("div").on("click", 'button.map-remove-geoconnex', function (e) {
            e.stopPropagation();
            let data = JSON.parse($(this).attr("data"));
            vue.values = vue.values.filter(s => s.value !== data.uri);
            vue.map.closePopup();
          });
        }

        // listen for spatial coverage  type change
        $("#div_id_type input[type=radio]").change((e)=>{
          vue.resSpatialType = e.target.value;
        });
      }
    },
    beforeMount(){
      this.setRules();
    },
    async mounted() {
      let vue = this;
      if(vue.resMode == "Edit"){
        vue.geoCache = await caches.open(vue.cacheName);
        await vue.getAllItems();
        vue.updateSpatialExtentType()
        vue.createMap();
        await vue.loadRelations();
        vue.loading = false;
        
        // load geometries in the background
        await vue.fetchAllGeometries();
      }else if(vue.resMode == "View" && vue.relations.length > 0){
        vue.geoCache = await caches.open(vue.cacheName);
        await vue.getOnlyRelationItems();
        vue.createMap();
        await vue.loadRelations();
        vue.loading = false;
      }
    }
})

/*
TODO: 
- combine the spatial coverage map with the leaflet map?
*/