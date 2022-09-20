const limitCollectionSize= 5000;
const geoconnexUrl = "https://reference.geoconnex.us/collections";
const geoconnexBaseURLQueryParam = `items?f=json&limit=${limitCollectionSize}`;
let geoconnexApp = new Vue({
  el: "#app-geoconnex",
  delimiters: ["${", "}"],
  vuetify: new Vuetify(),
  data() {
    return {
      metadataRelations: RELATIONS,
      relationObjects: [],
      debug: false,
      resMode: RESOURCE_MODE,
      resSpatialType: null,
      items: [],
      unfilteredItems: [],
      hasFilteredItems: false,
      collections: null,
      values: [],
      // TODO: isSearching was working for point select search. but now broken for all...
      isSearching: false,
      loadingCollections: true,
      loadingDescription: "",
      errorMsg: "",
      errored: false,
      cacheName: "geoconnexCache",
      collectionsDefaultHidden: ["principal_aq", "nat_aq"],
      ignoredCollections: ["pws"], // currently ignored because requests return as 500 errors
      geoCache: null,
      resShortId: SHORT_ID,
      cacheDuration: 0, // one week in milliseconds
      enforceCacheDuration: true,
      search: null,
      rules: null,
      showingMap: false,
      map: null,
      layerControl: null,
      selectedItemLayers: {},
      selectedFeatureGroup: null,
      selectedCollections: [],
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
      searchColor: "orange",
      selectColor: "purple",
    };
  },
  watch: {
    values(newValue, oldValue) {
      let geoconnexApp = this;
      geoconnexApp.errorMsg = "";

      let oldLength = oldValue ? oldValue.length : 0;
      let newLength = newValue ? newValue.length : 0;
      if (newLength > oldLength) {
        geoconnexApp.addSelectedToResMetadata(newValue.pop());
      } else if (newLength < oldLength) {
        let remove = oldValue.filter((obj) =>
          newValue.every((s) => s.id !== obj.id)
        );
        try {
          geoconnexApp.selectedFeatureGroup.removeLayer(
            geoconnexApp.selectedItemLayers[remove[0].value]
          );
          geoconnexApp.fitMapToFeatures();
        } catch (e) {
          console.error(e.message);
        }
        geoconnexApp.ajaxRemoveMetadata(remove);

        // re-enable the item for selection
        geoconnexApp.items.forEach((it) => {
          if (remove[0].value === it.uri) {
            it.disabled = false;
          }
        });
      }
    },
    selectedCollections(newValue, oldValue){
      let geoconnexApp = this;
      let oldLength = oldValue ? oldValue.length : 0;
      let newLength = newValue ? newValue.length : 0;
      if (newLength > oldLength) {
        geoconnexApp.queryUsingSpatialExtent([newValue.at(-1)]);
      } else if (newLength < oldLength) {
        let remove;
        if (newLength){
          remove = oldValue.filter((obj) =>
          newValue.every((s) => s.id !== obj.id)
          );
          for (let layer of remove) {
            geoconnexApp.searchFeatureGroup.removeLayer(
              geoconnexApp.layerGroupDictionary[layer.id]
            );
            geoconnexApp.layerGroupDictionary[layer.id].clearLayers();

            geoconnexApp.layerControl.removeLayer(
              geoconnexApp.layerGroupDictionary[layer.id]
            );
          }
        }else{
          geoconnexApp.clearLeafletOfMappedSearches()
          remove = oldValue;
        }

        geoconnexApp.fitMapToFeatures();
        for (let collection of remove){
          geoconnexApp.items = geoconnexApp.items.filter(item =>{
            return collection.id !== item.collection;
          });
        }
      }
    },
    loadingCollections(newValue, oldValue) {
      let geoconnexApp = this;
      if (!newValue) {
        $("#geoconnex-leaflet-info").show();
      }
    },
  },
  methods: {
    toggleItemFiltering() {
      let geoconnexApp = this;
      if (geoconnexApp.hasFilteredItems) {
        geoconnexApp.resetItems();
      } else {
        geoconnexApp.limitOptionsToMappedFeatures();
      }
    },
    resetItems() {
      let geoconnexApp = this;
      geoconnexApp.items = geoconnexApp.unfilteredItems;
      geoconnexApp.hasFilteredItems = false;
    },
    limitOptionsToMappedFeatures() {
      let geoconnexApp = this;
      geoconnexApp.loadingCollections = true;
      geoconnexApp.hasFilteredItems = true;
      // save a copy of the items
      geoconnexApp.unfilteredItems = geoconnexApp.items;

      // alternative to remove any unused collections
      // ommitted for now, as it is plenty fast just to use "filter"
      // geoconnexApp.items = geoconnexApp.items.filter(s => Object.keys(geoconnexApp.layerGroupDictionary).includes(s.collection));

      // remove all items currently not in the map search
      let keep = [];
      for (const val of Object.values(geoconnexApp.layerGroupDictionary)) {
        if (!val.uris.includes(undefined)) {
          keep = keep.concat(val.uris);
        }
      }
      geoconnexApp.items = geoconnexApp.items.filter((s) =>
        keep.includes(s.uri)
      );
      geoconnexApp.loadingCollections = false;
    },
    addSelectedToResMetadata(selected) {
      let geoconnexApp = this;
      geoconnexApp.addFeatureToMap(selected);
      geoconnexApp.ajaxSaveMetadata(selected);

      // disable so that it can't be duplicated
      geoconnexApp.items.forEach((it) => {
        if (selected.uri === it.uri) {
          it.disabled = true;
        }
      });
    },
    async addFeatureToMap(feature){
      let geoconnexApp = this;
      if (!feature.geometry){
        geoconnexApp.fetchSingleGeometry(feature).then((geometry) => {
          feature.geometry = geometry.geometry;
        });
        let shouldZoom = feature.geometry.type.includes("Poly");
        geoconnexApp.addToMap(feature, shouldZoom);
        shouldZoom ? null : geoconnexApp.fitMapToFeatures();
      }
    },
    async fetchSingleGeometry(geoconnexObj, refresh = false) {
      let geoconnexApp = this;
      if (refresh || !geoconnexObj.geometry) {
        let query = `${geoconnexUrl}/${geoconnexObj.collection}/items/${geoconnexObj.id}?f=json`;
        let response = await geoconnexApp.fetchFromCacheOrGeoconnex(query, refresh);
        geoconnexObj.geometry = response.geometry;
      }
      return geoconnexObj;
    },
    async fetchCollectionItemsInBbox(collection, bbox = null, refresh = false) {
      let geoconnexApp = this;
      let response = {};
      let query = `${geoconnexUrl}/${collection.id}/items/?f=json&bbox=${bbox.toString()}`;
      response = await geoconnexApp.fetchFromCacheOrGeoconnex(query, refresh);
      return response ? response.features : null
    },
    async fetchAllGeometries() {
      let geoconnexApp = this;
      var itemsWithGeo = [];
      const promises = [];

      for (let collection of geoconnexApp.collections) {
        const url = `${geoconnexUrl}/${collection.id}/${geoconnexBaseURLQueryParam}&skipGeometry=false`;
        promises.push(geoconnexApp.fetchFromCacheOrGeoconnex(url, false, collection));
      }

      const results = await Promise.all(promises);

      if (!$.isEmptyObject(results)) {
        for (let response of results) {
          if (response.features) {
            itemsWithGeo.push(
              geoconnexApp.createVuetifySelectSubheader(response.collection)
            );
            for (let feature of response.features) {
              itemsWithGeo.push(geoconnexApp.getFeatureProperties(feature));
            }
          }
        }
      }
      // overwrite now that we have the geometries
      geoconnexApp.items = itemsWithGeo;
      geoconnexApp.geometriesAreLoaded = true;
    },
    async fetchSingleReferenceItem(uri) {
      let geoconnexApp = this;
      let relative_id = uri.split("ref/").pop();
      let collection = relative_id.split("/")[0];
      let id = relative_id.split("/")[1];
      let query = `${geoconnexUrl}/${collection}/items/${id}?f=json`;
      let response = await geoconnexApp.fetchFromCacheOrGeoconnex(query);
      return response;
    },
    initLeafletFeatureGroups() {
      let geoconnexApp = this;
      geoconnexApp.selectedFeatureGroup = L.featureGroup();
      geoconnexApp.searchFeatureGroup = L.featureGroup();
    },
    initLeafletMap() {
      let geoconnexApp = this;
      geoconnexApp.selectedFeatureGroup ??
        geoconnexApp.initLeafletFeatureGroups();
      const southWest = L.latLng(-90, -180),
        northEast = L.latLng(90, 180);
      const bounds = L.latLngBounds(southWest, northEast);

      geoconnexApp.map = L.map("geoconnex-leaflet", {
        zoomControl: false,
        maxBounds: bounds,
        maxBoundsViscosity: 1.0,
      });

      let terrain = L.tileLayer(
        "https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.jpg",
        {
          attribution:
            'Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://www.openstreetmap.org/copyright">ODbL</a>.',
          maxZoom: 18,
        }
      );

      let streets = L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
          attribution:
            'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
          maxZoom: 18,
        }
      );

      let googleSat = L.tileLayer(
        "http://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        {
          maxZoom: 20,
          subdomains: ["mt0", "mt1", "mt2", "mt3"],
        }
      );

      let baseMaps = {
        Streets: streets,
        Terrain: terrain,
        Satelite: googleSat,
      };

      let overlayMaps = {
        "Selected Collection Items": geoconnexApp.selectedFeatureGroup,
      };
      if (geoconnexApp.resMode == "Edit") {
        overlayMaps["Search (all items)"] = geoconnexApp.searchFeatureGroup;
        geoconnexApp.map.addLayer(geoconnexApp.searchFeatureGroup);
      }
      L.control
        .zoom({
          position: "bottomright",
        })
        .addTo(geoconnexApp.map);

      geoconnexApp.layerControl = L.control.layers(baseMaps, overlayMaps, {
        position: "topright",
      });
      geoconnexApp.layerControl.addTo(geoconnexApp.map);

      L.control
        .fullscreen({
          position: "bottomright",
          title: {
            false: "Enter fullscreen",
            true: "Exit Fullscreen",
          },
        })
        .addTo(geoconnexApp.map);

      L.Control.GeoconnexRecenterButton = L.Control.extend({
        onAdd: function (map) {
          let recenterButton = L.DomUtil.create(
            "div",
            "leaflet-bar leaflet-control"
          );
          recenterButton.setAttribute("data-toggle", "tooltip");
          recenterButton.setAttribute("data-placement", "right");
          recenterButton.setAttribute("title", "Recenter");

          recenterButton.innerHTML = `<a role="button"><i class="fa fa-dot-circle-o fa-2x" style="padding-top:3px"></i></a>`;

          L.DomEvent.on(recenterButton, "click", (e) => {
            e.stopPropagation();
            geoconnexApp.fitMapToFeatures();
          });

          return recenterButton;
        },

        onRemove: function (map) {
          L.DomEvent.off();
        },
      });

      L.control.watermark = function (opts) {
        return new L.Control.GeoconnexRecenterButton(opts);
      };

      L.control
        .watermark({
          position: "bottomright",
        })
        .addTo(geoconnexApp.map);

      // show the default layers at start
      geoconnexApp.map.addLayer(streets);
      geoconnexApp.map.addLayer(geoconnexApp.selectedFeatureGroup);
      // USA
      // geoconnexApp.map.setView([41.850033, -87.6500523], 3);
      geoconnexApp.map.setView([30, 0], 1);
      geoconnexApp.setLeafletMapEvents();

      geoconnexApp.loadAllRelationGeometries();
    },
    addToMap(
      geojson,
      fit = false,
      style = { color: this.selectColor, radius: 5 },
      group = null
    ) {
      let geoconnexApp = this;
      try {
        let leafletLayer = L.geoJSON(geojson, {
          onEachFeature: function (feature, layer) {
            var popupText = `<h4>${feature.text}</h4>`;
            for (var k in feature.properties) {
              popupText += "<b>" + k + "</b>: ";
              if (k === "uri") {
                popupText += `<a href=${feature.properties[k]}>${feature.properties[k]}</a></br>`;
              } else {
                popupText += feature.properties[k] + "</br>";
              }
            }
            let hide = [
              "properties",
              "text",
              "geometry",
              "relative_id",
              "type",
              "links",
              "disabled",
            ];
            for (var k in feature) {
              if (hide.includes(k) | (k in feature.properties)) {
                continue;
              }
              popupText += "<b>" + k + "</b>: ";
              popupText += feature[k] + "</br>";
            }
            if (
              geoconnexApp.resMode == "Edit" &&
              style.color == geoconnexApp.searchColor
            ) {
              popupText += `<button type="button" class="white--text text-none v-btn v-btn--has-bg theme--light v-size--small btn btn-success map-add-geoconnex" data='${JSON.stringify(
                feature
              )}'>Add feature to resource metadata</button>`;
            } else if (
              geoconnexApp.resMode == "Edit" &&
              style.color == geoconnexApp.selectColor
            ) {
              popupText += `<button type="button" class="white--text text-none v-btn v-btn--has-bg theme--light v-size--small btn btn-danger map-remove-geoconnex" data='${JSON.stringify(
                feature
              )}'>Remove feature from resource metadata</button>`;
            }
            layer.bindPopup(popupText, { maxWidth: 400 });
          },
          pointToLayer: function (feature, latlng) {
            return L.circleMarker(latlng, style);
          },
        });
        leafletLayer.setStyle(style);
        if (geojson.uri) {
          geoconnexApp.selectedItemLayers[geojson.uri] = leafletLayer;
        }
        if (group) {
          group.addLayer(leafletLayer);
        } else {
          geoconnexApp.selectedFeatureGroup.addLayer(leafletLayer);
        }
        if (group === geoconnexApp.searchFeatureGroup) {
          if (!geojson.collection) {
            geojson.collection = "Search Bounds";
          }
          // check if layergroup exists in the "dictionary"
          if (
            !geoconnexApp.layerGroupDictionary ||
            geoconnexApp.layerGroupDictionary[geojson.collection] == undefined
          ) {
            geoconnexApp.layerGroupDictionary[geojson.collection] =
              L.layerGroup();
            geoconnexApp.layerGroupDictionary[geojson.collection].uris = [];
            geoconnexApp.layerControl.addOverlay(
              geoconnexApp.layerGroupDictionary[geojson.collection],
              geojson.collection
            );
            geoconnexApp.layerControl.expand();
          }
          geoconnexApp.map.addLayer(
            geoconnexApp.layerGroupDictionary[geojson.collection]
          );
          geoconnexApp.layerGroupDictionary[geojson.collection].addLayer(
            leafletLayer
          );
          geoconnexApp.layerGroupDictionary[geojson.collection].uris.push(
            geojson.uri
          );

          // we have to remove defaultHidden layers after adding them (we can't just not add them above)
          if (
            geoconnexApp.collectionsDefaultHidden.includes(geojson.collection)
          ) {
            geoconnexApp.map.removeLayer(
              geoconnexApp.layerGroupDictionary[geojson.collection]
            );
          }
        }

        // handle zooming
        if (fit) {
          geoconnexApp.map.fitBounds(leafletLayer.getBounds());
        }
      } catch (e) {
        console.error(e.message);
      }
    },
    fitMapToFeatures(group = null) {
      let geoconnexApp = this;
      try {
        if (group) {
          geoconnexApp.map.fitBounds(group.getBounds());
        } else {
          if (geoconnexApp.selectedFeatureGroup.getLayers().length !== 0) {
            geoconnexApp.map.fitBounds(
              geoconnexApp.selectedFeatureGroup.getBounds()
            );
          } else if (geoconnexApp.searchFeatureGroup.getLayers().length !== 0) {
            geoconnexApp.map.fitBounds(
              geoconnexApp.searchFeatureGroup.getBounds()
            );
          } else {
            // USA
            // geoconnexApp.map.setView([41.850033, -87.6500523], 3);
            geoconnexApp.map.setView([30, 0], 1);
          }
        }
      } catch (e) {
        console.warn(e.message);
      }
    },
    setCustomItemRules() {
      let geoconnexApp = this;
      geoconnexApp.rules = [
        function (v) {
          let invalid = [];
          for (let item of v) {
            try {
              url = new URL(item.value);
            } catch (_) {
              invalid.push(item.text);
            }
          }
          if (invalid.length === 1) {
            return `"${invalid}" is not a valid URI. We recommend that your custom feature be linkable`;
          }
          if (invalid.length === 2) {
            return `"${invalid.join(
              '" and "'
            )}" are not a valid URIs. We recommend that custom features be linkable.`;
          }
          if (invalid.length > 2) {
            return `"${invalid
              .join('", "')
              .replace(
                /, ([^,]*)$/,
                " and $1"
              )}" are not a valid URIs. We recommend that custom features be linkable`;
          }
          return true;
        },
      ];
    },
    async loadCollections(forceFresh = false) {
      let geoconnexApp = this;
      geoconnexApp.loadingCollections = true;
      try {
        let response = await geoconnexApp.fetchFromCacheOrGeoconnex(
          `${geoconnexUrl}?f=json&skipGeometry=true`,
          forceFresh
        );
        geoconnexApp.collections = response.collections.filter(col => {
          return !geoconnexApp.ignoredCollections.includes(col.id);
        });
      } catch (e) {
        console.error(e.message);
        geoconnexApp.errored = true;
      }
      geoconnexApp.loadingCollections = false;
    },
    createVuetifySelectSubheader(collection) {
      return {
        header: `${collection.description} (${collection.id})`,
        text: `${collection.description} (${collection.id})`,
      };
    },
    async loadAllCollectionItemsWithoutGeometries(forceFresh = false) {
      const promises = [];
      let geoconnexApp = this;
      for (let col of geoconnexApp.collections) {
        geoconnexApp.loadingDescription = col.description;
        promises.push(geoconnexApp.getItemsIn(col, forceFresh));
      }
      const results = await Promise.all(promises);
      for (let resp of results.flat()) {
        if (!jQuery.isEmptyObject(resp) && resp.features) {
          geoconnexApp.items.push(
            geoconnexApp.createVuetifySelectSubheader(resp.collection)
          );
          for (let feature of resp.features) {
            geoconnexApp.items.push(geoconnexApp.getFeatureProperties(feature));
          }
        }
      }
    },
    async refreshItemsSilently() {
      const promises = [];
      let geoconnexApp = this;
      if (geoconnexApp.debug) console.log("Refreshing from Geoconnex API");
      await geoconnexApp.loadCollections(true);
      let refreshedItems = [];
      for (let col of geoconnexApp.collections) {
        promises.push(geoconnexApp.getItemsIn(col, true));
      }
      const results = await Promise.all(promises);
      for (let resp of results) {
        if (!jQuery.isEmptyObject(resp) && resp.features) {
          refreshedItems.push(
            geoconnexApp.createVuetifySelectSubheader(resp.collection)
          );
          for (let feature of resp.features) {
            refreshedItems.push(geoconnexApp.getFeatureProperties(feature));
          }
        }
      }
      geoconnexApp.items = refreshedItems;
      if (geoconnexApp.debug)
        console.log("Completed background refresh from Geoconnex API");
    },
    setFeatureName(feature){
      feature.NAME = feature.properties.NAME;
      if (feature.properties.AQ_NAME) {
        feature.NAME = feature.properties.AQ_NAME;
      }
      if (feature.properties.name) {
        feature.NAME = feature.properties.name;
      }
      if (feature.properties.name_at_outlet) {
        feature.NAME = feature.properties.name_at_outlet;
      }
      if (feature.properties.SHR) {
        feature.NAME = feature.properties.SHR;
      }
      if (feature.properties.NAME10) {
        feature.NAME = feature.properties.NAME10;
      }
    },
    getFeatureProperties(feature) {
      let geoconnexApp = this;
      // Account for some oddities in the Geoconnex API schema
      feature.relative_id = feature.properties.uri.split("ref/").pop();
      feature.collection = feature.relative_id.split("/")[0];
      feature.uri = feature.properties.uri;
      geoconnexApp.setFeatureName(feature);
      feature.text = `${feature.NAME} [${feature.relative_id}]`;

      //prevent duplicate selections
      geoconnexApp.values.forEach((it) => {
        if (feature.uri === it.value) {
          feature.disabled = true;
        }
      });
      return feature;
    },
    async getRelationsFromMetadata() {
      let geoconnexApp = this;
      for (let relation of geoconnexApp.metadataRelations) {
        if (
          this.isUrl(relation.value) &&
          relation.value.indexOf("geoconnex") > -1
        ) {
          let feature = await geoconnexApp.fetchSingleReferenceItem(
            relation.value
          );
          // TODO: only push if not alreay an item?
          geoconnexApp.items.push(geoconnexApp.getFeatureProperties(feature));
          geoconnexApp.addFeatureToMap(feature);
        }
      }
    },
    async getItemsIn(collection, forceFresh = false) {
      let geoconnexApp = this;
      const url = `${geoconnexUrl}/${collection.id}/${geoconnexBaseURLQueryParam}&skipGeometry=true`;
      let featureCollection = await geoconnexApp.fetchFromCacheOrGeoconnex(url, forceFresh);
      featureCollection.collection = collection;
      return featureCollection;
    },
    async fetchFromCacheOrGeoconnex(url, forceFresh = false, collection = null) {
      let geoconnexApp = this;
      let data = {};
      if (!("caches" in window)) {
        if (geoconnexApp.debug)
          console.log(
            "Cache API not available. Fetching geoconnex data from:\n" + url
          );
        let fetch_resp = await fetch(url);
        if (!fetch_resp.ok) {
          console.error(
            `Error when attempting to fetch: ${fetch_resp.statusText}`
          );
        } else {
          data = await fetch_resp.json();
        }
      } else {
        let cache_resp = await geoconnexApp.geoCache.match(url);
        if (geoconnexApp.isCacheValid(cache_resp) && !forceFresh) {
          if (geoconnexApp.debug)
            console.log("Using Geoconnex from cache for:\n" + url);
          data = await cache_resp.json();
        } else {
          data = await geoconnexApp.fetchFromGeoconnex(url);
        }
      }
      if (collection && data) {
        data.collection = collection;
      }
      return data;
    },
    async fetchFromGeoconnex(url) {
      let fetchData = {};
      let geoconnexApp = this;
      if (geoconnexApp.debug)
        console.log("Fetching + adding to cache, geoconnex data from:\n" + url);
      try {
        let fetch_resp = await fetch(url);
        if (!fetch_resp.ok) {
          console.error(
            `Error when attempting to fetch Geoconnex relations: ${fetch_resp.statusText}`,
            fetch_resp
          );
        } else {
          let copy = fetch_resp.clone();
          let headers = new Headers(copy.headers);
          headers.append("fetched-on", new Date().getTime());
          let body = await copy.blob();
          geoconnexApp.geoCache.put(
            url,
            new Response(body, {
              status: copy.status,
              statusText: copy.statusText,
              headers: headers,
            })
          );
          fetchData = await fetch_resp.json();
        }
      } catch (e) {
        console.error(e.message);
        geoconnexApp.geoCache
          .match(url)
          .then(function (response) {
            console.error(
              "Geoconnex API fetch error. Falling back to old cached version."
            );
            return response.data;
          })
          .catch(function (e) {
            console.error(e.message);
            geoconnexApp.errored = true;
          });
      }
      return fetchData;
    },
    isCacheValid(response) {
      let geoconnexApp = this;
      if (!response || !response.ok) return false;
      if (geoconnexApp.enforceCacheDuration) {
        var fetched = response.headers.get("fetched-on");
        if (
          fetched &&
          parseFloat(fetched) + geoconnexApp.cacheDuration >
            new Date().getTime()
        )
          return true;
        if (geoconnexApp.debug) console.log("Cached data not valid.");
        return false;
      }
      return true;
    },
    isUrl(stringToTest) {
      try {
        new URL(stringToTest);
      } catch (_) {
        return false;
      }
      return true;
    },
    loadMetadataRelations() {
      // TODO redo this function so that it doesn't rely on preloaded items to get properties
      let geoconnexApp = this;
      for (relation of geoconnexApp.metadataRelations) {
        if (relation.type === "relation") {
          let item;
          try {
            new URL(relation.value);
            item = geoconnexApp.items.find((obj) => {
                return obj.uri && obj.uri == relation.value;
            });
          } catch (_) {
            item = null;
          }
          let data = {
            id: relation.id,
            text: item ? item.text : relation.value,
            value: relation.value,
          };
          geoconnexApp.values.push(data);

          // disable already selected items
          geoconnexApp.items.forEach((it) => {
            if (item && item.uri === it.uri) {
              it.disabled = true;
            }
          });

          if (item) {
            geoconnexApp.relationObjects.push(item);
          }
        }
      }
      geoconnexApp.loadingCollections = false;
    },
    async loadAllRelationGeometries() {
      let geoconnexApp = this;
      for (relation of geoconnexApp.relationObjects) {
        if (relation && geoconnexApp.showingMap) {
          let geometry = await geoconnexApp.fetchSingleGeometry(relation);
          relation.geometry = geometry.geometry;
          geoconnexApp.addToMap(relation, false);
        }
      }
      geoconnexApp.fitMapToFeatures();
    },
    ajaxSaveMetadata(selected) {
      let geoconnexApp = this;
      let url = `/hsapi/_internal/${geoconnexApp.resShortId}/relation/add-metadata/`;
      let data = {
        type: "relation",
        value: selected.uri ? selected.uri : selected,
      };
      $.ajax({
        type: "POST",
        url: url,
        data: data,
        success: function (result) {
          if (geoconnexApp.debug)
            console.log(
              `Added ${
                selected.text ? selected.text : selected
              } to resource metadata`
            );
          geoconnexApp.values.push({
            id: result.element_id,
            value: selected.uri ? selected.uri : selected,
            text: selected.text ? selected.text : selected,
          });
        },
        error: function (request, status, error) {
          geoconnexApp.errorMsg = `${error} while attempting to add related feature.`;
          console.error(request.responseText);
        },
      });
    },
    ajaxRemoveMetadata(relations) {
      let geoconnexApp = this;
      for (let relation of relations) {
        if (relation.id) {
          let url = `/hsapi/_internal/${geoconnexApp.resShortId}/relation/${relation.id}/delete-metadata/`;
          $.ajax({
            type: "POST",
            url: url,
            success: function (result) {
              if (geoconnexApp.debug)
                console.log(
                  `Removed ${
                    relation.text ? relation.text : relation
                  } from resource metadata`
                );
            },
            error: function (request, status, error) {
              geoconnexApp.errorMsg = `${error} while attempting to remove related feature.`;
              console.error(request.responseText);
            },
          });
        }
      }
    },
    getGeoItemsFromDebug(collections = null) {
      let geoconnexApp = this;
      geoconnexApp.isSearching = true;
      geoconnexApp.queryGeoItemsFromExtent(collections);
      geoconnexApp.isSearching = false;
    },
    queryGeoItemsFromExtent(collections = null) {
      let geoconnexApp = this;
      if (geoconnexApp.resSpatialType == "point") {
        // Geoconnex API only acccepts bounding box
        // if point, just make it a small bounding box
        var bbox = [
          geoconnexApp.pointLong,
          geoconnexApp.pointLat,
          geoconnexApp.pointLong + 1,
          geoconnexApp.pointLat + 1,
        ];
      } else if (geoconnexApp.resSpatialType == "box") {
        var bbox = [
          geoconnexApp.eastLong,
          geoconnexApp.southLat,
          geoconnexApp.westLong,
          geoconnexApp.northLat,
        ];
      } else {
        alert("Spatial extent isn't set?....");
      }
      geoconnexApp.queryGeoItemsInBbox(bbox, collections);
      geoconnexApp.hasExtentSearch = true;
    },
    queryGeoItemsRadius(lat = null, long = null) {
      let geoconnexApp = this;
      long = typeof long == "number" ? long : geoconnexApp.pointLong;
      lat = typeof lat == "number" ? lat : geoconnexApp.pointLat;
      let center = turf.point([long, lat]);
      let sides = geoconnexApp.searchRadius / 100;
      var options = {
        steps: sides < 25 ? 25 : sides,
        units: "kilometers",
        properties: {
          Radius: `${geoconnexApp.searchRadius} kilometers`,
        },
      };
      var polygon = turf.circle(center, geoconnexApp.searchRadius, options);
      polygon.text = "Search bounds";
      geoconnexApp.queryGeoItemsInPoly(polygon);
    },
    async queryGeoItemsContainingPoint(lat = null, long = null) {
      // https://turfjs.org/docs/#booleanPointInPolygon
      let geoconnexApp = this;
      long = typeof long == "number" ? long : geoconnexApp.pointLong;
      lat = typeof lat == "number" ? lat : geoconnexApp.pointLat;
      let center = turf.point([long, lat]);
      center.text = "Search point";
      geoconnexApp.isSearching = true;
      geoconnexApp.map.closePopup();

      var bbox = [
        long,
        lat,
        long + 10e-12,
        lat + 10e-12,
      ];
      geoconnexApp.queryGeoItemsInBbox(bbox);
    },
    async queryGeoItemsInBbox(bbox, collections = null) {
      let geoconnexApp = this;
      let items = [];
      // TODO: this doesn't work
      geoconnexApp.isSearching = true;
      geoconnexApp.map.closePopup();
      let poly = turf.bboxPolygon(bbox)
      poly.text = "Search bounds";
      geoconnexApp.addToMap(
        poly,
        false,
        { color: "red", fillColor: "red", fillOpacity: 0.1 },
        (group = geoconnexApp.searchFeatureGroup)
      );
      try {
        if (!collections){
          // fetch items from all collections
          collections = geoconnexApp.collections;
        }

        const promises = [];
        for (collection of collections){
          promises.push(geoconnexApp.fetchCollectionItemsInBbox(collection, bbox));
        }
        let results = await Promise.all(promises);
        items = results.flat().filter(Boolean);

        for (let item of items){
          let alreadySelected = geoconnexApp.values.find((obj) => {
            return obj.value && obj.value === item.uri;
          });
          if (alreadySelected) {
            item.disabled = true;
          }else{
            geoconnexApp.getFeatureProperties(item);
            if (item.geometry.type.includes("Point")) {
              await geoconnexApp.addToMap(
                item,
                false,
                {
                  color: geoconnexApp.searchColor,
                  radius: 5,
                  fillColor: "yellow",
                  fillOpacity: 0.8,
                },
                (group = geoconnexApp.searchFeatureGroup)
              );
            } else {
              await geoconnexApp.addToMap(
                item,
                false,
                { color: geoconnexApp.searchColor },
                (group = geoconnexApp.searchFeatureGroup)
              );
            }
          }
          // TODO: sometimes this works but not always?
          // seems like there are some odd state not refreshing issues
          geoconnexApp.items.push(item);

          let addCollection = item.collection;
          if (geoconnexApp.selectedCollections == [] || !geoconnexApp.selectedCollections.map(col => col.id).includes(addCollection)){
            addCollection = geoconnexApp.collections.filter(col=>{
              return col.id == addCollection
            });
            geoconnexApp.selectedCollections.push(
              addCollection.pop()
            );
          }
        }
      } catch (e) {
        console.error(
          `Error while attempting to find intersecting geometries: ${e.message}`
        );
      }

      geoconnexApp.fitMapToFeatures(geoconnexApp.searchFeatureGroup);
      geoconnexApp.isSearching = false;
      geoconnexApp.hasSearches = true;
      geoconnexApp.toggleItemFiltering();
    },
    async queryGeoItemsInPoly(polygon = null) {
      // https://turfjs.org/docs/#intersects
      // https://turfjs.org/docs/#booleanIntersects
      // https://turfjs.org/docs/#booleanContains
      let geoconnexApp = this;
      geoconnexApp.isSearching = true;
      geoconnexApp.map.closePopup();
      const promises = [];

      geoconnexApp.addToMap(
        polygon,
        false,
        { color: "red", fillColor: "red", fillOpacity: 0.1 },
        (group = geoconnexApp.searchFeatureGroup)
      );
      try {
        for (let item of geoconnexApp.items) {
          if (item.header) continue;
          geoconnexApp.loadingDescription = item.collection;
          let alreadySelected = geoconnexApp.values.find((obj) => {
            return obj.value === item.uri;
          });
          if (alreadySelected) {
            continue;
          }
          promises.push(geoconnexApp.fetchSingleGeometry(item));
        }

        const results = await Promise.all(promises);

        for (item of results) {
          if (turf.area(item) < geoconnexApp.maxAreaToReturn * 1e6) {
            if (turf.booleanIntersects(polygon, item)) {
              if (item.geometry.type.includes("Point")) {
                await geoconnexApp.addToMap(
                  item,
                  false,
                  {
                    color: geoconnexApp.searchColor,
                    radius: 5,
                    fillColor: "yellow",
                    fillOpacity: 0.8,
                  },
                  (group = geoconnexApp.searchFeatureGroup)
                );
              } else {
                await geoconnexApp.addToMap(
                  item,
                  false,
                  { color: geoconnexApp.searchColor },
                  (group = geoconnexApp.searchFeatureGroup)
                );
              }
            }
          }
        }
      } catch (e) {
        console.error(
          `Error while attempting to find intersecting geometries: ${e.message}`
        );
      }

      geoconnexApp.fitMapToFeatures(geoconnexApp.searchFeatureGroup);
      geoconnexApp.isSearching = false;
      geoconnexApp.hasSearches = true;
      geoconnexApp.toggleItemFiltering();
    },
    clearLeafletOfMappedSearches() {
      let geoconnexApp = this;
      geoconnexApp.searchFeatureGroup.clearLayers();
      for (let key in geoconnexApp.layerGroupDictionary) {
        geoconnexApp.layerControl.removeLayer(
          geoconnexApp.layerGroupDictionary[key]
        );
        delete geoconnexApp.layerGroupDictionary[key];
      }

      geoconnexApp.hasSearches = false;
      geoconnexApp.hasExtentSearch = false;
      geoconnexApp.selectedCollections = null;
      geoconnexApp.fitMapToFeatures();
      geoconnexApp.layerControl.collapse();
    },
    queryUsingSpatialExtent(collections = null) {
      let geoconnexApp = this;
      geoconnexApp.isSearching = true;

      // force isSearching state to updated before running search
      setTimeout(async function () {
        geoconnexApp.fillValuesFromResExtent();
        geoconnexApp.queryGeoItemsFromExtent(collections);
        geoconnexApp.isSearching = false;
      }, 0);
    },
    updateSpatialExtentType() {
      let geoconnexApp = this;
      let spatial_coverage_drawing = $("#coverageMap .leaflet-interactive");
      if (spatial_coverage_drawing.size() > 0) {
        let checked = $("#div_id_type input:checked").val();
        geoconnexApp.resSpatialType = checked;
      } else {
        geoconnexApp.resSpatialType = null;
      }
    },
    fillValuesFromResExtent() {
      let geoconnexApp = this;
      geoconnexApp.updateSpatialExtentType();
      if (geoconnexApp.resSpatialType == "point") {
        geoconnexApp.fillValuesFromResPointExtent();
      } else if (geoconnexApp.resSpatialType == "box") {
        geoconnexApp.fillValuesFromResBoxExtent();
      } else {
        console.error("Resource spatial extent isn't set");
        // TODO: decide what functionality we should allow in the case that no spatial extent
      }
    },
    fillValuesFromResPointExtent() {
      let geoconnexApp = this;
      geoconnexApp.pointLat = $("#id_north").val();
      geoconnexApp.pointLong = $("#id_east").val();
    },
    fillValuesFromResBoxExtent() {
      let geoconnexApp = this;
      geoconnexApp.northLat = $("#id_northlimit").val();
      geoconnexApp.eastLong = $("#id_eastlimit").val();
      geoconnexApp.southLat = $("#id_southlimit").val();
      geoconnexApp.westLong = $("#id_westlimit").val();
    },
    fillValuesFromResCoordinates(lat, long) {
      let geoconnexApp = this;
      geoconnexApp.pointLat = lat;
      geoconnexApp.pointLong = long;
    },
    setLeafletMapEvents() {
      let geoconnexApp = this;
      var popup = L.popup({ maxWidth: 400 });

      function onMapClick(e) {
        let loc = { lat: e.latlng.lat, long: e.latlng.lng };
        let content = `<button type="button" class="white--text text-none v-btn v-btn--has-bg theme--light v-size--small btn btn-success leaflet-point-search" data='${JSON.stringify(
          loc
        )}'>Search all collections for items containing this point</button>`;
        // TODO: maby make this "search selected collections --in the typeahead, instead of all collections"
        popup
          .setLatLng(e.latlng)
          .setContent(content)
          .openOn(geoconnexApp.map);
      }

      if (geoconnexApp.resMode === "Edit") {
        geoconnexApp.map.on("click", onMapClick);

        $("#geoconnex-map-wrapper").on(
          "click",
          "button.leaflet-point-search",
          function (e) {
            e.stopPropagation();
            const loc = JSON.parse($(this).attr("data"));
            geoconnexApp.fillValuesFromResCoordinates(loc.lat, loc.long);
            geoconnexApp.queryGeoItemsContainingPoint(loc.lat, loc.long);
          }
        );

        $("#geoconnex-map-wrapper").on(
          "click",
          "button.map-add-geoconnex",
          function (e) {
            e.stopPropagation();
            let data = JSON.parse($(this).attr("data"));
            let alreadySelected = geoconnexApp.values.find((obj) => {
              return obj.value === data.uri;
            });
            if (!alreadySelected) {
              geoconnexApp.addSelectedToResMetadata(data);
            }
            geoconnexApp.map.closePopup();
          }
        );

        $("#geoconnex-map-wrapper").on(
          "click",
          "button.map-remove-geoconnex",
          function (e) {
            e.stopPropagation();
            let data = JSON.parse($(this).attr("data"));
            geoconnexApp.values = geoconnexApp.values.filter(
              (s) => s.value !== data.uri
            );
            geoconnexApp.map.closePopup();
          }
        );
      }

      // listen for spatial coverage  type change
      $("#div_id_type input[type=radio]").change((e) => {
        geoconnexApp.resSpatialType = e.target.value;
      });
    },
    toggleMapVisibility() {
      let geoconnexApp = this;
      geoconnexApp.showingMap = !geoconnexApp.showingMap;
      // force state refresh
      setTimeout(function () {
        if (geoconnexApp.showingMap && geoconnexApp.map == null) {
          geoconnexApp.updateSpatialExtentType();
          geoconnexApp.initLeafletMap();
        }
      }, 0);
    },
    showMap() {
      let geoconnexApp = this;
      geoconnexApp.showingMap = true;
      // force state refresh
      setTimeout(function () {
        if (geoconnexApp.showingMap && geoconnexApp.map == null) {
          geoconnexApp.updateSpatialExtentType();
          geoconnexApp.initLeafletMap();
        }
      }, 0);
    }
  },
  beforeMount() {
    this.setCustomItemRules();
  },
  async mounted() {
    let geoconnexApp = this;
    if (geoconnexApp.resMode == "Edit") {
      geoconnexApp.geoCache = await caches.open(geoconnexApp.cacheName);
      await geoconnexApp.loadCollections(false);

      // TODO: only show the collectionOptions without loading all the other stuff
      // TODO: maybe we need to only load items from the selected collection? to reduce load time...

      // await geoconnexApp.loadAllCollectionItemsWithoutGeometries(false);

      await geoconnexApp.getRelationsFromMetadata();
      geoconnexApp.loadMetadataRelations();
      geoconnexApp.initLeafletFeatureGroups();
      geoconnexApp.showMap();
      
      // TODO: load items/geoms in the background and cache so that it is faster next time?
      // geoconnexApp.fetchAllGeometries();
      // refresh cache in the background
      // geoconnexApp.refreshItemsSilently();

    } else if (
      geoconnexApp.resMode == "View" &&
      geoconnexApp.metadataRelations.length > 0
    ) {
      geoconnexApp.showingMap = true;
      geoconnexApp.geoCache = await caches.open(geoconnexApp.cacheName);
      await geoconnexApp.getRelationsFromMetadata();
      geoconnexApp.loadMetadataRelations();
      geoconnexApp.initLeafletMap();
    }
  },
});
