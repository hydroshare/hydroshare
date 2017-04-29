/**
* Created by Mauriel on 3/9/2017.
*/
$(document).ready(function () {
    var json_response_file_types = {};
    var json_response_multiple_file = {};
    var selected_file = undefined;
    var myDropzone;
    var fileIcons = getFileIcons();

    if (sessionStorage.signininfo) {
        $("#sign-in-info").text(sessionStorage.signininfo);
        $("#btn-select-irods-file").show();
        $("#irods-sel-file").text("No file selected.");
    }

    Dropzone.options.hsDropzone = {
        previewTemplate: document.getElementById('preview-template').innerHTML,
        clickable: "#dz-container",
        previewsContainer: "#dz-container:not(.dz-details)",
        paramName: "files", // The name that will be used to transfer the file
        maxFilesize: 1024, // MB
        autoProcessQueue: false,
        uploadMultiple: true,
        parallelUploads: 99, // arbitrary large number for parallel uploads

        success: function (file, response) {
            if (response.status == "success") {
                window.location = response['resource_url'];
            }
            else {
                console.log(response);
            }
        },
        error: function (file, response) {
            console.log(response);
        },

        init: function () {
            myDropzone = this;

            $(".btn-create-resource").click(function () {
                $("html, #dz-container").css("cursor", "progress");

                // Delete invalid files from queue before uploading
                $(".dz-error .btn-remove").trigger("click");

                var title = $("#txtTitle").val().trim();
                if (!title) {
                    title = $("#txtTitle").attr("placeholder");
                }

                $("#form-title").val(title);

                if (myDropzone.files.length > 0) {
                    myDropzone.processQueue();
                }
                else {
                    var url = $("#hsDropzone").attr("action");
                    var datastring = $("#hsDropzone").serialize();
                    $.ajax({
                        type: "POST",
                        data: datastring,
                        url: url,
                        success: function (response) {
                            if (response.status == "success") {
                                window.location = response['resource_url'];
                            }
                        },
                        error: function (response) {
                            console.log(response);
                        }
                    });
                }
            });

            // The user dragged a file onto the Dropzone
            this.on("dragenter", function (file) {
                $("#hsDropzone").toggleClass("hs-dropzone-highlight", true);
            });

            // The user dragged a file out of the Dropzone
            this.on("dragleave", function (event) {
                $("#hsDropzone").toggleClass("hs-dropzone-highlight", false);
            });

            this.on("addedfile", function (file) {
                // Initialize tooltips
                var template = $(file.previewElement);
                template.find(".dz-filename").attr("title", template.find("span[data-dz-name]").text());

                // Set file type icon
                var fileName = template.find(".dz-filename").text();
                var fileTypeExt = fileName.substr(fileName.lastIndexOf(".") + 1, fileName.length).toUpperCase();
                if (fileIcons[fileTypeExt]) {
                    template.find(".file-type-icon").append(fileIcons[fileTypeExt]);
                }
                else {
                    template.find(".file-type-icon").append(fileIcons.DEFAULT);
                }

                template.find("[data-toggle='tooltip']").tooltip();

                if (!myDropzone.options.uploadMultiple && myDropzone.files[1] != null) {
                    this.removeFile(this.files[0]);
                }
                $("#hsDropzone").toggleClass("hs-dropzone-highlight", false);

                $(".hs-upload-indicator").hide();
            });

            this.on("removedfile", function (file) {
                $('#hsDropzone .tooltip').remove();
                if (myDropzone.files.length == 0) {
                    $(".hs-upload-indicator").show();
                }
            });

            this.on("error", function (file, error) {
                var template = $(file.previewElement);
                $(template).addClass("dz-error");
                $(template).attr("data-toggle", "tooltip");
                $(template).attr("data-placement", "top");
                $(template).attr("title", error);
                template.tooltip();
            });

            this.on('sendingmultiple', function (data, xhr, formData) {
                $("#upload-content").find("input[name]").each(function () {
                    formData.append($(this).attr("name"), $(this).val());
                });
            });
        }
    };

    $('input:radio[name="copy-move"]').change(function () {
        if ($(this).val() == 'move') {
            $("#copy-or-move").val('move');
            $("#file-move-warning").show();
        }
        else {
            $("#copy-or-move").val('copy');
            $("#file-move-warning").hide();
        }
    });

    $('#dropdown-resource-type li a').click(function () {
        // Remove all previously queued files when the resource type changes.
        Dropzone.forElement("#hsDropzone").removeAllFiles(true);
        $('#irods-sel-file').text("No file selected.");
        $('#irods_file_names').val("");

        if (selected_file != undefined) {
            selected_file.value = '';
        }

        $("#form-resource-type").val($(this).attr("data-value"));

        var template = this.innerHTML;
        $("#select-resource-type")[0].innerHTML = template;
        $("#select-resource-type").find(".resource-type-name").append("&nbsp;<span class='caret'></span>")

        // Get supported file types
        $.ajax({
            type: "GET",
            url: "/hsapi/_internal/" + $(this).attr("data-value") + "/supported-file-types/",
            success: function (result) {
                json_response_file_types = JSON.parse(result);

                if (JSON.parse(json_response_file_types.file_types).length == 0) {
                    $("#upload-content").hide();    // No files needed
                }
                else {
                    $("#upload-content").show();

                    var supported_file_types = JSON.parse(json_response_file_types.file_types);

                    $("#file-types").empty();

                    if (supported_file_types != ".*") {
                        // Append message
                        $("#file-types").append("<i class='fa fa-info-circle' aria-hidden='true'></i>" +
                                "<span>Only the following file types can be uploaded:</span><br>");

                        // Render badge for each file type
                        for (var i = 0; i < supported_file_types.length; i++) {
                            $("#file-types").append('<span class="badge">' + supported_file_types[i] + '</span>');
                        }

                        // Set controls
                        if (myDropzone) {
                            myDropzone.options.acceptedFiles = supported_file_types.toString();
                            $(myDropzone.hiddenFileInput).attr("accept", supported_file_types.toString());
                        }

                    }
                    else {
                        // Append message
                        $("#file-types").append("<i class='fa fa-check-circle' aria-hidden='true'></i>" +
                                "<span>Any file type can be uploaded.</span>");

                        // Set controls
                        if (myDropzone) {
                            myDropzone.options.acceptedFiles = "";
                            $(myDropzone.hiddenFileInput).removeAttr("accept");
                        }

                    }
                }
            },
            error: function (XMLHttpRequest, textStatus, errorThrown) {
                $("#file-types").empty();

                // Append message
                $("#file-types").append("<i class='fa fa-info-circle' aria-hidden='true'></i>" +
                                "<span>Error in determining supported file types</span><br>");

                // Set controls
                if (myDropzone) {
                    myDropzone.options.acceptedFiles = "";
                    $(myDropzone.hiddenFileInput).removeAttr("accept");
                }
            }
        });

        // Get multiple files flag value
        $.ajax({
            type: "GET",
            url: "/hsapi/_internal/" + $(this).attr("data-value") + "/allow-multiple-file/",
            success: function (result) {
                json_response_multiple_file = JSON.parse(result);

                $("#file-multiple").empty();
                if (json_response_multiple_file.allow_multiple_file == true) {
                    // Append message
                    $("#file-multiple").append("<i class='fa fa-check-circle' aria-hidden='true'></i>");
                    $("#file-multiple").append("<span>Multiple file upload is allowed.</span>");

                    // Set controls
                    if (myDropzone) {
                        myDropzone.options.uploadMultiple = true;
                        $(myDropzone.hiddenFileInput).attr("multiple", 'multiple');
                    }
                }
                else {
                    // Append message
                    $("#file-multiple").append("<i class='fa fa-info-circle' aria-hidden='true'></i>");
                    $("#file-multiple").append("<span>Only one file can be uploaded.</span>");

                    // Set controls
                    if (myDropzone) {
                        myDropzone.options.uploadMultiple = false;
                        $(myDropzone.hiddenFileInput).removeAttr('multiple');
                    }
                }
            },
            error: function (XMLHttpRequest, textStatus, errorThrown) {
                $("#file-multiple").empty();

                // Append message
                $("#file-multiple").append("<i class='fa fa-check-circle' aria-hidden='true'></i>");
                $("#file-multiple").append("<span>Error in determining if multiple file upload is allowed for this resource type.</span>");

                // Set controls
                if (myDropzone) {
                    myDropzone.options.uploadMultiple = true;
                    $(myDropzone.hiddenFileInput).attr("multiple", 'multiple');
                }
            }
        })
    });

    $("#btn-remove-all-files").click(function () {
        Dropzone.forElement("#hsDropzone").removeAllFiles(true);
        $(".hs-upload-indicator").show();
    });
});