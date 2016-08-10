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
            if (json_response.status == "success") {

                var action = form.find("input[name='action']");
                if (json_response.action == "CREATE") {
                    action.val("DELETE");
                    $("#btnMyResources").removeClass("btn-resource-add");
                    $("#btnMyResources").addClass("btn-resource-remove");
                    $("#btnMyResources").attr("title", "Remove from my resources");
                }
                else {
                    action.val("CREATE");
                    $("#btnMyResources").addClass("btn-resource-add");
                    $("#btnMyResources").removeClass("btn-resource-remove");
                    $("#btnMyResources").attr("title", "Add to my resources");
                }
            }
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {

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

function unshare_resource_ajax_submit(form_id) {
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
            $form.parent().closest("tr").remove();
            if ($(".access-table li.active[data-access-type='Is owner']").length == 1) {
                $(".access-table li.active[data-access-type='Is owner']").closest("tr").addClass("hide-actions");
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

            if (json_response.status == "success") {
                $form.parent().closest(".user-roles").find(".dropdown-toggle").text($form.attr("data-access-type"));
                $form.parent().closest(".user-roles").find(".dropdown-toggle").append(" <span class='caret'></span>");
                $form.parent().closest(".user-roles").find("li").removeClass("active");

                $form.parent().closest(".user-roles").find("li[data-access-type='" + $form.attr("data-access-type") + "']").addClass("active");
                $(".role-dropdown").removeClass("open");
                $form.parent().closest(".user-roles").find("li").removeClass("loading");

                updateActionsState(json_response.current_user_privilege);

                setPointerEvents(true);
            }
            else if (json_response.status == "error") {
                $("#div-invite-people").append("<span class='label label-danger'><strong>Error: </strong>" + json_response.error_msg + "</span>");
                $form.parent().closest(".user-roles").find("li").removeClass("loading");
                setPointerEvents(true);
            }
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
                if (shareType == "user"){
                    unshareUrl = $form.attr('action').replace("share-resource-with-user", "unshare-resource-with-user") + share_with + "/";
                }
                else {
                    unshareUrl = $form.attr('action').replace("share-resource-with-group", "unshare-resource-with-group") + share_with + "/";
                }

                var viewUrl = $form.attr('action') + "view" + "/" + share_with + "/";
                var changeUrl = $form.attr('action') + "edit" + "/" + share_with + "/";
                var ownerUrl = $form.attr('action') + "owner" + "/" + share_with + "/";


                rowTemplate.find(".remove-user-form").attr('action', unshareUrl);
                rowTemplate.find(".remove-user-form").attr('id', 'form-remove-user-' + share_with);
                rowTemplate.find(".remove-user-form .btn-remove-row").attr("onclick", "unshare_resource_ajax_submit('form-remove-user-" + share_with + "')")
                // Set form urls, ids, and onclick methods
                rowTemplate.find(".share-form-view").attr('action', viewUrl);
                rowTemplate.find(".share-form-view").attr("id", "share-view-" + share_with);
                rowTemplate.find(".share-form-view").attr("data-access-type", "Can view");
                rowTemplate.find(".share-form-view a").attr("onclick", "change_share_permission_ajax_submit('share-view-" + share_with + "')");
                rowTemplate.find(".share-form-edit").attr('action', changeUrl);
                rowTemplate.find(".share-form-edit").attr("id", "share-edit-" + share_with);
                rowTemplate.find(".share-form-edit").attr("data-access-type", "Can edit");
                rowTemplate.find(".share-form-edit a").attr("onclick", "change_share_permission_ajax_submit('share-edit-" + share_with + "')");
                if (shareType == "user") {
                    rowTemplate.find(".share-form-owner").attr('action', ownerUrl);
                    rowTemplate.find(".share-form-owner").attr("id", "share-owner-" + share_with);
                    rowTemplate.find(".share-form-owner").attr("data-access-type", "Is owner");
                    rowTemplate.find(".share-form-owner a").attr("onclick", "change_share_permission_ajax_submit('share-owner-" + share_with + "')");
                }
                else {
                    rowTemplate.find(".share-form-owner").parent().remove();
                }

                if (json_response.name) {
                    rowTemplate.find("span[data-col='name']").text(json_response.name);
                }
                else {
                    rowTemplate.find("span[data-col='name']").text(json_response.username);
                }

                if (!json_response.is_current_user) {
                    rowTemplate.find(".you-flag").hide();
                }
                if (shareType == "user") {
                    rowTemplate.find("span[data-col='user-name']").text(json_response.username);
                }
                else {
                    rowTemplate.find("span[data-col='user-name']").text("(Group)");
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
                    rowTemplate.find(".group-image-wrapper .group-image-extra-small").attr("style", "background-image: url('" + json_response.group_pic + "')");
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
                $(".access-table tbody").append($("<tr id='row-id-" + share_with + "'>" + rowTemplate.html() + "</tr>"));

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

    var flagAsync = (form_id == "id-subject" ? false : true);   // Run keyword related changes synchronously to prevent integrity error

    $form = $('#' + form_id);
    var datastring = $form.serialize();
    $.ajax({
        type: "POST",
        url: $form.attr('action'),
        dataType: 'html',
        data: datastring,
        async: flagAsync,
        success: function(result)
        {
            /* The div contains now the updated form */
            //$('#' + form_id).html(result);
            json_response = JSON.parse(result);
            if (json_response.status === 'success')
            {
                // start timeseries resource specific DOM manipulation
                if (($form.attr("id") == "id-site" || $form.attr("id") == "id-variable" ||
                    $form.attr("id") == "id-method" || $form.attr("id") == "id-processinglevel" ||
                    $form.attr("id") == "id-timeseriesresult") && ($("#can-update-sqlite-file").val()) === "True") {
                    $("#sql-file-update").show();
                }
                if (($form.attr("id") == "id-site")){
                    makeTimeSeriesMetaDataElementFormReadOnly(form_id, "id_site");
                }
                else if (($form.attr("id") == "id-variable")){
                    makeTimeSeriesMetaDataElementFormReadOnly(form_id, "id_variable");
                }
                else if (($form.attr("id") == "id-method")){
                    makeTimeSeriesMetaDataElementFormReadOnly(form_id, "id_method");
                }
                else if (($form.attr("id") == "id-processinglevel")){
                    makeTimeSeriesMetaDataElementFormReadOnly(form_id, "id_processinglevel");
                }
                // end of timeseries specific DOM manipulation

                $(document).trigger("submit-success");
                $form.find("button.btn-primary").hide();
                if (json_response.hasOwnProperty('element_id')){
                    form_update_action = $form.attr('action');
                    res_short_id = form_update_action.split('/')[3];
                    update_url = "/hsapi/_internal/" + res_short_id + "/" + json_response.element_name +"/" + json_response.element_id + "/update-metadata/"
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
                            customAlert("<i class='glyphicon glyphicon-flag custom-alert-icon'></i><strong>Metadata Status:</strong> sufficient to publish or make public", 3000);
                            $("#btn-public").prop("disabled", false);
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
    $element_selection_dropdown = $('#' + element_id + '_code_choices');
    if ($element_selection_dropdown.length && $element_selection_dropdown.attr('type') !== "hidden"){
        $('#' + form_id + ' :input').attr('readonly', 'readonly');
    }
}
function get_user_info_ajax_submit(url, obj) {
    var entry = $(obj).parent().parent().parent().parent().find("#id_user-deck > .hilight");
    if (entry.length < 1) {
        return;
    }

    var userID = entry[0].getAttribute("data-value");
    url = url + userID;

    $.ajax({
        type: "POST",
        url: url,
        dataType: 'html',
        success: function (result) {
            var formContainer = $(obj).parent().parent();
            var json_response = JSON.parse(result);

            formContainer.find("input[name='name']").val(json_response.name);
            formContainer.find("input[name='description']").val(json_response.url);
            formContainer.find("input[name='organization']").val(json_response.organization);
            formContainer.find("input[name='email']").val(json_response.email);
            formContainer.find("input[name='address']").val(json_response.address);
            formContainer.find("input[name='phone']").val(json_response.phone);
            formContainer.find("input[name='homepage']").val(json_response.website);
            formContainer.submit();
        },
        error: function(XMLHttpRequest, textStatus, errorThrown){

        }
    });
}