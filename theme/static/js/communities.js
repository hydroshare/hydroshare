$(document).ready(function () {
    let CommunitiesVm = new Vue({
        el: "#communities-app",
        data: {
            filterTo: [],
            groupIds: []
        },
        mounted: function () {
            let groupIds = {};

            $('#groups-list li').each(function(){
                let groupId = parseInt($(this).attr('id'));
                groupIds[$(this).text()] = groupId;
            });
            this.$data.groupIds = groupIds;

            let filterGroup = $('#filter-querystring').text();
            if (filterGroup && this.$data.groupIds[filterGroup]) {
                this.$data.filterTo.push(this.$data.groupIds[filterGroup])
            }
        },
        methods: {
            isVisible(groupId) {
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
