(function () {
  var app = window.HSDiscovery = window.HSDiscovery || {};

  app.clearControlsForFilterRemoval = function (trigger) {
    var keys = (trigger.dataset.filterKeys || '').split(',').map(function (value) {
      return value.trim();
    }).filter(Boolean);
    var singleKey = trigger.dataset.filterKey;
    if (singleKey && keys.indexOf(singleKey) === -1) {
      keys.push(singleKey);
    }
    var removeValue = trigger.dataset.filterValue || '';

    keys.forEach(function (key) {
      var controls = document.querySelectorAll('[name="' + key + '"]');
      controls.forEach(function (control) {
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
  };
})();
