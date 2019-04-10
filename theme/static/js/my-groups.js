/**
* Created by Mauriel on 3/9/2017.
*/

// Preview profile picture
function readURL(input) {
    if (input.files && input.files[0]) {
        var reader = new FileReader();
        reader.onload = function (e) {

        };

        reader.readAsDataURL(input.files[0]);
    }
}

// File name preview for picture field, change method
$(document).on('change', '.btn-file :file', function () {
    var input = $(this);
    var numFiles = input.get(0).files ? input.get(0).files.length : 1;
    var label = input.val().replace(/\\/g, '/').replace(/.*\//, '');
    input.trigger('fileselect', [numFiles, label]);
});

$(document).ready(function () {
    $("title").text("My Groups | HydroShare"); // Fix page title

    // File name preview for picture field, file select method
    $('.btn-file :file').on('fileselect', function (event, numFiles, label) {
        var input = $(this).parents('.input-group').find(':text');
        input.val(label);
    });
    $("#show-deleted-groups").click(function () {
        if ($(this).text() === "Show deleted groups"){
            $(this).text("Hide deleted groups");
        }
        else {
            $(this).text("Show deleted groups");
        }
    })
});