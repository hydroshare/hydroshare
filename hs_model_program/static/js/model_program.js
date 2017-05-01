/**
 * Created by tonycastronova on 10/12/15.
 */

$mp_alert_error = '<div class="alert alert-danger" id="error-alert"> \
                    <button type="button" class="close" data-dismiss="alert">x</button> \
                    <strong>Error </strong> \
                    failed to retrieve metadata for this resource.\
                </div>'


$(document).ready(function () {

    // check to see if the view is in edit mode
    if(document.getElementById("id-mpmetadata") != null)
        // load jquery generated elements
        loadWidgets();

        // initialize datepicker
        $( "#modelReleaseDate_picker" ).datepicker({

            // **
            // * Sets the hidden date field base on the datepicker.  The hidden field is what is submitted.
            // */
            onSelect: function (event) {

                // set the value of the hidden date field which will be submitted to the server on Save
                var date = document.getElementById('id_modelReleaseDate');
                var date_picker = document.getElementById("modelReleaseDate_picker");
                date.value = date_picker.value;

                // activate the save button
                $("#resourceSpecificTab").find('.btn-primary').show();
            }
        });
});

/**
 * Builds jQuery multiselect listboxes
 */
function loadWidgets(){

    // get the resource id from its url
    var url = document.URL;
    var url_array = url.split('/');
    var shortid = url_array[url_array.length - 2];

    // call django view to get model program metadata files
    $.ajax({
        type: "GET",
        url: '/hsapi/_internal/get-model-metadata/',
        data: {resource_id: shortid},
        success: function (data) {

            // get the multiselect items
            var multiselect = $("#id-mpmetadata fieldset .div-multi-select");

            for (var i = 0; i < multiselect.length; i++) {

                // get the metadata term associated with this multiselect field
                var term = multiselect[i].getAttribute('parent_metadata');

                // get the selected items that are saved to the resource
                var selected_terms = data[term];

                // loop through the options in the select list
                var options = $(multiselect[i]).find('option');
                for (var j = 0; j < options.length; j++) {

                    // set the selected attribute
                    if ($.inArray(options[j].value, selected_terms) >= 0) {
                        $(options[j]).attr("selected", 1);
                    }
                }
            }

            // set the initial value for the date picker
            var date = new Date(data['date_released']);
            if (isNaN(date) == false)
                $('#modelReleaseDate_picker').datepicker('setDate', date);

        },
        error: function (data) {
            show_error();
        },
        complete: function (data) {
            // once the selected fields (html) have been updated, build the jQuery multiselect boxes

            // destroy all multiselect listboxes for the model program resource (i.e.  that match the id mp-multi-select)
            $('#mp-multi-select.multi-select').multiselect('destroy');

            // get the size of the parent div
            var width = $('#mp-div-multiselect').css('max-width');

            // rebuild all the multiselect elements for the model program resource
            $('#mp-multi-select.multi-select').multiselect({
                buttonWidth: width,
                maxHeight: 200,
                numberDisplayed: 1,

                // bind to drop down list close event
                onDropdownHide: function (event, checked) {
                    set_metadata_terms(event);
                }
            });

            // add pull-right attribute to the dropdown menus
            var dd = $('.div-multi-select > .btn-group > .multiselect-container.dropdown-menu');
            for (var i = 0; i < dd.length; i++) {
                var classname = dd[i].className;
                if (classname.indexOf(' pull-right ') == -1) {
                    dd[i].className += ' pull-right';
                }
            }
        }
    });
}

function show_error(){
    $('body > .container').append($mp_alert_error);
    $(".alert-danger").fadeTo(3000, 500).fadeOut(1000, function(){
        $(".alert-danger").alert('close');
    });
}

/**
 * reloads the jQuery multi-select widgets on form submission
 */
$(document).on("submit-success submit-error", function(event){
    // reload dynamically generated widgets
    loadWidgets();
});

/**
 * Sets multi-select selections to hidden field values that are submitted with the form
 * @param e
 */
function set_metadata_terms(e){

    // get parent div
    var parent = $(e.currentTarget.parentElement);

    // get selected items from select list
    var selected = parent.find('#mp-multi-select').find("option:selected");

    // objects to store names and values in hidden metadata fields
    var values = [];

    // grab all of the selected values
    for (var i=0; i<selected.length; i++){
        values.push(selected[i].value);
    }

    // get parent metadata term
    var parent_meta_term = parent.get(0).getAttribute('parent_metadata');

    // get the metadata element based on this parent term
    var meta = document.getElementById("id_"+parent_meta_term);

    // set the value for this hidden field
    meta.value = values.join(';');

    // activate the save button
    $("#resourceSpecificTab").find('.btn-primary').show();
}
