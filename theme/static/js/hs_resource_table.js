/**
 * Created by Mauriel on 5/19/2016.
 */
var resourceTable;

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

var filtersUpdated = false
var filtersLoaded = []
var spinner = $('<i class="fa fa-spinner fa-pulse fa-lg my-res-filter-spinner" style="z-index: 1;"></i>')

$(document).ready(function () {
    ROUTE_NAME === "my_resources" && setInitialFilters();
    resourceTable = initTable("#item-selectors");
    ROUTE_NAME === "my_resources"  && updateFilterCount();
    updateTable();
    setEventListeners();
});

function setInitialFilters(){
    // filter badges spin for async
    let filterBadges = $("#filter li.list-group-item .badge");
    filterBadges.prepend(spinner);

    const url = new URL(window.location.href);
    let url_filters = url.searchParams.getAll('f');
    if (url_filters.length !== 0){
        filtersLoaded = url_filters;
    }else{
        // default filters (checked in the template) are:
        filtersLoaded = ['owned', 'discovered', 'favorites'];
        for(let filter of filtersLoaded){
            url.searchParams.append('f', filter);
        }
        window.history.pushState({}, '', url);
    }

    // check the boxes accordignly
    $("#filter input[type='checkbox']").prop("checked", false);
    for(let filter of filtersLoaded){
        $(`#filter input[type='checkbox'][data-facet='${filter}']`).prop("checked", true);
    }
}

