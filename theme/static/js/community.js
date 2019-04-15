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

function group_invite_ajax_submit() {
    if (!$("#id_user-deck > .hilight").length) {
        return false; // If no user selected, ignore the request
    }
    var share_with = $("#id_user-deck > .hilight")[0].getAttribute("data-value");
    var form = $("#invite-to-group");
    var datastring = form.serialize();
    var url = form.attr('action') + share_with + "/";

    $.ajax({
        type: "POST",
        url: url,
        dataType: 'html',
        data: datastring,
        success: function (result) {
            $(".hilight > span").click(); // Clears the search field
            $("#invite-dialog .modal-body").prepend('<div class="alert alert-success" role="alert"><span class="glyphicon glyphicon-ok glyphicon"></span> An invitation to join has been sent.</strong></div>');

            setTimeout(function () {
               $("#invite-dialog .modal-body .alert").fadeOut();
            }, 3000);
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            $("#invite-dialog .modal-body").prepend('<div class="alert alert-error" role="alert"><span class="glyphicon glyphicon-ok glyphicon"></span> This invitation could not be sent.</strong></div>');

            setTimeout(function () {
                $("#invite-dialog .modal-body .alert").fadeOut();
            }, 3000);
        }
    });
    //don't submit the form
    return false;
}

function onRoleSelect(event) {
    var el = $(event.target);
    $("#selected_role").text(el.text());
    $("#selected_role")[0].setAttribute("data-role", el[0].getAttribute("data-role"));
}

function act_on_request_ajax_submit() {
    var target = $(this);
    var form = $(this).closest("form");
    var datastring = form.serialize();
    var url = form.attr('action');
    $.ajax({
        type: "POST",
        url: url,
        dataType: 'html',
        data: datastring,
        success: function (result) {
            if (target.attr("data-user-action") == "Accept") {
                // Get a copy of the member row template
                var rowTemplate = $("#templateRow").clone();

                var name = target.attr("data-name");
                var title = target.attr("data-title");
                var picture = target.parent().parent().parent().find("[data-id='picture']");

                rowTemplate.find("[data-id='name']").text(name);
                rowTemplate.find("[data-id='name']").attr("href", "/user/" + target.attr("data-member-id") + "/");
                rowTemplate.find("[data-id='title']").text(title);
                var forms = rowTemplate.find("form");
                for (var i = 0; i < forms.length; i++) {
                    var newAction = $(forms[i]).attr("action").replace("member_id", target.attr("data-member-id"));
                    $(forms[i]).attr("action", newAction);
                }
                rowTemplate.prepend(picture);

                $("#all-members-table tbody").append($("<tr data-filter-by='view-user' style='display: none;'>" + rowTemplate.html() + "</tr>"));
                $(".btn-share-group").click(share_group_ajax_submit);
                $(".btn-unshare-group").click(unshare_group_ajax_submit);
            }

            target.parent().parent().parent().remove();
            updateMembersLabelCount();
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            console.log("error");
        }
    });
    //don't submit the form
    return false;
}

function share_group_ajax_submit() {
    var target = $(this);
    var form = target.closest("form");
    var role = target.attr("data-role");
    var datastring = form.serialize();
    var url = form.attr('action');
    $.ajax({
        type: "POST",
        url: url,
        dataType: 'html',
        data: datastring,
        success: function (result) {
            var dropdownButton = target.parent().parent().parent().parent().find(".dropdown-toggle");
            dropdownButton.text(role);
            dropdownButton.append('&nbsp;<span class="caret"></span>');

            var row = target.parent().parent().parent().parent().parent().parent();
            if (role == "Owner") {
                row.attr("data-filter-by", "edit-user");
            }
            else if (role == "Member") {
                row.attr("data-filter-by", "view-user");
            }

            dropdownButton.dropdown("toggle");
            updateMembersLabelCount();
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            console.log("error");
        }
    });
    //don't submit the form
    return false;
}

