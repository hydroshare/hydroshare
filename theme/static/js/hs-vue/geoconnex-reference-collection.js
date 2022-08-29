let counter = 0;
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
      isSearching: false,
      loadingCollections: true,
      loadingDescription: "",
      geometriesMessage: "",
      errorMsg: "",
      errored: false,
      geoconnexUrl: "https://reference.geoconnex.us/collections",
      apiQueryNoGeo: "items?f=json&lang=en-US&skipGeometry=true",
      apiQueryYesGeo: "items?f=json&lang=en-US&skipGeometry=false",
      cacheName: "geoconnexCache",
      collectionsDefaultHidden: ["principal_aq", "nat_aq"],
      geoCache: null,
      resShortId: SHORT_ID,
      cacheDuration: 1000 * 60 * 60 * 24 * 7, // one week in milliseconds
      enforceCacheDuration: false,
      search: null,
      rules: null,
      showingMap: false,
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
      searchColor: "orange",
      selectColor: "purple",
    };
  },
  watch: {
    values(newValue, oldValue) {
      let geoconnexApp = this;
      geoconnexApp.errorMsg = "";
      if (newValue.length > oldValue.length) {
        geoconnexApp.addSelectedToResMetadata(newValue.pop());
      } else if (newValue.length < oldValue.length) {
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
      geoconnexApp.fetchSingleGeometry(selected).then((geometry) => {
        selected.geometry = geometry.geometry;
        let shouldZoom = selected.geometry.type.includes("Poly");
        geoconnexApp.addToMap(selected, shouldZoom);
        shouldZoom ? null : geoconnexApp.fitMapToFeatures();
      });
      geoconnexApp.ajaxSaveMetadata(selected);

      // disable so that it can't be duplicated
      geoconnexApp.items.forEach((it) => {
        if (selected.uri === it.uri) {
          it.disabled = true;
        }
      });
    },
    async fetchSingleGeometry(geoconnexObj, refresh = false) {
      let geoconnexApp = this;
      let response = {};
      if (refresh || !geoconnexObj.geometry) {
        let query = `${geoconnexApp.geoconnexUrl}/${geoconnexObj.collection}/items/${geoconnexObj.id}?f=json`;
        response = await geoconnexApp.fetchFromCacheOrAPI(query, refresh);
      } else {
        response.geometry = geoconnexObj.geometry;
      }
      return response;
    },
    async fetchAllGeometries() {
      let geoconnexApp = this;
      var itemsWithGeo = [];
      let calls = [];
      for (let collection of geoconnexApp.collections) {
        geoconnexApp.geometriesMessage = `Loading geometries from collection: ${collection.id}`;
        const url = `${geoconnexApp.geoconnexUrl}/${collection.id}/${geoconnexApp.apiQueryYesGeo}`;
        calls.push(
          await geoconnexApp.fetchFromCacheOrAPI(url, false, collection)
        );
      }
      Promise.all(calls)
        .then(function (resultsArray) {
          if (!$.isEmptyObject(resultsArray)) {
            for (let response of resultsArray) {
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
        })
        .then(function () {
          // overwrite now that we have the geometries
          geoconnexApp.items = itemsWithGeo;
          geoconnexApp.geometriesAreLoaded = true;
        });
    },
    async fetchSingleReferenceItem(uri) {
      let geoconnexApp = this;
      let relative_id = uri.split("ref/").pop();
      let collection = relative_id.split("/")[0];
      let id = relative_id.split("/")[1];
      let query = `${geoconnexApp.geoconnexUrl}/${collection}/items/${id}?f=json`;
      let response = await geoconnexApp.fetchFromCacheOrAPI(query);
      return response;
    },
    initLeafletFeatureGroups(){
      let geoconnexApp = this;
      geoconnexApp.selectedFeatureGroup = L.featureGroup();
      geoconnexApp.searchFeatureGroup = L.featureGroup();
    },
    initLeafletMap() {
      let geoconnexApp = this;
      geoconnexApp.selectedFeatureGroup ?? geoconnexApp.initLeafletFeatureGroups();
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
      // World: geoconnexApp.map.setView([30, 0], 1);
      geoconnexApp.map.setView([41.850033, -87.6500523], 3);
      geoconnexApp.setLeafletMapEvents();

      geoconnexApp.loadAllRelationGeometries();
    },
    async addToMap(
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
            // World: geoconnexApp.map.setView([30, 0], 1);
            geoconnexApp.map.setView([41.850033, -87.6500523], 3);
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
    async getCollections(forceFresh = false) {
      let geoconnexApp = this;
      const collectionsUrl = `${geoconnexApp.geoconnexUrl}?f=json&lang=en-US`;
      try {
        let response = await geoconnexApp.fetchFromCacheOrAPI(
          collectionsUrl,
          forceFresh
        );
        return response;
      } catch (e) {
        console.error(e.message);
        geoconnexApp.errored = true;
      }
    },
    createVuetifySelectSubheader(collection) {
      return {
        header: `${collection.description} (${collection.id})`,
        text: `${collection.description} (${collection.id})`,
      };
    },
    async getAllItems(forceFresh = false) {
      let calls = [];
      let geoconnexApp = this;
      let collections = await geoconnexApp.getCollections(forceFresh);
      geoconnexApp.collections = collections.collections;
      for (let col of geoconnexApp.collections) {
        geoconnexApp.loadingDescription = col.description;
        calls.push(geoconnexApp.getItemsIn(col, forceFresh));
      }
      await Promise.all(calls).then(function (resultsArray) {
        for (let resp of resultsArray) {
          if (!jQuery.isEmptyObject(resp) && resp.features) {
            geoconnexApp.items.push(
              geoconnexApp.createVuetifySelectSubheader(resp.collection)
            );
            for (let feature of resp.features) {
              geoconnexApp.items.push(
                geoconnexApp.getFeatureProperties(feature)
              );
            }
          }
        }
      });
    },
    async refreshItemsSilently() {
      let calls = [];
      let geoconnexApp = this;
      if (geoconnexApp.debug) console.log("Refreshing from Geoconnex API");
      let collections = await geoconnexApp.getCollections(true);
      geoconnexApp.collections = collections.collections;
      let refreshedItems = [];
      for (let col of geoconnexApp.collections) {
        calls.push(geoconnexApp.getItemsIn(col, true));
      }
      Promise.all(calls)
        .then(function (resultsArray) {
          for (let resp of resultsArray) {
            if (!jQuery.isEmptyObject(resp) && resp.features) {
              refreshedItems.push(
                geoconnexApp.createVuetifySelectSubheader(resp.collection)
              );
              for (let feature of resp.features) {
                refreshedItems.push(geoconnexApp.getFeatureProperties(feature));
              }
            }
          }
        })
        .then(() => {
          geoconnexApp.items = refreshedItems;
          if (geoconnexApp.debug)
            console.log("Completed background refresh from Geoconnex API");
        });
    },
    getFeatureProperties(feature) {
      let geoconnexApp = this;
      // Account for some oddities in the Geoconnex API schema
      feature.relative_id = feature.properties.uri.split("ref/").pop();
      feature.collection = feature.relative_id.split("/")[0];
      feature.uri = feature.properties.uri;
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
      // Used in resource VIEW mode, when no new items will be added
      let geoconnexApp = this;
      for (let relation of geoconnexApp.metadataRelations) {
        if (
          this.isUrl(relation.value) &&
          relation.value.indexOf("geoconnex") > -1
        ) {
          let feature = await geoconnexApp.fetchSingleReferenceItem(
            relation.value
          );
          geoconnexApp.items.push(geoconnexApp.getFeatureProperties(feature));
        }
      }
    },
    async getItemsIn(collection, forceFresh = false) {
      let geoconnexApp = this;
      const url = `${geoconnexApp.geoconnexUrl}/${collection.id}/${geoconnexApp.apiQueryNoGeo}`;
      let response = await geoconnexApp.fetchFromCacheOrAPI(url, forceFresh);
      response.collection = collection;
      return response;
    },
    async fetchFromCacheOrAPI(url, forceFresh = false, collection = null) {
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
          data = await geoconnexApp.fetchFromGeoconnexApi(url);
        }
      }
      if (collection) {
        data.collection = collection;
      }
      return data;
    },
    async fetchFromGeoconnexApi(url) {
      let data = {};
      let geoconnexApp = this;
      if (geoconnexApp.debug)
        console.log("Fetching + adding to cache, geoconnex data from:\n" + url);
      try {
        let fetch_resp = await fetch(url);
        if (!fetch_resp.ok) {
          console.error(
            `Error when attempting to fetch Geoconnex relations: ${fetch_resp.statusText}`
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
          data = await fetch_resp.json();
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
      return data;
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
    async loadMetadataRelations() {
      let geoconnexApp = this;
      for (relation of geoconnexApp.metadataRelations) {
        if (relation.type === "relation") {
          let item;
          try {
            new URL(relation.value);
            item = geoconnexApp.items.find((obj) => {
              return obj.uri === relation.value;
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
    getGeoItemsFromDebug() {
      let geoconnexApp = this;
      if (geoconnexApp.resSpatialType == "point") {
        geoconnexApp.queryGeoItemsRadius(
          geoconnexApp.pointLat,
          geoconnexApp.pointLong
        );
      } else if (geoconnexApp.resSpatialType == "box") {
        let bbox = [
          geoconnexApp.eastLong,
          geoconnexApp.southLat,
          geoconnexApp.westLong,
          geoconnexApp.northLat,
        ];
        var polygon = turf.bboxPolygon(bbox);
        polygon.text = "Search bounds";
        geoconnexApp.queryGeoItemsInPoly(polygon);
      } else {
        alert("Spatial extent isn't set?....");
      }
    },
    queryGeoItemsFromExtent() {
      let geoconnexApp = this;
      if (geoconnexApp.resSpatialType == "point") {
        geoconnexApp.queryGeoItemsContainingPoint(
          geoconnexApp.pointLat,
          geoconnexApp.pointLong
        );
      } else if (geoconnexApp.resSpatialType == "box") {
        let bbox = [
          geoconnexApp.eastLong,
          geoconnexApp.southLat,
          geoconnexApp.westLong,
          geoconnexApp.northLat,
        ];
        var polygon = turf.bboxPolygon(bbox);
        polygon.text = "Search bounds";
        geoconnexApp.queryGeoItemsInPoly(polygon);
      } else {
        alert("Spatial extent isn't set?....");
      }
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
      geoconnexApp.loadingCollections = true;
      geoconnexApp.map.closePopup();

      geoconnexApp.addToMap(
        center,
        false,
        { color: "red", fillColor: "red", fillOpacity: 0.1, radius: 1 },
        (group = geoconnexApp.searchFeatureGroup)
      );

      for (let item of geoconnexApp.items) {
        if (item.header) continue;
        let alreadySelected = geoconnexApp.values.find((obj) => {
          return obj.value === item.uri;
        });
        if (alreadySelected) {
          continue;
        }
        try {
          geoconnexApp.loadingDescription = item.collection;
          let geometry = await geoconnexApp.fetchSingleGeometry(item);
          item.geometry = geometry.geometry;
          if (item.geometry.type.includes("Polygon")) {
            if (turf.area(item) < geoconnexApp.maxAreaToReturn * 1e6) {
              if (turf.booleanPointInPolygon(center, item)) {
                await geoconnexApp.addToMap(
                  item,
                  false,
                  { color: geoconnexApp.searchColor },
                  (group = geoconnexApp.searchFeatureGroup)
                );
              }
            }
          }
        } catch (e) {
          console.error(`Error while attempting to load ${item.text}: ${e}`);
        }
      }
      geoconnexApp.fitMapToFeatures(geoconnexApp.searchFeatureGroup);
      geoconnexApp.loadingCollections = false;
      geoconnexApp.hasSearches = true;
    },
    async queryGeoItemsInPoly(polygon = null) {
      // https://turfjs.org/docs/#intersects
      // https://turfjs.org/docs/#booleanIntersects
      // https://turfjs.org/docs/#booleanContains
      let geoconnexApp = this;
      geoconnexApp.loadingCollections = true;
      geoconnexApp.map.closePopup();

      geoconnexApp.addToMap(
        polygon,
        false,
        { color: "red", fillColor: "red", fillOpacity: 0.1 },
        (group = geoconnexApp.searchFeatureGroup)
      );

      for (let item of geoconnexApp.items) {
        if (item.header) continue;
        try {
          geoconnexApp.loadingDescription = item.collection;
          let alreadySelected = geoconnexApp.values.find((obj) => {
            return obj.value === item.uri;
          });
          if (alreadySelected) {
            continue;
          }
          let geometry = await geoconnexApp.fetchSingleGeometry(item);
          item.geometry = geometry.geometry;
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
        } catch (e) {
          console.error(
            `Error while attempting to find intersecting geometries: ${e.message}`
          );
        }
      }
      geoconnexApp.fitMapToFeatures(geoconnexApp.searchFeatureGroup);
      geoconnexApp.loadingCollections = false;
      geoconnexApp.hasSearches = true;
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
      geoconnexApp.fitMapToFeatures();
      geoconnexApp.layerControl.collapse();
    },
    queryUsingSpatialExtent() {
      let geoconnexApp = this;
      geoconnexApp.isSearching = true;

      // force isSearching state to updated before running search
      setTimeout(async function () {
        geoconnexApp.fillValuesFromResExtent();
        geoconnexApp.queryGeoItemsFromExtent();
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
        if (geoconnexApp.geometriesAreLoaded) {
          let content = `<button type="button" class="white--text text-none v-btn v-btn--has-bg theme--light v-size--small btn btn-success leaflet-point-search" data='${JSON.stringify(
            loc
          )}'>Search for related items containing this point</button>`;
          popup
            .setLatLng(e.latlng)
            .setContent(content)
            .openOn(geoconnexApp.map);
        }
      }

      if (geoconnexApp.resMode === "Edit") {
        geoconnexApp.map.on("click", onMapClick);

        $("div").on("click", "button.leaflet-point-search", function (e) {
          e.stopPropagation();
          var loc = JSON.parse($(this).attr("data"));
          geoconnexApp.fillValuesFromResCoordinates(loc.lat, loc.long);
          geoconnexApp.queryGeoItemsContainingPoint(loc.lat, loc.long);
        });

        $("div").on("click", "button.map-add-geoconnex", function (e) {
          e.stopPropagation();
          let data = JSON.parse($(this).attr("data"));
          let alreadySelected = geoconnexApp.values.find((obj) => {
            return obj.value === data.uri;
          });
          if (!alreadySelected) {
            geoconnexApp.addSelectedToResMetadata(data);
          }
          geoconnexApp.map.closePopup();
        });

        $("div").on("click", "button.map-remove-geoconnex", function (e) {
          e.stopPropagation();
          let data = JSON.parse($(this).attr("data"));
          geoconnexApp.values = geoconnexApp.values.filter(
            (s) => s.value !== data.uri
          );
          geoconnexApp.map.closePopup();
        });
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
  },
  beforeMount() {
    this.setCustomItemRules();
  },
  async mounted() {
    let geoconnexApp = this;
    if (geoconnexApp.resMode == "Edit") {
      geoconnexApp.geoCache = await caches.open(geoconnexApp.cacheName);
      await geoconnexApp.getAllItems(false);
      await geoconnexApp.loadMetadataRelations();
      geoconnexApp.loadingCollections = false;
      geoconnexApp.initLeafletFeatureGroups();
      // load geometries in the background
      geoconnexApp.fetchAllGeometries();
      // refresh cache in the background
      geoconnexApp.refreshItemsSilently();
    } else if (
      geoconnexApp.resMode == "View" &&
      geoconnexApp.metadataRelations.length > 0
    ) {
      geoconnexApp.showingMap = true;
      geoconnexApp.geoCache = await caches.open(geoconnexApp.cacheName);
      await geoconnexApp.getRelationsFromMetadata();
      await geoconnexApp.loadMetadataRelations();
      geoconnexApp.initLeafletMap();
      geoconnexApp.loadingCollections = false;
    }
  },
});
