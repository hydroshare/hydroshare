/**
* Created by Mauriel on 3/9/2017.
*/

function onRoleSelect(event) {
    var el = $(event.target);
    $("#selected_role").text(el.text());
    $("#selected_role")[0].setAttribute("data-role", el[0].getAttribute("data-role"));
}

// Toggles pointer events on and off for the access control interface
function setPointerEvents(flag) {
    if (!flag) {
        // Disable pointer events
        $(".access-table").css("pointer-events", "none");
        $("#manage-access .modal-content").css("pointer-events", "none");
    }
    else {
        // Enable pointer events
        $(".access-table").css("pointer-events", "auto");
        $("#manage-access .modal-content").css("pointer-events", "auto");
    }
}

// Enables and disables granting access buttons accordingly to the current access level
function updateActionsState(privilege){
    // Set the state of dropdown menu items and remove buttons to false by default
    $("form[data-access-type]").parent().addClass("disabled");
    $("#list-roles a[data-role]").parent().addClass("disabled");
    $(".access-table li.active[data-access-type]").closest("tr").addClass("hide-actions");

    if (privilege == "view") {
        // Dropdown menu items
        $("form[data-access-type='Can view']").parent().removeClass("disabled");
        $("#list-roles a[data-role='view']").parent().removeClass("disabled");

        // Remove buttons
        $(".access-table li.active[data-access-type='Can view']").closest("tr").removeClass("hide-actions");
    }
    else if(privilege == "change") {
        // Dropdown menu items
        $("form[data-access-type='Can view']").parent().removeClass("disabled");
        $("#list-roles a[data-role='view']").parent().removeClass("disabled");

        $("form[data-access-type='Can edit']").parent().removeClass("disabled");
        $("#list-roles a[data-role='edit']").parent().removeClass("disabled");

        // Remove buttons
        $(".access-table li.active[data-access-type='Can view']").closest("tr").removeClass("hide-actions");
        $(".access-table li.active[data-access-type='Can edit']").closest("tr").removeClass("hide-actions");
    }
    else if(privilege == "owner") {
        // Dropdown menu items
        $("form[data-access-type='Can view']").parent().removeClass("disabled");
        $("#list-roles a[data-role='view']").parent().removeClass("disabled");

        $("form[data-access-type='Can edit']").parent().removeClass("disabled");
        $("#list-roles a[data-role='edit']").parent().removeClass("disabled");

        $("form[data-access-type='Is owner']").parent().removeClass("disabled");
        $("#list-roles a[data-role='owner']").parent().removeClass("disabled");

        // Remove buttons
        $(".access-table li.active[data-access-type='Can view']").closest("tr").removeClass("hide-actions");
        $(".access-table li.active[data-access-type='Can edit']").closest("tr").removeClass("hide-actions");
        if ($(".access-table li.active[data-access-type='Is owner']").length > 1) {     // At least one owner constrain
            $(".access-table li.active[data-access-type='Is owner']").closest("tr").removeClass("hide-actions");
        }
    }
}

function onRemoveKeyword(event) {
    $(event.target).closest(".tag").remove();
    updateKeywords();
    metadata_update_ajax_submit('id-subject');
    $("#id-keywords-msg").hide();
}

function onAddKeyword(event) {
    var keyword = $("#txt-keyword").val();
    keyword = keyword.split(",");
    var existsNewKeywords = false;
    for (var i = 0; i < keyword.length; i++) {
        keyword[i] = keyword[i].trim(); // Remove leading and trailing whitespace
        var exists = false;
        // Check if the keyword already exists
        for (var x = 0; x < $("#lst-tags").find(".tag > span").length; x++) {
            if ($($("#lst-tags").find(".tag > span")[x]).text().toLowerCase() == keyword[i].toLowerCase()) {
                exists = true;
            }
        }
        if (exists){
            $("#id-keywords-msg").show();
        }
        else {
            $("#id-keywords-msg").hide();
        }
        // If does not exist, add it
        if (!exists && keyword[i] != "" && keyword[i].length <= 100) {
            var li = $("<li class='tag'><span></span></li>");
            li.find('span').text(keyword[i]);
            li.append('&nbsp;<a><span class="glyphicon glyphicon-remove-circle icon-remove"></span></a>');
            $("#lst-tags").append(li);

            $(".icon-remove").click(onRemoveKeyword);
            updateKeywords();
            existsNewKeywords = true;
        }
    }

    $("#txt-keyword").val("");  // Clear text input
    if(existsNewKeywords){
        metadata_update_ajax_submit('id-subject');
    }
}

