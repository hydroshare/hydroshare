$(document).ready(function () {

    // check to see if the view is in edit mode
    if ( $('#id-scriptspecificmetadata')[0] != null) {

        // initialize datepicker
        $('#scriptReleaseDate_picker').datepicker({

            // Sets the hidden date field base on the datepicker.  The hidden field is what is submitted.
            onSelect: function () {

                // Set the value of the hidden date field which will be submitted to the server on Save
                var dateElement = $('#id_scriptReleaseDate')[0];
                var datePickerElement = $("#scriptReleaseDate_picker")[0];
                dateElement.value = datePickerElement.value;

                // activate the save button
                $("#resourceSpecificTab").find('.btn-primary').show();
            }
        });

        // Populates the Release Date field to reflect the user's previously chosen date.
        var dateElement = $('#id_scriptReleaseDate')[0];
        var usrDateString = dateElement.value;
        if (usrDateString) {
            var usrDateObj = new Date(usrDateString);
            var usrDateFormatted = usrDateObj.toLocaleDateString();
            $('#scriptReleaseDate_picker').datepicker("setDate", usrDateFormatted);
        }
    }
});