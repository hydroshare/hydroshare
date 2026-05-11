(function () {
  var app = window.HSDiscovery = window.HSDiscovery || {};

  app.DEFAULT_SORT_ORDER = {
    relevance: "",
    "most-viewed": "desc",
    title: "asc",
    "first-author": "asc",
    "date-created": "desc",
    "last-modified": "desc"
  };

  app.resolveSortState = function (search) {
    var params = new URLSearchParams(search || "");
    var sort = params.get("sort") || "relevance";
    var defaultOrder = Object.prototype.hasOwnProperty.call(app.DEFAULT_SORT_ORDER, sort)
      ? app.DEFAULT_SORT_ORDER[sort]
      : "";
    var order = params.get("order");
    if (order !== "asc" && order !== "desc") {
      order = defaultOrder;
    }
    return {
      sort: sort,
      order: order || ""
    };
  };

  app.syncSortControlsFromUrl = function () {
    var sortControl = document.getElementById("id_sort");
    if (!sortControl) {
      return;
    }
    var state = app.resolveSortState(window.location.search);
    sortControl.value = state.sort;

    var orderControl = document.querySelector('input[name="order"]');
    if (orderControl) {
      orderControl.value = state.order;
    }

    var sortButtonLabel = document.getElementById("discovery-sort-button-label");
    var sortMenuItems = document.querySelectorAll(".discovery-sort-menu li[data-sort-value]");
    sortMenuItems.forEach(function (item) {
      if (!(item instanceof HTMLElement)) {
        return;
      }
      var isActive = item.dataset.sortValue === state.sort;
      item.classList.toggle("active", isActive);
      if (isActive && sortButtonLabel) {
        sortButtonLabel.textContent = item.dataset.sortLabel || item.textContent.trim();
      }
    });
  };
})();
