$(document).ready(function () {
  const CommunityApp = new Vue({
    el: "#community-app",
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
      targetOwner: null,
      isRemoving: {},
      isApproving: {},
      isInviting: {},
      isRemovingOwner: {},
      userCardSelected: {
        user_type: null,
        access: null,
        id: null,
        pictureUrl: null,
        best_name: null,
        user_name: null,
        can_undo: null,
        email: null,
        organization: null,
        title: null,
        contributions: null,
        subject_areas: null,
        identifiers: [],
        state: null,
        country: null,
        joined: null,
      },
      cardPosition: {
        top: 0,
        left: 0,
      }
    },
    mounted: function () {
      const groupIds = {};

      console.log(this.pending)

      $('#groups-list li').each(function () {
        const groupId = parseInt($(this).attr('id'));
        groupIds[$(this).text()] = groupId;
      });

      $("input[name='user-autocomplete']")
        .attr("placeholder", "Search by name or username")
        .addClass("form-control");

      this.$data.groupIds = groupIds;

      const filterGroup = $('#filter-querystring').text();
      if (filterGroup && this.$data.groupIds[filterGroup]) {
        this.$data.filterTo.push(this.$data.groupIds[filterGroup])
      }
    },
    methods: {
      loadOwnerCard(data) {
        const el = $(data.event.target).closest('.profile-link');
        const cardWidth = 350;

        this.userCardSelected = data.user;
        this.cardPosition.left = el.position().left - (cardWidth / 2) + (el.width() / 2);
        this.cardPosition.top = el.position().top + 30;
      },
      isVisible(groupId) {
        if (this.$data.filterTo.length === 0) {  // If no selections show all
          return true;
        } else {  // Display row if Group ID found in the filterTo Array
          return this.$data.filterTo.indexOf(groupId) > -1;
        }
      },
      updateContributors(groupId) {
        const loc = this.$data.filterTo.indexOf(groupId);

        if (loc < 0) {
          this.$data.filterTo.push(groupId)
        } else {
          this.$data.filterTo.splice(loc, 1);
        }
      },
      removeGroup: async function (id) {
        this.$set(this.isRemoving, id, true)
        // TODO: handle leaving
        const url = '/access/_internal/community/' + this.community.id + '/remove/' + id + '/';
        try {
          const response = await $.post(url)
          this.members = response.members
          this.availableToInvite = response.groups
          this.$set(this.isRemoving, id, false)
          $("#remove-group-modal").modal('hide')
          customAlert("Remove Group", 'Group has been removed from your Community', "success", 6000);
        }
        catch (e) {
          console.log(e)
          // abort
          this.$set(this.isRemoving, id, false)
        }
      },
      inviteGroup: async function (id) {
        this.$set(this.isInviting, id, true)
        // TODO: handle leaving
        const url = '/access/_internal/community/' + this.community.id + '/invite/' + id + '/';
        try {
          const response = await $.post(url)
          const group = this.availableToInvite.find(g => g.id === id)
          group.wasInvited = true

          this.pending = response.pending
          if (response.members) {
            // If members is included in the response, we update the state
            this.members = response.members
          }
          this.$set(this.isInviting, id, false)
          customAlert("Invite Group", response.message, "success", 6000);
        }
        catch (e) {
          console.log(e)
          // abort
          this.$set(this.isInviting, id, false)
        }
      },
      approve: async function (id) {
        this.$set(this.isApproving, id, true)
        // TODO: handle leaving
        const url = '/access/_internal/community/' + this.community.id + '/approve/' + id + '/';
        try {
          const response = await $.post(url)
          // this.joined = response.joined
          // this.availableToJoin = response.available_to_join
          console.log(response)
          this.$set(this.isApproving, id, false)
        }
        catch (e) {
          console.log(e)
          // abort
          this.$set(this.isApproving, id, false)
        }
      },
      removeOwner: async function (userId) {
        const url = `/access/_internal/community/${this.community.id}/owner/${userId}/remove`
        this.$set(this.isRemovingOwner, userId, true)
        try {
          const response = await $.post(url)
          if (response.community) {
            this.community.owners = response.community.owners
            customAlert('Remove Community Owner', 'User has been removed as an owner of this Community', 'success', 6000);
            $("#remove-community-owner-modal").modal('hide')
          }
        }
        catch (e) {
          customAlert("Add Community Owner", 'Failed to remove Community owner', 'error', 6000);
        }
        this.$set(this.isRemovingOwner, userId, false)
      },
      addOwner: async function () {
        let userId;

        if ($("#user-deck > .hilight").length > 0) {
          userId = parseInt($("#user-deck > .hilight")[0].getAttribute("data-value"));
        }
        else {
          return false;   // No user selected
        }

        $(".hilight > span").click(); // Clear the autocomplete
        // add owner here

        const url = `/access/_internal/community/${this.community.id}/owner/${userId}/add`
        try {
          const response = await $.post(url)
          if (response.community) {
            this.community.owners = response.community.owners
            customAlert('Add Community Owner', 'User has been added as an owner of this Community', 'success', 6000);
          }
        }
        catch (e) {
          if (e.status === 400 && e.responseText.indexOf('already owns community') >= 0) {
            customAlert('Add Community Owner', 'User is already an owner of this Community', 'info', 6000);
          }
          else {
            customAlert("Add Community Owner", 'Failed to add user as Community owner', 'error', 6000);
          }
        }
      },
    }
  });
});