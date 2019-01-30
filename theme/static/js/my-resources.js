/**
* Created by Mauriel on 3/9/2017.
*/

var ACTIONS_COL =           0;
var RESOURCE_TYPE_COL =     1;
var TITLE_COL =             2;
var OWNER_COL =             3;
var DATE_CREATED_COL =      4;
var LAST_MODIFIED_COL =     5;
var SUBJECT_COL =           6;
var AUTHORS_COL =           7;
var PERM_LEVEL_COL =        8;
var LABELS_COL =            9;
var FAVORITE_COL =          10;
var LAST_MODIF_SORT_COL =   11;
var SHARING_STATUS_COL =    12;
var DATE_CREATED_SORT_COL = 13;
var ACCESS_GRANTOR_COL =    14;

var colDefs = [
    {
        "targets": [RESOURCE_TYPE_COL],     // Resource type
        "width": "135px"
    },
    {
        "targets": [ACTIONS_COL],           // Actions
        "orderable": false,
        "searchable": false,
    },
    {
        "targets": [LAST_MODIFIED_COL],     // Last modified
        "iDataSort": LAST_MODIF_SORT_COL
    },
    {
        "targets": [DATE_CREATED_COL],      // Created
        "iDataSort": DATE_CREATED_SORT_COL
    },
    {
        "targets": [SUBJECT_COL],           // Subject
        "visible": false,
        "searchable": true
    },
    {
        "targets": [AUTHORS_COL],           // Authors
        "visible": false,
        "searchable": true
    },
    {
        "targets": [PERM_LEVEL_COL],        // Permission level
        "visible": false,
        "searchable": true
    },
    {
        "targets": [LABELS_COL],            // Labels
        "visible": false,
        "searchable": true
    },
    {
        "targets": [FAVORITE_COL],          // Favorite
        "visible": false,
        "searchable": true
    },
    {
        "targets": [LAST_MODIF_SORT_COL],   // Last modified (for sorting)
        "visible": false,
        "searchable": true
    },
    {
        "targets": [DATE_CREATED_SORT_COL], // Date Created (for sorting)
        "visible": false,
        "searchable": true
    },
    {
        "targets": [SHARING_STATUS_COL],    // Sharing status
        "visible": false,
        "searchable": false
    }
];
// TODO: fix the following references
// $(document).ready(function () {
//     start_resource_table();
//     $.fn.dataTable.ext.search.push(hs_resource_table_custom_search);
// });