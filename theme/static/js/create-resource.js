/**
* Created by Mauriel on 3/9/2017.
*/

// Resource type constraint definitions
constraints = {
    GeographicFeatureResource: {
        requiredFiles: ['.DBF', '.SHP', '.SHX'],    // File extensions in uppercase
        canBeEmpty: true,                           // Optional. Defaults to true
        singleFileFormat: '.ZIP',                   // File format when uploading a single file
        sameFileNames: true,                        // The files must share the same file name
        sameFileNamesExcep: ['SHP.XML']                 // Additional file extensions to check for
    }
};

// Displays error message if resource creation fails and restores UI state
function showCreateError() {
    showUniversalMessage("error", 'Failed to create resource.', 10000)();
    $(".btn-create-resource").removeClass("disabled");
    $(".btn-create-resource").text("Create Resource");
    $(".btn-cancel-create-resource").removeClass("disabled");
}

$(document).ready(function () {
    var json_response_file_types = {};
    var json_response_multiple_file = {};
    var selected_file = undefined;
    var myDropzone;
    var fileIcons = getFileIcons();

    $('[data-toggle="popover1"]').popover();

    if (sessionStorage.signininfo) {
        $("#sign-in-info").text(sessionStorage.signininfo);
        $("#btn-select-irods-file").show();
        $("#irods-sel-file").text("No file selected.");
    }
    $alert_error = '<div class="alert alert-danger" id="alert_error"> \
        <button type="button" class="close" data-dismiss="alert">x</button> \
        <strong>Error! </strong> \
        Resource failed to create.\
    </div>';
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
                $alert_error = $alert_error.replace("Resource failed to create.", response.message);
                $('.btn-create-resource').before($alert_error);
                $("#alert-error").fadeTo(2000, 500).slideUp(1000, function(){
                    $("#alert-error").alert('close');
                });
                $("html, #dz-container").css("cursor", "initial");
                Dropzone.forElement("#hsDropzone").removeAllFiles(true);
                $(".hs-upload-indicator").show();
            }
        },
        error: function (file, response) {
            console.log(response);
        },

        init: function () {
            myDropzone = this;
            $(".btn-create-resource").click(function () {
                $("html, #dz-container").css("cursor", "progress");
                $(".btn-create-resource").text("Creating Resource...");
                $(".btn-create-resource").addClass("disabled");
                $(":text").attr("disabled", true);
                $(".dropdown").css("pointer-events", "none");
                $("#btn-remove-all-files").addClass("disabled");
                $(".hs-dropzone-wrapper").css("pointer-events", "none");
                $("#btn-signin-irods").addClass("disabled");





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
                            else {
                                console.log(response);
                                showCreateError();
                            }
                        },
                        error: function (response) {
                            console.log(response);
                            showCreateError();
                        }
                    });
                }
            });

            $(".btn-cancel-create-resource").click(function () {
                history.back();
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
                template.find(".dz-filename").attr("title", file.fullPath);

                // Set file type icon
                var fileName = template.find(".dz-filename").text();
                var fileTypeExt = fileName.substr(fileName.lastIndexOf(".") + 1, fileName.length).toUpperCase();
                var iconTemplate;
                if (fileIcons[fileTypeExt]) {
                    iconTemplate = fileIcons[fileTypeExt];
                    if (iconTemplate === fileIcons.JSON){
                        // json is really for refts.json icon
                        if (!fileName.toUpperCase().endsWith(".REFTS.JSON")){
                            iconTemplate = fileIcons.DEFAULT;
                        }
                    }
                }
                else {
                    iconTemplate = fileIcons.DEFAULT;
                }
                template.find(".dz-filename").attr("title", file.fullPath);
                template.find(".file-type-icon").append(iconTemplate);

                template.find("[data-toggle='tooltip']").tooltip();

                if (!myDropzone.options.uploadMultiple && myDropzone.files[1] != null) {
                    this.removeFile(this.files[0]);
                }
                $("#hsDropzone").toggleClass("hs-dropzone-highlight", false);

                $(".hs-upload-indicator").hide();

                setConstraintsHelp();
                checkConstraints();
            });

            this.on("removedfile", function (file) {
                $('#hsDropzone .tooltip').remove();
                if (myDropzone.files.length == 0) {
                    $(".hs-upload-indicator").show();
                }
                setConstraintsHelp();
                checkConstraints();
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

            checkConstraints();
            setConstraintsHelp();
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

    // Prevents event from being defined twice
    $('#dropdown-resource-type li a').unbind("click");

    $('#dropdown-resource-type li a').on("click", function () {
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
        });

        setConstraintsHelp();
        checkConstraints();
    });

    $("#btn-remove-all-files").click(function () {
        Dropzone.forElement("#hsDropzone").removeAllFiles(true);
        $(".hs-upload-indicator").show();
    });
});

