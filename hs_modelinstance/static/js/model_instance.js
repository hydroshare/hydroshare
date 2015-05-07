
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

            // populate metadata inside description div

            c1 = '#f0f0f0';
            c2 = '#f8f8f8';

            desc.innerHTML = "<table cellpadding='1' style='width:100%;'>" +
            "<tr bgcolor="+c1+"><td style='padding:4px 20px 4px 4px;width:1%;white-space:nowrap;'><strong>Description: </strong></td> " +
            "       <td align='left'>"+data['description']+"</td></tr>" +
            "<tr bgcolor="+c2+"><td style='padding:4px 20px 4px 4px;width:1%;white-space:nowrap;'><strong>Release Date: </td>                " +
            "       <td align='left'>"+data['date_released']+"</td></tr>" +
            "<tr bgcolor="+c1+"><td style='padding:4px 20px 4px 4px;width:1%;white-space:nowrap;'><strong>Version: </strong></td>            " +
            "       <td align='left'>"+data['software_version']+"</td></tr>" +
            "<tr bgcolor="+c2+"><td style='padding:4px 20px 4px 4px;width:1%;white-space:nowrap;'><strong>Language: </strong> </td>          " +
            "       <td align='left'>"+data['software_language']+"</td></tr>" +
            "<tr bgcolor="+c1+"><td style='padding:4px 20px 4px 4px;width:1%;white-space:nowrap;'><strong>Operating System: </strong></td>   " +
            "       <td align='left'>"+data['operating_sys']+"</td></tr>" +
            "<tr bgcolor="+c2+"><td style='padding:4px 20px 4px 4px;width:1%;white-space:nowrap;'><strong>Url: </strong></td>                " +
            "       <td align='left'><a href="+data['url']+" target='_blank'>"+"Resource Landing Page"+"</a></td></tr>" +
            "<t/table>";

        }
    });

}