function updateKeywords() {
    var keywords = "";
    var count = $("#lst-tags").find(".tag > span").length;
    for (var x = 0; x < count; x++) {
        keywords += $($("#lst-tags").find(".tag > span")[x]).text();
        if (x != count - 1) {
            keywords += ",";
        }
    }

    $("#id-subject").find("#id_value").val(keywords);
}

// function for adding keywords associated with file type
function onAddKeywordFileType(event) {
    var keyword = $("#txt-keyword-filetype").val();
    keyword = keyword.split(",");
    var existsNewKeywords = false;
    for (var i = 0; i < keyword.length; i++) {
        keyword[i] = keyword[i].trim(); // Remove leading and trailing whitespace
        var exists = false;
        // Check if the keyword already exists
        for (var x = 0; x < $("#lst-tags-filetype").find(".tag > span").length; x++) {
            if ($($("#lst-tags-filetype").find(".tag > span")[x]).text().toLowerCase() == keyword[i].toLowerCase()) {
                exists = true;
                break;
            }
        }
        if (exists) {
            $("#id-keywords-filetype-msg").show();
        }
        else {
            $("#id-keywords-filetype-msg").hide();
        }
        // If does not exist, add it
        if (!exists && keyword[i] != "" && keyword[i].length <= 100) {
            existsNewKeywords = true;
        }
    }

    if(existsNewKeywords) {
        filetype_keywords_update_ajax_submit();
        $("#txt-keyword-filetype").val("");  // Clear text input
    }
}

// function for deleteing keywords associated with file type
function onRemoveKeywordFileType(event) {
    var tag = $(event.target).closest(".tag");
    var keyword = tag.find('span').text();
    filetype_keyword_delete_ajax_submit(keyword, tag);
    $("#id-keywords-filetype-msg").hide();
}

function customAlert(msg, duration) {
    var el = document.createElement("div");
    var top = 200;
    var left = ($(window).width() / 2) - 150;
    var style = "top:" + top + "px;left:" + left + "px";
    el.setAttribute("style", style);
    el.setAttribute("class", "custom-alert");
    el.innerHTML = msg;
    setTimeout(function () {
        $(el).fadeOut(300, function () {
            $(this).remove();
        });
    }, duration);
    document.body.appendChild(el);
    $(el).hide().fadeIn(400);
}

function showAddEditExtraMetaPopup(edit, row_id_str) {
    $("#edit_extra_meta_row_id").val('');
    $("#old_extra_meta_name").val('');
    $("#extra_meta_name_input").val('');
    $("#extra_meta_value_input").val('');
    if (edit) {
        var t = $('#extraMetaTable').DataTable();
        var row_to_edit = t.row("#" + row_id_str);
        var oldname = row_to_edit.data()[0];
        var oldvalue = row_to_edit.data()[1];
        $("#edit_extra_meta_row_id").val(row_id_str);
        $("#old_extra_meta_name").val(oldname);
        $("#extra_meta_name_input").val(oldname);
        $("#extra_meta_value_input").val(oldvalue);
        $("#extra_meta_title").text("Edit Extended Metadata");
    }
    else {
        $("#extra_meta_title").text("Add Extended Metadata");
    }
    $('#extraMetaDialog').modal('show');
}