function setEventListeners(){
    $("#item-selectors").css("width", "100%");

    // Fix for horizontal scroll bar appearing unnecessarily on firefox.
    if ($.browser.mozilla){
        $("#item-selectors").width($("#item-selectors").width() - 2);
    }

    function clearLabelErrorMessaging(){
        $("#txtLabelName").removeClass("invalid-input");
        $("#txtLabelName").closest(".modal-body").find(".error-label").remove();
    }

    // Trigger label creation when pressing Enter
    $("#txtLabelName").keyup(function (event) {
        clearLabelErrorMessaging();
        var label = $("#txtLabelName").val().trim();
        if (event.keyCode == 13 && label != "") {
            $("#btn-create-label").click();
        }
    });

    // Disable default form submission when pressing enter for textarea inputs
    $(window).keydown(function (event) {
        if (event.keyCode == 13 && event.target.tagName != "TEXTAREA") {
            event.preventDefault();
        }
    });

    // Autofocus input when modal appears
    $("#modalCreateLabel").on('shown.bs.modal', function () {
        $("#txtLabelName").focus();
    });

    // remove error messaging and input, if any
    $("#modalCreateLabel").on('hidden.bs.modal', function () {
        $("#txtLabelName").val("");
        clearLabelErrorMessaging();
    });

    $("#item-selectors").show();

    // Bind ajax submit events to favorite and label buttons
    $("#item-selectors").on("click", ".btn-inline-favorite, .btn-label-remove", label_ajax_submit);
    $("#btn-create-label").click(label_ajax_submit);
    $(".btn-label-remove").click(label_ajax_submit);

    $("#filter input[type='checkbox']").on("change", function (e) {
        let check_val = e.target.attributes['data-facet'].value;
        let ignore_filters = ["recent"];
        if(ignore_filters.includes(check_val)){
            updateTable();
            return;
        }
        dataRefresh(e.target);
    });

    $("#user-labels-left").on("change", "input[type='checkbox']", function () {
        resourceTable.draw();
        updateLabelDropdowns();
        updateLabelCount();
    });

    $("#item-selectors").on("change", ".inline-dropdown input[type='checkbox']", label_ajax_submit);

    $("#toolbar-labels-dropdown").on("change", "input[type='checkbox']", function () {
        var inlineCheckboxes = $(".row-selector:checked")
          .parent()
          .find(".inline-dropdown input[type='checkbox'][value='" + $(this).val() + "']");
        var status = $(this).prop("checked");

        for (var i = 0; i < inlineCheckboxes.length; i++) {
            if (status == false && $(inlineCheckboxes[i]).prop("checked") == true) {
                $(inlineCheckboxes[i]).prop("checked", false);
                $(inlineCheckboxes[i]).trigger("change");
            }
            else if (status == true && $(inlineCheckboxes[i]).prop("checked") == false) {
                $(inlineCheckboxes[i]).prop("checked", true);
                $(inlineCheckboxes[i]).trigger("change");
            }
        }
    });

    $("#filter-shared-by input[type='checkbox']").on("change", function () {
        resourceTable.draw();
    });

    $("#resource-search-input").keyup(function () {
        var searchString = removeQueryOccurrences($(this).val());
        applyQueryStrings();
        resourceTable.search(searchString).draw();
    });

    $("#btn-clear-author-input").click(function () {
        $("#input-author").val("");
        typeQueryStrings();
        $("#resource-search-input").keyup();
    });

    $("#btn-clear-subject-input").click(function () {
        $("#input-subject").val("");
        typeQueryStrings();
        $("#resource-search-input").keyup();
    });

    $("#btn-clear-search-input").click(function () {
        var searchInput = $("#resource-search-input");
        searchInput.val("");
        searchInput.keyup();
    });

    $('#input-author, #input-subject').keyup( function() {
        typeQueryStrings();
        resourceTable.draw();
    } );

    $("#input-resource-type").change(function(){
        typeQueryStrings();
        resourceTable.draw();
    });

    $(".all-rows-selector").change(function(){
        $(".row-selector").prop("checked", $(this).prop("checked"));

        var toolbarLabels = $("#toolbar-labels-dropdown input[type='checkbox']");
        if ($(this).prop("checked") == false) {
            toolbarLabels.attr("disabled", true);
        }
        else {
            toolbarLabels.attr("disabled", false);
        }

        refreshToolbarCheckboxState();
    });

    $(".row-selector").change(refreshToolbarCheckboxState);

    $("#btn-favorite").click(function(){
        var stars = $("#item-selectors input[type='checkbox']:checked").parent().find(".btn-inline-favorite");
        var checkedSome = false;
        for (var i = 0; i < stars.length; i++) {
            if (!$(stars[i]).hasClass("isfavorite")) {
                $(stars[i]).click();
                checkedSome = true;
            }
        }

        // If none was checked it means we are unchecking all
        if (checkedSome == false) {
            stars.click();
        }
    });

    // Categorizes the resources based on criteria about delete permissions.
    function inspectResources(indexes, notOwned, published) {
        var selectedRows = $("#item-selectors .row-selector:checked").closest("tr.data-row");
        for (var i = 0; i < selectedRows.length; i++) {
            var index = resourceTable.row($(selectedRows[i])).index();
            var permission = resourceTable.cell(index, PERM_LEVEL_COL).data();
            var status = resourceTable.cell(index, SHARING_STATUS_COL).data();

            if (permission != "Owned") {
                notOwned.push($(selectedRows[i]));
                // No permission to delete non owned resources.
            }
            else if (status.toUpperCase() == "PUBLISHED") {
                published.push($(selectedRows[i]));
            }
            else {
                indexes.push($(selectedRows[i]));
            }
        }
    }

    $( "#confirm-res-id-text" ).keyup(function() {
        $("#btn-delete-multiple-resources").prop("disabled", this.value !== "DELETE");
    });

    $("#delete-multiple-resources-dialog").on('hidden.bs.modal', function () {
        $("#confirm-res-id-text").val('');
        $("#btn-delete-multiple-resources").prop("disabled", true);
    });

    $("#btn-delete-multiple-resources").click(function() {
        var indexes = [];   // List of selected resources allowed for deletion
        var notOwned = [];
        var published = [];

        inspectResources(indexes, notOwned, published);

        if (indexes.length > 0) {
            delete_multiple_resources_ajax_submit(indexes); // Submit a delete request for each index
        }
    });

    $("#btn-confirm-delete-resources").click(function () {
        var indexes = [];   // List of selected resources allowed for deletion
        var notOwned = [];
        var published = [];

        inspectResources(indexes, notOwned, published);

        var messageBody = $("#delete-multiple-resources-dialog #delete-resource-messaging");

        messageBody.empty();

        // Resources that cannot be deleted because the current user does not own them
        if (notOwned.length > 0) {
            var notOwnedTemplate = "";
            for (var i = 0; i < notOwned.length; i++) {
                var index = resourceTable.row($(notOwned[i])).index();
                var resourceTitle = resourceTable.cell(index, TITLE_COL).data();
                notOwnedTemplate += "<li>" + resourceTitle + "</li>";
            }
            messageBody.append(
                '<div class="alert alert-warning">' +
                    '<strong>You do not have permission to delete the following resources:</strong>' +
                    '<ul>' +
                        notOwnedTemplate +
                    '</ul>' +
                '</div>'
            );
        }

        // Resources that cannot be deleted because they have been published
        if (published.length > 0) {
            var publishedTemplate = "";
            for (var i = 0; i < published.length; i++) {
                var index = resourceTable.row($(published[i])).index();
                var resourceTitle = resourceTable.cell(index, TITLE_COL).data();
                publishedTemplate += "<li>" + resourceTitle + "</li>";
            }
            messageBody.append(
                '<div class="alert alert-warning">' +
                    '<strong>The following resources have been published and cannot be deleted:</strong>' +
                    '<ul>' +
                        publishedTemplate +
                    '</ul>' +
                '</div>'
            );
        }

        if((published.length || notOwned.length) && indexes.length) {
            messageBody.append("<hr><h4>Continue with the rest?</h4>")
        }

        if (indexes.length > 0) {
            var actionWarningTemplate =
            '<div class="alert alert-danger">' +
                '<strong>WARNING! DELETING RESOURCES IS A PERMANENT ACTION!</strong>' +
                '<ul>' +
                    '<li>This will delete any resources you have selected and their content files.</li>' +
                    '<li>HydroShare will not retain copies of your resources or content files.</li>' +
                    '<li>We highly recommend that you download the latest copy of your resources before confirming ' +
                        'this action so that you do not lose any content you might need later.</li>' +
                '</ul>' +
                '<p>If you are sure you want to delete the selected resources, type the word "DELETE" in the ' +
                    'following text box and then click the "Delete" button below. ' +
                '</p>' +
            '</div>';

            messageBody.append(actionWarningTemplate);
            $("#confirm-res-id-text").show();
        }
        else {
            messageBody.append('<div>Select resources to delete.</div><br>');
            $("#confirm-res-id-text").hide();
        }

        messageBody.find("a").attr("target", "_blank"); // Make listed resources open in new tab
    });

    $("#item-selectors td").click(function(e){
        if (e.target.tagName != "TD") {
            return;
        }
        if ($(this).parent().find("input[type='checkbox']:checked.row-selector").length > 0) {
            $(this).parent().find("input[type='checkbox'].row-selector").prop("checked", false);
        }
        else {
            $(this).parent().find("input[type='checkbox'].row-selector").prop("checked", true);
        }
    });

    // Prevents dropdown form getting dismissed when clicking on items
    $('.dropdown-menu label, .list-labels label').click(function (e) {
        e.stopPropagation();
    });
}

