// Recommend subscribing to notifications for PRs to https://github.com/internetofwater/geoconnex.us/
const limitNumberOfFeaturesPerRequest = 1000;
const geoconnexAppVerbose = false; // set true to increase console verbosity
const geoconnexBaseURLQueryParam = `items?f=json&limit=${limitNumberOfFeaturesPerRequest}`;
const geoconnexApp = new Vue({
  el: "#app-geoconnex",
  delimiters: ["${", "}"],
  vuetify: new Vuetify(),
  data() {
    return {
      isLoading: false,
      ////// Geoconnex collection & feature data structures + configuration //////
      collections: null,
      features: [],
      collectionsSelectedToSearch: [],
      selectedReferenceFeatures: [],
      ignoredCollections: [],
      // collection: features that will not be mapped or allowed for list selection
      ignoredFeatures: {
        nat_aq: ["N9999OTHER"],
        principal_aq: [999],
      },
      featureNameMap: {},

      ////// Resource-level data //////
      resShortId: SHORT_ID,
      metadataRelations: GEOSPATIAL_RELATIONS,
      resMode: RESOURCE_MODE,
      resSpatialType: null,

      ////// Fetching and cacheing //////
      geoCache: null,
      cacheName: "geoconnexCache",
      cacheDuration: 0,
      enforceCacheDuration: false,
      geoconnexUrl: "https://reference.geoconnex.us/collections",
      limitNumberOfFeaturesPerRequest: limitNumberOfFeaturesPerRequest,

      ////// Mapping //////
      showingMap: true,
      map: null,
      spatialExtentGroup: null,
      searchFeatureGroup: null,
      selectedFeatureGroup: null,
      searchLayerGroupDictionary: {}, // dictionary of {collection.id, layerGroup} for layerGroups in searchFeatureGroup
      selectedLayerDictionary: {}, // dictionary of {feature.uri, leafletLayer.id} for layers in selectedFeatureGroup
      layerControl: null, // Leaflet layerControl
      largeExtentWarningThreshold: 5e11, // square meter area above which warning is provided
      fitBoundsMaxZoom: 9,
      expandLayerControlOnAdd: false,
      shouldFitMapAfterAddingLayers: false,
      onlyZoomInNotOutAfterLayerAddition: true,
      pointLat: 0,
      pointLong: 0,
      northLat: null,
      eastLong: null,
      southLat: null,
      westLong: null,
      bBox: null,
      resSpatialExtentArea: null,
      abortController: {},

      ////// Messages and logging //////
      searchingDescription: "",
      searchResultString: "",
      appMessages: [], // notifications displayed at top of App
      collectionMessages: [], // notifications displayed below "Collection" autoselect
      error: console.error.bind(
        window.console,
        "%cGeoconnex error:",
        "color: white; background:blue;"
      ),

      ////// State //////
      loadingRelations: true,
      loadingCollections: true,
      lockCollectionsInput: false,
      limitToSingleCollection: true,
      hasSearches: false,

      ////// VUE utility //////
      collectionTypeahead: null,
      itemTypeahead: null,
      featureRules: null,

      ////// UI "theme" //////
      stringLengthLimit: 40, // after which ellipse...
      featureMessageColor: "orange",
      collectionColor: "orange",
      mappedPointFillColor: "rgba(255, 165, 0, 0.32)",
      collectionSearchColor: "orange",
      featureSelectColor: "rgba(0,0,0,.87)",
      spatialExtentColor: "rgb(51, 136, 255)",
    };
  },
  computed: {
    hasSearchesWithouIssues() {
      const geoconnexApp = this;
      return (
        geoconnexApp.hasSearches &&
        !geoconnexApp.searchResultString &&
        geoconnexApp.searchingDescription == ""
      );
    },
  },
  watch: {
    async collectionsSelectedToSearch(newValue, oldValue) {
      const geoconnexApp = this;
      const oldLength = oldValue ? oldValue.length : 0;
      const newLength = newValue ? newValue.length : 0;

      if (geoconnexApp.limitToSingleCollection) {
        newLength == 1 && (geoconnexApp.lockCollectionsInput = true);
        newLength == 0 && (geoconnexApp.lockCollectionsInput = false);
      }
      geoconnexApp.searchResultString = "";
      geoconnexApp.map.closePopup();

      if (newLength > oldLength) {
        geoconnexApp.hasSearches = true;
        const newCollection = newValue.at(-1);
        if (geoconnexApp.resSpatialType) {
          geoconnexApp.fetchGeoconnexFeaturesInBbox({
            bbox: geoconnexApp.bbox,
            collections: [newCollection],
          });
        } else {
          geoconnexApp.searchingDescription = newCollection.description;
          const featureCount =
            await geoconnexApp.countFeaturesFromSingleCollectionInBbox({
              collection: newCollection,
              bbox: null,
            });
          if (featureCount >= limitNumberOfFeaturesPerRequest) {
            geoconnexApp.searchResultString = `Your search in ${newCollection.id} returned too many features.
            The limit is ${limitNumberOfFeaturesPerRequest} so no geometries were mapped.
            We recommend that you refine resource extent, conduct a point search by clicking on the map, or search using map bounds.`;
            geoconnexApp.searchingDescription = "";
            return;
          }
          const featureCollection =
            await geoconnexApp.fetchFeaturesInCollection({
              collection: newCollection,
              forceFresh: false,
              skipGeometry: false,
            });
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
          for (const collection of remove) {
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

        for (const collection of remove) {
          geoconnexApp.features = geoconnexApp.features.filter((item) => {
            return collection.id !== item.collection;
          });
        }
      }
    },
    selectedReferenceFeatures(newValue, oldValue) {
      const geoconnexApp = this;
      const oldLength = oldValue ? oldValue.length : 0;
      const newLength = newValue ? newValue.length : 0;
      if (newLength > oldLength) {
        geoconnexApp.addSelectedFeatureToResMetadata(newValue.pop());
      } else if (newLength < oldLength) {
        const remove = oldValue.filter((obj) =>
          newValue.every((s) => s.id !== obj.id)
        );

        geoconnexApp.ajaxRemoveFeatureFromResMetadata(remove);
        if (!this.isGeoconnexUrl(remove[0].value)) return;

        try {
          geoconnexApp.selectedFeatureGroup.removeLayer(
            geoconnexApp.selectedLayerDictionary[remove[0].value]
          );
          geoconnexApp.fitMapToFeatures();
        } catch (e) {
          const message = "Error while attempting to remove related feature";
          geoconnexApp.generateAppMessage(`${message}: ${e.message}`);
          geoconnexApp.error(message, e);
        }

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
      const geoconnexApp = this;
      try {
        const promises = [];
        for (const relation of geoconnexApp.metadataRelations) {
          if (this.isGeoconnexUrl(relation.value)) {
            promises.push(geoconnexApp.fetchSingleFeature(relation));
          } else {
            geoconnexApp.selectedReferenceFeatures.push(relation);
          }
        }
        const results = await Promise.all(promises);
        const features = results.flat().filter(Boolean);
        if (!features) {
          throw new Error("No features returned from fetch");
        }
        for (let feature of features) {
          feature = await geoconnexApp.getFeatureProperties(feature);
          feature.disabled = true;
          geoconnexApp.features.push(feature);
          geoconnexApp.addSelectedFeatureToMap(feature);
          const featureValues = {
            id: feature.relationId,
            text: feature.text,
            value: feature.uri,
          };
          geoconnexApp.selectedReferenceFeatures.push(featureValues);
        }
        geoconnexApp.loadingRelations = false;
      } catch (e) {
        const message =
          "Error while attempting to load related features from metadata";
        geoconnexApp.error(message, e);
        geoconnexApp.generateAppMessage(`${message}: ${e.message}`);
      }
    },
    addSelectedFeatureToResMetadata(feature) {
      const geoconnexApp = this;
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
      const geoconnexApp = this;
      if (typeof feature === "string") return;
      if (!feature.geometry) {
        geoconnexApp.fetchGeometryForSingleFeature(feature).then((geometry) => {
          feature.geometry = geometry.geometry;
        });
      }
      geoconnexApp.addGeojsonToMap({
        geojson: feature,
        fit: false,
        style: undefined,
        group: geoconnexApp.selectedFeatureGroup,
      });
    },
    ajaxSaveFeatureToResMetadata(feature) {
      const geoconnexApp = this;
      const url = `/hsapi/_internal/${geoconnexApp.resShortId}/geospatialrelation/add-metadata/`;
      const data = {
        text: feature.text || feature,
        value: feature.uri ? feature.uri : feature,
        type: "relation",
      };
      let ajaxResult;
      $.ajax({
        type: "POST",
        url: url,
        data: data,
        success: function (result) {
          // hsapi returns 200 even if the metadata creation fails
          ajaxResult = result;
        },
        complete: function (jqXHR, status) {
          const statusObj = JSON.parse(jqXHR.responseText);
          if (statusObj.status === "error") {
            const message = "Error while attempting to save related feature";
            geoconnexApp.error(message, statusObj.message);
            geoconnexApp.generateAppMessage(`${message}: ${statusObj.message}`);
          } else {
            geoconnexApp.log(
              `Added ${
                feature.text ? feature.text : feature
              } to resource metadata`
            );
            geoconnexApp.selectedReferenceFeatures.push({
              id: ajaxResult.element_id,
              value: feature.uri ? feature.uri : feature,
              text: feature.text ? feature.text : feature,
            });
          }
        },
      });
    },
    ajaxRemoveFeatureFromResMetadata(relations) {
      const geoconnexApp = this;
      for (const relation of relations) {
        if (relation.id) {
          const url = `/hsapi/_internal/${geoconnexApp.resShortId}/geospatialrelation/${relation.id}/delete-metadata/`;
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
              const message =
                "Error while attempting to remove related feature";
              geoconnexApp.error(message, error);
              geoconnexApp.generateAppMessage(`${message}: ${error}`);
            },
          });
        }
      }
    },
    limitSelectableFeaturesToSearch() {
      const geoconnexApp = this;
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
      geoconnexApp.features = geoconnexApp.features.filter((s) => {
        const ignoredDict = geoconnexApp.ignoredFeatures[s.collection];
        if (ignoredDict && ignoredDict.includes(s.id)) return false;
        return keep.includes(s.uri);
      });
      geoconnexApp.loadingRelations = false;
    },

    /* --------------------------------------------------
    Fetch Request Methods
    -------------------------------------------------- */
    async fetchCollections(forceFresh = false) {
      const geoconnexApp = this;
      geoconnexApp.loadingCollections = true;
      try {
        const response = await geoconnexApp.fetchURLFromCacheOrGeoconnex({
          url: `${geoconnexApp.geoconnexUrl}?f=json&skipGeometry=true`,
          forceFresh: forceFresh,
        });
        geoconnexApp.collections = response.collections.filter((col) => {
          return !geoconnexApp.ignoredCollections.includes(col.id);
        });
      } catch (e) {
        geoconnexApp.error("Error while loading collections", e);
      }
      geoconnexApp.loadingCollections = false;
    },
    fetchGeoconnexFeaturesContainingPoint(
      lat = null,
      long = null,
      collections = null
    ) {
      const geoconnexApp = this;
      long = typeof long == "number" ? long : geoconnexApp.pointLong;
      lat = typeof lat == "number" ? lat : geoconnexApp.pointLat;
      geoconnexApp.map.closePopup();

      const bbox = [long, lat, long + 10e-12, lat + 10e-12];
      geoconnexApp.fetchGeoconnexFeaturesInBbox({
        bbox: bbox,
        collections: collections,
      });
    },
    async fetchGeoconnexFeaturesInBbox({ bbox = null, collections = null }) {
      const geoconnexApp = this;
      if (!bbox) bbox = geoconnexApp.bBox;
      let features = [];
      geoconnexApp.map.closePopup();
      try {
        if (!collections || collections.length === 0) {
          // fetch features from all collections
          collections = geoconnexApp.collections;
        }

        const promises = [];
        for (let collection of collections) {
          const featureCount =
            await geoconnexApp.countFeaturesFromSingleCollectionInBbox({
              collection: collection,
              bbox: bbox,
            });
          if (featureCount >= limitNumberOfFeaturesPerRequest) {
            geoconnexApp.searchResultString = `Your search in ${collection.id} returned too many features.
            The limit is ${limitNumberOfFeaturesPerRequest} so no geometries were mapped.
            We recommend that you refine resource extent, conduct a point search by clicking on the map, or search using map bounds.`;
            return;
          }
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
        const results = await Promise.all(promises);
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
          "Error while attempting to find intersecting geometries",
          e
        );
      }
    },
    async fetchFeaturesFromSingleCollectionInBbox(
      collection,
      bbox = null,
      refresh = false
    ) {
      const geoconnexApp = this;
      geoconnexApp.searchingDescription = collection.description;
      let response = {};
      let nameProperty = await geoconnexApp.getFeatureNameField(collection.id);
      nameProperty = nameProperty ? `,${nameProperty}` : "";
      const propertiesParameter = `&properties=uri${nameProperty}`;
      const bboxParameter = bbox ? `&bbox=${bbox.toString()}` : "";
      const query = `${geoconnexApp.geoconnexUrl}/${collection.id}/${geoconnexBaseURLQueryParam}${propertiesParameter}${bboxParameter}`;
      response = await geoconnexApp.fetchURLFromCacheOrGeoconnex({
        url: query,
        forceFresh: refresh,
      });
      geoconnexApp.searchingDescription = "";

      // store the collection for future reference
      response &&
        response.features.forEach((feature) => {
          feature.collection = collection;
        });
      return response ? response.features : null;
    },
    async countFeaturesFromSingleCollectionInBbox({
      collection = null,
      bbox = null,
      refresh = false,
    }) {
      const geoconnexApp = this;
      let response = {};
      const propertiesParameter = "&properties=fid";
      const bboxParameter = bbox ? `&bbox=${bbox.toString()}` : "";
      const query = `${geoconnexApp.geoconnexUrl}/${collection.id}/${geoconnexBaseURLQueryParam}${propertiesParameter}&skipGeometry=true${bboxParameter}`;
      response = await geoconnexApp.fetchURLFromCacheOrGeoconnex({
        url: query,
        forceFresh: refresh,
      });
      return response ? response.features.length : 0;
    },
    async fetchGeometryForSingleFeature(geoconnexObj, refresh = false) {
      const geoconnexApp = this;
      geoconnexApp.searchingDescription = geoconnexObj.collection;
      if (refresh || !geoconnexObj.geometry) {
        const query = `${geoconnexApp.geoconnexUrl}/${geoconnexObj.collection}/items/${geoconnexObj.id}?f=json`;
        const response = await geoconnexApp.fetchURLFromCacheOrGeoconnex({
          url: query,
          forceFresh: refresh,
        });
        geoconnexObj.geometry = response.geometry;
      }
      geoconnexApp.searchingDescription = "";
      return geoconnexObj;
    },
    async fetchSingleFeature(relation) {
      try {
        const geoconnexApp = this;
        const uri = relation.value;
        geoconnexApp.searchingDescription = uri;
        const relative_id = uri.split("ref/").pop();
        const collection = relative_id.split("/")[0];
        const id = relative_id.split("/")[1];
        const query = `${geoconnexApp.geoconnexUrl}/${collection}/items/${id}?f=json`;
        const response = await geoconnexApp.fetchURLFromCacheOrGeoconnex({
          url: query,
        });
        geoconnexApp.searchingDescription = "";
        response.relationId = relation.id;
        return response;
      } catch (e) {
        const message = `Error fetching Geoconnex feature`;
        geoconnexApp.generateAppMessage(`${message}: ${e.message}`);
        geoconnexApp.error(message, e);
      }
    },
    async fetchFeaturesInCollection({
      collection = {},
      forceFresh = false,
      skipGeometry = true,
    }) {
      const geoconnexApp = this;
      let nameProperty = await geoconnexApp.getFeatureNameField(collection.id);
      nameProperty = nameProperty ? `,${nameProperty}` : "";
      const propertiesParameter = `&properties=uri${nameProperty}`;
      const url = `${geoconnexApp.geoconnexUrl}/${
        collection.id
      }/${geoconnexBaseURLQueryParam}${propertiesParameter}&skipGeometry=${skipGeometry.toString()}`;
      const featureCollection = await geoconnexApp.fetchURLFromCacheOrGeoconnex(
        {
          url: url,
          forceFresh: forceFresh,
        }
      );
      featureCollection.collection = collection;
      return featureCollection;
    },
    async fetchURLFromCacheOrGeoconnex({
      url,
      forceFresh = false,
      collection = null,
    }) {
      const geoconnexApp = this;
      let data = {};
      try {
        if (!("caches" in window)) {
          geoconnexApp.log(
            "Cache API not available. Fetching geoconnex data from:\n" + url
          );
          const fetch_resp = await fetch(url);
          if (!fetch_resp.ok) {
            const message =
              "Error while attempting to fetch data from Geoconnex";
            geoconnexApp.generateAppMessage(
              `${message}: ${fetch_resp.statusText}`
            );
            geoconnexApp.error(message, fetch_resp);
          } else {
            data = await fetch_resp.json();
          }
        } else {
          const cache_resp = await geoconnexApp.geoCache.match(url);
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
      } catch (e) {
        const message = `Error while attempting to fetch Geoconnex relations`;
        geoconnexApp.generateAppMessage(`${message}: ${e.message}`);
        geoconnexApp.error(message, e);
      }
    },
    async fetchURLFromGeoconnex(url) {
      let fetchData = {};
      const geoconnexApp = this;

      geoconnexApp.log(
        "Fetching + adding to cache, geoconnex data from:\n" + url
      );
      try {
        const fetch_resp = await fetch(url);
        if (!fetch_resp.ok) {
          const message = "Error while attempting to fetch Geoconnex relations";
          geoconnexApp.generateAppMessage(
            `${message}: ${fetch_resp.statusText}`
          );
          geoconnexApp.error(message, fetch_resp);
        } else {
          const copy = fetch_resp.clone();
          const headers = new Headers(copy.headers);
          headers.append("fetched-on", new Date().getTime());
          const body = await copy.blob();
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
        const response = await geoconnexApp.geoCache.match(url);
        if (response) {
          geoconnexApp.log(
            "Geoconnex API fetch error. Falling back to old cached version"
          );
          return response.data;
        } else {
          geoconnexApp.error(e.message);
          geoconnexApp.generateAppMessage(
            `Error while attempting to fetch Geoconnex items: ${e.message}`
          );
        }
      }
      return fetchData;
    },

    /* --------------------------------------------------
    Mapping Methods
    -------------------------------------------------- */
    showSpatialExtent({ bbox = null, fromPoint = false } = {}) {
      const geoconnexApp = this;
      if (!bbox) bbox = geoconnexApp.bBox;
      try {
        const rect = L.rectangle(
          [
            [bbox[1], bbox[0]],
            [bbox[3], bbox[2]],
          ],
          { interactive: false }
        );
        const poly = rect.toGeoJSON();
        poly.text = "Resource Spatial Extent";
        geoconnexApp.addGeojsonToMap({
          geojson: poly,
          fit: false,
          style: {
            color: geoconnexApp.spatialExtentColor,
            fillColor: geoconnexApp.spatialExtentColor,
            fillOpacity: 0.15,
          },
          group: geoconnexApp.spatialExtentGroup,
          interactive: false,
        });
        geoconnexApp.resSpatialExtentArea = L.GeometryUtil.geodesicArea(
          rect.getLatLngs()[0]
        ); //sq meters
        if (fromPoint) {
          // the bbox is just a tiny box generated by a point
          const geojson = {
            type: "Point",
            coordinates: [geoconnexApp.pointLong, geoconnexApp.pointLat],
            text: "Resource Spatial Extent",
          };
          geoconnexApp.addGeojsonToMap({
            geojson: geojson,
            fit: false,
            style: {},
            group: geoconnexApp.spatialExtentGroup,
            interactive: false,
            marker: true,
          });
        }
      } catch (e) {
        geoconnexApp.error("Error attempting to show spatial extent", e);
      }
    },
    initializeLeafletMap() {
      const geoconnexApp = this;
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

      const terrain = L.tileLayer(
        "https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.jpg",
        {
          attribution:
            'Map tiles by <a href="http://stamen.com" target="_blank">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0" target="_blank">CC BY 3.0</a>. Data by <a href="http://openstreetmap.org" target="_blank">OpenStreetMap</a>, under <a href="http://www.openstreetmap.org/copyright" target="_blank">ODbL</a>.',
          maxZoom: 18,
        }
      );

      const streets = L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
          attribution:
            'Map data &copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors',
          maxZoom: 18,
        }
      );

      const googleSat = L.tileLayer(
        "http://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        {
          maxZoom: 20,
          subdomains: ["mt0", "mt1", "mt2", "mt3"],
        }
      );

      const baseMaps = {
        Streets: streets,
        Terrain: terrain,
        Satelite: googleSat,
      };

      geoconnexApp.map.attributionControl.setPrefix(
        '<a href="https://leafletjs.com/" target="blank">Leaflet</a>'
      );

      const overlayMaps = {
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
          const recenterButton = L.DomUtil.create(
            "div",
            "leaflet-bar leaflet-control"
          );
          recenterButton.setAttribute("title", "Resize to features");

          recenterButton.innerHTML = `<a role="button"><i class="fa fa-dot-circle-o fa-2x" style="padding-top:3px"></i></a>`;

          L.DomEvent.on(recenterButton, "click", (e) => {
            e.stopPropagation();
            geoconnexApp.fitMapToFeatures({
              group: null,
              overrideShouldFit: true,
            });
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
    },
    async addSearchFeaturesToMap(features, collectionOverride = null) {
      const geoconnexApp = this;
      const abortSignal = geoconnexApp.abortController.signal;
      for (const feature of features) {
        if (abortSignal.aborted) {
          return;
        }
        // deal with collection first
        const collection = collectionOverride
          ? collectionOverride
          : feature.collection;

        if (geoconnexApp.ignoredFeatures[collection.id]?.includes(feature.id))
          return;

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
            geoconnexApp.trimString(
              collection.description,
              ` (${collection.id})`
            )
          );

          geoconnexApp.expandLayerControlOnAdd &&
            geoconnexApp.layerControl.expand();
        }
        geoconnexApp.map.addLayer(
          geoconnexApp.searchLayerGroupDictionary[collection.id]
        );

        // second deal with the actual item
        const alreadySelected = geoconnexApp.selectedReferenceFeatures.find(
          (obj) => {
            return obj.value && obj.value === feature.properties.uri;
          }
        );
        if (alreadySelected) {
          feature.disabled = true;
        } else {
          await geoconnexApp.getFeatureProperties(feature);
          if (feature.geometry.type.includes("Point")) {
            geoconnexApp.addGeojsonToMap({
              geojson: feature,
              fit: false,
              style: {
                color: geoconnexApp.collectionSearchColor,
                radius: 5,
                fillColor: geoconnexApp.mappedPointFillColor,
                fillOpacity: 0.8,
              },
              group: geoconnexApp.searchFeatureGroup,
            });
          } else {
            geoconnexApp.addGeojsonToMap({
              geojson: feature,
              fit: false,
              style: { color: geoconnexApp.collectionSearchColor },
              group: geoconnexApp.searchFeatureGroup,
            });
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
    addGeojsonToMap({
      geojson = {},
      fit = false,
      style = { color: this.featureSelectColor, radius: 5 },
      group = null,
      interactive = true,
      marker = false,
    }) {
      const geoconnexApp = this;
      const abortSignal = geoconnexApp.abortController.signal;
      if (abortSignal.aborted) {
        return;
      }
      try {
        const leafletLayer = L.geoJSON(geojson, {
          onEachFeature: function (feature, layer) {
            let popupText = `<h4>${feature.text}</h4>`;
            if (feature.uri) {
              popupText += `<a href=${feature["uri"]} target="_blank">${feature["uri"]}</a></br></br>`;
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
          if (!geoconnexApp.searchLayerGroupDictionary[geojson.collection]) {
            return;
          }
          geoconnexApp.searchLayerGroupDictionary[geojson.collection].addLayer(
            leafletLayer
          );
          geoconnexApp.searchLayerGroupDictionary[geojson.collection].uris.push(
            geojson.uri
          );
        }
        if (group && !group.hasLayer(leafletLayer)) {
          group?.addLayer(leafletLayer);
        }

        // handle zooming
        if (fit) {
          geoconnexApp.map.fitBounds(leafletLayer.getBounds(), {
            maxZoom: geoconnexApp.fitBoundsMaxZoom,
          });
        }
      } catch (e) {
        geoconnexApp.error(e.message);
        geoconnexApp.generateAppMessage(
          `Error while attempting to add item to map: ${e.message}`
        );
      }
    },
    fitMapToFeatures({ group = null, overrideShouldFit = false } = {}) {
      const geoconnexApp = this;
      if (!geoconnexApp.shouldFitMapAfterAddingLayers && !overrideShouldFit) {
        return;
      }
      try {
        if (group) {
          geoconnexApp.map.fitBounds(group.getBounds());
        } else {
          const bounds = L.latLngBounds();
          geoconnexApp.spatialExtentGroup &&
            bounds.extend(geoconnexApp.spatialExtentGroup.getBounds());
          geoconnexApp.searchFeatureGroup &&
            bounds.extend(geoconnexApp.searchFeatureGroup.getBounds());
          geoconnexApp.searchFeatureGroup &&
            bounds.extend(geoconnexApp.selectedFeatureGroup.getBounds());
          if (bounds.isValid()) {
            // check to see if already zoomed within bounds -- in which case dont re-zoom
            const alreadyZoomed = bounds.contains(geoconnexApp.map.getBounds());
            if (
              alreadyZoomed &&
              geoconnexApp.onlyZoomInNotOutAfterLayerAddition &&
              !overrideShouldFit
            ) {
              return;
            }
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
      const geoconnexApp = this;
      geoconnexApp.searchingDescription = `${
        geoconnexApp.collectionsSelectedToSearch.at(-1).description
      }`;
      geoconnexApp
        .fetchGeoconnexFeaturesInBbox({
          bbox: geoconnexApp.map.getBounds().toBBoxString(),
          collections: geoconnexApp.collectionsSelectedToSearch,
        })
        .then(() => {
          geoconnexApp.searchingDescription = "";
        });
    },
    mapDisplayNoFoundFeatures(bbox) {
      const poly = L.rectangle([
        [bbox[1], bbox[0]],
        [bbox[3], bbox[2]],
      ]);
      const loc = poly.getBounds().getCenter();
      const content = `<div data='${JSON.stringify(
        loc
      )}'>No features found for your search.</div>`;
      L.popup({ maxWidth: 400, autoClose: true })
        .setLatLng(loc)
        .setContent(content)
        .openOn(geoconnexApp.map);
    },
    async clearMapOfSearches() {
      const geoconnexApp = this;
      geoconnexApp.abortController.abort();
      geoconnexApp.abortController = new AbortController();
      for (const key in geoconnexApp.searchLayerGroupDictionary) {
        geoconnexApp.layerControl.removeLayer(
          geoconnexApp.searchLayerGroupDictionary[key]
        );
        delete geoconnexApp.searchLayerGroupDictionary[key];
      }

      geoconnexApp.hasSearches = false;
      geoconnexApp.collectionsSelectedToSearch = [];
      geoconnexApp.searchFeatureGroup.clearLayers();
      geoconnexApp.fitMapToFeatures();
      geoconnexApp.layerControl.collapse();
    },
    updateSpatialExtentType() {
      const geoconnexApp = this;
      geoconnexApp.resSpatialType = null;
      const spatial_coverage_drawing = $("#coverageMap .leaflet-interactive");
      if (spatial_coverage_drawing.size() > 0) {
        const checked = $("#div_id_type input:checked").val();
        geoconnexApp.resSpatialType = checked || spatial_coverage_type;
      }
    },
    updateAppWithResSpatialExtent() {
      const geoconnexApp = this;
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
        geoconnexApp.showSpatialExtent({ bbox: null, fromPoint: true });
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
        geoconnexApp.log("Resource spatial extent isn't set");
      }
    },
    fillCoordinatesFromClickedCoordinates(lat, long) {
      const geoconnexApp = this;
      geoconnexApp.pointLat = lat;
      geoconnexApp.pointLong = long;
    },
    setMapEvents() {
      const geoconnexApp = this;
      var popup = L.popup({ maxWidth: 400 });

      function onMapClick(e) {
        if (!geoconnexApp.hasSearches) return;
        const loc = { lat: e.latlng.lat, long: e.latlng.lng };
        const content = `<button class="btn btn-info leaflet-point-search" data='${JSON.stringify(
          loc
        )}'><i class="fa fa-map-marker"></i>Find features containing this point</button>`;
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
            const data = JSON.parse($(this).attr("data"));
            const alreadySelected = geoconnexApp.selectedReferenceFeatures.find(
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
            const data = JSON.parse($(this).attr("data"));
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
      const geoconnexApp = this;
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
    generateAppMessage(message, level = "danger") {
      if (level === "danger")
        message += " -- If this issue persists, please notify help@cuahsi.org.";
      if (!geoconnexApp.appMessages.some((m) => m.message === message)) {
        geoconnexApp.appMessages.push({ message: message, level: level });
      }
    },
    async setFeatureName(feature) {
      if (feature.NAME) return;
      const geoconnexApp = this;
      let nameField;
      if (feature.collection in geoconnexApp.featureNameMap) {
        nameField = geoconnexApp.featureNameMap[feature.collection];
      } else {
        nameField = await geoconnexApp.getFeatureNameField(feature.collection);
        geoconnexApp.featureNameMap[feature.collection] = nameField;
      }
      feature.NAME = feature.properties[nameField] || "";
    },
    async getFeatureNameField(collectionName) {
      const geoconnexApp = this;
      if (collectionName in geoconnexApp.featureNameMap) {
        return geoconnexApp.featureNameMap[collectionName];
      }
      const url = `${geoconnexApp.geoconnexUrl}/${collectionName}/items?f=jsonld&lang=en-US&skipGeometry=true&limit=1`;
      // don't fetch the contexts from cache, get it direct from Geoconnex api
      const featureJsonLd = await geoconnexApp.fetchURLFromCacheOrGeoconnex({
        url: url,
        forceFresh: true,
      });
      const contexts = featureJsonLd["@context"];
      for (let context of contexts) {
        const nameField = Object.keys(context).find(
          (key) => context[key] === "schema:name"
        );
        if (nameField) {
          geoconnexApp.featureNameMap[collectionName] = nameField;
          return nameField;
        }
      }
      return geoconnexApp.getFirstFeatureNameField(collectionName);
    },
    /**
     * Gracefully handle when there is no name field in a collection schema
     * @param  {String} collectionName Name of the geoconnex collection
     * @return {String} Key of the first feature property that resembles a potential name
     */
    async getFirstFeatureNameField(collectionName) {
      const geoconnexApp = this;
      const url = `${geoconnexApp.geoconnexUrl}/${collectionName}/items?f=json&lang=en-US&skipGeometry=true&limit=1`;
      const featureJson = await geoconnexApp.fetchURLFromCacheOrGeoconnex({
        url: url,
        forceFresh: true,
      });
      const properties = featureJson.features[0].properties;
      const match = Object.keys(properties).filter((key) =>
        /.*name.*/i.test(key)
      );
      let first = match[0];
      if (first) {
        geoconnexApp.featureNameMap[collectionName] = first;
        return first;
      }
      return "";
    },
    async getFeatureProperties(feature) {
      const geoconnexApp = this;
      // Account for some oddities in the Geoconnex API schema
      feature.relative_id = feature.properties.uri.split("ref/").pop();
      feature.collection = feature.relative_id.split("/")[0];
      feature.uri = feature.properties.uri;
      await geoconnexApp.setFeatureName(feature);
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
    isGeoconnexUrl(stringToTest) {
      return this.isUrl(stringToTest) && stringToTest.indexOf("geoconnex") > -1;
    },
    trimString(longString, append = "") {
      return longString.length + append.length > geoconnexApp.stringLengthLimit
        ? `${longString.substring(
            0,
            geoconnexApp.stringLengthLimit - append.length
          )}...${append}`
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
      const geoconnexApp = this;
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
      const geoconnexApp = this;
      geoconnexApp.featureRules = [
        function (v) {
          const invalid = [];
          for (const item of v) {
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
    configureLogging() {
      const geoconnexApp = this;
      if (geoconnexAppVerbose) {
        geoconnexApp.log = console.log.bind(
          window.console,
          "%cGeoconnex:",
          "color: white; background:blue;"
        );
      } else {
        geoconnexApp.log = function () {};
      }
    },
  },
  beforeMount() {
    this.setCustomFeatureRules();
  },
  async mounted() {
    const geoconnexApp = this;
    geoconnexApp.abortController = new AbortController();
    geoconnexApp.isLoading = true;
    geoconnexApp.configureLogging();
    if (
      geoconnexApp.resMode == "Edit" ||
      geoconnexApp.metadataRelations.length > 0
    ) {
      geoconnexApp.geoCache = await caches.open(geoconnexApp.cacheName);
      geoconnexApp.initializeLeafletMap();

      geoconnexApp.resMode == "Edit" && geoconnexApp.fetchCollections(false);
      await geoconnexApp.loadResourceMetadataRelations();

      if (geoconnexApp.resMode == "Edit") {
        // wait for spatial coverage map to load before getting extent
        await geoconnexApp
          .until((_) => coverageMap)
          .then(() => {
            geoconnexApp.updateAppWithResSpatialExtent();
          });
      }
      geoconnexApp.fitMapToFeatures({ group: null, overrideShouldFit: true });
    }
    geoconnexApp.isLoading = false;
  },
});
