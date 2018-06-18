/**
 * Created by Mauriel on 2/9/2016.
 */

function label_ajax_submit() {
    var el = $(this);
    var dataFormID = el.attr("data-form-id");
    var formID = $("form[data-id='" + dataFormID + "']");
    var form = $(formID);
    var datastring = form.serialize();
    var url = form.attr('action');

    $.ajax({
        type: "POST",
        url: url,
        dataType: 'html',
        data: datastring,
        success: function (result) {
            var json_response = JSON.parse(result);
            if (json_response.status === "success") {
                var action = form.find("input[name='action']");

                if (json_response.action === "CREATE")
                {
                    action.val("DELETE");
                    if (dataFormID == "form-add-to-my-resources")
                    {
                        $("#btnMyResources").removeClass("btn-resource-add");
                        $("#btnMyResources").addClass("btn-resource-remove");
                        $("#btnMyResources").attr("data-original-title", "Remove from my resources");
                    }
                    else if (dataFormID == "form-add-open-with-app")
                    {
                        $("#btnOpenWithApp").removeClass("btn-resource-add");
                        $("#btnOpenWithApp").addClass("btn-resource-remove");
                        $("#btnOpenWithApp").attr("data-original-title", "Remove WebApp from OpenWith list");
                    }
                }
                else
                {
                    action.val("CREATE");
                    if (dataFormID == "form-add-to-my-resources") {
                        $("#btnMyResources").addClass("btn-resource-add");
                        $("#btnMyResources").removeClass("btn-resource-remove");
                        $("#btnMyResources").attr("data-original-title", "Add to my resources");
                    }
                    else if (dataFormID == "form-add-open-with-app")
                    {
                         $("#btnOpenWithApp").addClass("btn-resource-add");
                         $("#btnOpenWithApp").removeClass("btn-resource-remove");
                         $("#btnOpenWithApp").attr("data-original-title", "Add WebApp to OpenWith list");
                    }
                }
                $("#btnMyResources").tooltip('show')
            }
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            console.log(errorThrown);
        }
    });
    //don't submit the form
    return false;
}

function shareable_ajax_submit(event) {
    var form = $(this).closest("form");
    var datastring = form.serialize();
    var url = form.attr('action');
    var element = $(this);
    var action = $(this).closest("form").find("input[name='t']").val();
    element.attr("disabled", true);

    $.ajax({
        type: "POST",
        url: url,
        dataType: 'html',
        data: datastring,
        success: function () {
            element.attr("disabled", false);
            if (action == "make_not_shareable") {
                element.closest("form").find("input[name='t']").val("make_shareable");
            }
            else {
                element.closest("form").find("input[name='t']").val("make_not_shareable");
            }
        },
        error: function () {
            element.attr("disabled", false);
        }
    });
    //don't submit the form
    return false;
}

function license_agreement_ajax_submit(event) {
    // this sets if user will be required to agree to resource rights statement prior
    // to any resource file or bag download
    var form = $(this).closest("form");
    var datastring = form.serialize();
    var url = form.attr('action');
    var element = $(this);
    var action = $(this).closest("form").find("input[name='flag']").val();
    element.attr("disabled", true);

    $.ajax({
        type: "POST",
        url: url,
        dataType: 'html',
        data: datastring,
        success: function () {
            element.attr("disabled", false);
            if (action == "make_not_require_lic_agreement") {
                element.closest("form").find("input[name='flag']").val("make_require_lic_agreement");
            }
            else {
                element.closest("form").find("input[name='flag']").val("make_not_require_lic_agreement");
            }
            // page refresh is needed to update if license agreement popup to show or not prior
            // to download of files/bag
            window.location = window.location.href;
        },
        error: function () {
            element.attr("disabled", false);
        }
    });
    //don't submit the form
    return false;
}

function unshare_resource_ajax_submit(form_id, check_for_prompt, remove_permission) {
    if (typeof check_for_prompt === 'undefined'){
        check_for_prompt = true;
    }
    if (typeof  remove_permission === 'undefined'){
        remove_permission = true;
    }
    if (check_for_prompt){
        if (!promptSelfRemovingAccess(form_id)){
            return;
        }
    }
    if (!remove_permission){
        return;
    }

    $form = $('#' + form_id);
    var datastring = $form.serialize();
    var url = $form.attr('action');
    setPointerEvents(false);
    $form.parent().closest("tr").addClass("loading");
    $.ajax({
        type: "POST",
        url: url,
        dataType: 'html',
        data: datastring,
        success: function (result) {
            var json_response = JSON.parse(result);
            if (json_response.status == "success") {
                if (json_response.hasOwnProperty('redirect_to')){
                    window.location.href = json_response.redirect_to;
                }
                $form.parent().closest("tr").remove();
                if ($(".access-table li.active[data-access-type='Is owner']").length == 1) {
                    $(".access-table li.active[data-access-type='Is owner']").closest("tr").addClass("hide-actions");
                }
                setPointerEvents(true);
            }
            else {
                $("#div-invite-people").find(".label-danger").remove(); // Remove previous alerts
                $("#div-invite-people").append("<span class='label label-danger'><strong>Error: </strong>" + json_response.message + "</span>");
                $form.parent().closest("tr").removeClass("loading");
                setPointerEvents(true);
            }
        },
        error: function(XMLHttpRequest, textStatus, errorThrown){
            $("#div-invite-people").find(".label-danger").remove(); // Remove previous alerts
            $("#div-invite-people").append("<span class='label label-danger'><strong>Error: </strong>" + errorThrown + "</span>");
            setPointerEvents(true);
        }
    });
    //don't submit the form
    return false;
}

function undo_share_ajax_submit(form_id) {
    $form = $('#' + form_id);
    var datastring = $form.serialize();
    var url = $form.attr('action');
    setPointerEvents(false);
    $form.parent().closest("tr").addClass("loading");

    $.ajax({
        type: "POST",
        url: url,
        dataType: 'html',
        data: datastring,
        success: function (result) {
            var json_response;
            var divInvite = $("#div-invite-people");

            try {
                json_response = JSON.parse(result);
            }
            catch (err) {
                console.log(err.message);
                // Remove previous alerts
                divInvite.find(".label-danger").remove();

                // Append new error message
                divInvite.append("<span class='label label-danger'>" +
                    "<strong>Error: </strong>Failed to undo action.</span>");

                $form.parent().closest("tr").removeClass("loading");
                setPointerEvents(true);
                return;
            }

            if (json_response.status == "success") {
                // Set the new permission level in the interface
                var userRoles = $form.closest("tr").find(".user-roles");

                userRoles.find("li").removeClass("active");

                if (json_response.undo_user_privilege == "view" || json_response.undo_group_privilege == "view") {
                    userRoles.find(".dropdown-toggle").text("Can view");
                    userRoles.find("li[data-access-type='" + "Can view"
                        + "']").addClass("active");
                }
                else if (json_response.undo_user_privilege == "change" || json_response.undo_group_privilege == "change") {
                    userRoles.find(".dropdown-toggle").text("Can edit");
                    userRoles.find("li[data-access-type='" + "Can edit"
                        + "']").addClass("active");
                }
                else if (json_response.undo_user_privilege == "owner" || json_response.undo_group_privilege == "owner") {
                    userRoles.find(".dropdown-toggle").text("Is owner");
                    userRoles.find("li[data-access-type='" + "Is owner"
                        + "']").addClass("active");
                }
                else {
                    // The item has no other permission. Remove it.
                    $form.parent().closest("tr").remove();
                    setPointerEvents(true);
                    return;
                }

                ownersConstrain();

                userRoles.find(".dropdown-toggle").append(" <span class='caret'></span>");
                $(".role-dropdown").removeClass("open");
                $form.toggleClass("hidden", true);
            }
            else {
                // An error occurred
                divInvite.find(".label-danger").remove(); // Remove previous alerts

                divInvite.append("<span class='label label-danger'><strong>Error: </strong>"
                    + json_response.message + "</span>");

                $form.parent().closest("tr").removeClass("loading");
            }

            $form.parent().closest("tr").removeClass("loading");
            setPointerEvents(true);
        },
        error: function(XMLHttpRequest, textStatus, errorThrown){
            $("#div-invite-people").find(".label-danger").remove(); // Remove previous alerts
            $("#div-invite-people").append("<span class='label label-danger'><strong>Error: </strong>" + errorThrown + "</span>");
            setPointerEvents(true);
        }
    });
    //don't submit the form
    return false;
}

