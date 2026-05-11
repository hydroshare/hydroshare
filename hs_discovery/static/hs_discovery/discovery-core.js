(function () {
  var app = window.HSDiscovery = window.HSDiscovery || {};

  document.addEventListener('DOMContentLoaded', function () {
    var eventRoot = document.body || document;

    if (app.activateSpatialMaps) {
      app.activateSpatialMaps(document.querySelector('#results-region') || document);
    }
    if (app.syncSortControlsFromUrl) {
      app.syncSortControlsFromUrl();
    }
    if (app.initializeTypeaheads) {
      app.initializeTypeaheads(document);
    }
    if (app.initializeRangeSliders) {
      app.initializeRangeSliders();
    }

    eventRoot.addEventListener('click', function (event) {
      var trigger = event.target.closest('.discovery-filter-chip-remove');
      if (!trigger || !app.clearControlsForFilterRemoval) {
        return;
      }
      app.clearControlsForFilterRemoval(trigger);
    });

    eventRoot.addEventListener('toggle', function (event) {
      if (!(event.target instanceof HTMLDetailsElement)) {
        return;
      }
      if (!event.target.classList.contains('discovery-row-accordion') || !event.target.open) {
        return;
      }
      requestAnimationFrame(function () {
        if (app.activateSpatialMaps) {
          app.activateSpatialMaps(event.target);
        }
      });
    });

    eventRoot.addEventListener('htmx:afterSwap', function (event) {
      var target = event.detail && event.detail.target;
      if (target && target.id === 'results-region') {
        if (app.syncSortControlsFromUrl) {
          app.syncSortControlsFromUrl();
        }
        if (app.activateSpatialMaps) {
          app.activateSpatialMaps(target);
        }
        if (app.initializeRangeSliders) {
          app.initializeRangeSliders();
        }
      }
    });
  });
})();