function initTable(selector){
    /*==================================================
        Table columns
        0 - actions
        1 - Resource Type
        2 - Title
        3 - Owner
        4 - Date Created
        5 - Last Modified
        6 - Subject
        7 - Authors
        8 - Permission Level
        9 - Labels
        10 - Favorite
        11 - Last modified (sortable format)
        12 - Sharing Status
        13 - Date created (sortable format)
        14 - Access Grantor
    ==================================================*/

    return $(selector).DataTable({
        "order": [[DATE_CREATED_COL, "desc"]],
        "paging": false,
        "info": false,
        "columnDefs": colDefs,
        "autoWidth": false
    });
}

function updateTable(){
    resourceTable.draw();
    updateLabelsList();
    updateLabelDropdowns();
    updateLabelCount();
}

function delete_multiple_resources_ajax_submit(indexes) {
    var calls = [];

    // Submit all delete requests asynchronously
    for (var i = 0; i < indexes.length; i++) {
        var form = $(indexes[i]).find("form[data-form-type='delete-resource']");
        var datastring = $(form).serialize();
        var url = $(form).attr("action");
        let deleteText = $('#confirm-res-id-text').val();
        url = url + deleteText + "/";
        $("html").css("cursor", "progress");

        calls.push(
            $.ajax({
                type: "POST",
                url: url,
                datastring: datastring,
                dataType: "html",
                success: function (task) {
                    task = JSON.parse(task);
                    notificationsApp.registerTask(task);
                    notificationsApp.show();
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    console.log(textStatus, errorThrown);
                }
            })
        );
    }

    // Wait for all asynchronous calls to finish
    $.when.apply($, calls)
      .done(function () {
          window.location.href = "/my-resources/";
      })
      .fail(function () {
          customAlert("Error", 'Failed to delete resource(s).', "error", 10000);
          $("html").css("cursor", "initial"); // Restore default cursor
      });
}

function errorLabel(message) {
    return "<div class='label label-danger error-label'>" + message + "</div>";
}

