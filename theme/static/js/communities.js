

function onRoleSelect(event) {
    var el = $(event.target);
    $("#selected_role").text(el.text());
    $("#selected_role")[0].setAttribute("data-role", el[0].getAttribute("data-role"));
}

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
    $("title").text($(".group-title").text() + " | HydroShare"); // Fix page title

     $("#id_user-autocomplete").addClass("form-control");

    $("#list-roles a").click(onRoleSelect);

    $("#id_user-autocomplete").attr("placeholder", "Search by name or username");

    // Filter
    $("#members").find(".table-members-list").hide();
    $("#members").find(".table-members-list.active").show();

    $("#members-filter tr").click(function() {
        $("#members").find(".table-members-list tr").hide();
        $("table[data-filter-by='pending'] tr").hide();
        $("table[data-filter-by='pending']").hide();

        var dataFilter = $(this).attr("data-filter-by");
        if (dataFilter == "edit-user") {
            $("#members").find(".table-members-list tr[data-filter-by='" + dataFilter + "']").fadeIn();
            $("#members").find(".table-members-list tr[data-filter-by='" + "creator" + "']").fadeIn();
        }
        else if (dataFilter == "all") {
            $("#members").find(".table-members-list tr").addClass("active").fadeIn();
        }
        else if(dataFilter == "pending") {
            $("#members").find(".table-members-list tr").addClass("active").hide();
            $("table[data-filter-by='pending'] tr").fadeIn();
            $("table[data-filter-by='pending']").fadeIn();
        }

        $(this).parent().find("tr").removeClass("active");
        $(this).addClass("active");
    });

    // Initialize Shared By filter
    var grantors = $("#grantors-list span");
    if (grantors.length)
        $("#filter-shared-by .no-items-found").remove();
    for (var i = 0; i < grantors.length; i++) {
        var id = $(grantors[i]).attr("data-grantor-id");
        if ($("#filter-shared-by .grantor[data-grantor-id='" + id + "']").length == 0) {
            var count = $("#grantors-list span[data-grantor-id='" + id + "']").length;
            var name = $(grantors[i]).attr("data-grantor-name").trim();

            $("#filter-shared-by .inputs-group").append('<li class="list-group-item">' +
                                                            '<span data-facet="owned" class="badge">' + count + '</span>' +
                                                            '<label class="checkbox noselect">' +
                                                            '<input type="checkbox" class="grantor" data-grantor-id="' + id + '">' + name + '</label>' +
                                                        '</li>')
        }
    }

    $("#grantors-list").remove();   // Remove temporary list

    // File name preview for picture field, file select method
    $('.btn-file :file').on('fileselect', function (event, numFiles, label) {
        var input = $(this).parents('.input-group').find(':text');
        input.val(label);
    });

    let CommunitiesVm = new Vue({
        el: "#communities-app",
        data: {
            contribs: []
        },
        methods: {
            showFrom(contributorId) {
                return this.$data.contribs.indexOf(contributorId) < 0;
            },
            updateContribs(contribId) {  // if not in the display list remove it otherwise add it effectively toggle
                let loc = this.$data.contribs.indexOf(contribId);
                if (loc < 0) {
                    this.$data.contribs.push(contribId)
                } else {
                    this.$data.contribs.splice(loc, 1);
                }
            }
        }
    });

});