$('#btn-select-irods-file').on('click',function(event) {
    $('#input_trigger').val('default');
    $('#res_type').val($('#resource-type').val());
    $('#file_struct').children().remove();
    $('.ajax-loader').hide();
    var store = '';
    if (sessionStorage.IRODS_signininfo) {
        $("#irods_content_label").text(sessionStorage.IRODS_username);
        $('#root_store').val(sessionStorage.IRODS_datastore);
        store = sessionStorage.IRODS_datastore;
    }

    // Setting up the view tab
    $('#file_struct').attr('name',store);
    $('#irods_view_store').val(store);
    // loading file structs
    var parent = $('#file_struct');
    get_store(store, parent, 0);
    $('body').off('click');
    $('body').on('click', '.folder', click_folder_opr);
});

$('#btn-select-irods-file-uz').on('click',function(event) {
    $('#input_trigger').val('userzone');
    $('#res_type').val($('#resource-type').val());
    $('#file_struct').children().remove();
    $('.ajax-loader').hide();
    $("#irods_content_label").text($("#irods_username_uz").val())
    $('#root_store').val($("#irods_store_uz").val());
    var store = $("#irods_store_uz").val();

    // Setting up the view tab
    $('#file_struct').attr('name',store);
    $('#irods_view_store').val(store);
    // loading file structs
    var parent = $('#file_struct');
    get_store_uz(store, parent, 0);
    $('body').off('click');
    $('body').on('click', '.folder', click_folder_opr_uz);
});

function set_store_display(store, parent, margin, json) {
    var files = json.files;
    var folder = json.folder;
    var lastSelected = [];
    if (files.length == 0 && folder.length == 0) {
        $(parent).append("<div class='file' style='margin-left:" + margin + "px;'></div>");
    }
    else {
        $.each(folder, function(i, v) {
            $(parent).append("<div class='folder' id='irods_folder_" + v + "' name='" + store + "/" + v + "' style='margin-left:" + margin + "px;'><img src='/static/img/folder.png' width='15' height='15'>&nbsp; " + v + "</div>");
        });

        $.each(files, function(i, v) {
            $(parent).append("<div class='file' id='irods_file_" + v + "' name='" + store + "/" + v + "' style='margin-left:" + margin + "px;'><img src='/static/img/file.png' width='15' height='15'>&nbsp; " + v + "</div>")
        });
    }
    $('.file').attr('unselectable', 'on'); // disable default browser shift text selection highlighting in IE
    $('.file').on('click',function(e) {
        var current = $(this), selected;
        if (e.shiftKey) {
            if (lastSelected.length > 0) {
                if (current[0] == lastSelected[0]) {
                    return false;
                }
                if (current.nextAll('.lastSelected').length > 0) {
                    // last selected is after the current selection
                    selected = current.nextUntil(lastSelected);
                }
                else {
                    // last selected is before the current selection
                    selected = lastSelected.nextUntil(current);
                }
                $('.file').removeClass('selected');
                selected.addClass('selected');
                lastSelected.addClass('selected');
                current.addClass('selected');
            }
            else {
                lastSelected = current;
                current.addClass('lastSelected');
                $('.file').removeClass('selected');
                current.addClass('selected');
            }
        }
        else { // Not a shift select
            $('.file').removeClass('lastSelected');
            if (!e.ctrlKey) { // not a ctrl select - clear up old selections
                $('.file').removeClass('selected');
            }

            if (e.ctrlKey && $(e.target).hasClass('selected')) { // ctrl-clicking on a selected item clears the selection
                $(e.target).removeClass('selected');
            }
            else {
                $(e.target).addClass('lastSelected selected');
                lastSelected = current;
            }
        }
        set_datastore(current.parent('div')[0], false);
        return false;
    });
}

function get_store(store, parent, margin) {
    if (store) {
        $.ajax({
            mode: "queue",
            url: '/irods/store/',
            async: true,
            type: "POST",
            data: {
                store: store,
                user: sessionStorage.IRODS_username,
                password: sessionStorage.IRODS_password,
                zone: sessionStorage.IRODS_zone,
                port: sessionStorage.IRODS_port,
                host: sessionStorage.IRODS_host
            },
            success: function (json) {
                return set_store_display(store, parent, margin, json);
            },

            error: function (xhr, errmsg, err) {
                console.log(xhr.status + ": " + xhr.responseText + ". Error message: " + errmsg);
                return false;
            }
        });
        return true;
    }
    else
        return false;
}

