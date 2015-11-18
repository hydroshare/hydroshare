
// variable to store the last submitted model program id
var mp_old_id = '';

/*
  Initialize the view on document ready
 */
$(document).ready(function(){

    // proceed only if selectbox_ exists (i.e. edit page)
    if($('[id^=selectbox_]').length > 0) {

        // set the initial value of the mp_old_id
        mp_old_id = $('[id^=selectbox_]').attr('id').split('_').pop();

        // initialize the model program listbox
        build_selectbox();

        // set the initial selection
        set_model_program_selection();

        // build metadata table (ajax query)
        show_model_details();


    }

});

/*
  Sets the selected item in the selectbox if a ModelProgram foreign key relationship has previously been set in the
  database.
 */
function set_model_program_selection(){

        // get the value stored in the model_name hidden field
        var mp_id = $('[id^=selectbox_]').attr('id').split('_').pop();

        // set the initial selection
        var model_name = document.getElementById('id_model_name');
        model_name.value = mp_id;

        // get the selectbox
        var options = $('[id^=selectbox_]').find('option');

        if (mp_id != "")
        {
            for (var i = 0; i< options.length; i++){
                var o = options[i];
                if (o.value == mp_id) {
                    $(o).attr("selected", 1);
                    break;
                }
            }
        }
        else {
            // set selected to 'Not Specified' if mp_id is empty
            $(options[0]).attr("selected", 1);
        }
}


/*
 Constructs a select box for the ModelProgram elements using JQuery.  This selectbox is used to define the
 ModelProgram foreign key relationship.
 */
function build_selectbox(){

    // destroy any existing multiselect widgets
    $('[id^=selectbox_].selectbox').multiselect('destroy');

    // rebuild the multiselect elements
    $('[id^=selectbox_].selectbox').multiselect({

        // specify a max height in case there are lots of models
        maxHeight: 200,

        /*
         Add any other selectbox attributes here.
         http://davidstutz.github.io/bootstrap-multiselect/
         e.g.
            dropRight: true,
            buttonWidth: '400px',
         */

        // bind to mulitselect box events
        onDropdownHide: function(event, checked){
            // populate a table of model program metadata when the selectbox closes
            show_model_details();

        }

    });


}

/*
    Queries for ModelProgram metadata using AJAX.  Populates a table on the edit page that displays this data.  If the
    selected ModelProgram has changed, the Save button is activated.
 */
function show_model_details() {

    // get the short id of the selected item
    var shortid = $('[id^=selectbox_]').parent().find("option:selected").val();

    // call django view to get model program metadata
    $.ajax({
        type: "GET",
        url: '/hsapi/_internal/get-model-metadata/',
        data: {resource_id:shortid},
        success: function (data) {

            // if the data is empty, hide the table
            if (Object.keys(data).length == 0){
                // set the visibility of the table element (hide)
                table = document.getElementById('program_details_div');
                table.style.display = 'none';
            }
            // if the data is not empty, populate the model details table
            else {
                // set the visibility of the table element (visible)
                table_div = document.getElementById('program_details_div');
                table_div.style.display = 'block';

                // create and ordered list of keys to access input data
                var keys = ["description", "date_released", "software_version", "software_language", "operating_sys", "url"];

                // populate metadata inside description div
                var rows = document.getElementById('program_details_table').rows;
                for (i = 0; i < rows.length; i++) {

                    // get the current row element
                    var row = rows[i];

                    // get the second cell in the row
                    var cell = row.cells[1];

                    if (keys[i] != "url") {
                        // set the text for this cell
                        cell.innerText = data[keys[i]]
                    }
                    else {
                        // insert an href for the url item
                        cell.innerHTML = "<a href= " + data['url'] + " target='_blank'>Resource Landing Page</a>"
                    }
                }
            }
        },
        error: function (data) {
            console.log('There was an error with model instance GET.')
        },
        complete: function(data){

            // Sets the ModelProgram shortid to the hidden model_name field.  This field is submitted to django and used to set
            // database fields ModelName and ModelForeignKey.
            document.getElementById('id_model_name').value = shortid;

            // enable/disable the save button if the value has been changed to something new
            if (shortid != mp_old_id)
                $('#id-executedby').find('.btn-primary').show();
            else
                $('#id-executedby').find('.btn-primary').hide();
        }
    });

}

/*
    Save the submitted id globally
 */
$(document).bind("submit-success", function(event){
    mp_old_id = $('[id^=selectbox_]').parent().find("option:selected").val();
});
