(function () {
    var BOX_MAX_ZOOM = 18;
    var POINT_MAX_ZOOM = 7;
    var DEFAULT_SORT_ORDER = {
      relevance: "",
      "most-viewed": "desc",
      title: "asc",
      "first-author": "asc",
      "date-created": "desc",
      "last-modified": "desc"
    };
    var mapRegistry = new WeakMap();

    function resolveSortState(search) {
      var params = new URLSearchParams(search || "");
      var sort = params.get("sort") || "relevance";
      var defaultOrder = Object.prototype.hasOwnProperty.call(DEFAULT_SORT_ORDER, sort)
        ? DEFAULT_SORT_ORDER[sort]
        : "";
      var order = params.get("order");
      if (order !== "asc" && order !== "desc") {
        order = defaultOrder;
      }
      return {
        sort: sort,
        order: order || ""
      };
    }

    function syncSortControlsFromUrl() {
      var sortControl = document.getElementById("id_sort");
      if (!sortControl) {
        return;
      }
      var state = resolveSortState(window.location.search);
      sortControl.value = state.sort;

      var orderControl = document.querySelector('input[name="order"]');
      if (orderControl) {
        orderControl.value = state.order;
      }

      var sortButtonLabel = document.getElementById("discovery-sort-button-label");
      var sortMenuItems = document.querySelectorAll(".discovery-sort-menu li[data-sort-value]");
      sortMenuItems.forEach(function(item) {
        if (!(item instanceof HTMLElement)) {
          return;
        }
        var isActive = item.dataset.sortValue === state.sort;
        item.classList.toggle("active", isActive);
        if (isActive && sortButtonLabel) {
          sortButtonLabel.textContent = item.dataset.sortLabel || item.textContent.trim();
        }
      });
    }

    function parseGeoShapeBounds(rawBox) {
      if (!rawBox) {
        return null;
      }
      var extents = rawBox.trim().split(/\s+/).map(function (value) {
        return parseFloat(value);
      });
      if (extents.length !== 4 || extents.some(function (value) { return Number.isNaN(value); })) {
        return null;
      }
      return {
        north: extents[0],
        east: extents[1],
        south: extents[2],
        west: extents[3]
      };
    }

    function fitToSpatialExtent(mapState) {
      if (!mapState || !mapState.markers || !mapState.map || !mapState.markers.getLayers().length) {
        return;
      }
      mapState.map.fitBounds(mapState.markers.getBounds(), {
        maxZoom: mapState.extentType === "GeoCoordinates" ? POINT_MAX_ZOOM : BOX_MAX_ZOOM
      });
    }

    function buildMap(container) {
      if (!window.L) {
        return null;
      }

      var markers = L.featureGroup();
      var worldBounds = L.latLngBounds(L.latLng(-90, -180), L.latLng(90, 180));
      var map = L.map(container, {
        scrollWheelZoom: true,
        zoomControl: false,
        maxBounds: worldBounds,
        maxBoundsViscosity: 1
      });

      var streets = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors',
        maxZoom: BOX_MAX_ZOOM
      });

      var satellite = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", {
        attribution: 'Tiles &copy; Esri',
        maxZoom: BOX_MAX_ZOOM
      });

      map.attributionControl.setPrefix('<a href="https://leafletjs.com/" target="_blank">Leaflet</a>');
      L.control.zoom({ position: "bottomright" }).addTo(map);
      L.control.layers({ Streets: streets, Satellite: satellite }, { "Spatial Extent": markers }, { position: "topright" }).addTo(map);

      var RecenterControl = L.Control.extend({
        options: { position: "bottomright" },
        onAdd: function () {
          var wrapper = L.DomUtil.create("div", "leaflet-bar leaflet-control");
          var button = L.DomUtil.create("a", "", wrapper);
          button.href = "#";
          button.title = "Recenter";
          button.setAttribute("role", "button");
          button.innerHTML = "&#9678;";
          L.DomEvent.disableClickPropagation(wrapper);
          L.DomEvent.on(button, "click", function (event) {
            L.DomEvent.preventDefault(event);
            fitToSpatialExtent(mapState);
          });
          return wrapper;
        }
      });

      var mapState = {
        container: container,
        map: map,
        markers: markers,
        extentType: null
      };

      map.addLayer(streets);
      map.addLayer(markers);
      map.addControl(new RecenterControl());

      return mapState;
    }

    function drawSpatialExtent(mapState) {
      if (!mapState) {
        return;
      }
      var container = mapState.container;
      var markers = mapState.markers;
      markers.clearLayers();

      var type = container.dataset.spatialType;
      mapState.extentType = type;
      if (type === "GeoCoordinates") {
        var latitude = parseFloat(container.dataset.latitude || "");
        var longitude = parseFloat(container.dataset.longitude || "");
        if (!Number.isNaN(latitude) && !Number.isNaN(longitude)) {
          markers.addLayer(L.marker([latitude, longitude]));
        }
      } else if (type === "GeoShape") {
        var bounds = parseGeoShapeBounds(container.dataset.box || "");
        if (bounds) {
          markers.addLayer(L.rectangle([
            [bounds.north, bounds.east],
            [bounds.south, bounds.west]
          ]));
        }
      }
    }

    function ensureSpatialMap(container) {
      if (!container || mapRegistry.has(container)) {
        return mapRegistry.get(container) || null;
      }
      var mapState = buildMap(container);
      if (!mapState) {
        return null;
      }
      drawSpatialExtent(mapState);
      mapRegistry.set(container, mapState);
      return mapState;
    }

    function isVisible(element) {
      return !!(element && element.offsetParent !== null && element.clientWidth > 0 && element.clientHeight > 0);
    }

    function refreshMapLayout(mapState) {
      if (!mapState) {
        return;
      }
      mapState.map.invalidateSize({ pan: false });
      if (mapState.markers && mapState.markers.getLayers().length) {
        fitToSpatialExtent(mapState);
        return;
      }
      mapState.map.setView([0, 0], 2, { animate: false });
    }

    function activateSpatialMaps(root) {
      if (!root || !root.querySelectorAll) {
        return;
      }
      var containers = root.querySelectorAll(".discovery-spatial-map");
      containers.forEach(function (container) {
        if (!isVisible(container)) {
          return;
        }
        var mapState = ensureSpatialMap(container);
        if (!mapState) {
          return;
        }

        requestAnimationFrame(function () {
          refreshMapLayout(mapState);
          setTimeout(function () {
            refreshMapLayout(mapState);
          }, 80);
        });
      });
    }

    function clearControlsForFilterRemoval(trigger) {
      var keys = (trigger.dataset.filterKeys || '').split(',').map(function(value) {
        return value.trim();
      }).filter(Boolean);
      var singleKey = trigger.dataset.filterKey;
      if (singleKey && keys.indexOf(singleKey) === -1) {
        keys.push(singleKey);
      }
      var removeValue = trigger.dataset.filterValue || '';

      keys.forEach(function(key) {
        var controls = document.querySelectorAll('[name="' + key + '"]');
        controls.forEach(function(control) {
          if (!(control instanceof HTMLElement)) {
            return;
          }
          if (control.type === 'checkbox' || control.type === 'radio') {
            if (!removeValue || control.value === removeValue || key.indexOf('enable') === 0) {
              control.checked = false;
            }
          } else {
            control.value = '';
          }
        });
      });

      if (keys.indexOf('contentType') !== -1) {
        var anyContentTypeChecked = document.querySelector('input[name="contentType"]:checked');
        var contentToggle = document.querySelector('input[name="enableContentType"]');
        if (contentToggle && !anyContentTypeChecked) {
          contentToggle.checked = false;
        }
      }

      if (keys.indexOf('creativeWorkStatus') !== -1) {
        var anyStatusChecked = document.querySelector('input[name="creativeWorkStatus"]:checked');
        var statusToggle = document.querySelector('input[name="enableAvailability"]');
        if (statusToggle && !anyStatusChecked) {
          statusToggle.checked = false;
        }
      }
    }

    document.addEventListener("DOMContentLoaded", function () {
      var eventRoot = document.body || document;
      activateSpatialMaps(document.querySelector("#results-region") || document);
      syncSortControlsFromUrl();
      initializeTypeaheads(document);
      initializeRangeSliders();

      eventRoot.addEventListener('click', function(event) {
        var trigger = event.target.closest('.discovery-filter-chip-remove');
        if (!trigger) {
          return;
        }
        clearControlsForFilterRemoval(trigger);
      });

      eventRoot.addEventListener("toggle", function (event) {
        if (!(event.target instanceof HTMLDetailsElement)) {
          return;
        }
        if (!event.target.classList.contains("discovery-row-accordion") || !event.target.open) {
          return;
        }
        requestAnimationFrame(function () {
          activateSpatialMaps(event.target);
        });
      });

      eventRoot.addEventListener("htmx:afterSwap", function (event) {
        var target = event.detail && event.detail.target;
        if (target && target.id === "results-region") {
          syncSortControlsFromUrl();
          activateSpatialMaps(target);
          initializeRangeSliders();
        }
      });
    });

    function initializeTypeaheads(root) {
      (root || document).querySelectorAll('.discovery-typeahead-input').forEach(function(input) {
        if (input.dataset.typeaheadBound === 'true') {
          return;
        }
        input.dataset.typeaheadBound = 'true';

        var wrapper = input.closest('.discovery-typeahead-wrap');
        if (!wrapper) {
          return;
        }

        var menu = document.createElement('ul');
        menu.className = 'discovery-typeahead-menu';
        wrapper.appendChild(menu);

        var activeIndex = -1;
        var suggestions = [];
        var debounceTimer = null;

        var applyOnSelect = input.dataset.applyOnSelect === 'true';

        function closeMenu() {
          menu.classList.remove('is-open');
          menu.innerHTML = '';
          activeIndex = -1;
          suggestions = [];
        }

        function renderMenu() {
          menu.innerHTML = '';
          if (!suggestions.length) {
            closeMenu();
            return;
          }
          suggestions.forEach(function(value, index) {
            var item = document.createElement('li');
            item.className = 'discovery-typeahead-item' + (index === activeIndex ? ' is-active' : '');
            item.textContent = value;
            item.addEventListener('mousedown', function(event) {
              event.preventDefault();
              input.value = value;
              closeMenu();
              if (window.htmx) {
                window.htmx.trigger(input, applyOnSelect ? 'typeahead-select' : 'change');
              }
            });
            menu.appendChild(item);
          });
          menu.classList.add('is-open');
        }

        function extractSuggestions(payload, query) {
          var lowerQuery = (query || '').toLowerCase();
          var values = [];
          (payload || []).forEach(function(entry) {
            (entry.highlights || []).forEach(function(highlight) {
              (highlight.texts || []).forEach(function(text) {
                if (text.type === 'hit' && text.value) {
                  var candidate = String(text.value).trim();
                  if (candidate && candidate.toLowerCase().indexOf(lowerQuery) !== -1) {
                    values.push(candidate);
                  }
                }
              });
            });
          });
          return Array.from(new Set(values)).slice(0, 8);
        }

        async function fetchSuggestions() {
          var query = input.value.trim();
          if (query.length < 3) {
            closeMenu();
            return;
          }
          try {
            var response = await fetch(
              input.dataset.typeaheadUrl + '?term=' + encodeURIComponent(query) + '&field=' + encodeURIComponent(input.dataset.typeaheadField || 'term'),
              { credentials: 'same-origin' }
            );
            if (!response.ok) {
              closeMenu();
              return;
            }
            var payload = await response.json();
            suggestions = extractSuggestions(payload, query);
            activeIndex = -1;
            renderMenu();
          } catch (_error) {
            closeMenu();
          }
        }

        input.addEventListener('input', function() {
          clearTimeout(debounceTimer);
          debounceTimer = setTimeout(fetchSuggestions, 250);
        });

        input.addEventListener('keydown', function(event) {
          if (!menu.classList.contains('is-open') || !suggestions.length) {
            return;
          }
          if (event.key === 'ArrowDown') {
            event.preventDefault();
            activeIndex = (activeIndex + 1) % suggestions.length;
            renderMenu();
          } else if (event.key === 'ArrowUp') {
            event.preventDefault();
            activeIndex = activeIndex <= 0 ? suggestions.length - 1 : activeIndex - 1;
            renderMenu();
          } else if (event.key === 'Enter' && activeIndex >= 0) {
            event.preventDefault();
            input.value = suggestions[activeIndex];
            closeMenu();
            if (window.htmx) {
              window.htmx.trigger(input, applyOnSelect ? 'typeahead-select' : 'change');
            }
          } else if (event.key === 'Escape') {
            closeMenu();
          }
        });

        input.addEventListener('blur', function() {
          setTimeout(closeMenu, 120);
        });
      });
    }

    function initializeRangeSlider(sliderId, startName, endName, enableName) {
      var slider = document.getElementById(sliderId);
      var startInput = document.querySelector('input[name="' + startName + '"]');
      var endInput = document.querySelector('input[name="' + endName + '"]');
      var enableInput = document.querySelector('input[name="' + enableName + '"]');

      if (!slider || !startInput || !endInput || !window.jQuery || !window.jQuery.fn.slider) {
        return;
      }

      var $slider = window.jQuery(slider);
      var minYear = parseInt(slider.dataset.min, 10) || 2010;
      var maxYear = parseInt(slider.dataset.max, 10) || new Date().getFullYear();
      var startValue = parseInt(startInput.value, 10) || minYear;
      var endValue = parseInt(endInput.value, 10) || maxYear;

      function normalizeRange(start, end) {
        start = isNaN(start) ? minYear : start;
        end = isNaN(end) ? maxYear : end;
        start = Math.max(minYear, Math.min(start, maxYear));
        end = Math.max(minYear, Math.min(end, maxYear));
        if (start > end) {
          var temp = start;
          start = end;
          end = temp;
        }
        return [start, end];
      }

      function setInputs(values) {
        startInput.value = values[0];
        endInput.value = values[1];
      }

      function triggerRefresh() {
        if (enableInput) {
          enableInput.checked = true;
        }
        if (window.htmx) {
          window.htmx.trigger(startInput, 'change');
        }
      }

      var initialValues = normalizeRange(startValue, endValue);
      setInputs(initialValues);

      if ($slider.hasClass('ui-slider')) {
        $slider.slider('destroy');
      }

      $slider.slider({
        range: true,
        min: minYear,
        max: maxYear,
        step: 1,
        values: initialValues,
        slide: function(_event, ui) {
          setInputs(ui.values);
        },
        stop: function(_event, ui) {
          setInputs(ui.values);
          triggerRefresh();
        }
      });

      function updateSliderFromInputs() {
        var values = normalizeRange(parseInt(startInput.value, 10), parseInt(endInput.value, 10));
        setInputs(values);
        $slider.slider('values', values);
      }

      if (!startInput.dataset.sliderBound) {
        startInput.addEventListener('change', updateSliderFromInputs);
        startInput.dataset.sliderBound = 'true';
      }
      if (!endInput.dataset.sliderBound) {
        endInput.addEventListener('change', updateSliderFromInputs);
        endInput.dataset.sliderBound = 'true';
      }
    }

    function initializeRangeSliders() {
      initializeRangeSlider('discovery-temporal-coverage-slider', 'dataCoverageStart', 'dataCoverageEnd', 'enableDataCoverage');
      initializeRangeSlider('discovery-date-created-slider', 'dateCreatedStart', 'dateCreatedEnd', 'enableDateCreated');
      initializeRangeSlider('discovery-published-slider', 'publishedStart', 'publishedEnd', 'enablePublished');
    }
  })();
