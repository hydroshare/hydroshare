let counter = 0;
let geoconnexApp = new Vue({
    el: '#app-geoconnex',
    delimiters: ['${', '}'],
    vuetify: new Vuetify(),
    data() {
        return{
            relations: RELATIONS,
            debug: true,
            items: null,
            collections: null,
            values: [],
            loading: true,
            errored: false,
            geoconnexUrl: "https://reference.geoconnex.us/collections",
            apiQueryAppend: "items?f=json&lang=en-US&skipGeometry=true",
            cacheName: "geoconnexCache",
            debounceMilliseconds: 250,
            geoCache: null,
            resShortId: SHORT_ID,
            cacheDuration: 1000 * 60 * 60 * 24 * 7 // one week in milliseconds
        }
    },
    watch: {
      values(newValue, oldValue){
        if (newValue.length > oldValue.length){
          console.log("Adding element to metadata...");
          let added = newValue.pop();
          console.log(added);
          this.addMetadata(added.uri);
        }else if (newValue.length < oldValue.length){
          console.log("TODO remove element from metadata...");
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
        vue = this;
        let collections = await vue.getCollections();
        let massive = [];
        for (col of collections.collections){
          let header = { 
            header: `${col.description} (${col.id})`,
            text: `${col.description} (${col.id})`
          }
          massive.push(header);
          let resp = await vue.getItemsIn(col.id);
          for (feature of resp.features){
            let properties = feature.properties;
            properties.relative_id = properties.uri.split('ref/').pop();
            properties.text = `${properties.NAME} [${properties.relative_id}]`;
            massive.push(properties);
          }
        }
        return massive;
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
        for (relation of this.relations){
          if (relation.type === "relation"){
            this.values.push(relation.value);
          }
        }
      },
      addMetadata(value){ 
        console.log(`Creating metadata for value: ${value}`);
        let url = `/hsapi/_internal/${this.resShortId}/relation/add-metadata/`;
        let data = {
          "type": 'relation',
          "value": value
        }
        $.ajax({
          type: "POST",
          url: url,
          data: data,
          success: function (result) {
            console.log(result);
            // TODO: we should add this element_id to the items so that we can remove it later
            console.log(result.element_id);
          }
        });
      },
      removeMetadata(relation){
        let url = `/hsapi/_internal/${this.resShortId}/relation/${relation.id}/delete-metadata/`;
        console.log(`Removing metadata for id:${relation.id} via ${url}`);
        $.ajax({
          type: "POST",
          url: url,
          success: function (result) {
            console.log(result);
          }
        });
      }
    },
    async mounted() {
      let vue = this;
      vue.loadRelations();
      vue.geoCache = await caches.open(vue.cacheName);
      let items = await vue.getAllItems();
      vue.items = items;
      vue.loading = false;
      }

})
