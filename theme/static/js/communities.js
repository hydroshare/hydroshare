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
            filterTo: [],
        },
        mounted: function () {
            let groupIds = {};
            let ids = [];

            $('#groups-list li').each(function(){
                let groupId = parseInt($(this).attr('id'));
                groupIds[$(this).text()] = groupId;
                ids.push(groupId)
            });
            this.$data.ids = ids
        },
        methods: {
            showFrom(groupId) {
                if (this.$data.filterTo.length === 0) {  // If no selections show all
                    return true;
                } else {  // Display row if Group ID found in the filterTo Array
                    return this.$data.filterTo.indexOf(groupId) > -1;
                }
            },
            updateContribs(groupId) {
                let loc = this.$data.filterTo.indexOf(groupId);

                if (loc < 0) {
                    this.$data.filterTo.push(groupId)
                } else {
                    this.$data.filterTo.splice(loc, 1);
                }
            }
        }
    });
});
