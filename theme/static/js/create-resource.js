/**
* Created by Mauriel on 3/9/2017.
*/
$(document).ready(function() {
    var json_response_file_types = {};
    var json_response_multiple_file = {};
    var selected_file = undefined;
    if (sessionStorage.signininfo) {
        $("#sign-in-info").text(sessionStorage.signininfo);
        $("#btn-select-irods-file").show();
        $("#irods-sel-file").text("No file selected.");
    }

    $('input:radio[name="copy-move"]').change(function(){
        if($(this).val()=='move') {
            $("#copy-or-move").val('move');
            $("#file-move-warning").show();
        }
        else {
            $("#copy-or-move").val('copy');
            $("#file-move-warning").hide();
        }
    });
    $('#resource-type').on('change', function(){
        $('#select-file').value = '';
        $('#select-file').attr('value', '');
        $('#irods-sel-file').text("No file selected.");

        if(selected_file != undefined){
            selected_file.value = '';
        }
        $.ajax({
            type: "GET",
            url: "/hsapi/_internal/" + this.value + "/supported-file-types/",
            success: function(result) {
                console.log(result);
                json_response_file_types = JSON.parse(result);
                console.log(json_response_file_types.file_types);
                var supported_file_types = "Any file type can be uploaded."
                if(JSON.parse(json_response_file_types.file_types).length == 0){
                    $("#upload-file").hide();
                }
                else{
                    if(JSON.parse(json_response_file_types.file_types)[0] != ".*"){
                        supported_file_types = "Only the listed file types can be uploaded: " + json_response_file_types.file_types + ".";
                    }
                    $("#upload-file").show();
                    $("#file-types").text(supported_file_types);
                }

            },
            error: function(XMLHttpRequest, textStatus, errorThrown)
            {
                $("#file-types").text('Error in determining supported file types');
            }
        })

        $.ajax({
            type: "GET",
            url: "/hsapi/_internal/" + this.value + "/allow-multiple-file/",
            success: function(result) {
                console.log(result);
                json_response_multiple_file = JSON.parse(result);
                console.log(json_response_multiple_file);
                if(json_response_multiple_file.allow_multiple_file == true){
                    $("#file-multiple").text("Multiple file upload is allowed.");
                    $("#select-file").attr('multiple', 'multiple')
                }
                else{
                    $("#file-multiple").text("Only one file can be uploaded.");
                    $("#select-file").removeAttr('multiple');
                }
            },
            error: function(XMLHttpRequest, textStatus, errorThrown)
            {
                $("#file-multiple").text('Error in determining if multiple file upload is allowed for this resource type');
            }
        })
    })

    $('#select-file').on('change', function(){
        var file_types = JSON.parse(json_response_file_types.file_types);
        if(file_types == ".*"){
            return;
        }

        var fileList = this.files || []
        var ext = ".*";
        for (var i = 0; i < fileList.length; i++) {
            ext = fileList[i].name.match(/\.([^\.]+)$/)[1];
            ext = "." + ext.toLowerCase();
            var ext_found = false;
            if (ext === file_types) {
                ext_found = true;
            }
            else {
                var index;
                for (index = 0; index < file_types.length; index++) {
                    if (ext === file_types[index].trim()) {
                        ext_found = true;
                        break;
                    }
                }
            }
            if(!ext_found){
                this.value ='';
                var err_msg = "Invalid file type: '" + ext +"'";
                $('#file-type-error').text(err_msg);
            }
            else{
                $('#file-type-error').text('');
            }
        }
    })
})