function get_store_uz(store, parent, margin) {
    if(store) {
        $.ajax({
            mode: "queue",
            url: '/irods/store_uz/',
            async: true,
            type: "POST",
            data: {
                store: store
            },
            success: function (json) {
                return set_store_display(store, parent, margin, json);
            },

            error: function (xhr, errmsg, err) {
                console.log(xhr.status + ": " + xhr.responseText + ". Error message: " + errmsg);
                return false;
            }
        });
        return true;
    }
    else
        return false;
}

function get_margin_left(element) {
    var margin_left;
    try {
        margin_left = parseInt(element.css('margin-left')) + 10;
    }
    catch(err) {
        margin_left = 0;
    }
    return margin_left;
}

function click_folder(parent, is_user_zone) {
    if(parent.hasClass('isOpen')) {
        parent.addClass('isClose');
        parent.removeClass('isOpen');
        parent.children('div').hide();
        set_datastore(parent.attr('name'), true);
    }
    else if(parent.hasClass('isClose')) {
        parent.addClass('isOpen');
        parent.removeClass('isClose');
        parent.children('div').show();
    }
    else {
        var store = parent.attr('name');
        var margin_left = get_margin_left(parent);
        if (is_user_zone)
            get_store_uz(store, parent, margin_left);
        else
            get_store(store, parent, margin_left);
        parent.addClass('isOpen');
        set_datastore(parent.attr('name'), true);
    }
}

function click_folder_opr() {
    click_folder($(this), false);
    return false;
}

function click_folder_opr_uz() {
    click_folder($(this), true);
    return false;
}

function set_datastore(store, isFolder) {
    if (store) {
        if (!isFolder) {
            store = $(store).attr('name');
        }
        $('#irods_view_store').val(store);
    }
}

// ### IRODS FUNCTION FOR VIEWING INPUT BOX UPON PRESSING RETURN ###
$('#irods_view_store').keypress(function(e) {
    if(e.which == 13) {
        e.preventDefault();
        var store = $(this).val();
        if (store=='') {
            store = $('#root_store').val();
        }
        // Setting up the view tab
        $('#file_struct').attr('name',store);
        $('#irods_view_store').val(store);

        // loading file structs
        var parent = $('#file_struct');
        var got_store;
        var is_user_zone = false;
        if (store.indexOf('hydroshareuserZone') > -1) {
            got_store = get_store_uz(store, parent, 0);
            is_user_zone = true;
        }
        else
            got_store = get_store(store, parent, 0);

        if (got_store) {
            $('#file_struct').children().remove();
            if(is_user_zone)
                click_folder_opr_uz();
            else
                click_folder_opr();
        }
        else {
            alert('Datastore does not exist');
        }
    }
});

$("#irodsContent form").bind("keypress", function(e) {
    if (e.keyCode == 13) {
        $("#btnSearch").attr('value');
        //add more buttons here
        return false;
    }
});

$('#iget_irods').on('click',function() {
    var selected = [];
    $('.selected').each( function() {
        selected.push($(this).attr('name'));
    });
    $('#upload_store').val(selected);
    $("#irods-username").val(sessionStorage.IRODS_username)
    $("#irods-password").val(sessionStorage.IRODS_password)
    $("#irods-host").val(sessionStorage.IRODS_host)
    $("#irods-zone").val(sessionStorage.IRODS_zone)
    $("#irods-port").val(sessionStorage.IRODS_port)
    $('#irodsContent .modal-backdrop.up-load').show();
    $('#irodsContent .ajax-loader').show();
});

function irods_upload() {
    $.ajax({
        url: "/irods/upload/",
        type: "POST",
        data: {
            upload: $('#upload_store').val(),
            res_type: $('#res_type').val()
        },
        success: function(json) {
            if ($('#input_trigger').val()=='default') {
                $("#irods-sel-file").text(json.irods_sel_file);
                $('#irods_file_names').val(json.irods_file_names);
            }
            else{
                $("#irods-sel-file-uz").text(json.irods_sel_file);
                $('#irods_file_names_uz').val(json.irods_file_names);
            }
            $("#file-type-error").text(json.file_type_error);
            $('#irodsContent').modal('hide');
        },
        error: function(xhr, errmsg, err) {
            console.log(xhr.status + ": " + xhr.responseText + ". Error message: " + errmsg);
            if ($('#input_trigger').val()=='default')
                $("#irods-sel-file").text("No file selected");
            else
                $("#irods-sel-file-uz").text("No file selected");
            $('#irodsContent').modal('hide');
        }
    });
}

$('#irodsUpload').on('submit', function(event) {
    event.preventDefault();
    irods_upload();
});