$(document).ready(function () {
  let CommunityApp = new Vue({
    el: "#communities-app",
    delimiters: ['${', '}'],
    data: {
      filterTo: [],
      groupIds: [],
      availableToInvite: GROUPS,
      members: MEMBERS,
      community: COMMUNITY,
      isAdmin: IS_ADMIN,
      pending: PENDING,
      targetGroup: null,
      isRemoving: {},
      isApproving: {},
      isInviting: {},
    },
    mounted: function () {
      let groupIds = {};

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
          this.availableToInvite = response.groups
          this.members = response.members
          delete this.isRemoving[id]
          $("#remove-group-modal").modal('hide')
          customAlert("Remove Group", response.message, "success", 6000);
        }
        catch(e) {
          console.log(e)
          // abort
          this.$set(this.isRemoving, id, false)
        }
      },
      invite: async function(id) {
        this.$set(this.isInviting, id, true)
        // TODO: handle leaving
        const url = '/access/_internal/communityjson/' + this.community.id + '/invite/' + id + '/';
        try {
          const response = await $.get(url, { 'responseType': 'text' })
          console.log(response)
          this.availableToInvite = response.groups
          this.members = response.members
          delete this.isInviting[id]
          customAlert("Invite Group", response.message, "success", 6000);
        }
        catch(e) {
          console.log(e)
          // abort
          this.$set(this.isInviting, id, false)
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
      removeOwner: async function(owner) {
        
      }
    }
  });
});