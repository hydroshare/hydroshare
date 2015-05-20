
// subscribe to the OnChange event for the model_name listbox
var model_list = document.getElementById('id_model_name');
model_list.addEventListener('change', show_model_details);

// Build a text area to display model information
var div = document.getElementById("div_id_model_name");
var desc = document.createElement("div");
desc.id = 'div_mp_details';
desc.style.height = "auto";
//desc.overflow= auto;
desc.style.width = "100%";
//desc.style.backgroundColor = '#f0f0f0';
desc.style.border = "1px solid #a0a0a0";
div.appendChild(desc);

// set the initial visibility of the description div
setTextAreaVisibility();
if (!desc.hidden){
    show_model_details(null);
}

function setTextAreaVisibility() {
    // get the text value of the select list
    var txt = model_list.item(model_list.selectedIndex).text

    // set the visibility of the text area
    if (txt != 'Unknown') {
        desc.hidden = false;
    }
    else {
        desc.hidden = true;
    }
}

function show_model_details(e) {

    // update the text area visibility
    setTextAreaVisibility();

    // get the id of the current model program name
    var shortid = model_list.item(model_list.selectedIndex).value;

    // call django view to get model program metadata
    $.ajax({
        type: "GET",
        url: '/hsapi/_internal/get-model-metadata/',
        data: {resource_id:shortid},
        success: function (data) {

            // if the data is empty, hide the table
            if (Object.keys(data).length == 0){
                // set the visibility of the table element
                table = document.getElementById('progam_details_div');
                table.style.display = 'none';
            }
            // if the data is not empty, populate the model details table
            else {
                // set the visibility of the table element
                table_div = document.getElementById('progam_details_div');
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
        }
    });

}
