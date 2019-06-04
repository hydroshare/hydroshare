/**
* Created by Mauriel on 3/9/2017.
*/

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

function showAddEditExtraMetaPopup(edit, row_id_str) {
    $("#edit_extra_meta_row_id").val('');
    $("#old_extra_meta_name").val('');
    $("#extra_meta_name_input").val('');
    $("#extra_meta_value_input").val('');

    // Restore validation UI state
    $("#extra_meta_msg").hide();
    $("#extra_meta_name_input").removeClass("form-invalid");

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

function showRemoveExtraMetaPopup(row_id_str) {
    // retrieving values from underlying data table
    let t = $('#extraMetaTable').DataTable();

    // get the row object via the row_id_str passed in
    let row_to_delete = t.row("#" + row_id_str);

    // get the row content - meta_name and meta_value
    let meta_name = row_to_delete.data()[0];
    let meta_value = row_to_delete.data()[1];

    // this is a hidden HTML element to store the row_id_str
    $("#delete_extra_meta_row_id").val(row_id_str);

    $("#old_extra_meta_name").val(meta_name);

    // set the meta_value.
    $("#delete_extra_meta_name_input").val(meta_name);
    $("#delete_extra_meta_value_input").val(meta_value);

    $('#deleteExtraMetaDialog').modal('show');
}

function addEditExtraMeta2Table() {
    // Restore validation UI state
    $("#extra_meta_msg").hide();
    $("#extra_meta_name_input").removeClass("form-invalid");
    var t = $('#extraMetaTable').DataTable();
    var extra_meta_name = $("#extra_meta_name_input").val().trim();
    var extra_meta_value = $("#extra_meta_value_input").val().trim();
    var edit_extra_meta_row_id = $("#edit_extra_meta_row_id").val().trim();

    if (foundDuplicatedName(t, extra_meta_name, edit_extra_meta_row_id)) {
        $("#extra_meta_name_input").addClass("form-invalid");
        $("#extra_meta_msg").html("<div class='alert alert-danger'>" +
            "The name already exists. Please input a different name.</div>");
        $("#extra_meta_msg").show();
        return;
    }

    if (extra_meta_name.length == 0 || extra_meta_value.length == 0) {
        $("#extra_meta_msg").html("<div class='alert alert-danger'>" +
            "Both name and value are required fields that cannot be left blank.</div>");
        $("#extra_meta_msg").show();
        return;
    }

    if (edit_extra_meta_row_id == "") {
        // Add new
        var new_row_id_0_base = findMaxRowID(t) + 1;
        var edit_icon_str = '<span data-loop-counter="' + new_row_id_0_base +
            '" class="btn-edit-icon btn-edit-extra-metadata glyphicon glyphicon-pencil icon-blue table-icon" ' +
            'data-toggle="tooltip" data-placement="top" title="Edit"></span>';
        var remove_icon_str = '<span data-loop-counter="' + new_row_id_0_base +
            '" class="btn-remove-icon btn-remove-extra-metadata glyphicon glyphicon-trash btn-remove table-icon" ' +
            'data-toggle="tooltip" data-placement="top" title="Remove"></span>';
        var row_ele = t.row.add([extra_meta_name, extra_meta_value, edit_icon_str +
            " " + remove_icon_str]).node();
        $(row_ele).attr('id', new_row_id_0_base);
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

    $("#extraMetaTable [data-toggle='tooltip']").tooltip();
    $("#extraMetaDialog").modal('hide');
    saveExtraMetadata();
}

function removeExtraMetaTable(table) {
    $("#deleteExtraMetaDialog").modal('hide');

    removeExtraMetadataFromTable($("#delete_extra_meta_row_id").val().trim());
    saveExtraMetadata();
}

function findMaxRowID(table) {
    var max_id = -1;
    table.rows(). every(function ( rowIdx, tableLoop, rowLoop ) {
        if(parseInt(this.node().id) > max_id) {
           max_id = parseInt(this.node().id);
        }
    });

    return max_id;
}

function foundDuplicatedName(table, newName, except_row_id) {
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

function saveExtraMetadata() {
    var successMsg = "Extended metadata updated.";
    var errorMsg = "Extended metadata failed to update.";

    var json_obj = {};
    var t = $('#extraMetaTable').DataTable();
    t.rows(). every(function ( rowIdx, tableLoop, rowLoop ) {
        var extra_meta_name = $("<div/>").html(this.data()[0].trim()).text();
        var extra_meta_value = $("<div/>").html(this.data()[1].trim()).text();
        json_obj[extra_meta_name] = extra_meta_value;
    });

    var json_str = JSON.stringify(json_obj);
    json_obj = JSON.parse(json_str);
    var update_key_value_metadata_url = "/hsapi/_internal/" + SHORT_ID + "/update-key-value-metadata/";

    $.ajax({
        type: "POST",
        url: update_key_value_metadata_url,
        dataType: "json",
        data: json_obj,

        success: function(result) {
            var json_response = result;
            if (json_response.status === 'success') {
                customAlert("Success!", successMsg, "success", 3000);
                if (json_response.is_dirty) {
                    $('#netcdf-file-update').show();
                }
            }
            else {
                customAlert("Error!", errorMsg, "error", 3000);
            }
        },
        error: function(XMLHttpRequest, textStatus, errorThrown) {
            customAlert("Error!", errorMsg, "error", 3000);
        }
    });
} // function saveExtraMetadata()

function removeExtraMetadataFromTable(row_id) {
    var removed_row = $('#extraMetaTable').DataTable().row('#' + row_id);
    removed_row.remove().draw(false);
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

    $('.authors-wrapper.sortable').sortable({
        placeholder: "ui-state-highlight",
        stop: function (event, ui) {
            var forms = $(".authors-wrapper.sortable form");

            // Set the new order value in the form items
            for (let i = 0; i < forms.length; i++) {
                $(forms[i]).find("input.input-order").val(i + 1);
                $(forms[i]).find("input.input-order").attr("value", i + 1);
            }

            let $form = $(ui.item.find("form"));
            var url = $form.attr('action');
            var datastring = $form.serialize();
            $("html").css("cursor", "progress");

            $.ajax({
                type: "POST",
                url: url,
                data: datastring,
                success: function () {
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

    $("#agree-chk-download-bag").on('click', function(e) {
        e.stopImmediatePropagation();
        if (e.currentTarget.checked)
            $('#download-bag-btn').removeAttr('disabled');
        else
            $('#download-bag-btn').attr('disabled', 'disabled');
    });

    $("#agree-chk-download-file").on('click', function(e) {
        e.stopImmediatePropagation();
        if (e.currentTarget.checked)
            $('#download-file-btn').removeAttr('disabled');
        else
            $('#download-file-btn').attr('disabled', 'disabled');
    });
    // add input element to each of the comment/rating forms to track resource mode (edit or view)
    var inputElementToAdd = '<input type="hidden" name="resource-mode" value="mode_to_replace" />';
    inputElementToAdd = inputElementToAdd.replace('mode_to_replace', RESOURCE_MODE.toLowerCase());

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

    $("#btn-lic-agreement").on("change", license_agreement_ajax_submit);
    $("#btnMyResources").click(label_ajax_submit);
    $("#btnOpenWithApp").click(label_ajax_submit);

    // Apply theme to comment's submit button
    $("#comment input[type='submit']").removeClass();
    $("#comment input[type='submit']").addClass("btn btn-default");

    $("input[name='user-autocomplete']").attr("placeholder", "Search by name or username").addClass("form-control");
    $("input[name='group-autocomplete']").attr("placeholder", "Search by group name").addClass("form-control");

    if (SUPPORTE_FILE_TYPES != ".*") {
        var display_file_types = SUPPORTE_FILE_TYPES.substring(0, SUPPORTE_FILE_TYPES.length - 1) + ').';
        display_file_types = display_file_types.replace(/'/g, '');
        $("#file-types").text("Only the listed file types can be uploaded: " + display_file_types);
        $("#file-types-irods").text("Only the listed file types can be uploaded: " + display_file_types);
    }
    else {
        $("#file-types").text("Any file type can be uploaded.");
    }

    // set if multiple files can be uploaded
    if (ALLLOW_MULTIPLE_FILE_UPLOAD === "True") {
        $("#file-multiple").text("Multiple file upload is allowed.");
        $("#file-multiple-irods").text("Multiple file upload is allowed.");
    }
    else {
        $("#file-multiple").text("Only one file can be uploaded.");
        $("#file-multiple-irods").text("Only one file can be uploaded.");

        if (FILE_COUNT > 0) {
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
        var $save_button = $(this).find("button").first();
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
            if (text == "This resource is shared under the Creative Commons Attribution CC BY.") {
                $(this).closest("form").find("#img-badge").first().attr('src', STATIC_URL + "img/cc-badges/CC-BY.png");
                $(this).closest("form").find("#img-badge").first().attr('alt', "CC-BY");
            }
            else if (text == "This resource is shared under the Creative Commons Attribution-ShareAlike CC BY-SA.") {
                $(this).closest("form").find("#img-badge").first().attr('src', STATIC_URL + "img/cc-badges/CC-BY-SA.png");
                $(this).closest("form").find("#img-badge").first().attr('alt', "CC-BY-SA");
            }
            else if (text == "This resource is shared under the Creative Commons Attribution-NoDerivs CC BY-ND.") {
                $(this).closest("form").find("#img-badge").first().attr('src', STATIC_URL + "img/cc-badges/CC-BY-ND.png");
                $(this).closest("form").find("#img-badge").first().attr('alt', "CC-BY-ND");
            }
            else if (text == "This resource is shared under the Creative Commons Attribution-NoCommercial-ShareAlike CC BY-NC-SA.") {
                $(this).closest("form").find("#img-badge").first().attr('src', STATIC_URL + "img/cc-badges/CC-BY-NC-SA.png");
                $(this).closest("form").find("#img-badge").first().attr('alt', "CC-BY-NC-SA");
            }
            else if (text == "This resource is shared under the Creative Commons Attribution-NoCommercial CC BY-NC.") {
                $(this).closest("form").find("#img-badge").first().attr('src', staticURL + "img/cc-badges/CC-BY-NC.png");
                $(this).closest("form").find("#img-badge").first().attr('alt', "CC-BY-NC");
            }
            else if (text == "This resource is shared under the Creative Commons Attribution-NoCommercial-NoDerivs CC BY-NC-ND.") {
                $(this).closest("form").find("#img-badge").first().attr('src', STATIC_URL + "img/cc-badges/CC-BY-NC-ND.png");
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

    $("#btn-add-new-entry").click(function() {
        showAddEditExtraMetaPopup(false, '');
    });

    $("#extraMetaTable").on("click", ".btn-remove-extra-metadata", function () {
        var loopCounter = $(this).attr("data-loop-counter");
        showRemoveExtraMetaPopup(loopCounter);
    });

    $("#extraMetaTable").on("click", ".btn-edit-extra-metadata", function () {
        var index = $(this).attr("data-loop-counter");
        showAddEditExtraMetaPopup(true, index);
    });

    $("#btn-confirm-edit-key-value").click(function () {
        var formID = $(this).closest("form").attr("id");
        updateFileTypeExtraMetadata(formID);
    });

    $("#btn-delete-key-value").click(function () {
        var formID = $(this).closest("form").attr("id");
        deleteFileTypeExtraMetadata(formID);
    });


    const SPACING = 22; // 2 * 10px(from margins) + 2 * 1px (from borders)
    var toolbar_offset = $(".custom-btn-toolbar").parent().offset().top - $("#hs-nav-bar").height() - SPACING;

    // Fix buttons toolbar when scrolling down
    // ========================================
    $(window).bind('scroll', function () {
        let toolbar = $(".custom-btn-toolbar");
        if ($(window).scrollTop() > toolbar_offset && !toolbar.hasClass('toolbar-fixed')) {
            toolbar.parent().height(toolbar.parent().height());
            toolbar.css("top", $("#hs-nav-bar").height() + 11);
            toolbar.addClass('toolbar-fixed');
            toolbar.css("right", toolbar.parent().offset().left + 4);
        }
        else if ($(window).scrollTop() <= toolbar_offset && toolbar.hasClass('toolbar-fixed')) {
            toolbar.parent().height("initial");
            toolbar.css("top", "initial");
            toolbar.removeClass('toolbar-fixed');
            // Recalculate in case UI elements were added/removed
            toolbar_offset = toolbar.parent().offset().top - $("#hs-nav-bar").height() - SPACING;
        }
    });

    $(window).resize(function () {
        // Recalculate on window re-size
        toolbar_offset = $(".custom-btn-toolbar").parent().offset().top - $("#hs-nav-bar").height() - SPACING;
    });
});