function showWaitDialog(){
    // display wait for the process to complete dialog
    return $("#wait-to-complete").dialog({
        resizable: false,
        draggable: false,
        height: "auto",
        width: 400,
        modal: true,
        dialogClass: 'noclose'
    });
}

function promptSelfRemovingAccess(form_id){
    $form = $('#' + form_id);
    var url = $form.attr('action');
    // check if we are unsharing a user or a group
    var isUserUnsharing = false;
    if(url.indexOf("unshare-resource-with-user") > 0){
        isUserUnsharing = true;
    }
    if(!isUserUnsharing){
        return true;
    }
    var formIDParts = form_id.split('-');
    var userID = parseInt(formIDParts[formIDParts.length -1]);
    var currentUserID = parseInt($("#current-user-id").val());
    if (currentUserID != userID){
        // no need to prompt for confirmation since self is not unsharing
        return true;
    }

    // close the manage access panel (modal)
    $("#manage-access .btn-primary").click();

    // display remove access confirmation dialog
    $("#dialog-confirm-delete-self-access").dialog({
        resizable: false,
        draggable: false,
        height: "auto",
        width: 500,
        modal: true,
        dialogClass: 'noclose',
        buttons: {
            Cancel: function () {
                $(this).dialog("close");
                // show manage access control panel again
                $("#manage-access").modal('show');
                unshare_resource_ajax_submit(form_id, false, false);
            },
            "Remove": function () {
                $(this).dialog("close");
                unshare_resource_ajax_submit(form_id, false, true);
            }
        },
        open: function () {
            $(this).closest(".ui-dialog")
                .find(".ui-dialog-buttonset button:first") // the first button
                .addClass("btn btn-default");

            $(this).closest(".ui-dialog")
                .find(".ui-dialog-buttonset button:nth-child(2)") // the first button
                .addClass("btn btn-danger");
        }
    });
}

function change_share_permission_ajax_submit(form_id) {
    $form = $('#' + form_id);
    var datastring = $form.serialize();
    var url = $form.attr('action');
    $form.parent().closest(".user-roles").find("li[data-access-type='" + $form.attr("data-access-type") + "']").addClass("loading");
    setPointerEvents(false);
    $.ajax({
        type: "POST",
        url: url,
        dataType: 'html',
        data: datastring,
        success: function (result) {
            $("#div-invite-people").find(".label-danger").remove(); // Remove previous alerts
            json_response = JSON.parse(result);

            try {
                json_response = JSON.parse(result);
            }
            catch (err) {
                console.log(err.message);
                // Remove previous alerts
                $("#div-invite-people").find(".label-danger").remove();

                // Append new error message
                $("#div-invite-people").append("<span class='label label-danger'>" +
                    "<strong>Error: </strong>Failed to change permission.</span>");

                $form.parent().closest("tr").removeClass("loading");
                setPointerEvents(true);
                return;
            }

            var userRoles = $form.parent().closest(".user-roles");

            if (json_response.status == "success") {
                userRoles.find(".dropdown-toggle").text($form.attr("data-access-type"));
                userRoles.find(".dropdown-toggle").append(" <span class='caret'></span>");
                userRoles.find("li").removeClass("active");

                userRoles.find("li[data-access-type='" + $form.attr("data-access-type")
                    + "']").addClass("active");
                $(".role-dropdown").removeClass("open");

                $form.closest("tr").find(".undo-share-form").toggleClass("hidden", false);

                updateActionsState(json_response.current_user_privilege);
            }
            else if (json_response.status == "error") {
                $("#div-invite-people").append("<span class='label label-danger'><strong>Error: </strong>" + json_response.error_msg + "</span>");
            }
            userRoles.find("li").removeClass("loading");
            setPointerEvents(true);
        },
        error: function(XMLHttpRequest, textStatus, errorThrown){
            $("#div-invite-people").find(".label-danger").remove(); // Remove previous alerts
            $("#div-invite-people").append("<span class='label label-danger'><strong>Error: </strong>" + errorThrown + "</span>");
            setPointerEvents(true);
        }
    });
}

