//TODO: we decided to not render any features if there are too many seems this stops at 5000 which I think is confusing, seeing a have rendered map?
const limitNumberOfFeaturesPerRequest = 5000;
const geoconnexBaseURLQueryParam = `items?f=json&limit=${limitNumberOfFeaturesPerRequest}`;
let geoconnexApp = new Vue({
  el: "#app-geoconnex",
  delimiters: ["${", "}"],
  vuetify: new Vuetify(),
  data() {
    return {
      isLoading: false,
      // Geoconnex collection and feature data structures
      collections: null,
      features: [],
      collectionsSelectedToSearch: [],
      selectedReferenceFeatures: [],

      // Resource-level data
      resShortId: SHORT_ID,
      metadataRelations: RELATIONS,
      resMode: RESOURCE_MODE,
      resSpatialType: null,

      // Fetching and cacheing
      geoCache: null,
      cacheName: "geoconnexCache",
      cacheDuration: 6.048e8, // one week in milliseconds
      enforceCacheDuration: false,
      geoconnexUrl: "https://reference.geoconnex.us/collections",
      limitNumberOfFeaturesPerRequest: limitNumberOfFeaturesPerRequest,
      ignoredCollections: ["pws"], // currently ignored because requests return as 500 errors
      featureNameFieldMap: {
        // Geoconnex features have different "name" fields depending on which collection the belong to
        nat_aq: "AQ_NAME",
        principal_aq: "AQ_NAME",
        dams: "name",
        gages: "name",
        mainstems: "name_at_outlet",
        sec_hydrg_reg: "SHR",
        ua10: "NAME10",
      },

      // Mapping
      showingMap: true,
      map: null,
      spatialExtentGroup: null,
      searchFeatureGroup: null,
      selectedFeatureGroup: null,
      searchLayerGroupDictionary: {}, // dictionary of {collection.id, layerGroup} for layerGroups in searchFeatureGroup
      selectedLayerDictionary: {}, // dictionary of {feature.uri, leafletLayer.id} for layers in selectedFeatureGroup
      layerControl: null, // Leaflet layerControl
      largeExtentWarningThreshold: 5e11, // square meter area above which warning is provided
      fitBoundsMaxZoom: 7,
      expandLayerControlOnAdd: false,
      shouldFitMap: false,
      pointLat: 0,
      pointLong: 0,
      northLat: null,
      eastLong: null,
      southLat: null,
      westLong: null,
      bBox: null,
      resSpatialExtentArea: null,

      // Messages and logging
      debug: false, // modifies log verbosity
      searchingDescription: "",
      searchResultString: "",
      appMessages: [], // notifications displayed at top of App
      collectionMessages: [], // notifications displayed below "Collection" autoselect
      log: console.log.bind(
        window.console,
        "%cGeoconnex:",
        "color: white; background:blue;"
      ),
      warn: console.warn.bind(
        window.console,
        "%cGeoconnex warning:",
        "color: white; background:blue;"
      ),
      error: console.error.bind(
        window.console,
        "%cGeoconnex error:",
        "color: white; background:blue;"
      ),

      // State
      loadingRelations: true,
      loadingCollections: true,
      lockCollectionsInput: false,
      limitToSingleCollection: true,
      hasSearches: false,

      // VUE utility
      collectionTypeahead: null,
      itemTypeahead: null,
      featureRules: null,

      // UI "theme"
      stringLengthLimit: 30, // after which ellipse...
      collectionMessageColor: "orange",
      mappedPointFillColor: "rgba(255, 165, 0, 0.32)",
      collectionSearchColor: "orange",
      featureSelectColor: "black",
      spatialExtentColor: "blue",
    };
  },
  watch: {
    async collectionsSelectedToSearch(newValue, oldValue) {
      let geoconnexApp = this;
      let oldLength = oldValue ? oldValue.length : 0;
      let newLength = newValue ? newValue.length : 0;

      if (geoconnexApp.limitToSingleCollection) {
        newLength == 1 && (geoconnexApp.lockCollectionsInput = true);
        newLength == 0 && (geoconnexApp.lockCollectionsInput = false);
      }
      geoconnexApp.searchResultString = "";
      geoconnexApp.map.closePopup();

      if (newLength > oldLength) {
        geoconnexApp.hasSearches = true;
        let newCollection = newValue.at(-1);
        if (geoconnexApp.resSpatialType) {
          geoconnexApp.fetchGeoconnexFeaturesInBbox(geoconnexApp.bbox, [
            newCollection,
          ]);
        } else {
          geoconnexApp.searchingDescription = newCollection.description;
          let featureCollection = await geoconnexApp.fetchFeaturesInCollection(
            newCollection,
            (forceFresh = false),
            (skipGeometry = false)
          );
          if (featureCollection.features) {
            geoconnexApp.addSearchFeaturesToMap(
              featureCollection.features,
              featureCollection.collection
            );
          } else {
            geoconnexApp.searchResultString = `Your search in ${newCollection.description} didn't return any features.`;
          }
          geoconnexApp.searchingDescription = "";
        }
      } else if (newLength < oldLength) {
        let remove;
        if (newLength) {
          remove = oldValue.filter((obj) =>
            newValue.every((s) => s.id !== obj.id)
          );
        } else {
          remove = oldValue;
          geoconnexApp.hasSearches = false;
        }

        if (newLength) {
          for (let collection of remove) {
            geoconnexApp.searchFeatureGroup.removeLayer(
              geoconnexApp.searchLayerGroupDictionary[collection.id]
            );
            geoconnexApp.searchLayerGroupDictionary[
              collection.id
            ].clearLayers();

            geoconnexApp.layerControl.removeLayer(
              geoconnexApp.searchLayerGroupDictionary[collection.id]
            );
          }
        } else {
          geoconnexApp.clearMapOfSearches();
        }
        geoconnexApp.fitMapToFeatures();

        for (let collection of remove) {
          geoconnexApp.features = geoconnexApp.features.filter((item) => {
            return collection.id !== item.collection;
          });
        }
      }
    },
    selectedReferenceFeatures(newValue, oldValue) {
      let geoconnexApp = this;
      let oldLength = oldValue ? oldValue.length : 0;
      let newLength = newValue ? newValue.length : 0;
      if (newLength > oldLength) {
        geoconnexApp.addSelectedFeatureToResMetadata(newValue.pop());
      } else if (newLength < oldLength) {
        let remove = oldValue.filter((obj) =>
          newValue.every((s) => s.id !== obj.id)
        );
        try {
          geoconnexApp.selectedFeatureGroup.removeLayer(
            geoconnexApp.selectedLayerDictionary[remove[0].value]
          );
          geoconnexApp.fitMapToFeatures();
        } catch (e) {
          geoconnexApp.error(e.message);
          geoconnexApp.appMessages.push({
            level: "danger",
            message: `${e.message} while attempting to remove related feature.`,
          });
        }
        geoconnexApp.ajaxRemoveFeatureFromResMetadata(remove);

        // re-enable the item for selection
        geoconnexApp.features.forEach((it) => {
          if (remove[0].value === it.uri) {
            it.disabled = false;
          }
        });
      }
    },
  },
  methods: {
    /* --------------------------------------------------
    Resource Metadata Modification Methods
    -------------------------------------------------- */
    async loadResourceMetadataRelations() {
      let geoconnexApp = this;
      const promises = [];
      for (let relation of geoconnexApp.metadataRelations) {
        if (
          this.isUrl(relation.value) &&
          relation.type === "relation" &&
          relation.value.indexOf("geoconnex") > -1
        ) {
          promises.push(geoconnexApp.fetchSingleFeature(relation));
        }
      }
      let results = await Promise.all(promises);
      let features = results.flat().filter(Boolean);
      for (let feature of features) {
        feature = geoconnexApp.getFeatureProperties(feature);
        feature.disabled = true;
        geoconnexApp.features.push(feature);
        geoconnexApp.addSelectedFeatureToMap(feature);
        let featureValues = {
          id: feature.relationId,
          text: feature.text,
          value: feature.uri,
        };
        geoconnexApp.selectedReferenceFeatures.push(featureValues);
      }
      geoconnexApp.fitMapToFeatures(group=null, overrideShouldFit=true);
      geoconnexApp.loadingRelations = false;
    },
    addSelectedFeatureToResMetadata(feature) {
      let geoconnexApp = this;
      geoconnexApp.addSelectedFeatureToMap(feature);
      geoconnexApp.ajaxSaveFeatureToResMetadata(feature);

      // disable so that it can't be duplicated
      geoconnexApp.features.forEach((it) => {
        if (feature.uri === it.uri) {
          it.disabled = true;
        }
      });
    },
    addSelectedFeatureToMap(feature) {
      let geoconnexApp = this;
      if (!feature.geometry) {
        geoconnexApp.fetchGeometryForSingleFeature(feature).then((geometry) => {
          feature.geometry = geometry.geometry;
        });
      }
      geoconnexApp.addGeojsonToMap(
        feature,
        (fit = false),
        (style = undefined),
        (group = geoconnexApp.selectedFeatureGroup)
      );
    },
    ajaxSaveFeatureToResMetadata(feature) {
      let geoconnexApp = this;
      let url = `/hsapi/_internal/${geoconnexApp.resShortId}/relation/add-metadata/`;
      let data = {
        type: "relation",
        value: feature.uri ? feature.uri : feature,
      };
      $.ajax({
        type: "POST",
        url: url,
        data: data,
        success: function (result) {
          geoconnexApp.log(
            `Added ${
              feature.text ? feature.text : feature
            } to resource metadata`
          );
          geoconnexApp.selectedReferenceFeatures.push({
            id: result.element_id,
            value: feature.uri ? feature.uri : feature,
            text: feature.text ? feature.text : feature,
          });
        },
        error: function (request, status, error) {
          geoconnexApp.appMessages.push({
            level: "danger",
            message: `${error} while attempting to save related feature.`,
          });
          geoconnexApp.error(request.responseText);
        },
      });
    },
    ajaxRemoveFeatureFromResMetadata(relations) {
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
              geoconnexApp.appMessages.push({
                level: "danger",
                message: `${error} while attempting to remove related feature.`,
              });
              geoconnexApp.error(request.responseText);
            },
          });
        }
      }
    },
    limitSelectableFeaturesToSearch() {
      let geoconnexApp = this;
      geoconnexApp.loadingRelations = true;

      // remove all features currently not in the map search
      let keep = [];
      for (const val of Object.values(
        geoconnexApp.searchLayerGroupDictionary
      )) {
        if (!val.uris.includes(undefined)) {
          keep = keep.concat(val.uris);
        }
      }
      geoconnexApp.features = geoconnexApp.features.filter((s) =>
        keep.includes(s.uri)
      );
      geoconnexApp.loadingRelations = false;
    },

    /* --------------------------------------------------
    Fetch Request Methods
    -------------------------------------------------- */
    async fetchCollections(forceFresh = false) {
      let geoconnexApp = this;
      geoconnexApp.loadingCollections = true;
      try {
        let response = await geoconnexApp.fetchURLFromCacheOrGeoconnex(
          `${geoconnexApp.geoconnexUrl}?f=json&skipGeometry=true`,
          forceFresh
        );
        geoconnexApp.collections = response.collections.filter((col) => {
          return !geoconnexApp.ignoredCollections.includes(col.id);
        });
      } catch (e) {
        geoconnexApp.error(e.message);
        geoconnexApp.appMessages.push({
          level: "danger",
          message: `${e.message} while loading collections.`,
        });
      }
      geoconnexApp.loadingCollections = false;
    },
    fetchGeoconnexFeaturesContainingPoint(
      lat = null,
      long = null,
      collections = null
    ) {
      let geoconnexApp = this;
      long = typeof long == "number" ? long : geoconnexApp.pointLong;
      lat = typeof lat == "number" ? lat : geoconnexApp.pointLat;
      geoconnexApp.map.closePopup();

      let bbox = [long, lat, long + 10e-12, lat + 10e-12];
      geoconnexApp.fetchGeoconnexFeaturesInBbox(bbox, collections);
    },
    async fetchGeoconnexFeaturesInBbox(bbox, collections = null) {
      let geoconnexApp = this;
      if (!bbox) bbox = geoconnexApp.bBox;
      let features = [];
      geoconnexApp.map.closePopup();
      try {
        if (!collections || collections.length === 0) {
          // fetch features from all collections
          collections = geoconnexApp.collections;
        }

        const promises = [];
        for (collection of collections) {
          promises.push(
            geoconnexApp.fetchFeaturesFromSingleCollectionInBbox(
              collection,
              bbox
            )
          );
          if (!geoconnexApp.collectionsSelectedToSearch.includes(collection)) {
            geoconnexApp.collectionsSelectedToSearch.push(collection);
          }
        }
        let results = await Promise.all(promises);
        features = results.flat().filter(Boolean);
        if (features.length > 0) {
          geoconnexApp.searchResultString = "";
          geoconnexApp.addSearchFeaturesToMap(features);
        } else {
          geoconnexApp.searchResultString = `Your search didn't return any features.`;
          geoconnexApp.mapDisplayNoFoundFeatures(bbox);
        }
      } catch (e) {
        geoconnexApp.error(
          `Error while attempting to find intersecting geometries: ${e.message}`
        );
      }
    },
    async fetchFeaturesFromSingleCollectionInBbox(
      collection,
      bbox = null,
      refresh = false
    ) {
      let geoconnexApp = this;
      geoconnexApp.searchingDescription = collection.description;
      let response = {};
      let propertiesParameter = `&properties=uri,${geoconnexApp.getFeatureNameField(
        collection.id
      )}`;
      let query = `${geoconnexApp.geoconnexUrl}/${
        collection.id
      }/${geoconnexBaseURLQueryParam}${propertiesParameter}&bbox=${bbox.toString()}`;
      response = await geoconnexApp.fetchURLFromCacheOrGeoconnex(
        query,
        refresh
      );
      geoconnexApp.searchingDescription = "";

      // store the collection for future reference
      response &&
        response.features.forEach((feature) => {
          feature.collection = collection;
        });
      return response ? response.features : null;
    },
    async fetchGeometryForSingleFeature(geoconnexObj, refresh = false) {
      let geoconnexApp = this;
      geoconnexApp.searchingDescription = geoconnexObj.collection;
      if (refresh || !geoconnexObj.geometry) {
        let query = `${geoconnexApp.geoconnexUrl}/${geoconnexObj.collection}/items/${geoconnexObj.id}?f=json`;
        let response = await geoconnexApp.fetchURLFromCacheOrGeoconnex(
          query,
          refresh
        );
        geoconnexObj.geometry = response.geometry;
      }
      geoconnexApp.searchingDescription = "";
      return geoconnexObj;
    },
    async fetchSingleFeature(relation) {
      let geoconnexApp = this;
      let uri = relation.value;
      geoconnexApp.searchingDescription = uri;
      let relative_id = uri.split("ref/").pop();
      let collection = relative_id.split("/")[0];
      let id = relative_id.split("/")[1];
      let query = `${geoconnexApp.geoconnexUrl}/${collection}/items/${id}?f=json`;
      let response = await geoconnexApp.fetchURLFromCacheOrGeoconnex(query);
      geoconnexApp.searchingDescription = "";
      response.relationId = relation.id;
      return response;
    },
    async fetchFeaturesInCollection(
      collection,
      forceFresh = false,
      skipGeometry = true
    ) {
      let geoconnexApp = this;
      let propertiesParameter = `&properties=uri,${geoconnexApp.getFeatureNameField(
        collection.id
      )}`;
      const url = `${geoconnexApp.geoconnexUrl}/${
        collection.id
      }/${geoconnexBaseURLQueryParam}${propertiesParameter}&skipGeometry=${skipGeometry.toString()}`;
      let featureCollection = await geoconnexApp.fetchURLFromCacheOrGeoconnex(
        url,
        forceFresh
      );
      featureCollection.collection = collection;
      return featureCollection;
    },
    async fetchURLFromCacheOrGeoconnex(
      url,
      forceFresh = false,
      collection = null
    ) {
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
          data = await geoconnexApp.fetchURLFromGeoconnex(url);
        }
      }
      if (collection && data) {
        data.collection = collection;
      }
      return data;
    },
    async fetchURLFromGeoconnex(url) {
      let fetchData = {};
      let geoconnexApp = this;

      geoconnexApp.log(
        "Fetching + adding to cache, geoconnex data from:\n" + url
      );
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

    /* --------------------------------------------------
    Mapping Methods
    -------------------------------------------------- */
    showSpatialExtent(bbox = null, fromPoint = false) {
      let geoconnexApp = this;
      if (!bbox) bbox = geoconnexApp.bBox;
      try {
        let rect = L.rectangle(
          [
            [bbox[1], bbox[0]],
            [bbox[3], bbox[2]],
          ],
          { interactive: false }
        );
        let poly = rect.toGeoJSON();
        poly.text = "Resource Spatial Extent";
        geoconnexApp.addGeojsonToMap(
          poly,
          (fit = false),
          {
            color: geoconnexApp.spatialExtentColor,
            fillColor: geoconnexApp.spatialExtentColor,
            fillOpacity: 0.1,
          },
          (group = geoconnexApp.spatialExtentGroup),
          (interactive = false)
        );
        geoconnexApp.resSpatialExtentArea = L.GeometryUtil.geodesicArea(
          rect.getLatLngs()[0]
        ); //sq meters
        if (fromPoint) {
          // the bbox is just a tiny box generated by a point
          let geojson = {
            type: "Point",
            coordinates: [geoconnexApp.pointLong, geoconnexApp.pointLat],
            text: "Resource Spatial Extent",
          };
          geoconnexApp.addGeojsonToMap(
            geojson,
            (fit = false),
            (style={}),
            (group = geoconnexApp.spatialExtentGroup),
            (interactive = false),
            (marker = true)
          );
        }
      } catch (e) {
        geoconnexApp.error(
          "Error attempting to show spatial extent:",
          e.message
        );
        geoconnexApp.appMessages.push({
          level: "danger",
          message: `${error} while attempting to show spatial extent.`,
        });
      }
      geoconnexApp.fitMapToFeatures(group=null, overrideShouldFit=true);
    },
    initializeLeafletMap() {
      let geoconnexApp = this;
      geoconnexApp.selectedFeatureGroup = L.featureGroup();
      geoconnexApp.searchFeatureGroup = L.featureGroup();
      !geoconnexApp.spatialExtentGroup &&
        (geoconnexApp.spatialExtentGroup = L.featureGroup());
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
        "Selected Features": geoconnexApp.selectedFeatureGroup,
      };
      overlayMaps["Resource Spatial Extent"] = geoconnexApp.spatialExtentGroup;
      geoconnexApp.map.addLayer(geoconnexApp.spatialExtentGroup);
      if (geoconnexApp.resMode == "Edit") {
        overlayMaps["Search (all features)"] = geoconnexApp.searchFeatureGroup;
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
      geoconnexApp.setMapEvents();
      geoconnexApp.fitMapToFeatures();
    },
    addSearchFeaturesToMap(features, collectionOverride = null) {
      for (let feature of features) {
        // deal with collection first
        let collection = collectionOverride
          ? collectionOverride
          : feature.collection;
        // check if layergroup exists in the "dictionary"
        if (
          !geoconnexApp.searchLayerGroupDictionary ||
          geoconnexApp.searchLayerGroupDictionary[collection.id] == undefined
        ) {
          geoconnexApp.searchLayerGroupDictionary[collection.id] =
            L.layerGroup();
          geoconnexApp.searchLayerGroupDictionary[collection.id].uris = [];
          geoconnexApp.layerControl.addOverlay(
            geoconnexApp.searchLayerGroupDictionary[collection.id],
            geoconnexApp.trimString(collection.description)
          );

          geoconnexApp.expandLayerControlOnAdd &&
            geoconnexApp.layerControl.expand();
        }
        geoconnexApp.map.addLayer(
          geoconnexApp.searchLayerGroupDictionary[collection.id]
        );

        // second deal with the actual item
        let alreadySelected = geoconnexApp.selectedReferenceFeatures.find(
          (obj) => {
            return obj.value && obj.value === feature.properties.uri;
          }
        );
        if (alreadySelected) {
          feature.disabled = true;
        } else {
          geoconnexApp.getFeatureProperties(feature);
          if (feature.geometry.type.includes("Point")) {
            geoconnexApp.addGeojsonToMap(
              feature,
              (fit = false),
              {
                color: geoconnexApp.collectionSearchColor,
                radius: 5,
                fillColor: geoconnexApp.mappedPointFillColor,
                fillOpacity: 0.8,
              },
              (group = geoconnexApp.searchFeatureGroup)
            );
          } else {
            geoconnexApp.addGeojsonToMap(
              feature,
              (fit = false),
              { color: geoconnexApp.collectionSearchColor },
              (group = geoconnexApp.searchFeatureGroup)
            );
          }
        }
        geoconnexApp.features.push(feature);
      }
      if (features.length) {
        geoconnexApp.searchResultString = "";
        geoconnexApp.fitMapToFeatures();
        geoconnexApp.limitSelectableFeaturesToSearch();
      } else {
        geoconnexApp.searchResultString = `Your search didn't return any features.`;
      }
    },
    addGeojsonToMap(
      geojson,
      fit = false,
      style = { color: this.featureSelectColor, radius: 5 },
      group = null,
      interactive = true,
      marker = false
    ) {
      let geoconnexApp = this;
      try {
        let leafletLayer = L.geoJSON(geojson, {
          onEachFeature: function (feature, layer) {
            let popupText = `<h4>${feature.text}</h4>`;
            if (feature.uri) {
              popupText += `<a href=${feature["uri"]}>${feature["uri"]}</a></br></br>`;
            }
            if (
              geoconnexApp.resMode == "Edit" &&
              style.color == geoconnexApp.collectionSearchColor
            ) {
              popupText += `<button type="button" class="white--text text-none v-btn v-btn--has-bg theme--light v-size--small btn btn-success map-add-geoconnex" data='${JSON.stringify(
                feature
              )}'><i class="fa fa-plus"></i> Add Feature</button>`;
            } else if (
              geoconnexApp.resMode == "Edit" &&
              style.color == geoconnexApp.featureSelectColor
            ) {
              popupText += `<button type="button" class="white--text text-none v-btn v-btn--has-bg theme--light v-size--small btn btn-danger map-remove-geoconnex" data='${JSON.stringify(
                feature
              )}'>Remove Feature</button>`;
            }
            layer.bindPopup(popupText, { maxWidth: 400 });
          },
          pointToLayer: function (feature, latlng) {
            return marker
              ? L.marker(latlng, style)
              : L.circleMarker(latlng, style);
          },
          interactive: interactive,
        });
        leafletLayer.setStyle(style);
        if (geojson.uri && group === geoconnexApp.selectedFeatureGroup) {
          geoconnexApp.selectedLayerDictionary[geojson.uri] =
            leafletLayer._leaflet_id;
        }
        if (group === geoconnexApp.searchFeatureGroup) {
          if (!geojson.collection) {
            geojson.collection = "Search Bounds";
          }
          geoconnexApp.searchLayerGroupDictionary[geojson.collection].addLayer(
            leafletLayer
          );
          geoconnexApp.searchLayerGroupDictionary[geojson.collection].uris.push(
            geojson.uri
          );
        }
        if (group && !group.hasLayer(leafletLayer)) {
          group.addLayer(leafletLayer);
        }

        // handle zooming
        if (fit) {
          geoconnexApp.map.fitBounds(leafletLayer.getBounds(), {
            maxZoom: geoconnexApp.fitBoundsMaxZoom,
          });
        }
      } catch (e) {
        geoconnexApp.error(e.message);
        geoconnexApp.appMessages.push({
          level: "danger",
          message: `${e.message} while attempting to add item to map.`,
        });
      }
    },
    fitMapToFeatures(group = null, overrideShouldFit=false) {
      let geoconnexApp = this;
      if(!geoconnexApp.shouldFitMap && !overrideShouldFit) return;
      try {
        if (group) {
          geoconnexApp.map.fitBounds(group.getBounds());
        } else {
          let bounds = L.latLngBounds();
          geoconnexApp.spatialExtentGroup &&
            bounds.extend(geoconnexApp.spatialExtentGroup.getBounds());
          geoconnexApp.searchFeatureGroup &&
            bounds.extend(geoconnexApp.searchFeatureGroup.getBounds());
          geoconnexApp.searchFeatureGroup &&
            bounds.extend(geoconnexApp.selectedFeatureGroup.getBounds());
          if (bounds.isValid()) {
            geoconnexApp.map.fitBounds(bounds, {
              maxZoom: geoconnexApp.fitBoundsMaxZoom,
            });
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
    searchForFeaturesUsingVisibleMapBounds() {
      let geoconnexApp = this;
      geoconnexApp.fetchGeoconnexFeaturesInBbox(
        geoconnexApp.map.getBounds().toBBoxString(),
        (collections = geoconnexApp.collectionsSelectedToSearch)
      );
    },
    mapDisplayNoFoundFeatures(bbox) {
      let poly = L.rectangle([
        [bbox[1], bbox[0]],
        [bbox[3], bbox[2]],
      ]);
      let loc = poly.getBounds().getCenter();
      // let loc = { lat: lat, lng: lng };
      let content = `<div data='${JSON.stringify(
        loc
      )}'>No features found for your search.</div>`;
      L.popup({ maxWidth: 400, autoClose: true })
        .setLatLng(loc)
        .setContent(content)
        .openOn(geoconnexApp.map);
    },
    clearMapOfSearches() {
      let geoconnexApp = this;
      geoconnexApp.searchFeatureGroup.clearLayers();
      for (let key in geoconnexApp.searchLayerGroupDictionary) {
        geoconnexApp.layerControl.removeLayer(
          geoconnexApp.searchLayerGroupDictionary[key]
        );
        delete geoconnexApp.searchLayerGroupDictionary[key];
      }

      geoconnexApp.hasSearches = false;
      geoconnexApp.collectionsSelectedToSearch = [];
      geoconnexApp.fitMapToFeatures();
      geoconnexApp.layerControl.collapse();
    },
    updateSpatialExtentType() {
      let geoconnexApp = this;
      geoconnexApp.resSpatialType = null;
      let spatial_coverage_drawing = $("#coverageMap .leaflet-interactive");
      if (spatial_coverage_drawing.size() > 0) {
        let checked = $("#div_id_type input:checked").val();
        geoconnexApp.resSpatialType = checked || spatial_coverage_type;
      }
    },
    updateAppWithResSpatialExtent() {
      let geoconnexApp = this;
      geoconnexApp.updateSpatialExtentType();
      geoconnexApp.spatialExtentGroup.clearLayers();
      if (geoconnexApp.resSpatialType == "point") {
        geoconnexApp.log("Setting point spatial extent");
        geoconnexApp.pointLat =
          parseFloat($("#id_north").val()) ||
          parseFloat(
            $("#cov_north")
              .text()
              .replace(/[^\d.-]/g, "")
          );
        geoconnexApp.pointLong =
          parseFloat($("#id_east").val()) ||
          parseFloat(
            $("#cov_east")
              .text()
              .replace(/[^\d.-]/g, "")
          );

        // Geoconnex API only acccepts bounding box
        // if point, just make it a small bounding box
        geoconnexApp.bBox = [
          geoconnexApp.pointLong,
          geoconnexApp.pointLat,
          geoconnexApp.pointLong + 1e-12,
          geoconnexApp.pointLat + 1e-12,
        ];
        geoconnexApp.showSpatialExtent((bbox = null), (fromPoint = true));
      } else if (geoconnexApp.resSpatialType == "box") {
        geoconnexApp.log("Setting box spatial extent");
        geoconnexApp.northLat =
          $("#id_northlimit").val() ||
          parseFloat(
            $("#cov_northlimit")
              .text()
              .replace(/[^\d.-]/g, "")
          );
        geoconnexApp.eastLong =
          $("#id_eastlimit").val() ||
          parseFloat(
            $("#cov_eastlimit")
              .text()
              .replace(/[^\d.-]/g, "")
          );
        geoconnexApp.southLat =
          $("#id_southlimit").val() ||
          parseFloat(
            $("#cov_southlimit")
              .text()
              .replace(/[^\d.-]/g, "")
          );
        geoconnexApp.westLong =
          $("#id_westlimit").val() ||
          parseFloat(
            $("#cov_westlimit")
              .text()
              .replace(/[^\d.-]/g, "")
          );

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
    fillCoordinatesFromClickedCoordinates(lat, long) {
      let geoconnexApp = this;
      geoconnexApp.pointLat = lat;
      geoconnexApp.pointLong = long;
    },
    setMapEvents() {
      let geoconnexApp = this;
      var popup = L.popup({ maxWidth: 400 });

      function onMapClick(e) {
        if (!geoconnexApp.hasSearches) return;
        let loc = { lat: e.latlng.lat, long: e.latlng.lng };
        let content = `<button class="btn btn-primary leaflet-point-search" style="border-color:${
          geoconnexApp.collectionSearchColor
        }" data='${JSON.stringify(
          loc
        )}'><i class="fa fa-search"></i>Find features containing this point</button>`;
        popup.setLatLng(e.latlng).setContent(content).openOn(geoconnexApp.map);
      }

      if (geoconnexApp.resMode === "Edit") {
        geoconnexApp.map.on("click", onMapClick);

        $("#geoconnex-map-wrapper").on(
          "click",
          "button.leaflet-point-search",
          function (e) {
            e.stopPropagation();
            const loc = JSON.parse($(this).attr("data"));
            geoconnexApp.fillCoordinatesFromClickedCoordinates(
              loc.lat,
              loc.long
            );
            geoconnexApp.fetchGeoconnexFeaturesContainingPoint(
              loc.lat,
              loc.long,
              geoconnexApp.collectionsSelectedToSearch
            );
          }
        );

        $("#geoconnex-map-wrapper").on(
          "click",
          "button.map-add-geoconnex",
          function (e) {
            e.stopPropagation();
            let data = JSON.parse($(this).attr("data"));
            let alreadySelected = geoconnexApp.selectedReferenceFeatures.find(
              (obj) => {
                return obj.value === data.uri;
              }
            );
            if (!alreadySelected) {
              geoconnexApp.addSelectedFeatureToResMetadata(data);
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
            geoconnexApp.selectedReferenceFeatures =
              geoconnexApp.selectedReferenceFeatures.filter(
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

      // listen for save after resource spatial change
      $("#coverage-spatial")
        .find(".btn-primary")
        .not("#btn-update-resource-spatial-coverage")
        .click(() => {
          geoconnexApp.updateAppWithResSpatialExtent();
        });
    },
    toggleMapVisibility() {
      let geoconnexApp = this;
      geoconnexApp.showingMap = !geoconnexApp.showingMap;
      if (geoconnexApp.showingMap && geoconnexApp.map == null) {
        geoconnexApp.initializeLeafletMap();
      }
    },

    /* --------------------------------------------------
    Utility Methods
    -------------------------------------------------- */
    createVuetifySelectSubheader(collection) {
      return {
        header: `${collection.description} (${collection.id})`,
        text: `${collection.description} (${collection.id})`,
      };
    },
    setFeatureName(feature) {
      let geoconnexApp = this;
      let nameField = geoconnexApp.getFeatureNameField(feature.collection);
      feature.NAME = feature.properties[nameField] || "";
    },
    getFeatureNameField(collectionName) {
      let geoconnexApp = this;
      // This could also be accomplished by flattening json-ld for the feature and searching for the "https://schema.org/name"
      return geoconnexApp.featureNameFieldMap[collectionName] || "NAME";
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
      geoconnexApp.selectedReferenceFeatures.forEach((it) => {
        if (feature.uri === it.value) {
          feature.disabled = true;
        }
      });
      return feature;
    },
    isUrl(stringToTest) {
      try {
        new URL(stringToTest);
      } catch (_) {
        return false;
      }
      return true;
    },
    trimString(longString) {
      return longString.length > geoconnexApp.stringLengthLimit
        ? `${longString.substring(0, geoconnexApp.stringLengthLimit)}...`
        : longString;
    },
    until(conditionFunction) {
      geoconnexApp.log(`Waiting for [ ${conditionFunction} ] to resolve...`);
      const poll = (resolve) => {
        if (conditionFunction()) {
          geoconnexApp.log(`Promise for [ ${conditionFunction} ] resolved`);
          resolve();
        } else setTimeout((_) => poll(resolve), 400);
      };
      return new Promise(poll);
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
    setCustomFeatureRules() {
      let geoconnexApp = this;
      geoconnexApp.featureRules = [
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
  },
  beforeMount() {
    this.setCustomFeatureRules();
  },
  async mounted() {
    const geoconnexApp = this;
    geoconnexApp.isLoading = true;
    if (
      geoconnexApp.resMode == "Edit" ||
      geoconnexApp.metadataRelations.length > 0
    ) {
      geoconnexApp.geoCache = await caches.open(geoconnexApp.cacheName);
      geoconnexApp.initializeLeafletMap();

      geoconnexApp.resMode == "Edit" && geoconnexApp.fetchCollections(false);
      geoconnexApp.loadResourceMetadataRelations();

      // wait for spatial coverage map to load before getting extent
      await geoconnexApp
        .until((_) => coverageMap)
        .then(() => {
          geoconnexApp.updateAppWithResSpatialExtent();
        });
    }
    geoconnexApp.isLoading = false;
  },
});