function label_ajax_submit() {
    var el = $(this);
    var formType = el.attr("data-form-type");

    if (formType == "create-label"){
        var labelText = $("#txtLabelName").val();
        var sanitizedLabelText = $("<div/>").html(labelText.trim()).text();
        let message = "";
        if (labelText.length >= 75){
            message = "Your label was too long. Please trim it to < 75 characters.";
        }else if (labelText.trim().length === 0){
            message = "Your label was empty, please try again.";
        }else if (labelText !== sanitizedLabelText){
            message = "Your label contains HTML and cannot be saved.";
        }
        $("#user-labels-left input").each(function(i, el){
            if ($(el).attr("data-label") === sanitizedLabelText){
                message = "You entered a duplicate label.";
            }
        });

        if(message){
            $("#txtLabelName").closest(".modal-body").append(errorLabel(message))
            $("#txtLabelName").addClass("invalid-input");
            return;
        }
    }
    
    $("#txtLabelName").val(labelText);
    var form = $("form[data-id='" + el.attr("data-form-id") + "']");
    var datastring = form.serialize();
    var url = form.attr('action');
    var tableRow = form.closest("tr");

    $.ajax({
        type: "POST",
        url: url,
        dataType: 'html',
        data: datastring,
        success: function (result) {
            var json_response = JSON.parse(result);
            if (json_response.status == "success") {
                var rowIndex = resourceTable.row(tableRow).index();
                if (formType == "create-label") {
                    createLabel();
                }
                else if (formType == "delete-label") {
                    var deletedLabel = el.attr("data-label");
                    $("#table-user-labels td[data-label='" + deletedLabel + "']").parent().remove();
                    if ($("#table-user-labels .user-label").length == 0 && $("#table-user-labels .no-items-found").length == 0) {
                        $("#table-user-labels tbody").append(
                                '<tr class="no-items-found"><td>No labels found.</td></tr>'
                        )
                    }
                    updateLabelsList();
                    updateLabelDropdowns();
                    refreshToolbarCheckboxState();
                }
                else if (formType == "toggle-favorite") {
                    var action = form.find("input[name='action']");

                    el.toggleClass("isfavorite");

                    if (json_response.action == "DELETE") { // Got unchecked
                        action.val("CREATE");
                        resourceTable.cell(rowIndex, FAVORITE_COL).data("").draw();
                    }
                    else {                          // Got checked
                        action.val("DELETE");

                        resourceTable.cell(rowIndex, FAVORITE_COL).data("Favorite").draw();  // .draw refreshed the internal cache of the table object
                    }
                }
                else if (formType = "toggle-label") {
                    var action = form.find("input[name='action']");
                    var label = el[0].value;

                    var currentCell = resourceTable.cell(rowIndex, LABELS_COL);

                    var dataColLabels = currentCell.data().replace(/\s+/g,' ').split(","); // List of labels already applied to the resource;

                    // Remove extra spaces from the labels collection
                    for (var i = 0; i < dataColLabels.length; i++) {
                        dataColLabels[i] = dataColLabels[i].trim();
                    }

                    if (json_response.action == "DELETE") { // Label got unchecked
                        action.val("CREATE");
                        var labelIndex = dataColLabels.indexOf(label);
                        dataColLabels.splice(labelIndex, 1);    // Remove label
                        currentCell.data(dataColLabels.join()).draw();
                    }
                    else {
                        action.val("DELETE");       // Label got checked
                        dataColLabels.push(label);
                        currentCell.data(dataColLabels.join()).draw();
                    }

                    // If the row has labels, color the label icon blue
                    var labelButton = tableRow.find(".btn-inline-label");
                    if (dataColLabels.length > 0) {
                        if (dataColLabels.length == 1 && dataColLabels[0].trim() == "") {   // The list could have an empty []
                            labelButton.removeClass("has-labels");
                        }
                        else {
                            labelButton.addClass("has-labels");
                        }
                    }
                    else {
                        labelButton.removeClass("has-labels");
                    }
                }

                updateLabelCount();
                refreshToolbarCheckboxState();
            }
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {

        }
    });

    //don't submit the form
    return false;
}

// Updates the status of labels in the dropdowns of table rows
function updateLabelsList() {
    $("#user-labels-left").empty();

    var labels = $("#table-user-labels td.user-label");

    if (labels.length === 0) {
        $("#user-labels-left").append(
          '<i class="list-group-item no-items-found"><h5>No labels found.</h5></i>'
        );
    }
    else {
        for (var h = 0; h < labels.length; h++) {
            var curr = $(labels[h]).text();

            $("#user-labels-left").append(
              '<li class="list-group-item">' +
              '<span class="badge">0</span>' +
              '<label class="checkbox">' +
              '<input data-label="' + curr + '" type="checkbox">' + curr + '</label>' +
              '</li>'
            );
        }
    }
}

// Gets new data when filters change
async function dataRefresh(target){
    
    // Check the url for query parameters
    let url = new URL(window.location.href);
    let filter_val = target.value.toLowerCase();
    let existing_filters = url.searchParams.getAll('f');
    if (existing_filters){
        let index = existing_filters.indexOf(filter_val);
        if(index > -1){
            if (!target.checked){
                existing_filters.splice(index, 1);
                url.searchParams.delete('f');
                existing_filters.forEach(filter => url.searchParams.append('f', filter));
            }
        }else{
            if (target.checked){
                url.searchParams.append('f', filter_val);
            }
        }
    }

    window.history.pushState({}, '', url);

    if(target.checked && !filtersLoaded.includes(filter_val)){
        // fetch the filter that is new
        await ajaxFetchResources(url, filter_val);
    }else{
        updateTable();
    }
}

function ajaxFetchResources(url, filter_val){
    $("#filter-panel .panel-title").append(spinner);
    $("#filter").addClass("no-interact")
    $('#item-selectors tbody').hide();
    $('#item-selectors thead').hide();

    $.ajax({
        type: 'GET',
        url: url,
        data: {
            new_filter: filter_val
        }
    })
    .done(function(data){
        resourceTable.destroy();
        $('#item-selectors tbody').append(data.trows);
        resourceTable = initTable('#item-selectors');
        resourceTable.deDupe();
        resourceTable.draw();
        filtersLoaded.push(filter_val);
    })
    .fail(function(jqXHR, textStatus, errorThrown) {
        customAlert("Error", `Failed fetch resources for your filter (${errorThrown})`, "error", 10000);
    })
    .always(function(){
        $('#item-selectors thead').show();
        $('#item-selectors tbody').show();
        spinner.remove();
        $("#filter").removeClass("no-interact");
        updateTable();
    });
}

// Updates the status of labels in the left panel
function updateLabelDropdowns() {
    $(".inline-dropdown ul").empty();
    $("#toolbar-labels-dropdown ul :not(.persist)").empty();
    $(".btn-inline-label").removeClass("has-labels");

    var labels = $("#table-user-labels td.user-label");
    for (var h = 0; h < labels.length; h++) {
        var curr = $(labels[h]).text();

        var dropdowns = $(".inline-dropdown ul");

        if (dropdowns) {
            for (var i = 0; i < dropdowns.length; i++) {
                var res_id = $(dropdowns[i]).attr("data-resource-id");
                var formID = "form-" + i + "-" + h + "-" + res_id;
                $(dropdowns[i]).append(
                        '<li>' +
                        '<label class="checkbox"><input data-form-type="toggle-label" data-form-id="' + formID + '" type="checkbox" value="' + curr + '">' + curr + '</label>' +
                        '<form data-id="' + formID + '" class="hidden-form" action="/hsapi/_internal/' + res_id + '/label-resource-action/"' +
                        'method="post">' +
                        document.getElementById("csrf").innerHTML +
                        '<input type="hidden" name="label" value="' + curr + '">' +
                        '<input type="hidden" name="label_type" value="LABEL">' +
                        '<input type="hidden" name="action" value="CREATE">' +
                        '</form>' +
                        '</li>'
                );
            }
        }

        if ($(".row-selector:checked").length == 0) {
            $("#toolbar-labels-dropdown ul").prepend(
                    '<li>' +
                    '<label class="checkbox"><input disabled type="checkbox" value="' + curr + '">' + curr + '</label>' +
                    '</li>'
            );
        }
        else {

            $("#toolbar-labels-dropdown ul").prepend(
                    '<li>' +
                    '<label class="checkbox"><input type="checkbox" value="' + curr + '">' + curr + '</label>' +
                    '</li>'
            );
        }
    }

    // Check checkboxes for labels currently in the resource
    if (dropdowns) {
        for (var i = 0; i < dropdowns.length; i++) {
            var rowIndex = resourceTable.row($(dropdowns[i]).closest("tr")).index();

            var dataColLabels = resourceTable.cell(rowIndex,LABELS_COL).data().replace(/\s+/g,' ').split(",");

            for (var j = 0; j < dataColLabels.length; j++) {
                var label = dataColLabels[j].trim();
                var currentCheckbox = $(dropdowns[i]).find("input[type='checkbox'][value='" + label + "']");
                currentCheckbox.prop("checked", true);
                currentCheckbox.closest("li").find("form input[name='action']").val("DELETE");
            }

            if (dataColLabels.length > 0) {
                if (dataColLabels.length == 1 && dataColLabels[0].trim() == "") {
                    $(dropdowns[i]).closest("tr").find(".btn-inline-label").removeClass("has-labels");
                }
                else {
                    $(dropdowns[i]).closest("tr").find(".btn-inline-label").addClass("has-labels");
                }
            }
        }
    }

    if (labels.length == 0) {
        $("#toolbar-labels-dropdown ul").prepend(
                 '<i class="no-items-found list-group-item"><h5>No labels found.</h5></i>'
        );

        $(".btn-inline-label").attr("data-toggle", "");
    }
    else {
        $(".btn-inline-label").attr("data-toggle", "dropdown");
    }

    // Prevents dropdown form getting dismissed when clicking on items
    $('.dropdown-menu label, .list-labels label').click(function (e) {
        e.stopPropagation();
    });
}

// Checks and unchecks label checkbox in the toolbar depending on which table rows are selected.
function refreshToolbarCheckboxState() {
    var toolbarLabels = $("#toolbar-labels-dropdown input[type='checkbox']");
    var selectedRows = $(".row-selector:checked");
    if (selectedRows.length == 0) {
        toolbarLabels.attr("disabled", true);
        return;
    }

    toolbarLabels.attr("disabled", false);
    toolbarLabels.prop("checked", true);

    var inlineCheckboxes = selectedRows.parent().find(".inline-dropdown input[type='checkbox']:not(:checked)");

    // Uncheck label checkbox in toolbar
    for (var i = 0; i < inlineCheckboxes.length; i++) {
        var label = $(inlineCheckboxes[i]).val();
        $("#toolbar-labels-dropdown .list-labels input[type='checkbox'][value='" + label + "']").prop("checked", false);
    }
}

function createLabel () {
    if ($("#txtLabelName").val() != "") {
        var userLabelsTable = $("#table-user-labels tbody");
        userLabelsTable.append(
                '<tr>' +
                    '<td class="user-label" data-label="' + $("#txtLabelName").val() + '">' + $("#txtLabelName").val() + '</td>' +
                    '<td>'+
                        '<form class="hidden-form" data-id="form-delete-label-'+ $("#txtLabelName").val() + '" ' +
                              'action="/hsapi/_internal/label-resource-action/"'+
                              'method="post">'+
                            document.getElementById("csrf").innerHTML +
                            '<input type="hidden" name="label" value="' + $("#txtLabelName").val() + '">'+
                            '<input type="hidden" name="label_type" value="SAVEDLABEL">'+
                            '<input type="hidden" name="action" value="DELETE">'+
                        '</form>'+
                        '<span data-label="' + $("#txtLabelName").val() + '" data-form-type="delete-label"'+
                              'class="btn-label-remove glyphicon glyphicon-remove"'+
                              'data-form-id="form-delete-label-' + $("#txtLabelName").val() + '"></span>'+
                    '</td>'+
                '</tr>');

        userLabelsTable.find(".no-items-found").remove();

        $(".btn-label-remove").click(label_ajax_submit);
        $("#modalCreateLabel").modal('hide');
        $("#txtLabelName").val("");
        updateLabelsList();
        updateLabelDropdowns();
    }
}



async function updateFilterCount() {
    if( !filtersUpdated ){
        $("#toolbar-labels-dropdown input[type='checkbox']").prop("checked", true);
        var favorites = 0;
        var ownedCount = 0;
        var addedCount = 0;
        var sharedCount = 0;
        await getFilterCounts();
    }
    function getFilterCounts(){
        return $.ajax({
            type: 'GET',
            url: '/my-resources-counts/',
            success: function (data) {
                favorites = data.filter_counts.favorites;
                ownedCount = data.filter_counts.ownedCount;
                addedCount = data.filter_counts.addedCount;
                sharedCount = data.filter_counts.sharedCount;
                $(".my-res-filter-spinner").remove();
                    // Update filter badges count
                $("#filter .badge[data-facet='owned']").text(ownedCount);
                $("#filter .badge[data-facet='shared']").text(sharedCount);
                $("#filter .badge[data-facet='discovered']").text(addedCount);
                $("#filter .badge[data-facet='favorites']").text(favorites);
                filtersUpdated = true;
            }
        })
    }
}

function updateLabelCount() {
    var recentCount = 0;
    var favorites = 0;
    var collection = [];

    var cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - 5);
    cutoff = Math.floor(cutoff.getTime() / 1000); // Seconds since the unix epoch,
    // subtract cutoff.getTimezoneOffset() * 60 to convert to local timezone

    resourceTable.rows().every(function(rowIndex, tableLoop, rowLoop) {
        // List of labels already applied to the resource;
        var dataColLabels = this.data()[LABELS_COL].replace(/\s+/g, ' ').split(",");
        var dataColFavorite = this.data()[FAVORITE_COL].trim();

        if (dataColFavorite == "Favorite") {
            favorites++;
        }

        if (this.data()[LAST_MODIF_SORT_COL] >= cutoff) {
            recentCount++;
        }

        // Loop through the labels in the row and update the collection count
        for (var i = 0; i < dataColLabels.length; i++) {
            var label = dataColLabels[i].trim();
            if (!collection[label]) {
                collection[label] = 0;
            }
            collection[label]++;
        }
    });

    $("#filter .badge[data-facet='recent']").text(recentCount);
    $("#filter .badge[data-facet='favorites']").text(favorites);

    // Set label counts
    for (var key in collection) {
        $("#labels input[data-label='" + key + "']").parent().parent().find(".badge").text(collection[key]);
    }
}