function share_resource_ajax_submit(form_id) {
    $form = $('#' + form_id);
    var datastring = $form.serialize();
    var share_with;
    var shareType;

    if ($("#div-invite-people button[data-value='users']").hasClass("btn-primary")) {
        if ($("#id_user-deck > .hilight").length > 0) {
            share_with = $("#id_user-deck > .hilight")[0].getAttribute("data-value");
            shareType = "user";
        }
        else {
            return false;
        }
    }
    else {
        if ($("#id_group-deck > .hilight").length > 0) {
            share_with = $("#id_group-deck > .hilight")[0].getAttribute("data-value");
            shareType = "group";
        }
        else {
            return false;
        }
    }

    var access_type = $("#selected_role")[0].getAttribute("data-role");
    var url = $form.attr('action') + access_type + "/" + share_with + "/";
    setPointerEvents(false);
    $.ajax({
        type: "POST",
        url: url,
        dataType: 'html',
        data: datastring,
        success: function (result) {
            $("#div-invite-people").find(".label-danger").remove(); // Remove previous alerts
            json_response = JSON.parse(result);
            if (json_response.status == "success") {
                $(".access-table #row-id-" + share_with).remove(); // Remove previous entry if it exists
                $(".hilight > span").click(); // Clears the search field

                // Get a copy of the user row template
                var rowTemplate = $("#templateRow").clone();

                // Form actions
                var unshareUrl;
                var undoUrl;
                if (shareType == "user") {
                    unshareUrl = $form.attr('action').replace("share-resource-with-user", "unshare-resource-with-user")
                        + share_with + "/";
                    undoUrl = rowTemplate.find(".undo-share-form").attr("action") + share_with + "/";
                }
                else {
                    unshareUrl =
                        $form.attr('action').replace("share-resource-with-group", "unshare-resource-with-group")
                        + share_with + "/";

                    undoUrl = rowTemplate.find(".undo-share-form").attr("action")
                            .replace("undo-share-resource-with-user", "undo-share-resource-with-group")
                        + share_with + "/";
                }

                var viewUrl = $form.attr('action') + "view" + "/" + share_with + "/";
                var changeUrl = $form.attr('action') + "edit" + "/" + share_with + "/";
                var ownerUrl = $form.attr('action') + "owner" + "/" + share_with + "/";

                rowTemplate.find(".remove-user-form").attr('action', unshareUrl);
                rowTemplate.find(".remove-user-form").attr('id', 'form-remove-user-' + share_with);

                rowTemplate.find(".undo-share-form").attr('action', undoUrl);
                rowTemplate.find(".undo-share-form").attr('id', 'form-undo-share-' + share_with);

                // Set form urls, ids
                rowTemplate.find(".share-form-view").attr('action', viewUrl);
                rowTemplate.find(".share-form-view").attr("id", "share-view-" + share_with);
                rowTemplate.find(".share-form-view").attr("data-access-type", "Can view");
                rowTemplate.find(".share-form-view a").attr("data-arg", "share-view-" + share_with);
                rowTemplate.find(".share-form-edit").attr('action', changeUrl);
                rowTemplate.find(".share-form-edit").attr("id", "share-edit-" + share_with);
                rowTemplate.find(".share-form-edit").attr("data-access-type", "Can edit");
                rowTemplate.find(".share-form-edit a").attr("data-arg", "share-edit-" + share_with);

                if (shareType == "user") {
                    rowTemplate.find(".share-form-owner").attr('action', ownerUrl);
                    rowTemplate.find(".share-form-owner").attr("id", "share-owner-" + share_with);
                    rowTemplate.find(".share-form-owner").attr("data-access-type", "Is owner");
                    rowTemplate.find(".share-form-owner a").attr("data-arg", "share-owner-" + share_with);
                }
                else {
                    rowTemplate.find(".share-form-owner").parent().remove();
                }

                if (json_response.name) {
                    rowTemplate.find("div[data-col='name'] a").text(json_response.name);
                }
                else {
                    rowTemplate.find("div[data-col='name'] a").text(json_response.username);
                }

                rowTemplate.find("div[data-col='name'] a").attr("href", "/" + shareType + "/" + share_with);

                if (!json_response.is_current_user) {
                    rowTemplate.find(".you-flag").hide();
                }

                if (shareType == "user") {
                    rowTemplate.find("div[data-col='user-name']").text(json_response.username);
                }
                else {
                    rowTemplate.find("div[data-col='user-name']").text("(Group)");
                }

                if (shareType == "user") {
                    rowTemplate.find(".group-image-wrapper").remove();
                    if (json_response.profile_pic != "No picture provided") {
                        rowTemplate.find(".profile-pic-thumbnail").attr("style", "background-image: url('" + json_response.profile_pic + "')");
                        rowTemplate.find(".profile-pic-thumbnail").removeClass("user-icon");
                    }
                }
                else {
                    rowTemplate.find(".profile-pic-thumbnail").remove();
                    if (json_response.group_pic != "No picture provided") {
                        rowTemplate.find(".group-image-wrapper .group-image-extra-small").attr("style", "background-image: url('" + json_response.group_pic + "')");
                    }
                    else {
                        // Set default group picture
                        var defaultImgURL = $("#templateRow .group-preview-image-default")[0].style.backgroundImage;
                        rowTemplate.find(".group-image-wrapper .group-image-extra-small").attr("style", "background-image: " + defaultImgURL);
                    }
                }

                if (access_type == "view") {
                    rowTemplate.find("span[data-col='current-access']").text("Can view");
                    rowTemplate.find("span[data-col='current-access']").append(" <span class='caret'></span>");
                    rowTemplate.find(".share-form-view").parent().addClass("active");
                }
                else if (access_type == "edit") {
                    rowTemplate.find("span[data-col='current-access']").text("Can edit");
                    rowTemplate.find("span[data-col='current-access']").append(" <span class='caret'></span>");
                    rowTemplate.find(".share-form-edit").parent().addClass("active");
                }
                else if (access_type == "owner") {
                    rowTemplate.find("span[data-col='current-access']").text("Is owner");
                    rowTemplate.find("span[data-col='current-access']").append(" <span class='caret'></span>");
                    rowTemplate.find(".share-form-owner").parent().addClass("active");
                }
                $(".access-table > tbody").append($("<tr id='row-id-" + share_with + "'>" + rowTemplate.html() + "</tr>"));

                updateActionsState(json_response.current_user_privilege);
            }
            else if (json_response.status == "error") {
                $("#div-invite-people").append("<span class='label label-danger'><strong>Error: </strong>" + json_response.error_msg + "</span>");
            }
            setPointerEvents(true);
        },
        error: function(XMLHttpRequest, textStatus, errorThrown){
            $("#div-invite-people").find(".label-danger").remove(); // Remove previous alerts
            $("#div-invite-people").append("<span class='label label-danger'><strong>Error: </strong>" + errorThrown + "</span>");
            setPointerEvents(true);
        }
    });
    //don't submit the form
    return false;
}

