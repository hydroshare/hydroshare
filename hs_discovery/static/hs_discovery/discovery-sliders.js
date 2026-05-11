(function () {
  var app = window.HSDiscovery = window.HSDiscovery || {};

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
      slide: function (_event, ui) {
        setInputs(ui.values);
      },
      stop: function (_event, ui) {
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

  app.initializeRangeSliders = function () {
    initializeRangeSlider('discovery-temporal-coverage-slider', 'dataCoverageStart', 'dataCoverageEnd', 'enableDataCoverage');
    initializeRangeSlider('discovery-date-created-slider', 'dateCreatedStart', 'dateCreatedEnd', 'enableDateCreated');
    initializeRangeSlider('discovery-published-slider', 'publishedStart', 'publishedEnd', 'enablePublished');
  };
})();