function addEditExtraMeta2Table() {
    $("#extra_meta_msg").hide();
    var t = $('#extraMetaTable').DataTable();
    var extra_meta_name = $("#extra_meta_name_input").val().trim();
    var extra_meta_value = $("#extra_meta_value_input").val().trim();
    var edit_extra_meta_row_id = $("#edit_extra_meta_row_id").val().trim();

    if(extra_meta_name.length==0 || extra_meta_value.length==0) {
        $("#extra_meta_msg").html("<font color='red'>Both name and value are required fields that cannot be left blank.</font>");
        $("#extra_meta_msg").show();
        return;
    }

    if(foundDuplicatedName(t, extra_meta_name, edit_extra_meta_row_id)) {
        $("#extra_meta_msg").html("<font color='red'>The name already exists. Please input a different name.</font>");
        $("#extra_meta_msg").show();
        return;
    }

    if (edit_extra_meta_row_id == "") {
        // Add new
        var new_row_id_0_base = findMaxRowID(t) + 1;
        var edit_icon_str = '<span data-arg="' + new_row_id_0_base + '" class="btn-edit-icon glyphicon glyphicon-edit btn-inline-favorite"></span>';
        var remove_icon_str = '<span data-arg="' + new_row_id_0_base + '" class="btn-remove-icon glyphicon glyphicon-remove btn-inline-favorite"></span>';
        var row_ele = t.row.add( [extra_meta_name,extra_meta_value, edit_icon_str+" "+remove_icon_str]).node();
        $(row_ele).attr( 'id', new_row_id_0_base);
    }
    else {
        // Edit existing
        var row_to_edit = t.row("#" + edit_extra_meta_row_id);
        var updated_data_array = row_to_edit.data();
        updated_data_array[0] = extra_meta_name;
        updated_data_array[1] = extra_meta_value;
        row_to_edit.data(updated_data_array);
    }
    t.rows().invalidate().draw();
    $("#extraMetaTable").find("td:nth-child(2)").each(function() {
        $(this).urlClickable();
    });

    $('#extraMetaDialog').modal('hide');
    $('#save-extra-meta-btn').show();

    // Bind click events
    $(".btn-edit-icon").click(function() {
        var arg = $(this).attr("data-arg");
        showAddEditExtraMetaPopup(true, arg);
    });

    $(".btn-remove-icon").click(function() {
        var arg = $(this).attr("data-arg");
        removeExtraMetadataFromTable(arg);
    });
}

function findMaxRowID(table)
{
    var max_id = -1;
    table.rows(). every(function ( rowIdx, tableLoop, rowLoop ) {
        if(parseInt(this.node().id) > max_id)
        {
           max_id = parseInt(this.node().id);
        }
    });
    return max_id;
}

function foundDuplicatedName(table, newName, except_row_id)
{
    var found_first_duplicated = false;
    var first_duplicated_row_id = -1;

    table.rows(). every(function ( rowIdx, tableLoop, rowLoop ) {
        if(this.node().id != except_row_id) {
            if (this.data()[0]==newName) {
               found_first_duplicated = true;
               first_duplicated_row_id = this.node().id;
            }
        }
    });
    return found_first_duplicated;
}

function saveExtraMetadata()
{
    $alert_success_extra_meta = "<i class='glyphicon glyphicon-flag custom-alert-icon'></i><strong>Success:</strong> Extended metadata updated";
    $alert_error_extra_meta = "<i class='glyphicon glyphicon-flag custom-alert-icon'></i><strong>Error:</strong> Extended metadata failed to update";

    var json_obj = {};
    var t = $('#extraMetaTable').DataTable();
    t.rows(). every(function ( rowIdx, tableLoop, rowLoop ) {
        var extra_meta_name = this.data()[0].trim();
        var extra_meta_value = $("<div/>").html(this.data()[1].trim()).text();
        json_obj[extra_meta_name] = extra_meta_value;
    });

    var json_str = JSON.stringify(json_obj);
    json_obj = JSON.parse(json_str);
    var shortID = $("#short-id").val();
    var update_key_value_metadata_url = "/hsapi/_internal/" + shortID + "/update-key-value-metadata/";
    $.ajax({
        type: "POST",
        url: update_key_value_metadata_url,
        dataType: "json",
        data: json_obj,

        success: function(result) {
            json_response = result;
            if (json_response.status === 'success') {
                 $('#save-extra-meta-btn').hide();
                 customAlert($alert_success_extra_meta, 3000);
                if(json_response.is_dirty) {
                    $('#netcdf-file-update').show();
                }
            }
            else {
                 customAlert($alert_error_extra_meta, 3000);
            }
        },
        error: function(XMLHttpRequest, textStatus, errorThrown) {
            customAlert($alert_error_extra_meta, 3000);
        }
    });
} // function saveExtraMetadata()

