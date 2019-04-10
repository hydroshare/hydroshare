/**
* Created by Mauriel on 3/9/2017.
*/

function request_join_group_ajax_submit() {
    var target = $(this);
    var dataFormID = $(this).attr("data-form-id");
    var form = $("#" + dataFormID);
    var datastring = form.serialize();
    var url = form.attr('action');
    $.ajax({
        type: "POST",
        url: url,
        dataType: 'html',
        data: datastring,
        success: function (result) {
            var container = target.parent().parent();
            target.parent().remove();
            container.append('<h4 class="flag-joined"><span class="glyphicon glyphicon-send"></span> Request Sent</h4>');
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            console.log("error");
        }
    });
    //don't submit the form
    return false;
}

function act_on_request_ajax_submit() {
    var target = $(this);
    var form = $(this).closest("form");
    var datastring = form.serialize();
    var url = form.attr('action');
    $.ajax({
        type: "POST",
        url: url,
        dataType: 'html',
        data: datastring,
        success: function (result) {
            var container = target.parent().parent().parent().parent();
            target.parent().parent().parent().remove();
            if (target.attr("data-user-action") == "Accept") {
                container.append('<div class="text-center"><h4 class="flag-joined"><span class="glyphicon glyphicon-ok"></span> You have joined this group</h4></div>');
            }
            else {
                container.append('<div class="text-center"><h4 class="flag-declined"><span class="glyphicon glyphicon-remove"></span> You have declined to join this group.</h4></div>');
            }
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            console.log("error");
        }
    });
    //don't submit the form
    return false;
}

// Makes all group preview containers have the same height.
function fixViewPort(current) {
    if (!current) {
        return;
    }

    $('.group-thumbnails').find('div.group-container').height("initial");   // Reset height

    var containers = $('.group-thumbnails').find('div.group-container');

    var maxHeight = 0;
    for (var i = 0; i < containers.length; i ++) {
        maxHeight = Math.max($(containers[i]).height() + $(containers[i]).find(".group-thumbnail-footer").height(), maxHeight);
    }

    // set to new max height
    for (var i = 0; i < containers.length; i++) {
        $(containers[i]).height(maxHeight);
        $(containers[i]).find(".group-thumbnail-footer").width($(containers[i]).find(".group-description").width())
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
    $(".btn-ask-to-join").click(request_join_group_ajax_submit);
    $(".btn-act-on-request").click(act_on_request_ajax_submit);
    $("#txt-search-groups").keyup(function () {
        var searchString = $("#txt-search-groups").val().toLowerCase();
        $(".group-container").show();
        var groups = $(".group-container");
        for (var i = 0; i < groups.length; i++) {
            var groupName = $(groups[i]).find(".group-name").text().toLowerCase();
            if (groupName.indexOf(searchString) < 0) {
                $(groups[i]).hide();
            }
        }
    });

    // File name preview for picture field, file select method
    $('.btn-file :file').on('fileselect', function (event, numFiles, label) {
        var input = $(this).parents('.input-group').find(':text');
        input.val(label);
    });

});

// Uses bootstrap toolkit to trigger FixViewPort on bootstrap responsive breakpoints
(function ($, viewport) {
    $(document).ready(function () {
        // Executes when page loads
        fixViewPort(viewport.current());

        // Executes each time window size changes
        $(window).resize(
                viewport.changed(function () {
                    fixViewPort(viewport.current());
                })
        );
    });
})(jQuery, ResponsiveBootstrapToolkit);