function unshare_group_ajax_submit() {
    var target = $(this);
    var form = target.closest("form");
    var datastring = form.serialize();
    var url = form.attr('action');
    $.ajax({
        type: "POST",
        url: url,
        dataType: 'html',
        data: datastring,
        success: function (result) {
            var row = target.parent().parent().parent().parent().parent().parent();
            row.remove();
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            console.log("error");
        }
    });
    //don't submit the form
    return false;
}

function updateMembersLabelCount() {
    var viewCount = $("#all-members-table tr[data-filter-by='view-user']").length - 1;  // Subtract hidden template row
    var editCount = $("#all-members-table tr[data-filter-by='edit-user']").length;
    var pendingCount = $("table[data-filter-by='pending'] tr:not('.no-pending-requests')").length;

    $("#members-filter .badge[data-filter-by='All']").text(viewCount + editCount);
    $("#members-filter .badge[data-filter-by='Owners']").text(editCount);
    $("#members-filter .badge[data-filter-by='Pending']").text(pendingCount);

    // Disable options to leave or remove for last owner item.
    if (editCount == 1) {
        $("#all-members-table tr[data-filter-by='edit-user'] .dropdown-toggle").attr("disabled", true);
    }
    else {
        $("#all-members-table tr[data-filter-by='edit-user'] .dropdown-toggle").attr("disabled", false);
    }
}

// Preview profile picture
function readURL(input) {
    if (input.files && input.files[0]) {
        var reader = new FileReader();
        reader.onload = function (e) {

        };

        reader.readAsDataURL(input.files[0]);
    }
}

// File name preview for picture field, change method
$(document).on('change', '.btn-file :file', function () {
    var input = $(this);
    var numFiles = input.get(0).files ? input.get(0).files.length : 1;
    var label = input.val().replace(/\\/g, '/').replace(/.*\//, '');
    input.trigger('fileselect', [numFiles, label]);
});

$(document).ready(function () {
    $("title").text($(".group-title").text() + " | HydroShare"); // Fix page title

     $("#id_user-autocomplete").addClass("form-control");

    $("#list-roles a").click(onRoleSelect);

    $("#id_user-autocomplete").attr("placeholder", "Search by name or username");

    // Filter
    $("#members").find(".table-members-list").hide();
    $("#members").find(".table-members-list.active").show();

    $("#members-filter tr").click(function() {
        $("#members").find(".table-members-list tr").hide();
        $("table[data-filter-by='pending'] tr").hide();
        $("table[data-filter-by='pending']").hide();

        var dataFilter = $(this).attr("data-filter-by");
        if (dataFilter == "edit-user") {
            $("#members").find(".table-members-list tr[data-filter-by='" + dataFilter + "']").fadeIn();
            $("#members").find(".table-members-list tr[data-filter-by='" + "creator" + "']").fadeIn();
        }
        else if (dataFilter == "all") {
            $("#members").find(".table-members-list tr").addClass("active").fadeIn();
        }
        else if(dataFilter == "pending") {
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

    // Initialize filters counters
    updateMembersLabelCount();

    // Initialize Shared By filter
    var grantors = $("#grantors-list span");
    if (grantors.length)
        $("#filter-shared-by .no-items-found").remove();
    for (var i = 0; i < grantors.length; i++) {
        var id = $(grantors[i]).attr("data-grantor-id");
        if ($("#filter-shared-by .grantor[data-grantor-id='" + id + "']").length == 0) {
            var count = $("#grantors-list span[data-grantor-id='" + id + "']").length;
            var name = $(grantors[i]).attr("data-grantor-name").trim();

            $("#filter-shared-by .inputs-group").append('<li class="list-group-item">' +
                                                            '<span data-facet="owned" class="badge">' + count + '</span>' +
                                                            '<label class="checkbox noselect">' +
                                                            '<input type="checkbox" class="grantor" data-grantor-id="' + id + '">' + name + '</label>' +
                                                        '</li>')
        }
    }

    $("#grantors-list").remove();   // Remove temporary list

    // File name preview for picture field, file select method
    $('.btn-file :file').on('fileselect', function (event, numFiles, label) {
        var input = $(this).parents('.input-group').find(':text');
        input.val(label);
    });

});