function metadata_update_ajax_submit(form_id){
    $alert_success = '<div class="alert alert-success" id="success-alert"> \
        <button type="button" class="close" data-dismiss="alert">x</button> \
        <strong>Success! </strong> \
        Metadata updated.\
    </div>';
    $alert_error = '<div class="alert alert-danger" id="error-alert"> \
        <button type="button" class="close" data-dismiss="alert">x</button> \
        <strong>Error! </strong> \
        Metadata failed to update.\
    </div>';

    if (typeof metadata_update_ajax_submit.resourceSatusDisplayed == 'undefined'){
        metadata_update_ajax_submit.resourceSatusDisplayed = false;
    }
    var flagAsync = (form_id == "id-subject" ? false : true);   // Run keyword related changes synchronously to prevent integrity error
    var resourceType = $("#resource-type").val();
    $form = $('#' + form_id);
    var datastring = $form.serialize();
    $.ajax({
        type: "POST",
        url: $form.attr('action'),
        dataType: 'html',
        data: datastring,
        async: flagAsync,
        success: function(result) {
            /* The div contains now the updated form */
            //$('#' + form_id).html(result);
            json_response = JSON.parse(result);
            if (json_response.status === 'success')
            {
                // show update netcdf file update option for NetCDFLogicalFile
                if (json_response.logical_file_type === "NetCDFLogicalFile"){
                    $("#div-netcdf-file-update").show();
                }
                // show update sqlite file update option for TimeSeriesLogicalFile
                if (json_response.logical_file_type === "TimeSeriesLogicalFile"  &&
                    json_response.is_dirty && json_response.can_update_sqlite) {
                    $("#div-sqlite-file-update").show();
                }
                // show update netcdf resource
                if (resourceType === 'Multidimensional (NetCDF)' &&
                    json_response.is_dirty) {
                    $("#netcdf-file-update").show();
                }

                // start timeseries resource specific DOM manipulation
                if(resourceType === 'Time Series') {
                    if ($("#can-update-sqlite-file").val() === "True" && ($("#metadata-dirty").val() === "True" || json_response.is_dirty)) {
                        $("#sql-file-update").show();
                    }
                }

                // dynamically update resource coverage when timeseries 'site' element gets updated or
                // file type 'coverage' element gets updated for composite resource
                if ((json_response.element_name.toLowerCase() === 'site' && resourceType === 'Time Series') ||
                    ((json_response.element_name.toLowerCase() === 'coverage' ||
                        json_response.element_name.toLowerCase() === 'site') && resourceType === 'Composite Resource')){
                    if (json_response.hasOwnProperty('temporal_coverage')){
                        var temporalCoverage = json_response.temporal_coverage;
                        updateResourceTemporalCoverage(temporalCoverage);
                        if(resourceType === 'Composite Resource' && json_response.has_logical_temporal_coverage) {
                             $("#btn-update-resource-temporal-coverage").show();
                        }
                        else {
                           $("#btn-update-resource-temporal-coverage").hide();
                        }
                    }

                    if (json_response.hasOwnProperty('spatial_coverage')) {
                        var spatialCoverage = json_response.spatial_coverage;
                        updateResourceSpatialCoverage(spatialCoverage);
                        if(resourceType === 'Composite Resource' && json_response.has_logical_spatial_coverage) {
                            $("#btn-update-resource-spatial-coverage").show();
                        }
                        else {
                           $("#btn-update-resource-spatial-coverage").hide();
                        }
                    }
                }
                if ($form.attr("id") == "id-site" || $form.attr("id") == "id-site-file-type"){
                    makeTimeSeriesMetaDataElementFormReadOnly(form_id, "id_site");
                }
                else if ($form.attr("id") == "id-variable" || $form.attr("id") == "id-variable-file-type"){
                    makeTimeSeriesMetaDataElementFormReadOnly(form_id, "id_variable");
                }
                else if ($form.attr("id") == "id-method" || $form.attr("id") == "id-method-file-type"){
                    makeTimeSeriesMetaDataElementFormReadOnly(form_id, "id_method");
                }
                else if ($form.attr("id") == "id-processinglevel" || $form.attr("id") == "id-processinglevel-file-type"){
                    makeTimeSeriesMetaDataElementFormReadOnly(form_id, "id_processinglevel");
                }
                // end of timeseries specific DOM manipulation

                $(document).trigger("submit-success");
                $form.find("button.btn-primary").hide();
                if (json_response.hasOwnProperty('element_id')){
                    form_update_action = $form.attr('action');
                    if (!json_response.hasOwnProperty('form_action')){
                        res_short_id = form_update_action.split('/')[3];
                        update_url = "/hsapi/_internal/" + res_short_id + "/"
                            + json_response.element_name + "/"
                            + json_response.element_id + "/update-metadata/";
                    }
                    else {
                        update_url = json_response.form_action
                    }

                    $form.attr('action', update_url);
                }
                if (json_response.element_exists == false){
                    form_update_action = $form.attr('action');
                    res_short_id = form_update_action.split('/')[3];
                    update_url = "/hsapi/_internal/" + res_short_id + "/" + json_response.element_name + "/add-metadata/";
                    $form.attr('action', update_url);
                }
                if (json_response.hasOwnProperty('element_name')){
                    if(json_response.element_name === 'title'){
                        $res_title = $(".section-header").find("span").first();
                        field_name_value = $res_title.text();
                        updated_title = $form.find("#id_value").val();
                        $res_title.text(updated_title);
                    }
                }
                if (json_response.hasOwnProperty('metadata_status')) {
                    if (json_response.metadata_status !== $('#metadata-status').text()) {
                        $('#metadata-status').text(json_response.metadata_status);
                        if (json_response.metadata_status.toLowerCase().indexOf("insufficient") == -1) {
                            if(resourceType != 'Web App Resource')
                                promptMessage = "This resource can be published or made public.";
                            else
                                promptMessage = "This resource can be made public.";
                            if (!metadata_update_ajax_submit.resourceSatusDisplayed){
                                metadata_update_ajax_submit.resourceSatusDisplayed = true;
                                if (json_response.hasOwnProperty('res_public_status')) {
                                    if (json_response.res_public_status.toLowerCase() === "not public") {
                                        // if the resource is already public no need to show the following alert message
                                        customAlert("Resource Status:", promptMessage, "success", 3000);
                                    }
                                }
                                else {
                                    customAlert("Resource Status:", promptMessage, "success", 3000);
                                }
                            }
                            $("#missing-metadata-or-file:not(.persistent)").fadeOut();
                            $("#missing-metadata-file-type:not(.persistent)").fadeOut();
                        }
                    }
                }
                if (json_response.hasOwnProperty('res_public_status') && json_response.hasOwnProperty('res_discoverable_status')) {
                    if (json_response.res_public_status == "public"){
                        if (!$("#btn-public").hasClass('active')){
                            $("#btn-public").prop("disabled", false);
                        }
                    }
                    else {
                        $("#btn-public").removeClass('active');
                        $("#btn-public").prop("disabled", true);
                    }
                    if (json_response.res_discoverable_status == "discoverable"){
                        if (!$("#btn-discoverable").hasClass('active')){
                            $("#btn-discoverable").prop("disabled", false);
                        }
                    }
                    else {
                        $("#btn-discoverable").removeClass('active');
                        $("#btn-discoverable").prop("disabled", true);
                    }
                    if (json_response.res_public_status !== "public" && json_response.res_discoverable_status !== "discoverable"){
                        $("#btn-private").addClass('active');
                        $("#btn-private").prop("disabled", true);
                    }
                    if (json_response.metadata_status.toLowerCase().indexOf("insufficient") == -1) {
                        if (!$("#btn-public").hasClass('active')){
                            $("#btn-public").prop("disabled", false);
                        }
                        if (!$("#btn-discoverable").hasClass('active')){
                            $("#btn-discoverable").prop("disabled", false);
                        }
                    }
                }
                $('body > .container').append($alert_success);
                $('#error-alert').each(function(){
                    this.remove();
                });
                $(".alert-success").fadeTo(2000, 500).fadeOut(1000, function(){
                    $(document).trigger("submit-success");
                    $(".alert-success").alert('close');
                });
            }
            else{
                $alert_error = $alert_error.replace("Metadata failed to update.", json_response.message);
                $('#' + form_id).before($alert_error);
                $(".alert-error").fadeTo(2000, 500).slideUp(1000, function(){
                    $(".alert-error").alert('close');
                });
            }
        },
        error: function(XMLHttpRequest, textStatus, errorThrown)
        {
            $('#' + form_id).before($alert_error);
            $(".alert-error").fadeTo(2000, 500).slideUp(1000, function(){
                $(".alert-error").alert('close');
            });
        }
    });
    //don't submit the form
    return false;
}

function makeTimeSeriesMetaDataElementFormReadOnly(form_id, element_id){
    var $element_selection_dropdown = $('#' + element_id + '_code_choices');
    if ($element_selection_dropdown.length && $element_selection_dropdown.attr('type') !== "hidden"){
        $('#' + form_id + ' :input').attr('readonly', 'readonly');
    }
}

function set_file_type_ajax_submit(url, folder_path) {
    var $alert_success = '<div class="alert alert-success" id="error-alert"> \
        <button type="button" class="close" data-dismiss="alert">x</button> \
        <strong>Success! </strong> \
        Selected content type creation was successful.\
    </div>';

    var waitDialog = showWaitDialog();
    return $.ajax({
        type: "POST",
        url: url,
        dataType: 'html',
        async: true,
        data: {
            folder_path: folder_path
        },
        success: function (result) {
            waitDialog.dialog("close");
            var json_response = JSON.parse(result);
            var spatialCoverage = json_response.spatial_coverage;
            updateResourceSpatialCoverage(spatialCoverage);
            $("#fb-inner-controls").before($alert_success);
            $(".alert-success").fadeTo(2000, 500).slideUp(1000, function(){
                $(".alert-success").alert('close');
            });
        },
        error: function (xhr, textStatus, errorThrown) {
            waitDialog.dialog("close");
            var jsonResponse = JSON.parse(xhr.responseText);
            display_error_message('Failed to set the selected aggregation type', jsonResponse.message);
            $(".file-browser-container, #fb-files-container").css("cursor", "auto");
        }
    });
}