// Shows help messages and their status for each relevant constraint
function setConstraintsHelp() {
    var type = $("#form-resource-type").val();
    var rules = constraints[type];
    var myDropzone = Dropzone.forElement("#hsDropzone");
    var someDisplayed = false;

    $("#constraints > li").css("display", "none");

    if (type in constraints) {
        if (!rules.canBeEmpty && myDropzone.files.length == 0) {
            $("#res-empty").css("display", "block");
            someDisplayed = true;
        }

        if (rules.requiredFiles && myDropzone.files.length > 0 && !(rules.singleFileFormat && myDropzone.files.length == 1)) {
            $("#required-types").css("display", "block");
            $("#required-types > span").empty();
            rules.requiredFiles.forEach(function(ext) {
                $("#required-types > span").append("<span class='badge'>" + ext.toLowerCase() + "</span>")
            });
            someDisplayed = true;
        }

        if (rules.singleFileFormat && myDropzone.files.length == 1) {
            $("#single-file").css("display", "block");
            $("#single-file-type").empty();
            $("#single-file-type").append("<span class='badge'>" + rules.singleFileFormat.toLowerCase() + "</span>")
            someDisplayed = true;
        }

        if (rules.sameFileNames && myDropzone.files.length > 1) {
            $("#same-file-names").css("display", "block");
            someDisplayed = true;
        }

        if (someDisplayed) {
            $("#constraints").css("display", "block");
        }
    }
    else {
        $("#constraints").css("display", "none");
    }
}

// Enables/disables Create Resource button based on resource type constraints
function checkConstraints() {
    var invalid = false;
    $("#constraints > li").toggleClass("invalid", false);
    var myDropzone = Dropzone.forElement("#hsDropzone");

    var type = $("#form-resource-type").val();

    if (type in constraints) {
        var rules = constraints[type];

        // Check canBeEmpty
        if (!rules.canBeEmpty && myDropzone.files.length == 0) {
            invalid = true;
            $("#res-empty").toggleClass("invalid", true);
        }

        // Check required files. Ignore when single file and single file format flag
        if (rules.requiredFiles && myDropzone.files.length > 0 && !(rules.singleFileFormat && myDropzone.files.length == 1)) {
            var extensions = [];
            myDropzone.files.forEach(function(element) {
                var fileTypeExt = element.name.substr(element.name.lastIndexOf("."), element.name.length).toUpperCase();
                extensions.push(fileTypeExt)
            });

            rules.requiredFiles.forEach(function(element) {
                if (!extensions.includes(element)) {
                    invalid = true;
                    $("#required-types").toggleClass("invalid", true)
                }
            });
        }

        // Check single file format
        if (rules.singleFileFormat && myDropzone.files.length == 1) {
            var fileName = myDropzone.files[0].name;
            var fileTypeExt = fileName.substr(fileName.lastIndexOf("."), fileName.length).toUpperCase();

            if (fileTypeExt.toUpperCase() != rules.singleFileFormat) {
                invalid = true;
                $("#single-file").toggleClass("invalid", true)
            }
        }

        // Check for same file names
        if (rules.sameFileNames && myDropzone.files.length > 1) {
            var fNames = [];
            myDropzone.files.forEach(function(element) {
                // Check the exceptions first
                var found = false;
                if (rules.sameFileNamesExcep && rules.sameFileNamesExcep.length > 0) {
                    rules.sameFileNamesExcep.forEach(function (excep) {
                        if (element.name.toUpperCase().endsWith(excep)) {
                            var fileName = element.name.substr(0, element.name.toUpperCase().lastIndexOf(excep) - 1);
                            fNames.push(fileName);
                            found = true;
                        }
                    });
                }

                // Check for file names
                if (!found) {
                    var fileName = element.name.substr(0, element.name.lastIndexOf("."));
                    fNames.push(fileName)
                }
            });

            var uniqueNames = fNames.filter(function (value, index, self) {
                return self.indexOf(value) === index
            });

            if (uniqueNames.length > 1) {
                invalid = true;
                $("#same-file-names").toggleClass("invalid", true)
            }
        }
    }

    $(".btn-create-resource").toggleClass("disabled", invalid);
}