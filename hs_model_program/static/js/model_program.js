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

    // get table div
    var table_div = $(e.currentTarget.parentElement).find("#div_section_table").get(0);

    // get the section table corresponding to the current select box
    var table = $(e.currentTarget.parentElement).find("#section_table").get(0);


    // clear table elements
    table.innerHTML = "";

    // set table visibility
    if (selected.length > 0){
        table_div.style.display = "block";
    }
    else{
        table_div.style.display = "none";
    }

    // objects to store names and values in hidden metadata fields
    var values = [];

    // populate the table
    for(var i=0; i<selected.length; i++){
        var row = table.insertRow(i);
        row.setAttribute("class", "selection_row");
        var cell = row.insertCell(0);
        cell.setAttribute("value",selected[i].value);
        cell.innerHTML = selected[i].innerHTML;

        // save this value for later use
        values.push(selected[i].value+':'+selected[i].innerHTML);
    }

    // get parent metadata term
    var parent_meta_term = parent.get(0).getAttribute('parent_metadata');

    // get the metadata element based on this parent term
    var meta = document.getElementById("id_"+parent_meta_term);

    // set the value for this hidden field
    meta.value = values.join();

}

//
//<button type="button" class="btn btn-default btn-sm">
//          <span class="glyphicon glyphicon-remove"></span> Remove
//        </button>
//
//function show_model_details() {
//
//    // get the id of the current model program name
//    var shortid = document.getElementById("res_id").value;
//
//    // call django view to get model program metadata
//    $.ajax({
//        type: "GET",
//        url: '/hsapi/_internal/get-model-files/',
//        data: {resource_id: shortid},
//        success: function (data) {
//
//            // get all multichar items
//            var items = document.getElementsByClassName("multichar");
//            if (items) {
//                for (var i = 0; i < items.length; i++) {
//                    var item = items[i];
//                    var name = item.name;
//                    var container = document.getElementById("div_id_"+name);
//
//                    if(!document.getElementById(name+'_listbox')) {
//                        // create div for dropdown
//                        var div = document.createElement('div');
//                        div.setAttribute('id', name + '_listbox');
//
//                        div.setAttribute('class', 'filelistbox');
//
//                        // create dropdown boxes for each multichar item
//                        var select = document.createElement('select');
//                        select.setAttribute('class', 'form-control input-sm select');
//                        select.setAttribute('name', name);
//                        for(var key in data) {
//                            var option = document.createElement('option');
//                            option.value = data[key];
//                            option.text = key;
//                            select.appendChild(option);
//                        }
//                        select.addEventListener('change', add_field);
//                        div.appendChild(select);
//
//                        // add div to current element
//                        document.getElementById(container.id).appendChild(div);
//
//
//                        // create ul object for each listbox
//                        var e = document.createElement('ul');
//                        e.setAttribute('id', name + '_ul');
//                        e.setAttribute('class', 'filelist');
//                        document.getElementById(container.id).appendChild(e);
//                    }
//                }
//            }
//            //alert('success');
//        }
//    });
//}

//function add_field(e){
//
//    var elem = e.currentTarget;
//    var options = elem.options;
//    var idx = elem.selectedIndex;
//
//    // get ul for the selection
//    var ul = document.getElementById(elem.name+'_ul');
//
//    // add a list item for the selection
//    var li = document.createElement('li');
//    li.appendChild(document.createTextNode(options[idx].innerHTML));
//    ul.appendChild(li);
//
//}
