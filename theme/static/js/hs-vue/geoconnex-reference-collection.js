let counter = 0;
let geoconnexApp = new Vue({
    el: '#app-geoconnex',
    delimiters: ['${', '}'],
    vuetify: new Vuetify(),
    data() {
        return{
            relations: RELATIONS,
            debug: false,
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
            debounceMilliseconds: 250,
            geoCache: null,
            resShortId: SHORT_ID,
            cacheDuration: 1000 * 60 * 60 * 24 * 7, // one week in milliseconds
            search: null,
        }
    },
    watch: {
      values(newValue, oldValue){
        this.errorMsg = "";
        if (newValue.length > oldValue.length){
          console.log("Adding selected element to metadata");
          let selected = newValue.pop();
          this.addMetadata(selected);
        }else if (newValue.length < oldValue.length){
          console.log("Removing element from metadata");
          let remove = oldValue.pop();
          console.log(remove);
          this.removeMetadata(remove);
        }
      }
    },
    methods: {
      async getCollections(){
          let vue = this;
          const collectionsUrl=`${this.geoconnexUrl}?f=json&lang=en-US`;
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
            let properties = feature.properties;
            properties.relative_id = properties.uri.split('ref/').pop();
            properties.text = `${properties.NAME} [${properties.relative_id}]`;
            vue.items.push(properties);
          }
        }
      },
      async getItemsIn(collectionId){
        let vue = this;
        const url = `${this.geoconnexUrl}/${collectionId}/${this.apiQueryAppend}`;
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
      loadRelations(){
        let vue = this;
        for (relation of this.relations){
          if (relation.type === "relation"){
            let text;
            try {
              new URL(relation.value);
              text = vue.items.find(obj => {
                return obj.uri === relation.value;
              }).text;
            } catch (_) {
              // if the relation value isn't a url, just load the custom text
              text = relation.value;
            }
            let data = {
              "id": relation.id,
              "text": text,
              "value": relation.value
            };
            vue.values.push(data);
          }
        }
      },
      addMetadata(selected){ 
        let vue = this;
        let url = `/hsapi/_internal/${this.resShortId}/relation/add-metadata/`;
        let data = {
          "type": 'relation',
          "value": selected.uri ? selected.uri : selected
        }
        $.ajax({
          type: "POST",
          url: url,
          data: data,
          success: function (result) {
            vue.values.push({
              "id":result.element_id,
              "value": selected.uri,
              "text": selected.text
            });
          },
          error: function (request, status, error) {
            vue.errorMsg = `${error} while attempting to add related feature.`;
            console.log(request.responseText);
          }
        });
      },
      removeMetadata(relation){
        let vue = this;
        let url = `/hsapi/_internal/${this.resShortId}/relation/${relation.id}/delete-metadata/`;
        console.log(`Removing metadata for id:${relation.id} via ${url}`);
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
    },
    async mounted() {
      let vue = this;
      vue.geoCache = await caches.open(vue.cacheName);
      await vue.getAllItems();
      vue.loadRelations();
      vue.loading = false;
      }

})
