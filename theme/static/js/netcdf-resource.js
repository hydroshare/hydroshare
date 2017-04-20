/**
 * Created by Mauriel on 3/9/2017.
 */

$(document).ready(function() {
    // show up file update button
    if (($("#metadata-dirty").val() === "True")) {
        $("#netcdf-file-update").show();
    }
})