function remove_aggregation_ajax_submit(url) {
    var $alert_success = '<div class="alert alert-success" id="error-alert"> \
        <button type="button" class="close" data-dismiss="alert">x</button> \
        <strong>Success! </strong> \
        Content type was removed successfully.\
    </div>';

    // This wait dialog may not be useful
    var waitDialog = showWaitDialog();
    return $.ajax({
        type: "POST",
        url: url,
        dataType: 'html',
        async: true,
        success: function (result) {
            waitDialog.dialog("close");
            var json_response = JSON.parse(result);
            var spatialCoverage = json_response.spatial_coverage;
            updateResourceSpatialCoverage(spatialCoverage);
            $("#fb-inner-controls").before($alert_success);
            $(".alert-success").fadeTo(2000, 500).slideUp(1000, function(){
                $(".alert-success").alert('close');
            });
        },
        error: function (xhr, textStatus, errorThrown) {
            waitDialog.dialog("close");
            var jsonResponse = JSON.parse(xhr.responseText);
            display_error_message('Failed to remove aggregation', jsonResponse.message);
            $(".file-browser-container, #fb-files-container").css("cursor", "auto");
        }
    });
}

function get_file_type_metadata_ajax_submit(url) {
    return $.ajax({
        type: "POST",
        url: url,
        dataType: 'html',
        async: false,
        success: function (result) {
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
        }
    });
}

function filetype_keywords_update_ajax_submit() {
    $form = $('#id-keywords-filetype');
    var datastring = $form.serialize();
    $.ajax({
        type: "POST",
        url: $form.attr('action'),
        dataType: 'html',
        data: datastring,
        success: function (result) {
            json_response = JSON.parse(result);
            if (json_response.status === 'success') {
                var keywords = json_response.added_keywords;
                // add each of the newly added keywords as new li element for display
                for (var i = 0; i < keywords.length; i++) {
                    var li = $("<li class='tag'><span></span></li>");
                    li.find('span').text(keywords[i]);
                    li.append('&nbsp;<a><span class="glyphicon glyphicon-remove-circle icon-remove"></span></a>');
                    $("#lst-tags-filetype").append(li);
                    $(".icon-remove").click(onRemoveKeywordFileType);
                }
                // Refresh keywords field for the resource
                var resKeywords = json_response.resource_keywords;
                $("#lst-tags").empty();
                for (var i = 0; i < resKeywords.length; i++) {
                    if (resKeywords[i] != "") {
                        var li = $("<li class='tag'><span></span></li>");
                        li.find('span').text(resKeywords[i]);
                        li.append('&nbsp;<a><span class="glyphicon glyphicon-remove-circle icon-remove"></span></a>')
                        $("#lst-tags").append(li);
                    }
                }
                // show update netcdf file update option for NetCDFLogicalFile
                if (json_response.logical_file_type === "NetCDFLogicalFile"){
                    $("#div-netcdf-file-update").show();
                }
            }
        }
    });
}

function filetype_keyword_delete_ajax_submit(keyword, tag) {
    var datastring = 'keyword=' + keyword;
    var url = $('#id-delete-keyword-filetype-action').val();
    $.ajax({
        type: "POST",
        url: url,
        dataType: 'html',
        data: datastring,
        success: function (result) {
            json_response = JSON.parse(result);
            if (json_response.status === 'success') {
                // remove the li element containing the deleted keyword
                tag.remove();
                // show update netcdf file update option for NetCDFLogicalFile
                if (json_response.logical_file_type === "NetCDFLogicalFile"){
                    $("#div-netcdf-file-update").show();
                }
            }
        }
    });
}

function update_netcdf_file_ajax_submit() {
    var $alert_success = '<div class="alert alert-success" id="error-alert"> \
        <button type="button" class="close" data-dismiss="alert">x</button> \
        <strong>Success! </strong> \
        File update was successful.\
    </div>';

    var url = $('#update-netcdf-file').attr("action");
    $.ajax({
        type: "POST",
        url: url,
        dataType: 'html',
        success: function (result) {
            json_response = JSON.parse(result);
            if (json_response.status === 'success') {
                $("#div-netcdf-file-update").hide();
                $alert_success = $alert_success.replace("File update was successful.", json_response.message);
                $("#fb-inner-controls").before($alert_success);
                $(".alert-success").fadeTo(2000, 500).slideUp(1000, function(){
                    $(".alert-success").alert('close');
                });
                // refetch file metadata to show the updated header file info
                 showFileTypeMetadata(false, "");
            }
            else {
                display_error_message("File update.", json_response.message);
            }
        }
    });
}

function update_sqlite_file_ajax_submit() {
    var $alert_success = '<div class="alert alert-success" id="error-alert"> \
        <button type="button" class="close" data-dismiss="alert">x</button> \
        <strong>Success! </strong> \
        File update was successful.\
    </div>';

    var url = $('#update-sqlite-file').attr("action");
    $.ajax({
        type: "POST",
        url: url,
        dataType: 'html',
        success: function (result) {
            json_response = JSON.parse(result);
            if (json_response.status === 'success') {
                $("#div-sqlite-file-update").hide();
                $alert_success = $alert_success.replace("File update was successful.", json_response.message);
                $("#fb-inner-controls").before($alert_success);
                $(".alert-success").fadeTo(2000, 500).slideUp(1000, function(){
                    $(".alert-success").alert('close');
                });
                // refetch file metadata to show the updated header file info
                showFileTypeMetadata(false, "");
            }
            else {
                display_error_message("File update.", json_response.message);
            }
        }
    });
}

function get_user_info_ajax_submit(url, obj) {
    var is_group = false;
    var entry = $(obj).closest("div[data-hs-user-type]").find("#id_user-deck > .hilight");
    if (entry.length < 1) {
        entry = $(obj).parent().parent().parent().parent().find("#id_group-deck > .hilight");
        is_group = true;
    }
    if (entry.length < 1) {
        return;
    }

    var userID = entry[0].getAttribute("data-value");
    url = url + userID + "/" + is_group;

    $.ajax({
        type: "POST",
        url: url,
        dataType: 'html',
        success: function (result) {
            var formContainer = $(obj).parent().parent();
            var json_response = JSON.parse(result);
            if (is_group){
                formContainer.find("input[name='description']").val(json_response.url);
                formContainer.find("input[name='organization']").val(json_response.organization);
            }
            else{
                formContainer.find("input[name='name']").val(json_response.name);
                formContainer.find("input[name='description']").val(json_response.url);
                formContainer.find("input[name='organization']").val(json_response.organization);
                formContainer.find("input[name='email']").val(json_response.email);
                formContainer.find("input[name='address']").val(json_response.address);
                formContainer.find("input[name='phone']").val(json_response.phone);
                formContainer.find("input[name='homepage']").val(json_response.website);

                for (var identif in json_response.identifiers) {
                    modalBody = formContainer.find(".modal-body");
                    modalBody.append(
                        $('<input />').attr('type', 'hidden')
                            .attr('name', "identifier_name")
                            .attr('value', identif));

                    modalBody.append(
                        $('<input />').attr('type', 'hidden')
                            .attr('name', "identifier_link")
                            .attr('value', json_response.identifiers[identif]));
                }

            }
            formContainer.submit();
        },
        error: function(XMLHttpRequest, textStatus, errorThrown){

        }
    });
}

function display_error_message(title, err_msg) {
    $("#fb-alerts .upload-failed-alert").remove();
    $("#hsDropzone").toggleClass("glow-blue", false);

    $("#fb-alerts").append(
        '<div class="alert alert-danger alert-dismissible upload-failed-alert" role="alert">' +
        '<button type="button" class="close" data-dismiss="alert" aria-label="Close">' +
        '<span aria-hidden="true">&times;</span></button>' +
        '<div>' +
        '<strong>' + title + '</strong>' +
        '</div>' +
        '<div>' +
        '<span>' + err_msg + '</span>' +
        '</div>' +
        '</div>').fadeIn(200);
}