function removeExtraMetadataFromTable(row_id)
{
    var removed_row = $('#extraMetaTable').DataTable().row('#' + row_id);
    removed_row.remove().draw(false);
    $('#save-extra-meta-btn').show();
}

function update_download_status(task_id, download_path) {
    download_status_timeout_id=-1;
    // disable download button to prevent it from being clicked again
    $('#btn-download-all').attr('disabled', 'disabled');
    $.ajax({
        dataType: "json",
        cache: false,
        timeout: 60000,
        type: "POST",
        url: '/django_irods/check_task_status/',
        data: {
            task_id: task_id
        },
        success: function(data) {
            if(data.status) {
                $("#loading").html('');
                if(download_status_timeout_id > -1)
                    clearTimeout(download_status_timeout_id);
                $("#btn-download-all").removeAttr('disabled');
                $("#download-status-info").html(
                        "If your download does not start automatically, " +
                        "please click <a href='" + download_path + "'>here</a>.");
                window.location.href = download_path;
            }
            // only check status again in 3 seconds when $("#loading") is not
            // cleared up by success status above
            else if($("#loading").html()) {
                $("#loading").html($("#loading").html() + ".");
                download_status_timeout_id = setTimeout(function () {
                    update_download_status(task_id, download_path);
                }, 3000);
            }
        },
        error: function (xhr, errmsg, err) {
            if(download_status_timeout_id > -1)
                clearTimeout(download_status_timeout_id);
            $("#btn-download-all").removeAttr('disabled');
            console.log(errmsg);
            alert("Resource bag cannot be generated due to download poll errors: " + errmsg);
        }
    });
}

