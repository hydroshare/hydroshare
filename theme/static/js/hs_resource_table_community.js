/**
 * Created by Mauriel on 5/19/2016.
 */
var resourceTable;

var ACTIONS_COL = 0;
var RESOURCE_TYPE_COL = 1;
var TITLE_COL = 2;
var OWNER_COL = 3;
var DATE_CREATED_COL = 4;
var LAST_MODIFIED_COL = 5;
var SUBJECT_COL = 6;
var AUTHORS_COL = 7;
var PERM_LEVEL_COL = 8;
var LABELS_COL = 9;
var FAVORITE_COL = 10;
var LAST_MODIF_SORT_COL = 11;
var SHARING_STATUS_COL = 12;
var DATE_CREATED_SORT_COL = 13;
var ACCESS_GRANTOR_COL = 14;

var colDefs = [
    {
        "targets": [ACTIONS_COL],     // Row selector and controls
        "visible": false,
    },
    {
        "targets": [RESOURCE_TYPE_COL],     // Resource type
        "width": "100px"
    },
    {
        "targets": [ACTIONS_COL],     // Actions
        "orderable": false,
        "searchable": false,
        "width": "70px"
    },
    {
        "targets": [LAST_MODIFIED_COL],     // Last modified
        "iDataSort": LAST_MODIF_SORT_COL
    },
    {
        "targets": [DATE_CREATED_COL],     // Created
        "iDataSort": DATE_CREATED_SORT_COL
    },
    {
        "targets": [SUBJECT_COL],     // Subject
        "visible": false,
        "searchable": true
    },
    {
        "targets": [AUTHORS_COL],     // Authors
        "visible": false,
        "searchable": true
    },
    {
        "targets": [PERM_LEVEL_COL],     // Permission level
        "visible": false,
        "searchable": true
    },
    {
        "targets": [LABELS_COL],     // Labels
        "visible": false,
        "searchable": true
    },
    {
        "targets": [FAVORITE_COL],     // Favorite
        "visible": false,
        "searchable": true
    },
    {
        "targets": [LAST_MODIF_SORT_COL],     // Last modified (for sorting)
        "visible": false,
        "searchable": true
    },
    {
        "targets": [DATE_CREATED_SORT_COL],     // Last modified (for sorting)
        "visible": false,
        "searchable": true
    },
    {
        "targets": [SHARING_STATUS_COL],     // Sharing status
        "visible": false,
        "searchable": false
    },
    {
        "targets": [ACCESS_GRANTOR_COL],     // Access Grantor
        "visible": false,
        "searchable": true
    }
];

$(document).ready(function () {
    /*==================================================
        Table columns
        0 - actions
        1 - Resource Type
        2 - Title
        3 - Owner
        4 - Date Created
        5 - Last Modified
        6 - Subject
        7 - Authors
        8 - Permission Level
        9 - Labels
        10 - Favorite
        11 - Last modified (sortable format)
        12 - Sharing Status
        13 - Date created (sortable format)
        14 - Access Grantor
    ==================================================*/

    resourceTable = $("#item-selectors").DataTable({
        "order": [[DATE_CREATED_COL, "desc"]],
        "paging": false,
        "info": false,
        "columnDefs": colDefs
    });

    $("#item-selectors").css("width", "100%");

    // Fix for horizontal scroll bar appearing unnecessarily on firefox.
    if ($.browser.mozilla) {
        $("#item-selectors").width($("#item-selectors").width() - 2);
    }

    // Trigger label creation when pressing Enter
    $("#txtLabelName").keyup(function (event) {
        var label = $("#txtLabelName").val().trim();
        if (event.keyCode == 13 && label != "") {
            $("#btn-create-label").click();
        }
    });

    // Disable default form submission when pressing enter for textarea inputs
    $(window).keydown(function (event) {
        if (event.keyCode == 13 && event.target.tagName != "TEXTAREA") {
            event.preventDefault();
        }
    });

    // Autofocus input when modal appears
    $("#modalCreateLabel").on('shown.bs.modal', function () {
        $("#txtLabelName").focus();
    });

    $("#item-selectors").show();


    $("#resource-search-input").keyup(function () {
        var searchString = removeQueryOccurrences($(this).val());
        applyQueryStrings();
        resourceTable.search(searchString).draw();
    });

    $("#btn-clear-author-input").click(function () {
        $("#input-author").val("");
        typeQueryStrings();
        $("#resource-search-input").keyup();
    });

    $("#btn-clear-subject-input").click(function () {
        $("#input-subject").val("");
        typeQueryStrings();
        $("#resource-search-input").keyup();
    });

    $("#btn-clear-search-input").click(function () {
        var searchInput = $("#resource-search-input");
        searchInput.val("");
        searchInput.keyup();
    });

    // Prevents dropdown form getting dismissed when clicking on items
    $('.dropdown-menu label, .list-labels label').click(function (e) {
        e.stopPropagation();
    });

});

//strips query inputs from a search string
function removeQueryOccurrences(inputString) {
    // Matches occurrences of query strings. i.e.: "[author:mauriel ramirez]", "[]", etc
    var regExp = /\[([^\]|^\[]?)+\]/g;
    var occurrences = inputString.match(regExp);

    if (occurrences) {
        // Remove query occurrences from input string
        for (var i = 0; i < occurrences.length; i++) {
            inputString = inputString.replace(occurrences[i], "");
        }
    }

    return inputString;
}

function applyQueryStrings() {
    return true
}