//strips query inputs from a search string
function removeQueryOccurrences(inputString) {
    // Matches occurrences of query strings. i.e.: "[author:mauriel ramirez]", "[]", etc
    var regExp = /\[([^\]|^\[]?)+\]/g;
    var occurrences = inputString.match(regExp);

    if (occurrences) {
        // Remove query occurrences from input string
        for (var i = 0; i < occurrences.length; i++) {
            inputString = inputString.replace(occurrences[i], "");
        }
    }

    return inputString;
}

// Looks at the query strings in the searchbox and sets the values in the dropdown options
function applyQueryStrings() {
    var inputString = $("#resource-search-input").val().toLowerCase();
    // Matches occurrences of query strings. i.e.: author:mauriel
    var regExp = /\[(type|author|subject):[^\]|^\[]+]/g;
    var occurrences = inputString.match(regExp);

    var inputType = "";
    var inputSubject = "";
    var inputAuthor = "";

    var collection = [];
    if (occurrences) {
        for (var item in occurrences) {
            var content = occurrences[item].replace("[", "").replace("]", "").split(":");
            collection.push(content);
        }
    }

    for (var item in collection) {
        if (collection[item][0].toUpperCase() == "TYPE") {
            inputType = collection[item][1];
        }
        else if (collection[item][0].toUpperCase() == "AUTHOR") {
            inputAuthor = collection[item][1];
        }
        else if (collection[item][0].toUpperCase() == "SUBJECT") {
            inputSubject = collection[item][1];
        }
    }

    $("#input-author").val(inputAuthor);
    $("#input-subject").val(inputSubject);
    $("#input-resource-type").val(inputType.toLowerCase());

}

