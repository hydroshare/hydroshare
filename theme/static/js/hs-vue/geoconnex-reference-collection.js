let counter = 0;
let geoconnexApp = new Vue({
    el: '#app-geoconnex',
    delimiters: ['${', '}'],
    vuetify: new Vuetify(),
    data() {
        return{
            relations: RELATIONS,
            debug: false,
            resMode: RESOURCE_MODE,
            items: [],
            collections: null,
            values: [],
            loading: true,
            currentLoading: "",
            errorMsg: "",
            errored: false,
            geoconnexUrl: "https://reference.geoconnex.us/collections",
            apiQueryAppend: "items?f=json&lang=en-US&skipGeometry=true",
            cacheName: "geoconnexCache",
            geoCache: null,
            resShortId: SHORT_ID,
            cacheDuration: 1000 * 60 * 60 * 24 * 7, // one week in milliseconds
            search: null,
            rules: null,
            showMap: false,
            map: null,
            leafletLayers: {},
            featureGroup: null,
            searchGroup: null,
            layerControl: null,
            radius: 1e3,
            maxArea: 1e4,
            lat: -111.48381550548234,
            long: 36.9378850872748
        }
    },
    watch: {
      values(newValue, oldValue){
        let vue = this;
        vue.errorMsg = "";
        if (newValue.length > oldValue.length){
          let selected = newValue.pop();
          vue.fetchGeometry(selected).then(geometry =>{
            selected.geometry = geometry.geometry;
            vue.addToMap(selected, true);
          });
          vue.addMetadata(selected);
        }else if (newValue.length < oldValue.length){
          let remove = oldValue.filter(obj => newValue.every(s => s.id !== obj.id));
          try{
            vue.featureGroup.removeLayer(vue.leafletLayers[remove[0].value]);
            vue.map.fitBounds(vue.featureGroup.getBounds());
          }catch(e){
            console.log(e.message);
          }
          vue.removeMetadata(remove);
        }
      }
    },
    methods: {
      async fetchGeometry(geoconnexObj){
        let vue = this;
        let query = `${vue.geoconnexUrl}/${geoconnexObj.collection}/items/${geoconnexObj.id}?f=json`;
        let response = await vue.getFromCacheOrFetch(query);
        return response;
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
        vue.map = L.map('geo-leaflet').setView([42.423935477911236, -71.17395771137696], 4);

        let streets = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 18,
        });

        var baseMaps = {
          "Streets": streets
        };

        vue.featureGroup =  L.featureGroup();
        vue.searchGroup =  L.featureGroup();

        var overlayMaps = {
          "Selected": vue.featureGroup,
          "Search": vue.searchGroup
        };

        vue.layerControl = L.control.layers(baseMaps, overlayMaps);
        vue.layerControl.addTo(vue.map);

        // show the default layers at start
        vue.map.addLayer(streets);
        vue.map.addLayer(vue.featureGroup);
      },
      addToMap(geojson, zoom=false, style={color: 'blue', radius: 5}, group=null){
        let vue = this;
        try {
           let leafletLayer = L.geoJSON(geojson,{
            onEachFeature: function (feature, layer) {
              var text = `<h4>${feature.text}</h4>`
              for (var k in feature.properties) {
                  text += '<b>'+k+'</b>: ';
                  if(k==="uri"){
                    text += `<a href=${feature.properties[k]}>${feature.properties[k]}</a></br>`
                  }
                  else{
                    text += feature.properties[k]+'</br>'
                  }
              }
              let hide = ['properties', 'text', 'geometry', 'relative_id'];
              for (var k in feature) {
                if(hide.includes(k) | k in feature.properties){
                  continue
                }
                text += '<b>'+k+'</b>: ';
                text += feature[k]+'</br>'
              }
              text += `<a href="">TODO: Add clickable to add this item to the input field</a></br>`
              layer.bindPopup(text);
            },
            pointToLayer: function (feature, latlng) {
              return L.circleMarker(latlng, style);
            }
          }
          );
          leafletLayer.setStyle(style);
          if(!geojson.uri){
            vue.leafletLayers[leafletLayer._leaflet_id] = leafletLayer;
          }else{
            vue.leafletLayers[geojson.uri] = leafletLayer;
          }
          if(group){
            group.addLayer(leafletLayer);
            vue.map.addLayer(vue.searchGroup);
          }else{
            vue.featureGroup.addLayer(leafletLayer);
          }
          if(zoom){
            vue.map.fitBounds(leafletLayer.getBounds());
          }else{
            if(group){
              vue.map.fitBounds(group.getBounds());
            }else{
              vue.map.fitBounds(vue.featureGroup.getBounds());
            }
          }

        } catch (error) {
          console.log(error.message);
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
          }catch(error){
            console.log(error)
            vue.errored = true;
          }
        },
      async getAllItems(){
        let vue = this;
        let collections = await vue.getCollections();
        for (let col of collections.collections){
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
        const url = `${vue.geoconnexUrl}/${collectionId}/${vue.apiQueryAppend}`;
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
            }catch(error){
              console.log(error)
              vue.geoCache.match(url).then(function (response) {
                console.log("Geoconnex API fetch error. Falling back to old cached version.")
                return response.data;
              }).catch(function (error){
                console.log(error)
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
      loadRelations(){
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
            if (item){
              vue.fetchGeometry(item).then(geometry =>{
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
      getGeoItemsInRange(){
        // https://turfjs.org/docs/#intersects
        // https://turfjs.org/docs/#booleanIntersects
        let vue=this;
        let center = turf.point([vue.lat, vue.long])
        var options = {
          steps: 10, 
          units: 'kilometers', 
          properties: {
            Radius: `${vue.radius} kilometers`,
            MaxArea: `${vue.maxArea} sq km`
          }
        };
        var circle = turf.circle(center, vue.radius * 1000, options);
        circle.text = "Search area";
        center.text = "Center point";
        // TODO: add these in a different group so that we can clear them?
        vue.addToMap(center, true, {color:'red', radius: 3, fillColor: 'black', fillOpacity: .8}, group=vue.searchGroup);
        vue.addToMap(circle, true, {color:'red', fillColor: 'red', fillOpacity: 0.1}, group=vue.searchGroup);

        for (let item of vue.items){
          vue.fetchGeometry(item).then(geometry =>{
            item.geometry = geometry.geometry;
            try{
              if (turf.area(item) < vue.maxArea*1e6){
                if(item.geometry.type.includes("Polygon") && turf.booleanIntersects(circle, item)){
                  vue.addToMap(item, false, {color:'green'}, group=vue.searchGroup);
                }
                if(item.geometry.type.includes("Point") && turf.booleanPointInPolygon(item, circle)){
                  vue.addToMap(item, false, {color:'green', radius: 5, fillColor: 'yellow', fillOpacity: 0.8}, group=vue.searchGroup);
                }
                if(item.geometry.type.includes("Line") && turf.booleanIntersects(circle, item)){
                  vue.addToMap(item, false, {color:'green'}, group=vue.searchGroup);
                }
              }
            }catch(e){
              console.log(e);
            }
          });
        }
      },
      clearSearches(){

      },
      fillFromExtent(){
        let vue = this;
        vue.lat = -72.56428830847662;
        vue.long = 42.85084818160041;
      },
      runGeoExample(){
        try{
          let vue=this;
          // CUAHSI
        // vue.getGeoItemsInRange([-72.56428830847662, 42.85084818160041])
  
        // SALT LAKE
        // vue.getGeoItemsInRange([-112.551445, 41.149411])
  
        // Glen Canyon
        // vue.getGeoItemsInRange([-111.48381550548234, 36.9378850872748]);
        
  
        // FL
        // vue.getGeoItemsInRange([-80.7839365138525, 26.932581283846268])
  
        // Salton sea
        // vue.getGeoItemsInRange([-115.827709, 33.317246]);
        }catch(e){
          console.log(e);
        }
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
        vue.createMap();
        vue.loadRelations();
        vue.loading = false;
      }else if(vue.resMode == "View" && vue.relations.length > 0){
        vue.geoCache = await caches.open(vue.cacheName);
        await vue.getOnlyRelationItems();
        vue.createMap();
        vue.loadRelations();
        vue.loading = false;
      }
    }
})