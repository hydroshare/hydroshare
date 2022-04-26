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
      },
      remove: async function(id) {
        this.$set(this.isRemoving, id, true)
        // TODO: handle leaving
        const url = '/access/_internal/communityjson/' + this.community.id + '/remove/' + id + '/';
        try {
          const  response = await $.get(url)
          console.log(response)
          // this.joined = response.joined
          // this.availableToJoin = response.available_to_join
          delete this.isRemoving[id]
        }
        catch(e) {
          console.log(e)
          // abort
          this.$set(this.isRemoving, id, false)
        }
      },
      approve: async function(id) {
        this.$set(this.isApproving, id, true)
        // TODO: handle leaving
        const url = '/access/_internal/communityjson/' + this.community.id + '/approve/' + id + '/';
        try {
          const response = await $.get(url, { 'responseType': 'text' })
          console.log(response)
          // this.joined = response.joined
          // this.availableToJoin = response.available_to_join
          delete this.isApproving[id]
        }
        catch(e) {
          console.log(e)
          // abort
          this.$set(this.isApproving, id, false)
        }
      },
    }
  });
});