// Looks at the values in the dropdown options and appends the corresponding query string to the search box.
function typeQueryStrings () {
    var searchInput = $("#resource-search-input");

    var type = $("#input-resource-type").val();
    var author = $("#input-author").val();
    var subject = $("#input-subject").val();

    var searchQuery = "";

    if (type) {
        if (type === "composite resource") {
            type = "resource";
        }
        else if (type === "collection resource") {
            type = "collection";
        }
        else if (type === "web app resource") {
            type = "app connector";
        }
        searchQuery = searchQuery + " [type:" + type + "]";
    }

    if (author) {
        searchQuery = searchQuery + " [author:" + author + "]";
    }

    if (subject){
        searchQuery = searchQuery + " [subject:" + subject + "]";
    }

    searchQuery = searchQuery + removeQueryOccurrences(searchInput.val());
    searchQuery = searchQuery.trim();
    searchInput.val(searchQuery);
}

/*==================================================
    Table columns
    0 - actions
    1 - Resource Type
    2 - Title
    3 - Owner
    4 - Date Created
    5 - Last Modified
    6 - Subject
    7 - Authors
    8 - Permission Level
    9 - Labels
    10 - Favorite
    11 - Last modified (sortable format)
    12 - Sharing Status
    13 - Date created (sortable format)
    14 - Access Grantor
==================================================*/

