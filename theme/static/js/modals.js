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

$(document).ready(function() {
    var resID = $("#resID").val();

    $("#btn-replicate").click(function() {
        rep_res_to_irods_user_zone_ajax_submit(resID);
    });

    $("#btn-add-author, #btn-add-hydroshare-user").click(function() {
        get_user_info_ajax_submit('/hsapi/_internal/get-user-or-group-data/', this)
    });

    $("#btn-confirm-extended-metadata").click(function () {
        addEditExtraMeta2Table();
    });

    $("#btn-confirm-add-access").click(function () {
        var formID = $(this).closest("form").attr("id");
        share_resource_ajax_submit(formID);
    });

    $(".btn-unshare-resource").click(function() {
        var formID = $(this).closest("form").attr("id");
        unshare_resource_ajax_submit(formID);
    });

    $(".btn-change-share-permission").click(function() {
        var arg = $(this).attr("data-arg");
        change_share_permission_ajax_submit(arg);
    });
});