$(document).ready(function () {
    var task_id = $('#task_id').val();
    var download_path = $('#download_path').val();
    if (task_id) {
        update_download_status(task_id, download_path);
    }

    $('.contact-table .sortable').sortable({
        axis: "y",
        stop: function( event, ui ) {
            var forms = $("#authors-table .drag-indicator > form");

            // Set the new order value in the form items
            for (var i = 0; i < forms.length; i++) {
                $(forms[i]).find("input.order-input").attr("value", i + 1);
                $("#id_creator-" + i + "-order").attr("value", $("input[name='creator-" + i + "-order']").val());
            }

            $form = $(ui.item.find(".drag-indicator > form"));
            var url = $form.attr('action');
            var datastring = $form.serialize();
            $("html").css("cursor", "progress");

            $.ajax({
                type: "POST",
                url: url,
                data: datastring,
                success: function (result) {
                    $("html").css("cursor", "initial");

                },
                error: function (xhr, errmsg, err) {
                    $("html").css("cursor", "initial");
                    console.log(errmsg, err);
                }
            });
        }
    });

    $("#agree-chk").on('click', function(e) {
        e.stopImmediatePropagation();
        if (e.currentTarget.checked)
            $('#publish-btn').removeAttr('disabled');
        else
            $('#publish-btn').attr('disabled', 'disabled');
    });

    $("#agree-chk-copy").on('click', function(e) {
        e.stopImmediatePropagation();
        if (e.currentTarget.checked)
            $('#copy-btn').removeAttr('disabled');
        else
            $('#copy-btn').attr('disabled', 'disabled');
    });

    // add input element to each of the comment/rating forms to track resource mode (edit or view)
    var resourceMode = $("#resource-mode").val().toLowerCase();
    var inputElementToAdd = '<input type="hidden" name="resource-mode" value="mode_to_replace" />';
    inputElementToAdd = inputElementToAdd.replace('mode_to_replace', resourceMode);

    $("[id^=comment-]").find('form').each(function () {
        $(this).append(inputElementToAdd);
    });
    // new comment form
    $("#comment").append(inputElementToAdd);

    // On manage access interface, prevent form submission when pressing the enter key on the search box.
    $('#id_user-autocomplete').keypress(function (e) {
        e = e || event;
        var txtArea = /textarea/i.test((e.target || e.srcElement).tagName);
        return txtArea || (e.keyCode || e.which || e.charCode || 0) !== 13;
    });

    // Submit for metadata update forms
    $(".btn-form-submit").click(function () {
        var formID = $(this).closest("form").attr("id");
        metadata_update_ajax_submit(formID);
    });

    // Display toggle for Add Author/Contributor radio buttons
    function onAddContributorTypeChange() {
        var type = $(this).val();
        $("div[data-hs-user-type]").hide();
        $("div[data-hs-user-type='" + type + "']").show();
    }
    $("input[name='add_author_user_type']").click(onAddContributorTypeChange);
    $("input[name='add_contributor_user_type']").click(onAddContributorTypeChange);

    // Display toggle for author type radio buttons ('person' or 'organization')
    function onOrgTypeChange() {
        var type = $(this).val();
        $("div[data-hs-org-type]").hide();
        $("div[data-hs-org-type='" + type + "']").show();
    }
    $("input[name='choose_org_type']").click(onOrgTypeChange);

    // Display toggle for author type radio buttons ('person' or 'organization')
    function onPersonTypeChange() {
        var type = $(this).val();
        $("div[data-hs-person-type]").hide();
        $("div[data-hs-person-type='" + type + "']").show();
    }
    $("input[name='add_author_person']").click(onPersonTypeChange);


    $("#citation-text").on("click", function (e) {
        // document.selection logic is added in for IE 8 and lower
        if (document.selection) {
            document.selection.empty();
            var range = document.body.createTextRange();
            range.moveToElementText(this);
            range.select();
        }
        else if (window.getSelection) {
            // Get the selection object
            var selection = window.getSelection();
            selection.removeAllRanges();
            var range = document.createRange();
            range.selectNode(this);
            selection.addRange(range);
        }
    });

    $("#btn-shareable").on("change", shareable_ajax_submit);
    $("#btnMyResources").click(label_ajax_submit);

    // Apply theme to comment's submit button
    $("#comment input[type='submit']").removeClass();
    $("#comment input[type='submit']").addClass("btn btn-default");

    $(".list-separator").parent().hover(function(){
        $(this).css("text-decoration", "none");
        $(this).css("pointer-events", "none");
    });

    var keywordString = $("#keywords-string").val();
    $("#id-subject").find("#id_value").val(keywordString);

    // Populate keywords field
    var keywords = keywordString.split(",");
    $("#lst-tags").empty();
    for (var i = 0; i < keywords.length; i++) {
        if (keywords[i] != "") {
            var li = $("<li class='tag'><span></span></li>");
            li.find('span').text(keywords[i]);
            li.append('&nbsp;<a><span class="glyphicon glyphicon-remove-circle icon-remove"></span></a>');
            $("#lst-tags").append(li);
        }
    }

    $(".icon-remove").click(onRemoveKeyword);
    $("#btn-add-keyword").click(onAddKeyword);
    $("#txt-keyword").keyup(function (e) {
        e.which = e.which || e.keyCode;
        if (e.which == 13) {
            onAddKeyword();
        }
    });

    $("#list-roles a").click(onRoleSelect);
    $("#add-access-form #id_user-autocomplete").attr("placeholder", "Search by name or username");
    $("#id_group-autocomplete").attr("placeholder", "Search by group name");

    var file_types = $("#supported-file-types").attr('value');
    if (file_types != ".*") {
        var display_file_types = file_types.substring(0, file_types.length - 1) + ').';
        display_file_types = display_file_types.replace(/'/g, '');
        $("#file-types").text("Only the listed file types can be uploaded: " + display_file_types);
        $("#file-types-irods").text("Only the listed file types can be uploaded: " + display_file_types);
    }
    else {
        $("#file-types").text("Any file type can be uploaded.");
    }
    var file_count = $("#file-count").attr('value');

    // set if multiple files can be uploaded
    var allow_multiple_file_upload = $("#allow-multiple-file-upload").attr('value');
    if (allow_multiple_file_upload === "True") {
        $("#file-multiple").text("Multiple file upload is allowed.");
        $("#file-multiple-irods").text("Multiple file upload is allowed.");
    }
    else {
        $("#file-multiple").text("Only one file can be uploaded.");
        $("#file-multiple-irods").text("Only one file can be uploaded.");

        if (file_count > 0) {
            $("#log-into-irods").hide();
            $("#sign-in-info").hide();
            $("#btn-select-irods-file").hide();
        }
    }

    if ($("input:button[value='Delete creator']").length == 1) {
        $("input:button[value='Delete creator']").first().hide();
    }
    // disable all save changes button on load
    $("form").each(function () {
        $save_button = $(this).find("button").first();
        if ($save_button.text() === "Save changes") {
            $save_button.hide();
        }
    });

    $("#select_license").on('change', function () {
        var value = this.value;
        if (value === "other") {
            $(this).closest("form").find("#id_statement").first().text("");
            $(this).closest("form").find("#id_url").first().attr('value', "");
            $(this).closest("form").find("#id_statement").first().attr('readonly', false);
            $(this).closest("form").find("#id_url").first().attr('readonly', false);
            $("#img-badge").first().hide();
        }
        else {
            var text = $(this).find('option:selected').text();
            text = "This resource is shared under the " + text + ".";
            $(this).closest("form").find("#id_statement").first().text(text);
            $(this).closest("form").find("#id_url").first().attr('value', value);
            $(this).closest("form").find("#id_statement").first().attr('readonly', true);
            $(this).closest("form").find("#id_url").first().attr('readonly', true);
            $("#img-badge").first().show();
            var staticURL = $("#static-url").val();
            if (text == "This resource is shared under the Creative Commons Attribution CC BY.") {
                $(this).closest("form").find("#img-badge").first().attr('src', staticURL + "img/cc-badges/CC-BY.png");
                $(this).closest("form").find("#img-badge").first().attr('alt', "CC-BY");
            }
            else if (text == "This resource is shared under the Creative Commons Attribution-ShareAlike CC BY-SA.") {
                $(this).closest("form").find("#img-badge").first().attr('src', staticURL + "img/cc-badges/CC-BY-SA.png");
                $(this).closest("form").find("#img-badge").first().attr('alt', "CC-BY-SA");
            }
            else if (text == "This resource is shared under the Creative Commons Attribution-NoDerivs CC BY-ND.") {
                $(this).closest("form").find("#img-badge").first().attr('src', staticURL + "img/cc-badges/CC-BY-ND.png");
                $(this).closest("form").find("#img-badge").first().attr('alt', "CC-BY-ND");
            }
            else if (text == "This resource is shared under the Creative Commons Attribution-NoCommercial-ShareAlike CC BY-NC-SA.") {
                $(this).closest("form").find("#img-badge").first().attr('src', staticURL + "img/cc-badges/CC-BY-NC-SA.png");
                $(this).closest("form").find("#img-badge").first().attr('alt', "CC-BY-NC-SA");
            }
            else if (text == "This resource is shared under the Creative Commons Attribution-NoCommercial CC BY-NC.") {
                $(this).closest("form").find("#img-badge").first().attr('src', staticURL + "img/cc-badges/CC-BY-NC.png");
                $(this).closest("form").find("#img-badge").first().attr('alt', "CC-BY-NC");
            }
            else if (text == "This resource is shared under the Creative Commons Attribution-NoCommercial-NoDerivs CC BY-NC-ND.") {
                $(this).closest("form").find("#img-badge").first().attr('src', staticURL + "img/cc-badges/CC-BY-NC-ND.png");
                $(this).closest("form").find("#img-badge").first().attr('alt', "CC-BY-NC-ND");
            }
        }
    });

    // set the selected license in the select license dropdown
    var value_exists = false;
    $("#select_license option").each(function () {
        if (this.value == $("#id_url").attr('value')) {
            $("#select_license").val($("#id_url").attr('value'));
            value_exists = true;
            return;
        }
    });

    if (value_exists == false) {
        // set the selected license type to 'other'
        $("#select_license").val('other');
        if ($("#select_license").attr('readonly') == undefined) {
            $("#select_license").closest("form").find("#id_statement").first().attr('readonly', false);
            $("#select_license").closest("form").find("#id_url").first().attr('readonly', false);
            $("#img-badge").first().hide();
        }
        else {
            $("#select_license").attr('style', "background-color:white;");
            $("#select_license").closest("form").find("#id_statement").first().attr('readonly', true);
            $("#select_license").closest("form").find("#id_url").first().attr('readonly', true);
        }
    }

    // show "Save changes" button when form editing starts
    showMetadataFormSaveChangesButton();

    // Initialize date pickers
    initializeDatePickers();

    // init ExtraMetadata Table
    extraMetaTable = $("#extraMetaTable").DataTable({
        "paging": false,
        "bSort": false,
        "bLengthChange": false,
        "info": false,
        "bFilter": false,
        "bInfo": false,
        "language": {"emptyTable": "No Extended Metadata"}
    });

    // Toggle visibility for invite users or groups
    $(".add-view-group-form").hide();

    // Toggle invite user or group form
    $("#invite-flag button").click(function () {
        var form = $("#add-access-form");
        var action = form.attr("action");
        if ($(this).attr("data-value") == "users") {
            $(".add-view-user-form").show();
            $(".add-view-group-form").hide();
            action = action.replace("share-resource-with-group", "share-resource-with-user");
            form.attr("action", action);
            $("#list-roles li:nth-child(3)").show();

            $("#invite-flag button[data-value='groups']").removeClass("btn-primary");
            $("#invite-flag button[data-value='groups']").addClass("btn-default");
            $("#invite-flag button[data-value='users']").removeClass("btn-default");
            $("#invite-flag button[data-value='users']").addClass("btn-primary");

        }
        else {
            $(".add-view-group-form").show();
            $(".add-view-user-form").hide();
            action = action.replace("share-resource-with-user", "share-resource-with-group");
            form.attr("action", action);
            if ($("#selected_role").attr("data-role") == "owner") {
                $("#selected_role").attr("data-role", "view");
                $("#selected_role").text("Can view");
            }
            $("#list-roles li:nth-child(3)").hide();
            $("#invite-flag button[data-value='users']").disabled = true;
            $("#invite-flag button[data-value='groups']").disabled = false;


            $("#invite-flag button[data-value='users']").removeClass("btn-primary");
            $("#invite-flag button[data-value='users']").addClass("btn-default");
            $("#invite-flag button[data-value='groups']").removeClass("btn-default");
            $("#invite-flag button[data-value='groups']").addClass("btn-primary");
        }
    });

    $("#btn-add-new-entry").click(function() {
        showAddEditExtraMetaPopup(false, '');
    });

    $(".btn-edit-extra-metadata").click(function () {
        var loopCounter = $(this).attr("data-loop-counter");
        showAddEditExtraMetaPopup(true, loopCounter);
    });

    $(".btn-remove-extra-metadata").click(function () {
        var loopCounter = $(this).attr("data-loop-counter");
        removeExtraMetadataFromTable(loopCounter);
    });

    $("#save-extra-meta-btn").click(saveExtraMetadata);

    $("#btn-confirm-edit-key-value").click(function () {
        var formID = $(this).closest("form").attr("id");
        updateFileTypeExtraMetadata(formID);
    });

    $("#btn-delete-key-value").click(function () {
        var formID = $(this).closest("form").attr("id");
        deleteFileTypeExtraMetadata(formID);
    });
});