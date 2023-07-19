/**
 * Created by Mauriel on 2/9/2016.
 */

var radioPointSelector = 'input[type="radio"][value="point"]';
var radioBoxSelector = 'input[type="radio"][value="box"]';

function getErrorMessage(xhr) {
    let errorMsg = JSON.stringify(xhr.responseText);
    try {
        let errorMessageJSON = JSON.parse(xhr.responseText);
        if (errorMessageJSON.hasOwnProperty("error")) {
            errorMsg = errorMessageJSON.error;
        }
    } catch (e) {
        console.error(e);
    }
    return errorMsg
}

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
                        $("#btnOpenWithApp").attr("data-original-title", "Remove WebApp from 'Open With' list");
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
                         $("#btnOpenWithApp").attr("data-original-title", "Add WebApp to 'Open With' list");
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
        success: function (result) {
            var json_response = JSON.parse(result);
            if (json_response.status === 'success') {
                element.attr("disabled", false);
                if (action === "make_not_require_lic_agreement") {
                    element.closest("form").find("input[name='flag']").val("make_require_lic_agreement");
                    $("#hs-file-browser").attr("data-agreement", "false");
                    $("#btn-download-all").attr("href", $("#download-bag-btn").attr("href"));
                    $("#btn-download-all").removeAttr("data-toggle");
                }
                else {
                    element.closest("form").find("input[name='flag']").val("make_not_require_lic_agreement");
                    $("#hs-file-browser").attr("data-agreement", "true");
                    $("#btn-download-all").removeAttr("href");
                    $("#btn-download-all").attr("data-toggle", "modal");
                    $("#btn-download-all").attr("data-target", "#license-agree-dialog-bag");
                    $("#btn-download-all").attr("data-placement", "auto");
                }
            }
            else {
                element.attr("disabled", false);
                element.closest("form").append("<span class='label label-danger'><strong>Error: </strong>" + json_response.message + "</span>")
            }
        },
        error: function () {
            element.attr("disabled", false);
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

function handleIsDirty(json_response) {
    // show update netcdf file update option for NetCDFLogicalFile
    if (json_response.logical_file_type === "NetCDFLogicalFile" && json_response.is_update_file) {
        $("#div-netcdf-file-update").show();
    }
    // show update sqlite file update option for TimeSeriesLogicalFile
    if (json_response.logical_file_type === "TimeSeriesLogicalFile" &&
        json_response.is_update_file && json_response.can_update_sqlite) {
        $("#div-sqlite-file-update").show();
    }
}

function metadata_update_ajax_submit(form_id){
    let $alert_success = '<div class="alert alert-success" id="success-alert"> \
        <button type="button" class="close" data-dismiss="alert">x</button> \
        <strong>Success! </strong> \
        Metadata updated.\
    </div>';
    let $alert_error = '<div class="alert alert-danger" id="error-alert"> \
        <button type="button" class="close" data-dismiss="alert">x</button> \
        <strong>Error! </strong> \
        Metadata failed to update.\
    </div>';

    if (typeof metadata_update_ajax_submit.resourceSatusDisplayed == 'undefined'){
        metadata_update_ajax_submit.resourceSatusDisplayed = false;
    }

    var resourceType = RES_TYPE;
    let $form = $('#' + form_id);
    var formData = new FormData($form.get(0));
    if (form_id === "filetype-modelprogram") {
        // Attach file
        formData.append('file', $('input[type=file]')[0].files[0]);
    }

    // Disable button while request is being made
    var defaultBtnText = $form.find(".btn-form-submit").text();
    $form.find(".btn-form-submit").text("Saving changes...");
    $form.find(".btn-form-submit").addClass("disabled");

    $.ajax({
        type: "POST",
        url: $form.attr('action'),
        dataType: 'html',
        data: formData,
        contentType: false,
        processData: false,
        success: function(result) {
            /* The div contains now the updated form */
            let json_response = JSON.parse(result);
            if (json_response.status === 'success') {
                handleIsDirty(json_response);

                // dynamically update resource coverage when timeseries 'site' element gets updated or
                // file type 'coverage' element gets updated for composite resource
                if ((json_response.element_name.toLowerCase() === 'site' && resourceType === 'Time Series') ||
                    ((json_response.element_name.toLowerCase() === 'coverage' ||
                    json_response.element_name.toLowerCase() === 'site') && resourceType === 'Resource')){
                    const element_type = json_response.element_type?.toLowerCase() || '';
                    if (element_type === 'period' && json_response.hasOwnProperty('temporal_coverage')){
                        var temporalCoverage = json_response.temporal_coverage;
                        updateResourceTemporalCoverage(temporalCoverage);
                        // show/hide delete option for resource temporal coverage
                        setResourceTemporalCoverageDeleteOption();

                        if(resourceType === 'Resource' && json_response.has_logical_temporal_coverage) {
                             $("#btn-update-resource-temporal-coverage").show();
                        }
                        else {
                           $("#btn-update-resource-temporal-coverage").hide();
                        }
                    }

                    if (['box', 'point'].includes(element_type) && json_response.hasOwnProperty('spatial_coverage')) {
                        var spatialCoverage = json_response.spatial_coverage;
                        updateResourceSpatialCoverage(spatialCoverage);
                        if(resourceType === 'Resource' && json_response.has_logical_spatial_coverage) {
                            $("#btn-update-resource-spatial-coverage").show();
                        }
                        else {
                           $("#btn-update-resource-spatial-coverage").hide();
                        }
                        if(resourceType === 'Resource') {
                            // show/hide spatial coverage delete option for resource
                            setResourceSpatialCoverageDeleteOption();
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
                    let form_update_action = $form.attr('action');
                    let update_url;
                    if (!json_response.hasOwnProperty('form_action')){
                        let res_short_id = form_update_action.split('/')[3];
                        update_url = "/hsapi/_internal/" + res_short_id + "/"
                            + json_response.element_name + "/"
                            + json_response.element_id + "/update-metadata/";
                    }
                    else {
                        update_url = json_response.form_action
                    }

                    $form.attr('action', update_url);
                }

                if (json_response.element_name.toLowerCase() === 'coverage' &&
                    (json_response.logical_file_type === "FileSetLogicalFile" ||
                    json_response.logical_file_type === "GenericLogicalFile")) {
                    var bindCoordinatesPicker = false;
                    var logical_type = json_response.logical_file_type;
                    setFileTypeSpatialCoverageFormFields(logical_type, bindCoordinatesPicker);
                    setFileTypeTemporalCoverageDeleteOption(logical_type);
                }

                if (json_response.element_exists == false){
                    let form_update_action = $form.attr('action');
                    let res_short_id = form_update_action.split('/')[3];
                    let update_url = "/hsapi/_internal/" + res_short_id + "/" + json_response.element_name + "/add-metadata/";
                    $form.attr('action', update_url);
                }
                if (json_response.hasOwnProperty('element_name')){
                    if(json_response.element_name === 'title'){
                        let $res_title = $(".section-header").find("span").first();
                        let updated_title = $form.find("#id_value").val();
                        $res_title.text(updated_title);
                    }
                }

                showCompletedMessage(json_response);

                $('body > .main-container > .container').append($alert_success);
                $('#error-alert').each(function(){
                    this.remove();
                });
                $("#success-alert").fadeTo(2000, 500).fadeOut(1000, function(){
                    $(document).trigger("submit-success");
                    $("#success-alert").alert('close');
                });
                if((json_response.logical_file_type === "ModelInstanceLogicalFile" ||
                    json_response.logical_file_type === "ModelProgramLogicalFile") && json_response.refresh_metadata) {
                    showFileTypeMetadata(false, "");
                }
            }
            else{
                $alert_error = $alert_error.replace("Metadata failed to update.", json_response.message);
                $('#' + form_id).before($alert_error);
                $(".alert-error").fadeTo(2000, 500).slideUp(1000, function(){
                    $(".alert-error").alert('close');
                });
            }

            // Restore button
            $form.find(".btn-form-submit").text(defaultBtnText);
            $form.find(".btn-form-submit").removeClass("disabled");
        },
        error: function(XMLHttpRequest, textStatus, errorThrown) {
            var responseMessage = "Could not parse the error message";
            try{
                responseMessage = JSON.parse(XMLHttpRequest.responseText).message;
            } catch (Error){
            }
            var errMessage = "Metadata failed to update " + JSON.stringify(responseMessage);
            $alert_error = $alert_error.replace("Metadata failed to update.", errMessage);
            $('#' + form_id).before($alert_error);
            $(".alert-error").fadeTo(2000, 500).slideUp(1000, function(){
                $(".alert-error").alert('close');
            });

            // Restore button
            $form.find(".btn-form-submit").text(defaultBtnText);
            $form.find(".btn-form-submit").removeClass("disabled");
        }
    });
    //don't submit the form
    return false;
}

function showCompletedMessage(json_response) {
    if (json_response.hasOwnProperty('metadata_status')) {
        if (json_response.metadata_status !== $('#metadata-status').text()) {
            $('#metadata-status').text(json_response.metadata_status);
            let showMetaStatus = true;
            if (json_response.hasOwnProperty('show_meta_status')) {
                showMetaStatus = json_response.show_meta_status;
            }
            if (showMetaStatus) {
                let sufficient = json_response.metadata_status.toLowerCase().indexOf("insufficient") == -1;
                if (sufficient && manageAccessApp.canChangeResourceFlags) {
                    manageAccessApp.$data.canBePublicDiscoverable = true;
                    let resourceType = RES_TYPE;
                    let promptMessage = "";
                    if (resourceType === 'Resource')
                        promptMessage = "All required fields are completed. The resource can now be made discoverable " +
                            "or public. To permanently publish the resource and obtain a DOI, the resource " +
                            "must first be made public.";
                    else
                        promptMessage = "All required fields are completed. The " + resourceType.toLowerCase() +
                            " can now be made discoverable or public.";

                    if (!metadata_update_ajax_submit.resourceSatusDisplayed) {
                        metadata_update_ajax_submit.resourceSatusDisplayed = true;
                        const alertTitle = resourceType + " Status:"
                        if (json_response.hasOwnProperty('res_public_status')) {
                            if (json_response.res_public_status.toLowerCase() === "not public") {
                                // if the resource is already public no need to show the following alert message
                                customAlert(alertTitle, promptMessage, "success", 8000);
                            }
                        } else {
                            customAlert(alertTitle, promptMessage, "success", 8000);
                        }
                    }
                    $("#missing-metadata-or-file:not(.persistent)").fadeOut();
                    $("#missing-metadata-file-type:not(.persistent)").fadeOut();
                } else {
                    manageAccessApp.onMetadataInsufficient();
                }
            }
        }
    }
}

function makeTimeSeriesMetaDataElementFormReadOnly(form_id, element_id){
    var $element_selection_dropdown = $('#' + element_id + '_code_choices');
    if ($element_selection_dropdown.length && $element_selection_dropdown.attr('type') !== "hidden"){
        $('#' + form_id + ' :input').attr('readonly', 'readonly');
    }
}

function set_file_type_ajax_submit(url, folder_path) {
    var $alert_success = '<div class="alert alert-success" id="success-alert"> \
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
            $("#fb-inner-controls").before($alert_success);
            $("#success-alert").fadeTo(2000, 500).slideUp(1000, function(){
                $("#success-alert").alert('close');
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
    var $alert_success = '<div class="alert alert-success" id="success-alert"> \
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
            $("#fb-inner-controls").before($alert_success);
            $("#success-alert").fadeTo(2000, 500).slideUp(1000, function () {
                $("#success-alert").alert('close');
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

function getResourceMetadata() {
    return $.ajax({
        type: "POST",
        url: '/hsapi/_internal/' + SHORT_ID + '/get-metadata/',
        dataType: 'html',
        async: false,
        success: function (result) {
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            console.log(XMLHttpRequest, textStatus, errorThrown);
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
    $("#btn-add-keyword-filetype").toggleClass("disabled", true);    // Disable button during ajax
    $form = $('#id-keywords-filetype');
    // Data pre processing: trim keywords
    let subjects = $("#txt-keyword-filetype").val().split(",").map(function (d) {
        return d.trim()
    }).join(",");
    $("#txt-keyword-filetype").val(subjects);
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
                    $("#lst-tags-filetype").find(".icon-remove").click(onRemoveKeywordFileType);
                }
                // Refresh keywords field for the resource
                var resKeywords = json_response.resource_keywords;
                for (var i = 0; i < resKeywords.length; i++) {
                    if (resKeywords[i] != "") {
                        if ($.inArray(resKeywords[i].trim(), subjKeywordsApp.resKeywords) === -1) {
                            subjKeywordsApp.resKeywords.push(resKeywords[i].trim());
                        }
                    }
                }
                // show update netcdf file update option for NetCDFLogicalFile
                if (json_response.logical_file_type === "NetCDFLogicalFile"){
                    $("#div-netcdf-file-update").show();
                }
            }
            $("#btn-add-keyword-filetype").toggleClass("disabled", false);
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
    $("#id-update-netcdf-file").text("Updating...");
    $("#id-update-netcdf-file").attr("disabled", true);

    var url = $('#update-netcdf-file').attr("action");
    $.ajax({
        type: "POST",
        url: url,
        dataType: 'html',
        success: function (result) {
            let json_response = JSON.parse(result);
            if (json_response.status === 'success') {
                $("#div-netcdf-file-update").hide();
                customAlert("Success!", json_response.message, "success", 8000);
                showFileTypeMetadata(false, "");    // refetch file metadata to show the updated header file info
            }
            else {
                display_error_message("File update.", json_response.message);
            }
        }
    });
}
function updateModelInstanceMetaSchema() {
    var $alert_success = '<div class="alert alert-success" id="success-alert"> \
        <button type="button" class="close" data-dismiss="alert">x</button> \
        <strong>Success! </strong> \
        Schema update was successful.\
    </div>';

    var url = $("#btn-mi-schema-update").attr("data-schema-update-url");
    $.ajax({
        type: "POST",
        url: url,
        dataType: 'html',
        success: function (result) {
            json_response = JSON.parse(result);
            if (json_response.status === 'success') {
                $("#btn-mi-schema-update").hide();
                $("#div-invalid-schema-message").hide();
                $("#fb-inner-controls").before($alert_success);
                $("#success-alert").fadeTo(2000, 500).slideUp(1000, function () {
                    $("#success-alert").alert('close');
                });
                // refetch file metadata to show the updated information related to the schema
                showFileTypeMetadata(false, "");
            }
            else {
                display_error_message("Schema update failed.", json_response.message);
            }
        },
        error: function(xhr, errmsg, err){
            display_error_message('Schema update failed', xhr.responseText);
        }
    });
}

function update_sqlite_file_ajax_submit() {
    var $alert_success = '<div class="alert alert-success" id="success-alert"> \
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
                $("#success-alert").fadeTo(2000, 500).slideUp(1000, function () {
                    $("#success-alert").alert('close');
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
    var entry = $(obj).closest("div[data-contributor-type]").find("#user-deck > .hilight");
    if (entry.length < 1) {
        return false;
    }

    var userID = entry[0].getAttribute("data-value");
    url = url + userID + "/false";

    $.ajax({
        type: "POST",
        url: url,
        dataType: 'html',
        success: function (result) {
            var formContainer = $(obj).parent().parent();
            var json_response = JSON.parse(result);
            formContainer.find("input[name='name']").val(json_response.name);
            formContainer.find("input[name='hydroshare_user_id']").val(userID);
            formContainer.find("input[name='organization']").val(json_response.organization);
            formContainer.find("input[name='email']").val(json_response.email);
            formContainer.find("input[name='address']").val(json_response.address);
            formContainer.find("input[name='phone']").val(json_response.phone);
            formContainer.find("input[name='homepage']").val(json_response.website);

            for (var identifier in json_response.identifiers) {
                let modalBody = formContainer.find(".modal-body");
                modalBody.append(
                    $('<input />').attr('type', 'hidden')
                        .attr('name', "identifier_name")
                        .attr('value', identifier));

                modalBody.append(
                    $('<input />').attr('type', 'hidden')
                        .attr('name', "identifier_link")
                        .attr('value', json_response.identifiers[identifier]));
            }
            formContainer.submit();
        },
        error: function(XMLHttpRequest, textStatus, errorThrown){

        }
    });

    return true;
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

function delete_virtual_folder_ajax_submit(hs_file_type, file_type_id) {
    $(".file-browser-container, #fb-files-container").css("cursor", "progress");
    let url = '/hsapi/_internal/' + SHORT_ID + '/' + hs_file_type + '/' + file_type_id + '/delete-aggregation/';

    return $.ajax({
        type: "POST",
        url: url,
        async: true,
        success: function (result) {
        },
        error: function (xhr, errmsg, err) {
            display_error_message('Folder Deletion Failed', xhr.responseText);
        }
    });
}

function resetAfterFBDelete() {
    refreshFileBrowser();
    $("#fb-files-container li.ui-selected").css("cursor", "auto").removeClass("deleting");
    $(".file-browser-container, #fb-files-container").css("cursor", "auto");
    $(".fb-cust-spinner").remove();
}

function deleteRemainingFiles(filesToDelete) {
    // Add the data into the form and then serialize it because we need the csrf token
    $("#fb-delete-files-form input[name='file_ids']").val(filesToDelete);
    let data = $("#fb-delete-files-form").serialize();
    
    $.ajax({
        type: "POST",
        url: `/hsapi/_internal/${SHORT_ID}/delete-multiple-files/`,
        data: data,
    })
    .fail(function(e){
        console.log(e.responseText);
    })
    .always(function(){
        resetAfterFBDelete();
    });
}

function get_aggregation_folder_struct(aggregation) {
    let files = aggregation.files;
    $('#fb-files-container').empty();

    $.each(files, function (i, file) {
        $('#fb-files-container').append(getFileTemplateInstance(file));
    });

    onSort();
    bindFileBrowserItemEvents();
    updateSelectionMenuContext();
    setBreadCrumbs(jQuery.extend(true, {}, getCurrentPath()));   // Use a deep copy.
    updateNavigationState();
}

// This method is called to refresh the loader with the most recent structure after every other call
function get_irods_folder_struct_ajax_submit(res_id, store_path) {
    $("#fb-files-container, #fb-files-container").css("cursor", "progress");

    return $.ajax({
        type: "POST",
        url: '/hsapi/_internal/data-store-structure/',
        async: true,
        data: {
            res_id: res_id,
            store_path: store_path.path.join('/')
        },
        success: function (result) {
            var files = result.files;
            var folders = result.folders;
            var can_be_public = result.can_be_public;
            const mode = $("#hs-file-browser").attr("data-mode");

            $('#fb-files-container').empty();
            currentAggregations = result.aggregations.filter(function(agg) {
                return agg['logical_type'] !== "FileSetLogicalFile"; // Exclude FileSet aggregations
            });

            // Render each file. Aggregation files get loaded in memory instead.
            $.each(files, function (i, file) {
                // Check if the file belongs to an aggregation. Exclude FileSets and their files.
                if (file['logical_file_id'] && file['logical_type'] !== "GenericLogicalFile" && file['logical_type'] !== "FileSetLogicalFile"
                    && file['logical_type'] !== "ModelProgramLogicalFile" && file['logical_type'] !== "ModelInstanceLogicalFile") {
                    let selectedAgg = currentAggregations.filter(function (agg) {
                        return agg.logical_file_id === file['logical_file_id'] && agg.logical_type === file['logical_type'];
                    })[0];

                    if (!selectedAgg.hasOwnProperty('files')) {
                        selectedAgg.files = [];     // Initialize the array
                    }
                    selectedAgg.files.push(file);   // Push the aggregation files to the collection
                }
                else {
                    // Regular files
                    $('#fb-files-container').append(getFileTemplateInstance(file));
                }
            });

            // Display virtual folders for each aggregation.
            $.each(currentAggregations, function (i, agg) {
                $('#fb-files-container').append(getVirtualFolderTemplateInstance(agg));
            });

            // Display regular folders
            $.each(folders, function (i, folder) {
                $('#fb-files-container').append(getFolderTemplateInstance(folder));
            });

            // Default display message for empty directories
            if (!files.length && !folders.length) {
                if (mode === "edit") {
                    $('#fb-files-container').append(
                        '<div>' +
                            '<span class="text-muted fb-empty-dir has-space-bottom">This directory is empty</span>' +
                            '<div class="hs-upload-indicator text-center">' +
                                '<i class="fa fa-file" aria-hidden="true"></i>' +
                                '<h4>Drop files here or click "Add files" to upload</h4>' +
                            '</div>' +
                        '</div>'
                    );
                }
                else {
                    $('#fb-files-container').append(
                        '<span class="text-muted fb-empty-dir">This directory is empty</span>'
                    );
                }
            }

            if (can_be_public) {
                $("#missing-metadata-or-file:not(.persistent)").fadeOut();
            }

            onSort();
            bindFileBrowserItemEvents();
            pathLog[pathLogIndex] = store_path;
            $("#hs-file-browser").attr("data-res-id", res_id);
            setBreadCrumbs(jQuery.extend(true, {}, store_path));

            if ($("#hsDropzone").hasClass("dropzone")) {
                // If no multiple files allowed and a file already exists, disable upload
                var allowMultiple = $("#hs-file-browser").attr("data-allow-multiple-files") == "True";
                if (!allowMultiple && files.length > 0) {
                    $('.dz-input').hide();
                    $(".fb-upload-caption").toggleClass("hidden", true);
                    $(".upload-toggle").toggleClass("hidden", true);
                    $("#irods-group").toggleClass("hidden", true);
                }
                else {
                    $('.dz-input').show();
                    $(".fb-upload-caption").toggleClass("hidden", false);
                    $(".upload-toggle").toggleClass("hidden", false);
                    $("#irods-group").toggleClass("hidden", false);
                    Dropzone.forElement("#hsDropzone").files = [];
                }
            }

            updateNavigationState();
            updateSelectionMenuContext();
            $(".selection-menu").hide();
            $("#flag-uploading").remove();
            $("#fb-files-container, #fb-files-container").css("cursor", "default");
        },
        error: function(xhr, errmsg, err){
            $(".selection-menu").hide();
            $("#flag-uploading").remove();
            $("#fb-files-container, #fb-files-container").css("cursor", "default");
            $('#fb-files-container').empty();
            setBreadCrumbs(jQuery.extend(true, {}, store_path));
            $("#fb-files-container").prepend("<span>No files to display.</span>");
            updateSelectionMenuContext();
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
            $("#fb-files-container, #fb-files-container").css("cursor", "default");
        },
        error: function (xhr, errmsg, err) {
            let errorMsg = getErrorMessage(xhr)
            display_error_message('Folder Zipping Failed', errorMsg);
            $("#fb-files-container, #fb-files-container").css("cursor", "default");
        }
    });
}

function zip_by_aggregation_file_ajax_submit(res_id, aggregationPath, zipFileName) {
    $("#fb-files-container, #fb-files-container").css("cursor", "progress");
    return $.ajax({
        type: "POST",
        url: '/hsapi/_internal/zip-by-aggregation-file/',
        async: true,
        data: {
            res_id: res_id,
            aggregation_path: aggregationPath,
            output_zip_file_name: zipFileName
        },
        success: function (result) {
            $("#fb-files-container, #fb-files-container").css("cursor", "default");
        },
        error: function (xhr, errmsg, err) {
            let errorMsg = getErrorMessage(xhr)
            display_error_message('Folder Zipping Failed', errorMsg);
            $("#fb-files-container, #fb-files-container").css("cursor", "default");
        }
    });
}

function unzip_irods_file_ajax_submit(res_id, zip_with_rel_path, overwrite, unzip_to_folder) {
    $("#fb-files-container, #fb-files-container").css("cursor", "progress");
    return $.ajax({
        type: "POST",
        url: '/hsapi/_internal/data-store-folder-unzip/',
        async: true,
        data: {
            res_id: res_id,
            zip_with_rel_path: zip_with_rel_path,
            remove_original_zip: "false",
            overwrite: overwrite,
            unzip_to_folder: unzip_to_folder
        },
        success: function (task) {
            $('#unzip_res_id').val(res_id);
            $('#zip_with_rel_path').val(zip_with_rel_path);
            notificationsApp.registerTask(task);
            notificationsApp.show();
            $("#fb-files-container, #fb-files-container").css("cursor", "default");
        },
        error: function (xhr, errmsg, err) {
            let errorMsg = getErrorMessage(xhr)
            display_error_message('Folder Creation Failed', errorMsg);
            $("#fb-files-container, #fb-files-container").css("cursor", "default");
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
            $("#fb-alerts .upload-failed-alert").remove();
            var new_folder_rel_path = result.new_folder_rel_path;
            if (new_folder_rel_path.length > 0) {
                $('#create-folder-dialog').modal('hide');
                $("#txtFolderName").val("");
            }
            else {
                $('#create-folder-dialog').modal('hide');
            }
        },
        error: function(xhr, errmsg, err){
            let errorMsg = getErrorMessage(xhr)
            display_error_message('Folder Creation Failed', errorMsg);
            $('#create-folder-dialog').modal('hide');
        }
    });
}

function add_ref_content_ajax_submit(res_id, curr_path, ref_name, ref_url, validate_url_flag) {
    $("#fb-files-container, #fb-files-container").css("cursor", "progress");
    return $.ajax({
        type: "POST",
        url: '/hsapi/_internal/data-store-add-reference/',
        async: true,
        data: {
            res_id: res_id,
            curr_path: curr_path,
            ref_name: ref_name,
            ref_url: ref_url,
            validate_url_flag: validate_url_flag
        },
        success: function (result) {
            $('#add-reference-url-dialog').modal('hide');
            $('#validate-reference-url-dialog').modal('hide');
            $("#txtRefName").val("");
            $("#txtRefURL").val("");
            $("#ref_file_note").show();
        },
        error: function(xhr, errmsg, err) {
            if(validate_url_flag) {
                $('#add-reference-url-dialog').modal('hide');
                // display warning modal dialog
                $("#ref_name_passover").val(ref_name);
                $("#ref_url_passover").val(ref_url);
                $("#new_ref_url_passover").val('');
                $('#validate-reference-url-dialog').modal('show');
            }
            else {
                // Response text is not yet user friendly enough to display in UI
                display_error_message('Error', "Failed to add reference content.");
                $('#add-reference-url-dialog').modal('hide');
                $('#validate-reference-url-dialog').modal('hide');
            }
        }
    });
}

function update_ref_url_ajax_submit(res_id, curr_path, url_filename, new_ref_url, validate_url_flag) {
    $("#fb-files-container, #fb-files-container").css("cursor", "progress");
    return $.ajax({
        type: "POST",
        url: '/hsapi/_internal/data-store-edit-reference-url/',
        async: true,
        data: {
            res_id: res_id,
            curr_path: curr_path,
            url_filename: url_filename,
            new_ref_url: new_ref_url,
            validate_url_flag: validate_url_flag
        },
        success: function (result) {
            $('#validate-reference-url-dialog').modal('hide');
        },
        error: function (xhr, errmsg, err) {
            if (validate_url_flag) {
                // display warning modal dialog
                $("#ref_name_passover").val(url_filename);
                $("#ref_url_passover").val('');
                $("#new_ref_url_passover").val(new_ref_url);
                $('#validate-reference-url-dialog').modal('show');
            }
            else {
                // TODO: xhr.responseText not user friendly enough to display in the UI. Update once addressed.
                display_error_message('Error', 'Failed to edit referenced URL.');
                $('#validate-reference-url-dialog').modal('hide');
            }
        }
    });
}

// target_path must be a folder
function move_to_folder_ajax_submit(source_paths, target_path, file_override) {
    $("#fb-files-container, #fb-files-container").css("cursor", "progress");
    return $.ajax({
        type: "POST",
        url: '/hsapi/_internal/data-store-move-to-folder/',
        async: true,
        data: {
            res_id: SHORT_ID,
            source_paths: JSON.stringify(source_paths),
            target_path: target_path,
            file_override: file_override
        },
        success: function (result) {
            var target_rel_path = result.target_rel_path;
            if (target_rel_path.length > 0) {
                $("#fb-files-container li").removeClass("fb-cutting");
            }
        },
        error: function(xhr, errmsg, err){
            if (xhr.status == 300) {
                $('#resp-message').text(xhr.responseText);
                $("#source_paths").val(JSON.stringify(source_paths));
                $("#target_path").val(target_path);
                $('#move-override-confirm-dialog').modal('show');
            }
            else {
                display_error_message('File/Folder Moving Failed', xhr.responseText);
                $('#move-override-confirm-dialog').modal('hide');
            }
        }
    });
}

function move_virtual_folder_ajax_submit(hs_file_type, file_type_id, targetPath, file_override) {
    $("#fb-files-container, #fb-files-container").css("cursor", "progress");
    return $.ajax({
        type: "POST",
        url: '/hsapi/_internal/' + SHORT_ID + '/' + hs_file_type + '/' + file_type_id + '/move-aggregation/' + targetPath,
        data: {
            file_override: file_override
        },
        async: true,
        success: function (task) {
            notificationsApp.registerTask(task);
            notificationsApp.show();
            $("#fb-files-container, #fb-files-container").css("cursor", "default");
        },
        error: function(xhr, errmsg, err){
            if (xhr.status == 300) {
                $('#aggr-move-resp-message').text(xhr.responseText);
                $("#file_type").val(hs_file_type);
                $("#file_type_id").val(file_type_id);
                $("#target_path").val(targetPath);
                $('#move-aggr-override-confirm-dialog').modal('show');
            }
            else {
                display_error_message('File/Folder Moving Failed', xhr.responseText);
                $('#move-aggr-override-confirm-dialog').modal('hide');
            }
            $("#fb-files-container, #fb-files-container").css("cursor", "default");
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
            let errorMsg = getErrorMessage(xhr)
            display_error_message('File/Folder Renaming Failed', errorMsg);
        }
    });
}

// prefixes must be the same on source_path and target_path
function rename_virtual_folder_ajax_submit(fileType, fileTypeId, newName) {
    let url = '/hsapi/_internal/' + fileType + '/' + fileTypeId + '/update-filetype-dataset-name/';
    $("#fb-files-container, #fb-files-container").css("cursor", "progress");

    return $.ajax({
        type: "POST",
        url: url,
        async: true,
        data: {
            dataset_name: newName,
        },
        success: function (response) {
            handleIsDirty(response);
        },
        error: function(xhr, errmsg, err){
            display_error_message('Failed to rename aggregation', xhr.responseText);
        }
    });
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

function deleteFileTypeSpatialCoverage(url, deleteButton) {
    $.ajax({
        type: "POST",
        url: url,
        dataType: 'html',
        success: function (result) {
            var json_response = JSON.parse(result);
            if (json_response.status === 'success') {
                deleteButton.hide();
                // set the spatial coverage form url to add metadata
                var $form = deleteButton.closest('form');
                var logicalFileType = json_response.logical_file_type;
                var logicalFileID = json_response.logical_file_id;
                var addMetadataURL = "/hsapi/_internal/" + logicalFileType + "/" + logicalFileID +  "/coverage/add-file-metadata/";
                $form.attr('action', addMetadataURL);
                // remove coverage data from the coverage text fields
                $("#id_northlimit_filetype").val("");
                $("#id_eastlimit_filetype").val("");
                $("#id_southlimit_filetype").val("");
                $("#id_westlimit_filetype").val("");
                $("#id_north_filetype").val("");
                $("#id_east_filetype").val("");
                if(json_response.has_logical_spatial_coverage) {
                    $("#btn-update-resource-spatial-coverage").show();
                }
                else {
                   $("#btn-update-resource-spatial-coverage").hide();
                }
            }
            else {
                display_error_message("Failed to delete spatial coverage for content type.", json_response.message);
            }
        }
    });
}

function deleteFileTypeTemporalCoverage(url, deleteButton) {
    $.ajax({
        type: "POST",
        url: url,
        dataType: 'html',
        success: function (result) {
            var json_response = JSON.parse(result);
            if (json_response.status === 'success') {
                deleteButton.hide();
                // set the temporal coverage form url to add metadata
                var $form = deleteButton.closest('form');
                var logicalFileType = json_response.logical_file_type;
                var logicalFileID = json_response.logical_file_id;
                var addMetadataURL = "/hsapi/_internal/" + logicalFileType + "/" + logicalFileID +  "/coverage/add-file-metadata/";
                $form.attr('action', addMetadataURL);
                // remove coverage data from the coverage text fields
                $("#id_start_filetype").val("");
                $("#id_end_filetype").val("");

                if(json_response.has_logical_temporal_coverage) {
                     $("#btn-update-resource-temporal-coverage").show();
                }
                else {
                   $("#btn-update-resource-temporal-coverage").hide();
                }
            }
            else {
                display_error_message("Failed to delete temporal coverage for content type.", json_response.message);
            }
        }
    });
}

function BindKeyValueFileTypeClickHandlers(){
    // bind key value add modal form OK button click event
    var keyvalue_add_modal_form = $("#fileTypeMetaData").find('#add-keyvalue-filetype-metadata');
    keyvalue_add_modal_form.find("button.btn-primary").click(function () {
        addFileTypeExtraMetadata();
    });
    
    // clear the form on cancel
    keyvalue_add_modal_form.find("button.btn-default:contains('Cancel')").click(function () {
        keyvalue_add_modal_form.find("input[type=text], textarea").val("");
    });

    // bind all key value edit modal forms OK button click event
    $("#fileTypeMetaData").find('[id^=edit-keyvalue-filetype-metadata]').each(function(){
        var formId = $(this).attr('id');
        $(this).find("button.btn-primary").click(function (){
            updateFileTypeExtraMetadata(formId);
        });

        // reset the form on cancel
        $(this).find("button.btn-default:contains('Cancel')").click(function() {
            $(this).closest('form').find("input[type=text], textarea").each(function(){
                $(this).val($(this).prop("defaultValue"));
            });
        });
    });

    // bind all key value delete modal forms Delete button click event
    $("#fileTypeMetaData").find('[id^=delete-keyvalue-filetype-metadata]').each(function(){
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
        var dateString = null;
        var pickerDate = null;
        if($(this).attr('data-date')){
            // resource temporal date picker
            dateString = $(this).attr("data-date").split("-");
        }
        else{
            // file type temporal date picker
            if($(this).attr('value')){
                dateString = $(this).attr("value").split("-");
            }
        }
        if(dateString != null) {
            pickerDate = new Date(dateString);
        }
        if(pickerDate != null){
            $(this).datepicker("setDate", pickerDate);
        }
    });

    // Temporal coverage: only allow submit if both dates are completed
    let temporal_button = $("#coverage-temporal button");
    let temporal_warn = $('#temporal-warn');
    if (temporal_warn.length === 0) {
        temporal_warn = $("<em>", {
            id: "temporal-warn",
            text: "Both a Start Date and End Date are required when providing temporal information",
            css: {
                "font-style": "italic",
                "color": "red"
            }
        });
        temporal_button.closest('div').before(temporal_warn);
    }
    temporal_warn.hide();

    $("#coverage-temporal .dateinput").each(function () {
        $(this).on('change', function (e) {
            let this_date = $(this)
            let other_date = $(this).closest("form").find(".form-control").not(this).first();
            if (this_date.val() && other_date.val()) {
                temporal_button.removeClass("disabled");
                temporal_warn.hide();
            }else if (this_date.val()) {
                temporal_button.addClass("disabled");
                other_date.after(temporal_warn);
                temporal_warn.show();
            }else if (other_date.val()) {
                temporal_button.addClass("disabled");
                this_date.after(temporal_warn);
                temporal_warn.show();
            }else{
                temporal_button.hide()
                temporal_warn.hide()
            }
        });
    });
}

function updateEditCoverageStateFileType() {
    // Set state for file type/aggregation spatial coverage metadata editing
    var $radioBox = $("#id-coverage-spatial-filetype").find(radioBoxSelector);

    if ($radioBox.prop("checked")) {
        $("#id-coverage-spatial-filetype").attr("data-coordinates-type", "rectangle");
    }
    else {
        $("#id-coverage-spatial-filetype").attr("data-coordinates-type", "point");
    }

    if ($radioBox.prop("checked")) {
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

// set form fields for spatial coverage for aggregation/file type
function setFileTypeSpatialCoverageFormFields(logical_type, bindCoordinatesPicker) {
    if (logical_type !== "ModelProgramLogicalFile") {

        var $id_type_filetype_div = $("#id_type_filetype");

        if (logical_type !== "GenericLogicalFile" && logical_type !== "FileSetLogicalFile" &&
            logical_type !== "ModelInstanceLogicalFile") {
            // don't allow changing coverage type if aggregation type is not GenericLogicalFile or
            // FileSetLogicalFile or ModelInstanceLogicalFile
            $id_type_filetype_div.parent().closest("div").css('pointer-events', 'none');
            $id_type_filetype_div.find(radioBoxSelector).attr('onclick', 'return false');
            $id_type_filetype_div.find(radioPointSelector).attr('onclick', 'return false');

            var selectBoxTypeCoverage = false;
            if ($id_type_filetype_div.find(radioBoxSelector).attr("checked") === "checked" ||
                logical_type === "NetCDFLogicalFile" || logical_type === "GeoRasterLogicalFile") {
                selectBoxTypeCoverage = true;
            }
            if (selectBoxTypeCoverage) {
                $id_type_filetype_div.find(radioPointSelector).attr('disabled', true);
                $id_type_filetype_div.find(radioPointSelector).parent().closest("label").addClass("text-muted");
            } else {
                $id_type_filetype_div.find(radioBoxSelector).attr('disabled', true);
                $id_type_filetype_div.find(radioBoxSelector).parent().closest("label").addClass("text-muted");
            }

            if (logical_type === "NetCDFLogicalFile" || logical_type === "GeoRasterLogicalFile") {
                // set box type coverage checked
                $id_type_filetype_div.find(radioBoxSelector).attr('checked', 'checked');

                // enable spatial coordinate picker (google map interface)
                $("#id-spatial-coverage-file-type").attr('data-coordinates-type', 'rectangle');
                $("#id-spatial-coverage-file-type").coordinatesPicker();
                $("#id-origcoverage-file-type").attr('data-coordinates-type', 'rectangle');
                $("#id-origcoverage-file-type").coordinatesPicker();
            }
        } else {
            // file type is "GenericLogicalFile" or "FileSetLogicalFile or ModelProgramLogicalFile or ModelInstanceLogicalFile"
            // allow changing coverage type
            // provide option to delete spatial coverage at the aggregation level
            $id_type_filetype_div.find("input:radio").change(updateEditCoverageStateFileType);
            var onSpatialCoverageDelete = function () {
                var $btnDeleteSpatialCoverage = $("#id-btn-delete-spatial-filetype");
                $btnDeleteSpatialCoverage.show();
                var formSpatialCoverage = $btnDeleteSpatialCoverage.closest('form');
                var url = formSpatialCoverage.attr('action');
                url = url.replace('update-file-metadata', 'delete-file-coverage');
                $btnDeleteSpatialCoverage.unbind('click');
                $btnDeleteSpatialCoverage.click(function () {
                    deleteFileTypeSpatialCoverage(url, $btnDeleteSpatialCoverage);

                })
            };

            var addSpatialCoverageLink = function () {
                var $spatialForm = $("#id-coverage-spatial-filetype");
                var deleteLink = '<a id="id-btn-delete-spatial-filetype" type="button" style="display: block;" class="pull-right"><span class="glyphicon glyphicon-trash icon-button btn-remove"></span>';
                $spatialForm.find('legend').html('Spatial Coverage' + deleteLink);
                $btnDeleteSpatialCoverage = $("#id-btn-delete-spatial-filetype");
                return $btnDeleteSpatialCoverage;
            };
            // set spatial form attribute 'data-coordinates-type' to point or rectangle
            if ($id_type_filetype_div.find(radioBoxSelector).attr("checked") === "checked") {
                $("#id-coverage-spatial-filetype").attr('data-coordinates-type', 'rectangle');
            } else {
                $("#id-coverage-spatial-filetype").attr('data-coordinates-type', 'point');
            }
            // check if spatial coverage exists
            var $btnDeleteSpatialCoverage = $("#id-btn-delete-spatial-filetype");
            if (!$btnDeleteSpatialCoverage.length) {
                // delete option doesn't exist
                $btnDeleteSpatialCoverage = addSpatialCoverageLink();
            }
            var formSpatialCoverage = $btnDeleteSpatialCoverage.closest('form');
            var url = formSpatialCoverage.attr('action');
            if (url.indexOf('update-file-metadata') !== -1) {
                onSpatialCoverageDelete();
            } else {
                $btnDeleteSpatialCoverage.hide()
            }
            if (bindCoordinatesPicker) {
                $("#id-coverage-spatial-filetype").coordinatesPicker();
            }
        }

        // #id_type_1 is the box radio button
        if ($id_type_filetype_div.find(radioBoxSelector).attr("checked") === "checked" ||
            (logical_type !== 'GeoFeatureLogicalFile' && logical_type !== 'RefTimeseriesLogicalFile' &&
                logical_type !== 'GenericLogicalFile' && logical_type !== "FileSetLogicalFile"
                && logical_type !== "ModelProgramLogicalFile" && logical_type !== "ModelInstanceLogicalFile")) {
            // coverage type is box or logical file type is either NetCDF or TimeSeries
            $("#id_north_filetype").parent().closest("#div_id_north").hide();
            $("#id_east_filetype").parent().closest("#div_id_east").hide();
        } else {
            // coverage type is point
            $("#id_northlimit_filetype").parent().closest("#div_id_northlimit").hide();
            $("#id_eastlimit_filetype").parent().closest("#div_id_eastlimit").hide();
            $("#id_southlimit_filetype").parent().closest("#div_id_southlimit").hide();
            $("#id_westlimit_filetype").parent().closest("#div_id_westlimit").hide();
        }
    }
}

// updates the UI spatial coverage elements for resource
function updateResourceSpatialCoverage(spatialCoverage) {
    if ($("#id-coverage-spatial").length) {
        spatial_coverage_type = spatialCoverage.type;
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
        var $point_radio = $("#id_type_2");
        var $box_radio = $("#id_type_1");
        var resourceType = RES_TYPE;
        $("#id_name").val(spatialCoverage.name);
        if (spatialCoverage.type === 'point') {
            $point_radio.attr('checked', 'checked');
            if(resourceType !== "Resource"){
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
            if(resourceType !== "Resource"){
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

function addFileTypeTemporalCoverageDeleteLink() {
    var $temporalForm = $("#id-coverage-temporal-file-type");
    var deleteLink = '<a id="id-btn-delete-temporal-filetype" type="button" style="display: block;" class="pull-right"><span class="glyphicon glyphicon-trash icon-button btn-remove"></span>';
    $temporalForm.find('legend').html('Temporal Coverage' + deleteLink);
    var $btnDeleteTemporalCoverage = $("#id-btn-delete-temporal-filetype");
    return $btnDeleteTemporalCoverage;
}

function setFileTypeTemporalCoverageDeleteOption(logicalFileType) {
    // show/hide delete option for temporal coverage at aggregation level
    if(logicalFileType !== "ModelProgramLogicalFile") {
        var $btnDeleteTemporalCoverage = $("#id-btn-delete-temporal-filetype");
        if (!$btnDeleteTemporalCoverage.length) {
            // delete option doesn't exist - so add it
            $btnDeleteTemporalCoverage = addFileTypeTemporalCoverageDeleteLink();
        }

        var $formTemporalCoverage = $btnDeleteTemporalCoverage.closest('form');
        if (logicalFileType === 'GenericLogicalFile' || logicalFileType === 'FileSetLogicalFile' ||
            logicalFileType === 'ModelInstanceLogicalFile') {
            var url = $formTemporalCoverage.attr('action');
            if (url.indexOf('update-file-metadata') !== -1) {
                url = url.replace('update-file-metadata', 'delete-file-coverage');
                $btnDeleteTemporalCoverage.unbind('click');
                $btnDeleteTemporalCoverage.show();
                $btnDeleteTemporalCoverage.click(function () {
                    deleteFileTypeTemporalCoverage(url, $btnDeleteTemporalCoverage);
                })
            } else {
                $btnDeleteTemporalCoverage.hide()
            }
        } else {
            $btnDeleteTemporalCoverage.hide()
        }
    }
}

// updates the UI temporal coverage elements for the resource
function updateResourceTemporalCoverage(temporalCoverage) {
    var $form = $("#id-coverage-temporal");
    var form_update_action = $form.attr('action');
    var res_short_id = form_update_action.split('/')[3];
    var update_url;
    if($.isEmptyObject(temporalCoverage)) {
        $("#id_start").val("");
        $("#id_start").attr('data-date', "");
        $("#id_end").val("");
        $("#id_end").attr('data-date', "");
        update_url = "/hsapi/_internal/" + res_short_id + "/coverage/add-metadata/";
    }
    else {
        $("#id_start").val(temporalCoverage.start);
        $("#id_start").attr('data-date', temporalCoverage.start);
        $("#id_end").val(temporalCoverage.end);
        $("#id_end").attr('data-date', temporalCoverage.end);
        update_url = "/hsapi/_internal/" + res_short_id + "/coverage/" + temporalCoverage.element_id + "/update-metadata/";
    }
    $form.attr('action', update_url);

    $("#id-coverage-temporal").find("button.btn-primary").hide();
    initializeDatePickers();
}

// updates the UI spatial coverage elements for the aggregation
function updateAggregationSpatialCoverageUI(spatialCoverage, logicalFileType, logicalFileID, elementID) {
    var $id_type_div = $("#id_type_filetype");
    var $point_radio = $id_type_div.find(radioPointSelector);
    var $box_radio = $id_type_div.find(radioBoxSelector);
    // show the button to delete spatial coverage
    var $btnDeleteSpatialCoverage = $("#id-btn-delete-spatial-filetype");
    var $formSpatialCoverage = $btnDeleteSpatialCoverage.closest('form');
    $btnDeleteSpatialCoverage.show();
    // set the coverage form action to update metadata url
    var updateAction = "/hsapi/_internal/" + logicalFileType + "/" + logicalFileID + "/coverage/" + elementID + "/update-file-metadata/";
    $formSpatialCoverage.attr('action', updateAction);
    var coverageDeleteURL = updateAction.replace('update-file-metadata', 'delete-file-coverage');
    // set a new click event handler for the spatial coverage delete
    $btnDeleteSpatialCoverage.unbind('click');
    $btnDeleteSpatialCoverage.click(function () {
        deleteFileTypeSpatialCoverage(coverageDeleteURL, $btnDeleteSpatialCoverage);
    });
    if (spatialCoverage.type === 'point') {
        $point_radio.attr('checked', 'checked');
        $("#id_north_filetype").val(spatialCoverage.north);
        $("#id_east_filetype").val(spatialCoverage.east);
        $("#id_north_filetype").parent().closest("#div_id_north").show();
        $("#id_east_filetype").parent().closest("#div_id_east").show();
        $("#id_northlimit_filetype").parent().closest("#div_id_northlimit").hide();
        $("#id_eastlimit_filetype").parent().closest("#div_id_eastlimit").hide();
        $("#id_southlimit_filetype").parent().closest("#div_id_southlimit").hide();
        $("#id_westlimit_filetype").parent().closest("#div_id_westlimit").hide();
    }
    else {
        $box_radio.attr('checked', 'checked');
        $("#id_eastlimit_filetype").val(spatialCoverage.eastlimit);
        $("#id_northlimit_filetype").val(spatialCoverage.northlimit);
        $("#id_westlimit_filetype").val(spatialCoverage.westlimit);
        $("#id_southlimit_filetype").val(spatialCoverage.southlimit);
        $("#id_northlimit_filetype").parent().closest("#div_id_northlimit").show();
        $("#id_eastlimit_filetype").parent().closest("#div_id_eastlimit").show();
        $("#id_southlimit_filetype").parent().closest("#div_id_southlimit").show();
        $("#id_westlimit_filetype").parent().closest("#div_id_westlimit").show();
        $("#id_north_filetype").parent().closest("#div_id_north").hide();
        $("#id_east_filetype").parent().closest("#div_id_east").hide();
    }
    initMapFileType();
}

// updates the UI temporal coverage elements for the aggregation
function updateAggregationTemporalCoverage(temporalCoverage, logicalFileType, logicalFileID, coverageElementID) {
    $("#id_start_filetype").val(temporalCoverage.start);
    $("#id_end_filetype").val(temporalCoverage.end);

    $("#id-coverage-temporal").find("button.btn-primary").hide();
    var updateAction = "/hsapi/_internal/" + logicalFileType + "/" + logicalFileID + "/coverage/" + coverageElementID + "/update-file-metadata/";
    var $btnDeleteTemporalCoverage = $("#id-btn-delete-temporal-filetype");
    if(!$btnDeleteTemporalCoverage.length) {
        // delete option doesn't exist - so add it
        $btnDeleteTemporalCoverage = addFileTypeTemporalCoverageDeleteLink();
    }
    var $formTemporalCoverage = $btnDeleteTemporalCoverage.closest('form');
    $formTemporalCoverage.attr('action', updateAction);
    setFileTypeTemporalCoverageDeleteOption(logicalFileType);

    initializeDatePickers();
}

function setFileTypeMetadataFormsClickHandlers(){
    $("#fileTypeMetaData").find('form').each(function () {
        var formId = $(this).attr('id');
        if (formId !== "update-netcdf-file" && formId !== "update-sqlite-file"&& formId !== "id-keywords-filetype" && formId !== "add-keyvalue-filetype-metadata") {
              $(this).find("button.btn-primary").click(function () {
                metadata_update_ajax_submit(formId);
              });
        }
    });
    BindKeyValueFileTypeClickHandlers();
}

function updateResourceAuthors(authors) {
    leftHeaderApp.$data.authors = authors.map(function(author) {
        return {
            name: author.name,
            address: author.address,
            email: author.email,
            id: author.id.toString(),
            identifiers: author.identifiers,
            order: author.order.toString(),
            organization: author.organization,
            phone: author.phone,
            profileUrl: author.relative_uri,
            homepage: author.homepage,
        };
    })
}