/* Custom filtering function which will search data for the values in the custom filter dropdown or query strings */
// https://datatables.net/manual/plug-ins/search
$.fn.dataTable.ext.search.push (
    function (settings, data, dataIndex) {
        var inputString = $("#resource-search-input").val().toLowerCase();
        // Matches occurrences of query strings. i.e.: author:mauriel
        var regExp = /\[(type|author|subject):[^\]|^\[]+]/g;
        var occurrences = inputString.match(regExp);

        var inputType = "";
        var inputSubject = "";
        var inputAuthor = "";

        // Split the occurrences at ':' and move to an array.
        var collection = [];
        if (occurrences) {
            for (var item in occurrences) {
                var content = occurrences[item].replace("[", "").replace("]", "").split(":");
                collection.push(content);
            }
        }

        // Extract the pieces of information
        for (var item in collection) {
            if (collection[item][0].toUpperCase() == "TYPE") {
                inputType = collection[item][1];
            }
            else if (collection[item][0].toUpperCase() == "AUTHOR") {
                inputAuthor = collection[item][1];
            }
            else if (collection[item][0].toUpperCase() == "SUBJECT") {
                inputSubject = collection[item][1];
            }
        }

        // Filter the table for each value
        if (inputType && data[RESOURCE_TYPE_COL].toUpperCase().indexOf(inputType.toUpperCase()) < 0) {
            return false;
        }

        if (inputSubject && data[SUBJECT_COL].toUpperCase().indexOf(inputSubject.toUpperCase()) < 0) {
            return false;
        }

        if (inputAuthor && data[AUTHORS_COL].toUpperCase().indexOf(inputAuthor.toUpperCase()) < 0) {
            return false;
        }

        let inFilters = false;

        if ($("#filter").find("input[type='checkbox']:checked").length) {
            //---------------- Facet filters --------------------
            // Owned by me
            if ($('#filter input[type="checkbox"][value="Owned"]').prop("checked") == true) {
                if (data[PERM_LEVEL_COL] == "Owned") {
                    inFilters = true;
                }
            }

            // Shared with me
            if ($('#filter input[type="checkbox"][value="Shared"]').prop("checked") == true) {
                if (data[PERM_LEVEL_COL] != "Owned" && data[PERM_LEVEL_COL] != "Discovered" && data[PERM_LEVEL_COL] != "") {
                    inFilters = true;
                }
            }

            // Added by me
            if ($('#filter input[type="checkbox"][value="Discovered"]').prop("checked") == true) {
                if (data[PERM_LEVEL_COL] == "Discovered") {
                    inFilters = true;
                }
            }

            // Favorite
            if ($('#filter input[type="checkbox"][value="Favorites"]').prop("checked") == true) {
                if (data[FAVORITE_COL] == "Favorite") {
                    inFilters = true;
                }
            }

            // Recent
            if ($('#filter input[type="checkbox"][value="Recent"]').prop("checked") == true) {
                var cutoff = new Date();
                cutoff.setDate(cutoff.getDate() - 5);
                cutoff = Math.floor(cutoff.getTime() / 1000); // Seconds since the unix epoch
                // Subtract cutoff.getTimezoneOffset() * 60 to convert to local timezone
                if (data[LAST_MODIF_SORT_COL] >= cutoff) {
                    inFilters = true;
                }
            }
        }
        else {
            inFilters = true;    // Ignore if nothing selected
        }

        // Shared by - Used in group resource listing
        var grantors = $('#filter-shared-by .grantor:checked');
        let inGrantors = false;
        if (grantors.length) {
            for (var i = 0; i < grantors.length; i++) {
                var user = parseInt($(grantors[i]).attr("data-grantor-id"));
                if (parseInt(data[ACCESS_GRANTOR_COL]) == user) {
                    inGrantors = true;
                    break;
                }
            }
        }
        else {
            inGrantors = true;  // Ignore if nothing selected
        }

        // Labels - Check if the label exists in the table
        let inLabels = false;
        var labelCheckboxes = $("#user-labels-left input[type='checkbox']:checked");
        if (labelCheckboxes.length) {
            for (var i = 0; i < labelCheckboxes.length; i++) {
                var label = $(labelCheckboxes[i]).attr("data-label");

                var dataColLabels = data[LABELS_COL].replace(/\s+/g, ' ').split(",");
                for (var h = 0; h < dataColLabels.length; h++) {
                    dataColLabels[h] = dataColLabels[h].trim();
                }

                if (dataColLabels.indexOf(label) >= 0) {
                    inLabels = true;
                }
            }
        }
        else {
            inLabels = true;    // Ignore if nothing selected
        }

        return inLabels && inFilters && inGrantors;
    }
);

$.fn.dataTable.Api.register('deDupe', function (idColumn) {
    idColumn = idColumn || TITLE_COL;

    let regex = /resource\/([0-9a-z]*)\/">/;
    let titles = this.columns().data()[idColumn];
    let resIds = titles.map(x => x.match(regex)[1]);

    let i=0;
    while(i < resIds.length) {
        let matchedIndex = resIds.lastIndexOf(resIds[i]);
        if(matchedIndex !== i) {
            let matchedRow = $(this.rows().nodes()[i]);
            this.row(matchedRow).remove();
            resIds.splice(matchedIndex, 1);
        }
        i++;
    }
    
    return this;
  });