function delete_folder_ajax_submit(res_id, folder_path) {
    $(".file-browser-container, #fb-files-container").css("cursor", "progress");

    return $.ajax({
        type: "POST",
        url: '/hsapi/_internal/data-store-delete-folder/',
        async: true,
        data: {
            res_id: res_id,
            folder_path: folder_path
        },
        success: function (result) {
        },
        error: function(xhr, errmsg, err){
            display_error_message('Folder Deletion Failed', xhr.responseText);
        }
    });
}

// This method is called to refresh the loader with the most recent structure after every other call
function get_irods_folder_struct_ajax_submit(res_id, store_path) {
    $("#fb-files-container, #fb-files-container").css("cursor", "progress");
    // TODO: 2105: doesn't return enough information for intelligent decision 
    return $.ajax({
        type: "POST",
        url: '/hsapi/_internal/data-store-structure/',
        async: true,
        data: {
            res_id: res_id,
            store_path: store_path
        },
        success: function (result) {
            var files = result.files;
            var folders = result.folders;
            var can_be_public = result.can_be_public;
            $('#fb-files-container').empty();
            if (files.length > 0) {
                $.each(files, function(i, v) {
                    $('#fb-files-container').append(getFileTemplateInstance(v['name'], v['type'], v['aggregation_name'], v['logical_type'], v['logical_file_id'], v['size'], v['pk'], v['url']));
                });
            }
            if (folders.length > 0) {
                $.each(folders, function(i, v) {
                    $('#fb-files-container').append(getFolderTemplateInstance(v['name'], v['url'], v['folder_aggregation_type'], v['folder_aggregation_name'], v['folder_aggregation_id'], v['folder_aggregation_type_to_set'], v['folder_short_path'], v['main_file']));
                });
            }
            if (!files.length && !folders.length) {
                $('#fb-files-container').append('<span class="text-muted">This directory is empty</span>');
            }
            if (can_be_public) {
                $("#missing-metadata-or-file:not(.persistent)").fadeOut();
            }
            onSort();

            bindFileBrowserItemEvents();

            $("#hs-file-browser").attr("data-current-path", store_path);
            $("#upload-folder-path").text(store_path);
            $("#hs-file-browser").attr("data-res-id", res_id);

            // strip the 'data' folder from the path
            setBreadCrumbs(store_path.replace("data/", ""));

            if ($("#hsDropzone").hasClass("dropzone")) {
                // If no multiple files allowed and a file already exists, disable upload
                var allowMultiple = $("#hs-file-browser").attr("data-allow-multiple-files") == "True";
                if (!allowMultiple && files.length > 0) {
                    $('.dz-input').hide();
                    $(".fb-upload-caption").toggleClass("hidden", true);
                }
                else {
                    $('.dz-input').show();
                    $(".fb-upload-caption").toggleClass("hidden", false);
                    Dropzone.forElement("#hsDropzone").files = [];
                }
            }

            updateNavigationState();
            $(".selection-menu").hide();
            $("#flag-uploading").remove();
            $("#fb-files-container, #fb-files-container").css("cursor", "default");
            if (result.hasOwnProperty('spatial_coverage')){
                var spatialCoverage = result.spatial_coverage;
                updateResourceSpatialCoverage(spatialCoverage);
            }
            if (result.hasOwnProperty('temporal_coverage')){
                var temporalCoverage = result.temporal_coverage;
                updateResourceTemporalCoverage(temporalCoverage);
            }
        },
        error: function(xhr, errmsg, err){
            $(".selection-menu").hide();
            $("#flag-uploading").remove();
            $("#fb-files-container, #fb-files-container").css("cursor", "default");
            $('#fb-files-container').empty();
            setBreadCrumbs(store_path);
            $("#fb-files-container").prepend("<span>No files to display.</span>")
        }
    });
}

function zip_irods_folder_ajax_submit(res_id, input_coll_path, fileName) {
    $("#fb-files-container, #fb-files-container").css("cursor", "progress");
    return $.ajax({
        type: "POST",
        url: '/hsapi/_internal/data-store-folder-zip/',
        async: true,
        data: {
            res_id: res_id,
            input_coll_path: input_coll_path,
            output_zip_file_name: fileName,
            remove_original_after_zip: "false"
        },
        success: function (result) {
        },
        error: function (xhr, errmsg, err) {
            display_error_message('Folder Zipping Failed', xhr.responseText);
        }
    });
}

function unzip_irods_file_ajax_submit(res_id, zip_with_rel_path) {
    $("#fb-files-container, #fb-files-container").css("cursor", "progress");
    return $.ajax({
        type: "POST",
        url: '/hsapi/_internal/data-store-folder-unzip/',
        async: true,
        data: {
            res_id: res_id,
            zip_with_rel_path: zip_with_rel_path,
            remove_original_zip: "false"
        },
        success: function (result) {
            // TODO: handle "File already exists" errors
        },
        error: function (xhr, errmsg, err) {
            display_error_message('File Unzipping Failed', xhr.responseText);
        }
    });
}

function create_irods_folder_ajax_submit(res_id, folder_path) {
    $("#fb-files-container, #fb-files-container").css("cursor", "progress");
    return $.ajax({
        type: "POST",
        url: '/hsapi/_internal/data-store-create-folder/',
        async: true,
        data: {
            res_id: res_id,
            folder_path: folder_path
        },
        success: function (result) {
            var new_folder_rel_path = result.new_folder_rel_path;
            if (new_folder_rel_path.length > 0) {
                $('#create-folder-dialog').modal('hide');
                $("#txtFolderName").val("");
            }

        },
        error: function(xhr, errmsg, err){
            display_error_message('Folder Creation Failed', xhr.responseText);
        }
    });
}

// TODO: #2105: replace with move-to-folder and rename-file-or-folder: 
// TODO: ambiguous function based upon conflation in REST API
function move_or_rename_irods_file_or_folder_ajax_submit(res_id, source_path, target_path) {
    $("#fb-files-container, #fb-files-container").css("cursor", "progress");
    return $.ajax({
        type: "POST",
        url: '/hsapi/_internal/data-store-move-or-rename/',
        async: true,
        data: {
            res_id: res_id,
            source_path: source_path,
            target_path: target_path
        },
        success: function (result) {
            var target_rel_path = result.target_rel_path;
            if (target_rel_path.length > 0) {
                $("#fb-files-container li").removeClass("fb-cutting");
            }
        },
        error: function(xhr, errmsg, err){
            display_error_message('File Moving/Renaming Failed', xhr.responseText);
        }
    });
}

// target_path must be a folder
function move_to_folder_ajax_submit(res_id, source_paths, target_path) {
    $("#fb-files-container, #fb-files-container").css("cursor", "progress");
    return $.ajax({
        type: "POST",
        url: '/hsapi/_internal/data-store-move-to-folder/',
        async: true,
        data: {
            res_id: res_id,
            source_paths: JSON.stringify(source_paths),
            target_path: target_path
        },
        success: function (result) {
            var target_rel_path = result.target_rel_path;
            if (target_rel_path.length > 0) {
                $("#fb-files-container li").removeClass("fb-cutting");
            }
        },
        error: function(xhr, errmsg, err){
            display_error_message('File/Folder Moving Failed', xhr.responseText);
        }
    });
}

