/**
* Created by Mauriel on 3/9/2017.
*/

function rep_res_to_irods_user_zone_ajax_submit(res_id) {
    setPointerEvents(false);
    $.ajax({
        url: "/hsapi/_internal/" + res_id + "/rep-res-bag-to-irods-user-zone/",
        type: "POST",
        data: {},
        success: function(json) {
            if (json.success) {
                $("#rep-alert-success").show();
                $("#rep-status-success").text(json.success);
            }
            if (json.error) {
                $("#rep-alert-error").show();
                $("#rep-status-error").text(json.error);
            }
            $('#rep-resource-to-irods-dialog').modal('hide');
        },
        error: function(xhr, errmsg, err) {
            status_error = xhr.status + ": " + xhr.responseText + ". Error message: " + errmsg;
            console.log(status_error);
            $("#rep-status-error").text(status_error);
            $('#rep-resource-to-irods-dialog').modal('hide');
        }
    });
}

// These event bindings will work even for elements created dynamically
$(document).on('click', '.btn-unshare-resource', function () {
    var formID = $(this).closest("form").attr("id");
    unshare_resource_ajax_submit(formID);
});

$(document).on('click', '.btn-undo-share', function () {
    var formID = $(this).closest("form").attr("id");
    undo_share_ajax_submit(formID);
});

$(document).on("click", ".btn-change-share-permission", function () {
    var arg = $(this).attr("data-arg");
    change_share_permission_ajax_submit(arg);
});

$(document).ready(function() {
    var resID = $("#resID").val();

    $("#btn-replicate").click(function() {
        rep_res_to_irods_user_zone_ajax_submit(resID);
    });

    $("#download-bag-btn").click(function() {
        $("#license-agree-dialog-bag").modal('hide');
    });

    $("#btn-add-author, #btn-add-hydroshare-user").click(function () {
        $(this).text("Saving Changes...");
        $(this).addClass("disabled");
        var response = get_user_info_ajax_submit('/hsapi/_internal/get-user-or-group-data/', this);
        if (!response) {
            $(this).text("Save Changes");
            $(this).removeClass("disabled");
        }
    });

    $("#btn-add-relation, #btn-edit-relation, #btn-add-source, #btn-edit-source, #btn-edit-contributor, .btn-save-funding-agency").click(function () {
        let form = $(this).closest("form");
        if (form[0].checkValidity()) {
            $(this).text("Saving Changes...");
            $(this).addClass("disabled");
        }
    });

    $("#btn-confirm-extended-metadata").click(addEditExtraMeta2Table);

    $("#btn-confirm-add-access").click(function () {
        var formID = $(this).closest("form").attr("id");
        share_resource_ajax_submit(formID);
    });

    $("input#id_user-autocomplete").addClass("form-control");

    $('#usage-info').on('hidden.bs.collapse', function () {
        $("a[data-target='#usage-info']").text("Show More");
    }).on('shown.bs.collapse', function () {
        $("a[data-target='#usage-info']").text("Show Less");
    });

    $(".authors-wrapper").on("click", ".author-modal-trigger", function () {
        $("#edit-creator-dialog").modal('show');
        let data = $.extend(true, {}, $(this).data());    // Shallow copy
        let dialog = $("#edit-creator-dialog");
        let shortID = $("#short-id").val();
        let form = dialog.find("form");

        form.attr("action", "/hsapi/_internal/" + shortID + "/creator/" + data.id + "/update-metadata/");

        // Set delete author link
        $("#confirm-delete-author").find(".btn-danger").attr("href", "/hsapi/_internal/" + shortID + "/creator/" + data.id + "/delete-metadata/");

        data.order -= 1;    // The value we use in the back end is 0 based and in the UI it is not

        // NAME
        let name = dialog.find(".control-group--name");
        name.find("input").attr("name", "creator-" + data.order + "-name");
        name.find("input").val(data.name != null ? data.name : "");
        if (!data.name) {
            name.hide();
            name.find("input").removeAttr("required");
        }
        else {
            name.show();
            name.find("input").attr("required", "required");
        }

        // USER IDENTIFIER
        let identifier = dialog.find(".control-group--description");
        identifier.find("input").val(data.description != null ? data.description : "");
        if (!data.description) {
            identifier.hide();
            identifier.find("input").removeAttr("name");
        }
        else {
            identifier.show();
            identifier.find("input").attr("name", "creator-" + data.order + "-description");
        }

        // ORGANIZATION
        let organization = dialog.find(".control-group--organization");
        organization.find("input").val(data.organization);
        organization.find("input").attr("name", "creator-" + data.order + "-organization");
        // If you don't have an author name, an organization is required
        if (!data.name) {
            organization.addClass("requiredField");
            organization.find("input").attr("required", "required");
            organization.find(".asteriskField").show();
        }
        else {
            organization.removeClass("requiredField");
            organization.find("input").removeAttr("required");
            organization.find(".asteriskField").hide();
        }

        // EMAIL
        let email = dialog.find(".control-group--email");
        email.find("input").attr("name", "creator-" + data.order + "-email");
        email.find("input").val(data.email != null ? data.email : "");

        // ADDRESS
        let address = dialog.find(".control-group--address");
        address.find("input").attr("name", "creator-" + data.order + "-address");
        address.find("input").val(data.address != null ? data.address : "");

        // PHONE
        let phone = dialog.find(".control-group--phone");
        phone.find("input").attr("name", "creator-" + data.order + "-phone");
        phone.find("input").val(data.phone != null ? data.phone : "");

        // HOMEPAGE
        let homepage = dialog.find(".control-group--homepage");
        homepage.find("input").attr("name", "creator-" + data.order + "-homepage");
        homepage.find("input").val(data.homepage != null ? data.homepage : "");
    });
});