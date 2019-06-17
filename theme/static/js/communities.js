function onRoleSelect(event) {
    var el = $(event.target);
    $("#selected_role").text(el.text());
    $("#selected_role")[0].setAttribute("data-role", el[0].getAttribute("data-role"));
}

$(document).ready(function () {
    $("title").text($(".group-title").text() + " | HydroShare"); // Fix page title

    $("#id_user-autocomplete").addClass("form-control");

    $("#list-roles a").click(onRoleSelect);

    $("#id_user-autocomplete").attr("placeholder", "Search by name or username");

    // Filter
    $("#members").find(".table-members-list").hide();
    $("#members").find(".table-members-list.active").show();

    let CommunitiesVm = new Vue({
        el: "#communities-app",
        data: {
            contribs: []
        },
        methods: {
            showFrom(contributorId) {
                return this.$data.contribs.indexOf(contributorId) < 0;
            },
            updateContribs(contribId, chkState) {  // if not in the display list remove it otherwise add it effectively toggle
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