// prefixes must be the same on source_path and target_path 
function rename_file_or_folder_ajax_submit(res_id, source_path, target_path) {
    $("#fb-files-container, #fb-files-container").css("cursor", "progress");
    return $.ajax({
        type: "POST",
        url: '/hsapi/_internal/data-store-rename-file-or-folder/',
        async: true,
        data: {
            res_id: res_id,
            source_path: source_path,
            target_path: target_path
        },
        success: function (result) {
            var target_rel_path = result.target_rel_path;
            if (target_rel_path.length > 0) {
                $("#fb-files-container li").removeClass("fb-cutting");
            }
        },
        error: function(xhr, errmsg, err){
            display_error_message('File/Folder Renaming Failed', xhr.responseText);
        }
    });
}

function refreshResourceEditPage() {
    var form = $("#frm_refresh_page_edit_mode");
    form.submit();
}

function addFileTypeExtraMetadata(){
    $form = $('#add-keyvalue-filetype-metadata');
    var url = $form.attr('action');
    var key = $("#file_extra_meta_name").val();
    var value = $("#file_extra_meta_value").val();
    $alert_error = '<div class="alert alert-danger" id="error-alert"> \
        <button type="button" class="close" data-dismiss="alert">x</button> \
        <strong>Error! </strong> \
        Metadata failed to update.\
    </div>';

    $.ajax({
        type: "POST",
        url: url,
        data: {
            key: key,
            value: value
        },
        success: function (result) {
            var json_response = result;
            if (json_response.status === "success"){
                $("#add-keyvalue-filetype-modal").modal('hide');
                $("div").removeClass("modal-backdrop");
                $("body").removeClass("modal-open");
                $("#filetype-extra-metadata").replaceWith(json_response.extra_metadata);
                BindKeyValueFileTypeClickHandlers();

                // show update netcdf file update option for NetCDFLogicalFile
                if (json_response.logical_file_type === "NetCDFLogicalFile"){
                    $("#div-netcdf-file-update").show();
                }
            }
            else {
                $("#add-keyvalue-filetype-modal").modal('hide');
                $("div").removeClass("modal-backdrop");
                $("body").removeClass("modal-open");
                $alert_error = $alert_error.replace("Metadata failed to update.", json_response.message);
                $("#filetype-extra-metadata").before($alert_error);
                $(".alert-error").fadeTo(2000, 500).slideUp(1000, function(){
                    $(".alert-error").alert('close');
                });

            }
        },
        error: function(xhr, errmsg, err){
        }
    });
}

function updateFileTypeExtraMetadata(form_id){
    $form = $('#' + form_id);
    var datastring = $form.serialize();
    var url = $form.attr('action');
    var form_counter = $form.attr('data-counter');
    $alert_error = '<div class="alert alert-danger" id="error-alert"> \
        <button type="button" class="close" data-dismiss="alert">x</button> \
        <strong>Error! </strong> \
        Metadata failed to update.\
    </div>';

    $.ajax({
        type: "POST",
        url: url,
        data: datastring,
        success: function (result) {
            var json_response = result;
            if (json_response.status === "success"){
                $("#edit-keyvalue-filetype-modal-" + form_counter).modal('hide');
                $("div").removeClass("modal-backdrop");
                $("body").removeClass("modal-open");
                $("#filetype-extra-metadata").replaceWith(json_response.extra_metadata);
                // show update netcdf file update option for NetCDFLogicalFile
                if (json_response.logical_file_type === "NetCDFLogicalFile"){
                    $("#div-netcdf-file-update").show();
                }
                BindKeyValueFileTypeClickHandlers();
            }
            else {
                $("#edit-keyvalue-filetype-modal-" + form_counter).modal('hide');
                $("div").removeClass("modal-backdrop");
                $("body").removeClass("modal-open");
                $alert_error = $alert_error.replace("Metadata failed to update.", json_response.message);
                $("#filetype-extra-metadata").before($alert_error);
                $(".alert-error").fadeTo(2000, 500).slideUp(1000, function(){
                    $(".alert-error").alert('close');
                });
            }
        },
        error: function(xhr, errmsg, err){
        }
    });
}

function deleteFileTypeExtraMetadata(form_id){
    $form = $('#' + form_id);
    var datastring = $form.serialize();
    var url = $form.attr('action');
    var form_counter = $form.attr('data-counter');
    $alert_error = '<div class="alert alert-danger" id="error-alert"> \
        <button type="button" class="close" data-dismiss="alert">x</button> \
        <strong>Error! </strong> \
        Metadata failed to update.\
    </div>';

    $.ajax({
        type: "POST",
        url: url,
        data: datastring,
        success: function (result) {
            var json_response = result;
            if (json_response.status === "success"){
                $("#delete-keyvalue-filetype-modal-" + form_counter).modal('hide');
                $("div").removeClass("modal-backdrop");
                $("body").removeClass("modal-open");
                $("#filetype-extra-metadata").replaceWith(json_response.extra_metadata);
                // show update netcdf file update option for NetCDFLogicalFile
                if (json_response.logical_file_type === "NetCDFLogicalFile"){
                    $("#div-netcdf-file-update").show();
                }
                BindKeyValueFileTypeClickHandlers();
            }
            else {
                $("#delete-keyvalue-filetype-modal-" + form_counter).modal('hide');
                $("div").removeClass("modal-backdrop");
                $("body").removeClass("modal-open");
                $alert_error = $alert_error.replace("Metadata failed to update.", json_response.message);
                $("#filetype-extra-metadata").before($alert_error);
                $(".alert-error").fadeTo(2000, 500).slideUp(1000, function(){
                    $(".alert-error").alert('close');
                });
            }
        },
        error: function(xhr, errmsg, err){
        }
    });
}

function BindKeyValueFileTypeClickHandlers(){
    // bind key value add modal form OK button click event
    var keyvalue_add_modal_form = $("#fileTypeMetaDataTab").find('#add-keyvalue-filetype-metadata');
    keyvalue_add_modal_form.find("button.btn-primary").click(function () {
        addFileTypeExtraMetadata();
    });

    // bind all key value edit modal forms OK button click event
    $("#fileTypeMetaDataTab").find('[id^=edit-keyvalue-filetype-metadata]').each(function(){
        var formId = $(this).attr('id');
        $(this).find("button.btn-primary").click(function (){
            updateFileTypeExtraMetadata(formId);
        })
    });

    // bind all key value delete modal forms Delete button click event
    $("#fileTypeMetaDataTab").find('[id^=delete-keyvalue-filetype-metadata]').each(function(){
        var formId = $(this).attr('id');
        $(this).find("button.btn-danger").click(function (){
            deleteFileTypeExtraMetadata(formId);
        })
    });
}
// show "Save changes" button when metadata form editing starts
function showMetadataFormSaveChangesButton(){
    $(".form-control").each(function () {
        $(this).on('input', function (e) {
            $(this).closest("form").find("button").show();
        });
        $(this).on('change', function (e) {
            $(this).closest("form").find("button").show();
        });
    });
}

// Initialize date pickers
function initializeDatePickers(){
    $(".dateinput").each(function () {
        $(this).datepicker({dateFormat: 'mm/dd/yy'});
        $(this).on('change', function () {
            $(this).closest("form").find("button").show();
        });
    });

    // Set stored dates
    $(".dateinput").each(function () {
        var dateString;
        var pickerDate = null;
        if($(this).attr('data-date')){
            // resource temporal date picker
            dateString = $(this).attr("data-date").split("-");
            pickerDate = new Date(dateString);
        }
        else{
            // file type temporal date picker
            if($(this).attr('value')){
                pickerDate = new Date($(this).attr("value"));
            }
        }
        if(pickerDate != null){
            $(this).datepicker("setDate", pickerDate);
        }
    });
}

