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

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 18,
        }).addTo(vue.map);

        vue.featureGroup =  L.featureGroup();
        vue.featureGroup.addTo(vue.map);
      },
      addToMap(geojson, zoom=false){
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
              layer.bindPopup(text);
            }}
          );
          vue.leafletLayers[geojson.uri] = leafletLayer;
          vue.featureGroup.addLayer(leafletLayer);
          if(zoom){
            vue.map.fitBounds(leafletLayer.getBounds());
          }else{
            vue.map.fitBounds(vue.featureGroup.getBounds());
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