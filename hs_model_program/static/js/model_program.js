/**
 * Created by tonycastronova on 10/12/15.
 */


$(document).ready(function () {

    // initialize help text popover
    $('[data-toggle="popover"]').popover({
        container: 'body'
    });

    // initialize bindings for multiselect boxes
    $('.multi-select').multiselect({
        // bind to the on close event
        onDropdownHide: function (event, checked) {
            populate_dropdown_table(event, checked);
        }
    });

    // add pull-right to the dropdown-menu
    var dd = document.getElementsByClassName('multiselect-container dropdown-menu');
    for (var i = 0; i < dd.length; i ++){
        var classname = dd[i].className;
        if (classname.indexOf(' pull-right ') == -1 ){
           dd[i].className += ' pull-right';
        }
    }
});

function populate_dropdown_table(e, checked){

    // get parent div
    var parent = $(e.currentTarget.parentElement);

    // get selected items from select list
    var selected = parent.find('#multi-select').find("option:selected");


    // objects to store names and values in hidden metadata fields
    var values = [];

    // grab all of the selected values
    for(var i=0; i<selected.length; i++){
        values.push(selected[i].value+':'+selected[i].innerHTML);
    }

    // get parent metadata term
    var parent_meta_term = parent.get(0).getAttribute('parent_metadata');

    // get the metadata element based on this parent term
    var meta = document.getElementById("id_"+parent_meta_term);

    // set the value for this hidden field
    meta.value = values.join();

    // activate the save button
    $("#resourceSpecificTab").find('.btn-primary').show();
}