/**
 * Created by Mauriel on 3/9/2017.
 */

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
    targets: [ACTIONS_COL], // Row selector and controls
    visible: false,
  },
  {
    targets: [RESOURCE_TYPE_COL], // Resource type
    width: "100px",
  },
  {
    targets: [ACTIONS_COL], // Actions
    orderable: false,
    searchable: false,
    width: "70px",
  },
  {
    targets: [LAST_MODIFIED_COL], // Last modified
    iDataSort: LAST_MODIF_SORT_COL,
  },
  {
    targets: [DATE_CREATED_COL], // Created
    iDataSort: DATE_CREATED_SORT_COL,
  },
  {
    targets: [SUBJECT_COL], // Subject
    visible: false,
    searchable: true,
  },
  {
    targets: [AUTHORS_COL], // Authors
    visible: false,
    searchable: true,
  },
  {
    targets: [PERM_LEVEL_COL], // Permission level
    visible: false,
    searchable: true,
  },
  {
    targets: [LABELS_COL], // Labels
    visible: false,
    searchable: true,
  },
  {
    targets: [FAVORITE_COL], // Favorite
    visible: false,
    searchable: true,
  },
  {
    targets: [LAST_MODIF_SORT_COL], // Last modified (for sorting)
    visible: false,
    searchable: true,
  },
  {
    targets: [DATE_CREATED_SORT_COL], // Last modified (for sorting)
    visible: false,
    searchable: true,
  },
  {
    targets: [SHARING_STATUS_COL], // Sharing status
    visible: false,
    searchable: false,
  },
  {
    targets: [ACCESS_GRANTOR_COL], // Access Grantor
    visible: false,
    searchable: true,
  },
];

// File name preview for picture field, change method
$(document).on("change", ".btn-file :file", function () {
  var input = $(this);
  var numFiles = input.get(0).files ? input.get(0).files.length : 1;
  var label = input.val().replace(/\\/g, "/").replace(/.*\//, "");
  input.trigger("fileselect", [numFiles, label]);
});

$(document).ready(function () {
  $("title").text($(".group-title").text() + " | HydroShare"); // Fix page title

  $("#id_user-autocomplete").addClass("form-control");

  $("#list-roles a").click(onRoleSelect);

  $("#id_user-autocomplete").attr("placeholder", "Search by name or username");

  // Filter
  $("#members").find(".table-members-list").hide();
  $("#members").find(".table-members-list.active").show();

  $("#members-filter tr").click(function () {
    $("#members").find(".table-members-list tr").hide();
    $("table[data-filter-by='pending'] tr").hide();
    $("table[data-filter-by='pending']").hide();

    var dataFilter = $(this).attr("data-filter-by");
    if (dataFilter == "edit-user") {
      $("#members")
        .find(".table-members-list tr[data-filter-by='" + dataFilter + "']")
        .fadeIn();
      $("#members")
        .find(".table-members-list tr[data-filter-by='" + "creator" + "']")
        .fadeIn();
    } else if (dataFilter == "all") {
      $("#members").find(".table-members-list tr").addClass("active").fadeIn();
    } else if (dataFilter == "pending") {
      $("#members").find(".table-members-list tr").addClass("active").hide();
      $("table[data-filter-by='pending'] tr").fadeIn();
      $("table[data-filter-by='pending']").fadeIn();
    }

    $(this).parent().find("tr").removeClass("active");
    $(this).addClass("active");
  });

  $(".btn-act-on-request").click(act_on_request_ajax_submit);
  $(".btn-share-group").click(share_group_ajax_submit);
  $(".btn-unshare-group").click(unshare_group_ajax_submit);
  $("#btn-group-invite").click(group_invite_ajax_submit);
  $(".btn-ask-join").click(request_join_group_ajax_submit);

  // Initialize filters counters
  updateMembersLabelCount();

  // Initialize Shared By filter
  var grantors = $("#grantors-list span");
  if (grantors.length) $("#filter-shared-by .no-items-found").remove();
  for (var i = 0; i < grantors.length; i++) {
    var id = $(grantors[i]).attr("data-grantor-id");
    if (
      $("#filter-shared-by .grantor[data-grantor-id='" + id + "']").length == 0
    ) {
      var count = $("#grantors-list span[data-grantor-id='" + id + "']").length;
      var name = $(grantors[i]).attr("data-grantor-name").trim();

      $("#filter-shared-by .inputs-group").append(
        '<li class="list-group-item">' +
          '<span data-facet="owned" class="badge">' +
          count +
          "</span>" +
          '<label class="checkbox noselect">' +
          '<input type="checkbox" class="grantor" data-grantor-id="' +
          id +
          '">' +
          name +
          "</label>" +
          "</li>"
      );
    }
  }

  $("#grantors-list").remove(); // Remove temporary list

  // File name preview for picture field, file select method
  $(".btn-file :file").on("fileselect", function (event, numFiles, label) {
    var input = $(this).parents(".input-group").find(":text");
    input.val(label);
  });

  // Hide explanation checkbox if auto-approval is enabled
  if ($("#auto-approve").is(":checked")) {
    $("#requires_explanation").prop("checked", false);
    $("#requires_explanation").parent().hide();
  }
  $("#auto-approve").change(function () {
    if (this.checked) {
      $("#requires_explanation").prop("checked", false);
      $("#requires_explanation").parent().hide();
    } else {
      $("#requires_explanation").parent().show();
    }
  });
});