function updateEditCoverageState() {
    // Set state for composite resource file metadata editing
    chkBox = $("#id-coverage-spatial-filetype #id_type_1");
    chkPoint = $("#id-coverage-spatial-filetype #id_type_2");

    if ($("#id-coverage-spatial-filetype #id_type_1").prop("checked")) {
        $("#id-coverage-spatial-filetype").attr("data-coordinates-type", "rectangle");
    }
    else {
        $("#id-coverage-spatial-filetype").attr("data-coordinates-type", "point");
    }

    if (chkBox.prop("checked")) {
        // coverage type is box
        $("#id_north_filetype").parent().closest("#div_id_north").hide();
        $("#id_east_filetype").parent().closest("#div_id_east").hide();
        $("#id_northlimit_filetype").parent().closest("#div_id_northlimit").show();
        $("#id_eastlimit_filetype").parent().closest("#div_id_eastlimit").show();
        $("#id_southlimit_filetype").parent().closest("#div_id_southlimit").show();
        $("#id_westlimit_filetype").parent().closest("#div_id_westlimit").show();
    }
    else {
        // coverage type is point
        $("#id_north_filetype").parent().closest("#div_id_north").show();
        $("#id_east_filetype").parent().closest("#div_id_east").show();
        $("#id_northlimit_filetype").parent().closest("#div_id_northlimit").hide();
        $("#id_eastlimit_filetype").parent().closest("#div_id_eastlimit").hide();
        $("#id_southlimit_filetype").parent().closest("#div_id_southlimit").hide();
        $("#id_westlimit_filetype").parent().closest("#div_id_westlimit").hide();
    }
}

// act on spatial coverage type change
function setFileTypeSpatialCoverageFormFields(logical_type){
    // Don't allow the user to change the coverage type
    var $id_type_filetype_div = $("#id_type_filetype");

    if (logical_type !== "GenericLogicalFile"){
        // don't allow changing coverage type
        $id_type_filetype_div.parent().closest("div").css('pointer-events', 'none');
        $id_type_filetype_div.find("#id_type_1").attr('onclick', 'return false');
        $id_type_filetype_div.find("#id_type_2").attr('onclick', 'return false');
        if (logical_type !== "RefTimeseriesLogicalFile"){
            $id_type_filetype_div.find("#id_type_1").attr('checked', 'checked');
        }
        $id_type_filetype_div.find("#id_type_2").attr('disabled', true);
        $id_type_filetype_div.find("#id_type_2").parent().closest("label").addClass("text-muted");
    }
    else {
        // file type is "GenericLogicalFile" - allow changing coverage type
        $id_type_filetype_div.find("input:radio").change(updateEditCoverageState);
    }

    // #id_type_1 is the box radio button
    if ($id_type_filetype_div.find("#id_type_1").attr("checked") == "checked" ||
        (logical_type != 'GeoFeatureLogicalFile' && logical_type != 'RefTimeseriesLogicalFile' && logical_type != 'GenericLogicalFile')) {
        // coverage type is box
        $("#id_north_filetype").parent().closest("#div_id_north").hide();
        $("#id_east_filetype").parent().closest("#div_id_east").hide();
    }
    else {
        // coverage type is point
        $("#id_northlimit_filetype").parent().closest("#div_id_northlimit").hide();
        $("#id_eastlimit_filetype").parent().closest("#div_id_eastlimit").hide();
        $("#id_southlimit_filetype").parent().closest("#div_id_southlimit").hide();
        $("#id_westlimit_filetype").parent().closest("#div_id_westlimit").hide();
    }
}

// updates the UI spatial coverage elements
function updateResourceSpatialCoverage(spatialCoverage) {
    if ($("#id-coverage-spatial").length) {
        $("#spatial-coverage-type").val(spatialCoverage.type);
        var $form = $("#id-coverage-spatial");
        var form_update_action = $form.attr('action');
        var res_short_id = form_update_action.split('/')[3];
        var update_url;
        if(!$.isEmptyObject(spatialCoverage)){
            update_url = "/hsapi/_internal/" + res_short_id + "/coverage/" + spatialCoverage.element_id + "/update-metadata/";
        }
        else {
            update_url = "/hsapi/_internal/" + res_short_id + "/coverage/add-metadata/";
        }
        $form.attr('action', update_url);
        var $id_type_div = $("#div_id_type");
        var $point_radio = $id_type_div.find("#id_type_2");
        var $box_radio = $id_type_div.find("#id_type_1");
        var resourceType = $("#resource-type").val();
        if (spatialCoverage.type === 'point') {
            $point_radio.attr('checked', 'checked');
            if(resourceType !== "Composite Resource"){
                $box_radio.attr('disabled', true);
                $box_radio.parent().closest("label").addClass("text-muted");
            }
            $point_radio.parent().closest("label").removeClass("text-muted");
            $point_radio.attr('disabled', false);
            $("#id_north").val(spatialCoverage.north);
            $("#id_east").val(spatialCoverage.east);
            $("#div_id_north").show();
            $("#div_id_east").show();
            $("#div_id_elevation").show();
            $("#div_id_northlimit").hide();
            $("#div_id_eastlimit").hide();
            $("#div_id_southlimit").hide();
            $("#div_id_westlimit").hide();
            $("#div_id_uplimit").hide();
            $("#div_id_downlimit").hide();
        }
        else { //coverage type is 'box'
            $box_radio.attr('checked', 'checked');
            if(resourceType !== "Composite Resource"){
                $point_radio.attr('disabled', true);
                $point_radio.parent().closest("label").addClass("text-muted");
            }
            $box_radio.parent().closest("label").removeClass("text-muted");
            $box_radio.attr('disabled', false);
            $("#id_eastlimit").val(spatialCoverage.eastlimit);
            $("#id_northlimit").val(spatialCoverage.northlimit);
            $("#id_westlimit").val(spatialCoverage.westlimit);
            $("#id_southlimit").val(spatialCoverage.southlimit);
            $("#div_id_north").hide();
            $("#div_id_east").hide();
            $("#div_id_elevation").hide();
            $("#div_id_northlimit").show();
            $("#div_id_eastlimit").show();
            $("#div_id_southlimit").show();
            $("#div_id_westlimit").show();
            $("#div_id_uplimit").show();
            $("#div_id_downlimit").show();
        }
        initMap();
    }
}

// updates the UI temporal coverage elements
function updateResourceTemporalCoverage(temporalCoverage) {
    $("#id_start").val(temporalCoverage.start);
    $("#id_start").attr('data-date', temporalCoverage.start);
    $("#id_end").val(temporalCoverage.end);
    $("#id_end").attr('data-date', temporalCoverage.end);
    $("#id-coverage-temporal").find("button.btn-primary").hide();
    initializeDatePickers();
}

function setFileTypeMetadataFormsClickHandlers(){
    $("#fileTypeMetaDataTab").find('form').each(function () {
        var formId = $(this).attr('id');
        if (formId !== "update-netcdf-file" && formId !== "update-sqlite-file"&& formId !== "id-keywords-filetype" && formId !== "add-keyvalue-filetype-metadata") {
              $(this).find("button.btn-primary").click(function () {
                metadata_update_ajax_submit(formId);
              });
        }
    });
    BindKeyValueFileTypeClickHandlers();
}
