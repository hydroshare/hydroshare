$(document).ready(function () {
  let CommunityApp = new Vue({
    el: "#communities-app",
    delimiters: ['${', '}'],
    data: {
      filterTo: [],
      groupIds: [],
      groups: GROUPS,
      community: COMMUNITY,
      isAdmin: IS_ADMIN,
      pending: PENDING,
      members: MEMBERS,
      isRemoving: {},
      isApproving: {},
    },
    mounted: function () {
      let groupIds = {};

      console.log(this.community)
      console.log(this.groups)

      $('#groups-list li').each(function () {
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
