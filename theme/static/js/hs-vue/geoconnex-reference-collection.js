const limitNumberOfItemsPerRequest= 50000;
const geoconnexBaseURLQueryParam = `items?f=json&limit=${limitNumberOfItemsPerRequest}`;
let geoconnexApp = new Vue({
  el: "#app-geoconnex",
  delimiters: ["${", "}"],
  vuetify: new Vuetify(),
  data() {
    return {
      // TODO: organize parameters and functions so that they are grouped in a way that makes sense
      metadataRelations: RELATIONS,
      relationObjects: [],
      debug: true,
      resMode: RESOURCE_MODE,
      resSpatialType: null,
      items: [],
      unfilteredItems: [],
      collections: null,
      selectedReferenceItems: [],
      loadingCollections: true,
      searchingDescription: "",
      loadingRelations: true,
      appMessages: [],
      collectionMessages: [],
      featureMessages: [],
      geoconnexUrl: "https://reference.geoconnex.us/collections",
      cacheName: "geoconnexCache",
      ignoredCollections: ["pws"], // currently ignored because requests return as 500 errors
      limitNumberOfItemsPerRequest: limitNumberOfItemsPerRequest,
      geoCache: null,
      resShortId: SHORT_ID,
      cacheDuration: 6.048e+8, // one week in milliseconds
      enforceCacheDuration: false,
      collectionTypeahead: null,
      itemTypeahead: null,
      rules: null,
      showingMap: true,
      map: null,
      layerControl: null,
      stringLengthLimit: 30, 
      selectedItemLayers: {},
      selectedFeatureGroup: null,
      selectedCollections: [],
      lockCollections: false,
      limitToSingleCollection: true,
      hasSearches: false,
      searchFeatureGroup: null,
      spatialExtentGroup: null,
      layerGroupDictionary: {},
      largeExtentWarningThreshold: 5e+11, // sq meters
      pointLat: 0,
      pointLong: 0,
      northLat: null,
      eastLong: null,
      southLat: null,
      westLong: null,
      bBox: null,
      infoColor: "#3a87ad",
      pointFillColor: "yellow",
      searchColor: "orange",
      selectColor: "purple",
      spatialExtentColor: "red",
      log: console.log.bind(window.console, "%cGeoconnex:", "color: white; background:blue;"),
      warn: console.warn.bind(window.console, "%cGeoconnex warning:", "color: white; background:blue;"),
      error: console.error.bind(window.console, "%cGeoconnex error:", "color: white; background:blue;")
    };
  },
  computed: {
    hasSelections() {
      return this.selectedCollections.length > 0 || this.selectedReferenceItems.length > 0
    }
  },
  watch: {
    selectedReferenceItems(newValue, oldValue) {
      let geoconnexApp = this;
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
          geoconnexApp.error(e.message);
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
    async selectedCollections(newValue, oldValue){
      let geoconnexApp = this;
      let oldLength = oldValue ? oldValue.length : 0;
      let newLength = newValue ? newValue.length : 0;
      
      if(geoconnexApp.limitToSingleCollection){
        newLength == 1 && (geoconnexApp.lockCollections = true);
        newLength == 0 && (geoconnexApp.lockCollections = false);
      }

      if (newLength > oldLength) {
        geoconnexApp.hasSearches = true;
        let newCollection = newValue.at(-1);
        if(geoconnexApp.resSpatialType){
          geoconnexApp.queryGeoItemsFromExtent([newCollection]);
        }else{
          geoconnexApp.searchingDescription = newCollection.description;
          let featureCollection = await geoconnexApp.getItemsIn(newCollection, forceFresh = false, skipGeometry = false);
          geoconnexApp.addFeaturesToMap(featureCollection.features, featureCollection.collection);
          geoconnexApp.searchingDescription = "";
        }
      } else if (newLength < oldLength) {
        let remove;
        if (newLength){
          remove = oldValue.filter((obj) =>
          newValue.every((s) => s.id !== obj.id)
          );
        }else{
          remove = oldValue;
          geoconnexApp.hasSearches = false;
        }

        // TODO: maybe we remove layers even if the map is hidden?
        if (geoconnexApp.showingMap){
          if (newLength){
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
          }
          geoconnexApp.fitMapToFeatures();
        }else{
          if (newLength){
            geoconnexApp.unmappedSelectedCollectionIds = geoconnexApp.unmappedSelectedCollectionIds.filter(col=>col != remove[0].id);
          }else{
            geoconnexApp.unmappedSelectedCollectionIds = [];
          }
        }

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
    limitOptionsToMappedFeatures() {
      let geoconnexApp = this;
      geoconnexApp.loadingCollections = true;
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
      geoconnexApp.addSelectedFeatureToMap(selected);
      geoconnexApp.ajaxSaveMetadata(selected);

      // disable so that it can't be duplicated
      geoconnexApp.items.forEach((it) => {
        if (selected.uri === it.uri) {
          it.disabled = true;
        }
      });
    },
    addSelectedFeatureToMap(feature){
      let geoconnexApp = this;
      if (!feature.geometry){
        geoconnexApp.fetchSingleGeometry(feature).then((geometry) => {
          feature.geometry = geometry.geometry;
        });
      }
      geoconnexApp.addToMap(feature);
    },
    async fetchSingleGeometry(geoconnexObj, refresh = false) {
      let geoconnexApp = this;
      geoconnexApp.searchingDescription = geoconnexObj.collection;
      if (refresh || !geoconnexObj.geometry) {
        let query = `${geoconnexApp.geoconnexUrl}/${geoconnexObj.collection}/items/${geoconnexObj.id}?f=json`;
        let response = await geoconnexApp.fetchFromCacheOrGeoconnex(query, refresh);
        geoconnexObj.geometry = response.geometry;
      }
      geoconnexApp.searchingDescription = "";
      return geoconnexObj;
    },
    async fetchCollectionItemsInBbox(collection, bbox = null, refresh = false) {
      let geoconnexApp = this;
      geoconnexApp.searchingDescription = collection.description
      let response = {};
      let query = `${geoconnexApp.geoconnexUrl}/${collection.id}/${geoconnexBaseURLQueryParam}&bbox=${bbox.toString()}`;
      response = await geoconnexApp.fetchFromCacheOrGeoconnex(query, refresh);
      geoconnexApp.searchingDescription = "";

      // store the collection for future reference
      response && response.features.forEach(feature=>{feature.collection = collection});
      return response ? response.features : null
    },
    async fetchSingleReferenceItem(uri) {
      let geoconnexApp = this;
      geoconnexApp.searchingDescription = uri;
      let relative_id = uri.split("ref/").pop();
      let collection = relative_id.split("/")[0];
      let id = relative_id.split("/")[1];
      let query = `${geoconnexApp.geoconnexUrl}/${collection}/items/${id}?f=json`;
      let response = await geoconnexApp.fetchFromCacheOrGeoconnex(query);
      geoconnexApp.searchingDescription = "";
      return response;
    },
    initLeafletMap() {
      let geoconnexApp = this;
      geoconnexApp.selectedFeatureGroup = L.featureGroup();
      geoconnexApp.searchFeatureGroup = L.featureGroup();
      geoconnexApp.spatialExtentGroup = L.featureGroup();
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
        overlayMaps["Resource Spatial Extent"] = geoconnexApp.spatialExtentGroup;
        geoconnexApp.map.addLayer(geoconnexApp.searchFeatureGroup);
        geoconnexApp.map.addLayer(geoconnexApp.spatialExtentGroup);
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
      geoconnexApp.fitMapToFeatures();
    },
    addFeaturesToMap(features, collectionOverride = null){
      for (let feature of features){

        // deal with collection first
        let collection = collectionOverride ? collectionOverride :  feature.collection
        // check if layergroup exists in the "dictionary"
        if (
          !geoconnexApp.layerGroupDictionary ||
          geoconnexApp.layerGroupDictionary[collection.id] == undefined
        ) {
          geoconnexApp.layerGroupDictionary[collection.id] =
            L.layerGroup();
          geoconnexApp.layerGroupDictionary[collection.id].uris = [];
          geoconnexApp.layerControl.addOverlay(
            geoconnexApp.layerGroupDictionary[collection.id],
            geoconnexApp.trimString(collection.description)
          );
          geoconnexApp.layerControl.expand();
        }
        geoconnexApp.map.addLayer(
          geoconnexApp.layerGroupDictionary[collection.id]
        );
        
        // second deal with the actual item
        let alreadySelected = geoconnexApp.selectedReferenceItems.find((obj) => {
          return obj.value && obj.value === feature.uri;
        });
        if (alreadySelected) {
          feature.disabled = true;
        }else{
          geoconnexApp.getFeatureProperties(feature);
          if (feature.geometry.type.includes("Point")) {
            geoconnexApp.addToMap(
              feature,
              false,
              {
                color: geoconnexApp.searchColor,
                radius: 5,
                fillColor: geoconnexApp.pointFillColor,
                fillOpacity: 0.8,
              },
              (group = geoconnexApp.searchFeatureGroup)
            );
          } else {
            geoconnexApp.addToMap(
              feature,
              false,
              { color: geoconnexApp.searchColor },
              (group = geoconnexApp.searchFeatureGroup)
            );
          }
        }
        geoconnexApp.items.push(feature);
      }
      if(features.length){
        geoconnexApp.fitMapToFeatures();
        geoconnexApp.limitOptionsToMappedFeatures();
      }else{
        geoconnexApp.displayNoFoundItems(bbox[1], bbox[0]);
      }
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
          geoconnexApp.layerGroupDictionary[geojson.collection].addLayer(
            leafletLayer
          );
          geoconnexApp.layerGroupDictionary[geojson.collection].uris.push(
            geojson.uri
          );
        }

        // handle zooming
        if (fit) {
          geoconnexApp.map.fitBounds(leafletLayer.getBounds());
        }
      } catch (e) {
        geoconnexApp.error(e.message);
      }
    },
    fitMapToFeatures(group = null) {
      let geoconnexApp = this;
      try {
        if (group) {
          geoconnexApp.map.fitBounds(group.getBounds());
        } else {
          let bounds = L.latLngBounds();
          geoconnexApp.spatialExtentGroup && bounds.extend(geoconnexApp.spatialExtentGroup.getBounds());
          geoconnexApp.searchFeatureGroup && bounds.extend(geoconnexApp.searchFeatureGroup.getBounds());
          geoconnexApp.searchFeatureGroup && bounds.extend(geoconnexApp.selectedFeatureGroup.getBounds());
          if (bounds.isValid()) {
            geoconnexApp.map.fitBounds(bounds);
          } else {
            // USA
            // geoconnexApp.map.setView([41.850033, -87.6500523], 3);
            geoconnexApp.map.setView([30, 0], 1);
          }
        }
      } catch (e) {
        geoconnexApp.error(e.message);
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
          `${geoconnexApp.geoconnexUrl}?f=json&skipGeometry=true`,
          forceFresh
        );
        geoconnexApp.collections = response.collections.filter(col => {
          return !geoconnexApp.ignoredCollections.includes(col.id);
        });
      } catch (e) {
        geoconnexApp.error(e.message);
      }
      geoconnexApp.loadingCollections = false;
    },
    createVuetifySelectSubheader(collection) {
      return {
        header: `${collection.description} (${collection.id})`,
        text: `${collection.description} (${collection.id})`,
      };
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
      geoconnexApp.selectedReferenceItems.forEach((it) => {
        if (feature.uri === it.value) {
          feature.disabled = true;
        }
      });
      return feature;
    },
    async getItemsIn(collection, forceFresh = false, skipGeometry = true) {
      let geoconnexApp = this;
      const url = `${geoconnexApp.geoconnexUrl}/${collection.id}/${geoconnexBaseURLQueryParam}&skipGeometry=${skipGeometry.toString()}`;
      let featureCollection = await geoconnexApp.fetchFromCacheOrGeoconnex(url, forceFresh);
      featureCollection.collection = collection;
      return featureCollection;
    },
    async fetchFromCacheOrGeoconnex(url, forceFresh = false, collection = null) {
      let geoconnexApp = this;
      let data = {};
      if (!("caches" in window)) {
          geoconnexApp.log(
            "Cache API not available. Fetching geoconnex data from:\n" + url
          );
        let fetch_resp = await fetch(url);
        if (!fetch_resp.ok) {
          geoconnexApp.error(
            `Error when attempting to fetch: ${fetch_resp.statusText}`
          );
        } else {
          data = await fetch_resp.json();
        }
      } else {
        let cache_resp = await geoconnexApp.geoCache.match(url);
        if (geoconnexApp.isCacheValid(cache_resp) && !forceFresh) {
            geoconnexApp.log("Using Geoconnex from cache for:\n" + url);
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
      
        geoconnexApp.log("Fetching + adding to cache, geoconnex data from:\n" + url);
      try {
        let fetch_resp = await fetch(url);
        if (!fetch_resp.ok) {
          geoconnexApp.error(
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
        geoconnexApp.error(e.message);
        geoconnexApp.geoCache
          .match(url)
          .then(function (response) {
            geoconnexApp.error(
              "Geoconnex API fetch error. Falling back to old cached version."
            );
            return response.data;
          })
          .catch(function (e) {
            geoconnexApp.error(e.message);
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
        geoconnexApp.log("Cached data not valid.");
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
    trimString(longString){
      return (longString.length > geoconnexApp.stringLengthLimit ? `${longString.substring(0, geoconnexApp.stringLengthLimit)}...` : longString);
    },
    async loadMetadataRelations() {
      let geoconnexApp = this;
      const promises = [];
      for (let relation of geoconnexApp.metadataRelations) {
        if (
          this.isUrl(relation.value) &&
          relation.type === "relation" &&
          relation.value.indexOf("geoconnex") > -1
        ) {
        geoconnexApp.fetchSingleReferenceItem(relation.value).then(feature=>{
          feature = geoconnexApp.getFeatureProperties(feature)
          feature.disabled = true;
          geoconnexApp.items.push(feature);
          geoconnexApp.addSelectedFeatureToMap(feature);

          let featureValues = {
            id: relation.id,
            text: feature.text,
            value: feature.uri,
          };

          geoconnexApp.selectedReferenceItems.push(featureValues);
          geoconnexApp.relationObjects.push(feature);
        });
      }
    }
      geoconnexApp.fitMapToFeatures();
      geoconnexApp.loadingRelations = false;
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
          
            geoconnexApp.log(
              `Added ${
                selected.text ? selected.text : selected
              } to resource metadata`
            );
          geoconnexApp.selectedReferenceItems.push({
            id: result.element_id,
            value: selected.uri ? selected.uri : selected,
            text: selected.text ? selected.text : selected,
          });
        },
        error: function (request, status, error) {
          geoconnexApp.appMessages.push({"level": "danger", "message":`${error} while attempting to add related feature.`});
          geoconnexApp.error(request.responseText);
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
              
                geoconnexApp.log(
                  `Removed ${
                    relation.text ? relation.text : relation
                  } from resource metadata`
                );
            },
            error: function (request, status, error) {
              geoconnexApp.errorMsg = `${error} while attempting to remove related feature.`;
              geoconnexApp.error(request.responseText);
            },
          });
        }
      }
    },
    queryGeoItemsFromExtent(collections = null) {
      let geoconnexApp = this;
      geoconnexApp.queryGeoItemsInBbox(geoconnexApp.bbox, collections);
    },
    queryGeoItemsContainingPoint(lat = null, long = null, collections = null) {
      let geoconnexApp = this;
      long = typeof long == "number" ? long : geoconnexApp.pointLong;
      lat = typeof lat == "number" ? lat : geoconnexApp.pointLat;
      geoconnexApp.map.closePopup();

      var bbox = [
        long,
        lat,
        long + 10e-12,
        lat + 10e-12,
      ];
      geoconnexApp.queryGeoItemsInBbox(bbox, collections);
    },
    showSpatialExtent(bbox=null){
      let geoconnexApp = this;
      if (!bbox) bbox = geoconnexApp.bBox;
      try{
        let poly = L.rectangle([[bbox[1], bbox[0]],[bbox[3], bbox[2]]])
        poly.text = "Resource Spatial Extent";
        geoconnexApp.addToMap(
          poly.toGeoJSON(),
          false,
          { color: geoconnexApp.spatialExtentColor, fillColor: geoconnexApp.spatialExtentColor, fillOpacity: 0.1 },
          (group = geoconnexApp.spatialExtentGroup)
        );
        let area = L.GeometryUtil.geodesicArea(poly.getLatLngs()[0]); //sq meters
        if(area > geoconnexApp.largeExtentWarningThreshold){
          geoconnexApp.appMessages.push({"level": "warn", "message": `Please note: your resource spatial extent (${(area * 1e-6).toFixed(0)} square kilometers) is on the order of large US state. You might experience reduced performance during your searches.`});
        }
      }catch(e) {
        geoconnexApp.error("Error attempting to show spatial extent:", e.message);
      }
      geoconnexApp.fitMapToFeatures();
    },
    async queryGeoItemsInBbox(bbox, collections = null) {
      let geoconnexApp = this;
      if (!bbox) bbox = geoconnexApp.bBox
      let items = [];
      geoconnexApp.map.closePopup();
      try {
        if (collections.length === 0){
          // fetch items from all collections
          collections = geoconnexApp.collections;
        }

        const promises = [];
        for (collection of collections){
          promises.push(geoconnexApp.fetchCollectionItemsInBbox(collection, bbox));
          if (!geoconnexApp.selectedCollections.includes(collection)){
            geoconnexApp.selectedCollections.push(collection);
          }
        }
        let results = await Promise.all(promises);
        items = results.flat().filter(Boolean);
        geoconnexApp.addFeaturesToMap(items);
      } catch (e) {
        geoconnexApp.error(
          `Error while attempting to find intersecting geometries: ${e.message}`
        );
      }
    },
    displayNoFoundItems(lat, lng) {
      let loc = { lat: lat, lng: lng };
      let content = `<div data='${JSON.stringify(
        loc
      )}'>No collection items found containing this search.</div>`;
      L.popup({ maxWidth: 400, autoClose: true})
        .setLatLng(loc)
        .setContent(content)
        .openOn(geoconnexApp.map);
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
      geoconnexApp.selectedCollections = [];
      geoconnexApp.fitMapToFeatures();
      geoconnexApp.layerControl.collapse();
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
    updateGeoconnexWithResSpatialExtent() {
      let geoconnexApp = this;
      geoconnexApp.updateSpatialExtentType();
      geoconnexApp.spatialExtentGroup.clearLayers()
      if (geoconnexApp.resSpatialType == "point") {
        geoconnexApp.log("Setting point spatial extent");
        geoconnexApp.pointLat = $("#id_north").val();
        geoconnexApp.pointLong = $("#id_east").val();

        // Geoconnex API only acccepts bounding box
        // if point, just make it a small bounding box
        geoconnexApp.bBox = [
          geoconnexApp.pointLong,
          geoconnexApp.pointLat,
          geoconnexApp.pointLong + 1,
          geoconnexApp.pointLat + 1,
        ];
        geoconnexApp.showSpatialExtent();
      } else if (geoconnexApp.resSpatialType == "box") {
        geoconnexApp.log("Setting box spatial extent");
        geoconnexApp.northLat = $("#id_northlimit").val();
        geoconnexApp.eastLong = $("#id_eastlimit").val();
        geoconnexApp.southLat = $("#id_southlimit").val();
        geoconnexApp.westLong = $("#id_westlimit").val();

        geoconnexApp.bBox = [
          geoconnexApp.eastLong,
          geoconnexApp.southLat,
          geoconnexApp.westLong,
          geoconnexApp.northLat,
        ];
        geoconnexApp.showSpatialExtent();
      } else {
        geoconnexApp.warn("Resource spatial extent isn't set");
      }
    },
    fillValuesFromClickedCoordinates(lat, long) {
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
        )}'>Search collections for items containing this point</button>`;
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
            geoconnexApp.fillValuesFromClickedCoordinates(loc.lat, loc.long);
            geoconnexApp.queryGeoItemsContainingPoint(loc.lat, loc.long, geoconnexApp.selectedCollections);
          }
        );

        $("#geoconnex-map-wrapper").on(
          "click",
          "button.map-add-geoconnex",
          function (e) {
            e.stopPropagation();
            let data = JSON.parse($(this).attr("data"));
            let alreadySelected = geoconnexApp.selectedReferenceItems.find((obj) => {
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
            geoconnexApp.selectedReferenceItems = geoconnexApp.selectedReferenceItems.filter(
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
          geoconnexApp.initLeafletMap();
        }
      }, 0);
    },
    showMap() {
      let geoconnexApp = this;
      if (geoconnexApp.showingMap && geoconnexApp.map == null) {
        geoconnexApp.initLeafletMap();
      }
      geoconnexApp.showingMap = true;
    }
  },
  beforeMount() {
    this.setCustomItemRules();
  },
  async mounted() {
    // TODO: reduce size of collection box so it doesn't look like you should add more
    // TODO: 
    let geoconnexApp = this;
    if (geoconnexApp.resMode == "Edit") {
      geoconnexApp.geoCache = await caches.open(geoconnexApp.cacheName);
      geoconnexApp.initLeafletMap();

      // geoconnexApp.$nextTick(async function () {
        // coverageMap.initialShapesDrawn
        // await geoconnexApp.updateGeoconnexWithResSpatialExtent();
        // geoconnexApp.showSpatialExtent();
      // })

    // TODO: remove this + above once have a good way to handle spatial extent changes
    checkFlag();
    async function checkFlag() {
      if(!coverageMap || !coverageMap.initialShapesDrawn) {
         window.setTimeout(checkFlag, 100); /* this checks the flag every 100 milliseconds*/
      } else {
      geoconnexApp.updateGeoconnexWithResSpatialExtent();
      }
    }
      
      geoconnexApp.loadCollections(false);
      geoconnexApp.loadMetadataRelations();

    } else if (
      geoconnexApp.resMode == "View" &&
      geoconnexApp.metadataRelations.length > 0
    ) {
      geoconnexApp.geoCache = await caches.open(geoconnexApp.cacheName);
      geoconnexApp.initLeafletMap();
      geoconnexApp.loadMetadataRelations();
      geoconnexApp.loadingCollections = false;
    }
  },
});