// Looks at the values in the dropdown options and appends the corresponding query string to the search box.
function typeQueryStrings() {
    var searchInput = $("#resource-search-input");

    var type = $("#input-resource-type").val();
    var author = $("#input-author").val();
    var subject = $("#input-subject").val();

    var searchQuery = "";
    if (type) {
        searchQuery = searchQuery + " [type:" + type + "]";
    }

    if (author) {
        searchQuery = searchQuery + " [author:" + author + "]";
    }

    if (subject) {
        searchQuery = searchQuery + " [subject:" + subject + "]";
    }

    searchQuery = searchQuery + removeQueryOccurrences(searchInput.val());
    searchQuery = searchQuery.trim();
    searchInput.val(searchQuery);
}

/*==================================================
    Table columns
    0 - actions
    1 - Resource Type
    2 - Title
    3 - Owner
    4 - Date Created
    5 - Last Modified
    6 - Subject
    7 - Authors
    8 - Permission Level
    9 - Labels
    10 - Favorite
    11 - Last modified (sortable format)
    12 - Sharing Status
    13 - Date created (sortable format)
    14 - Access Grantor
==================================================*/

/* Custom filtering function which will search data for the values in the custom filter dropdown or query strings */
$.fn.dataTable.ext.search.push(
    function (settings, data, dataIndex) {
        var inputString = $("#resource-search-input").val().toLowerCase();
        // Matches occurrences of query strings. i.e.: author:mauriel
        var regExp = /\[(type|author|subject):[^\]|^\[]+]/g;
        var occurrences = inputString.match(regExp);

        var inputType = "";
        var inputSubject = "";
        var inputAuthor = "";

        // Split the occurrences at ':' and move to an array.
        var collection = [];
        if (occurrences) {
            for (var item in occurrences) {
                var content = occurrences[item].replace("[", "").replace("]", "").split(":");
                collection.push(content);
            }
        }

        // Extract the pieces of information
        for (var item in collection) {
            if (collection[item][0].toUpperCase() == "TYPE") {
                inputType = collection[item][1];
            } else if (collection[item][0].toUpperCase() == "AUTHOR") {
                inputAuthor = collection[item][1];
            } else if (collection[item][0].toUpperCase() == "SUBJECT") {
                inputSubject = collection[item][1];
            }
        }

        // Filter the table for each value
        if (inputType && data[RESOURCE_TYPE_COL].toUpperCase().indexOf(inputType.toUpperCase()) < 0) {
            return false;
        }

        if (inputSubject && data[SUBJECT_COL].toUpperCase().indexOf(inputSubject.toUpperCase()) < 0) {
            return false;
        }

        if (inputAuthor && data[AUTHORS_COL].toUpperCase().indexOf(inputAuthor.toUpperCase()) < 0) {
            return false;
        }

        let inFilters = false;

        if ($("#filter").find("input[type='checkbox']:checked").length) {
            //---------------- Facet filters --------------------
            // Owned by me
            if ($('#filter input[type="checkbox"][value="Owned"]').prop("checked") == true) {
                if (data[PERM_LEVEL_COL] == "Owned") {
                    inFilters = true;
                }
            }

            // Shared with me
            if ($('#filter input[type="checkbox"][value="Shared"]').prop("checked") == true) {
                if (data[PERM_LEVEL_COL] != "Owned" && data[PERM_LEVEL_COL] != "Discovered") {
                    inFilters = true;
                }
            }

            // Added by me
            if ($('#filter input[type="checkbox"][value="Discovered"]').prop("checked") == true) {
                if (data[PERM_LEVEL_COL] == "Discovered") {
                    inFilters = true;
                }
            }

            // Favorite
            if ($('#filter input[type="checkbox"][value="Favorites"]').prop("checked") == true) {
                if (data[FAVORITE_COL] == "Favorite") {
                    inFilters = true;
                }
            }

            // Recent
            if ($('#filter input[type="checkbox"][value="Recent"]').prop("checked") == true) {
                var cutoff = new Date();
                cutoff.setDate(cutoff.getDate() - 5);
                cutoff = Math.floor(cutoff.getTime() / 1000); // Seconds since the unix epoch
                // Subtract cutoff.getTimezoneOffset() * 60 to convert to local timezone
                if (data[LAST_MODIF_SORT_COL] >= cutoff) {
                    inFilters = true;
                }
            }
        } else {
            inFilters = true;    // Ignore if nothing selected
        }

        // Shared by - Used in group resource listing
        var grantors = $('#filter-shared-by .grantor:checked');
        let inGrantors = false;
        if (grantors.length) {
            for (var i = 0; i < grantors.length; i++) {
                var user = parseInt($(grantors[i]).attr("data-grantor-id"));
                if (parseInt(data[ACCESS_GRANTOR_COL]) == user) {
                    inGrantors = true;
                    break;
                }
            }
        } else {
            inGrantors = true;  // Ignore if nothing selected
        }

        // Labels - Check if the label exists in the table
        let inLabels = false;
        var labelCheckboxes = $("#user-labels-left input[type='checkbox']:checked");
        if (labelCheckboxes.length) {
            for (var i = 0; i < labelCheckboxes.length; i++) {
                var label = $(labelCheckboxes[i]).attr("data-label");

                var dataColLabels = data[LABELS_COL].replace(/\s+/g, ' ').split(",");
                for (var h = 0; h < dataColLabels.length; h++) {
                    dataColLabels[h] = dataColLabels[h].trim();
                }

                if (dataColLabels.indexOf(label) >= 0) {
                    inLabels = true;
                }
            }
        } else {
            inLabels = true;    // Ignore if nothing selected
        }

        return inLabels && inFilters && inGrantors;
    }
);
