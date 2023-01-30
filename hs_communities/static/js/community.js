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
      allCommunities: ALL_COMMUNITIES,
      groupsJoined: GROUPS_JOINED,
      isAdmin: IS_ADMIN,
      pending: PENDING,
      targetGroup: null,
      targetOwner: null,
      isRemoving: {},
      isApprovingGroup: {},
      isInviting: {},
      isRemovingOwner: {},
      isCancelingInvitation: {},
      inviteSearch: '',
      isDeletingCommunity: false,
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
    computed: {
      filteredAvailableToInvite() {
        if (!this.inviteSearch) {
          return this.availableToInvite
        }
        return this.availableToInvite.filter(group => {
          return group.name.toLowerCase().indexOf(this.inviteSearch) >= 0
        })
      }
    },
    mounted: function () {
      // Styling and placeholder for user auto-complete
      $("input[name='user-autocomplete']")
        .attr("placeholder", "Search by name or username")
        .addClass("form-control");

      // Initialize DataTables filter data
      const groupIds = {};

      $('#groups-list li').each(function () {
        const groupId = parseInt($(this).attr('id'));
        groupIds[$(this).text()] = groupId;
      });

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
        $("#remove-group-modal").modal('hide')
        try {
          const response = await $.post(url)
          this.members = response.members
          this.availableToInvite = response.groups
          customAlert("Remove Group", 'Group has been removed from your Community', "success", 6000);
        }
        catch (e) {
          console.log(e)
          // abort
        }
        this.$set(this.isRemoving, id, false)
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
          customAlert("Invite Group", response.message, "success", 6000);
        }
        catch (e) {
          console.log(e)
        }
        this.$set(this.isInviting, id, false)
      },
      cancelGroupInvitation: async function(id) {
        this.$set(this.isCancelingInvitation, id, true)
        $("#cancel-group-invitation-modal").modal('hide')
        const url = `/access/_internal/community/${this.community.id}/retract/${id}/`
        try {
          const response = await $.post(url)
          this.pending = response.pending
          this.availableToInvite = response.groups
        }
        catch(e) {
          console.log(e)
          customAlert("Retract Group Invitation", 'Failed to retract invitation', 'error', 6000);
        }
        this.$set(this.isCancelingInvitation, id, false)
      },
      deleteCommunity: async function() {
        const url = `/access/_internal/community/${this.community.id}/deactivate/`;
        this.isDeletingCommunity = true
        try {
          await $.post(url)
          // redirect to my-communities
          window.location.href = "/my-communities/";
        }
        catch (e) {
          console.log(e)
          customAlert("Delete Community", 'Failed to delete Community', 'error', 6000);
        }
        $("#delete-community-dialog").modal('hide')
        this.isDeletingCommunity = false
      },
      approveGroup: async function (id) {
        this.$set(this.isApprovingGroup, id, true)
        const url = `/access/_internal/community/${this.community.id}/approve/${id}/`;
        try {
          const response = await $.post(url)
          // TODO: update state
        }
        catch (e) {
          console.log(e)
          customAlert("Approve Group Join Request", 'Failed to approve request', 'error', 6000);
        }
        this.$set(this.isApprovingGroup, id, false)

      },
      removeOwner: async function (userId) {
        const url = `/access/_internal/community/${this.community.id}/owner/${userId}/remove`
        $("#remove-community-owner-modal").modal('hide')
        this.$set(this.isRemovingOwner, userId, true)
        try {
          const response = await $.post(url)
          if (response.community) {
            this.community.owners = response.community.owners
            if (response.hasOwnProperty('is_admin')) {
              this.isAdmin = !!response.is_owner
              if (!this.isAdmin) {
                // User should no longer see the admin tab. Make resources tab active.
                $('#user-profile-tabs a[href="#resources"]').tab('show')
              }
            }
            customAlert('Remove Community Owner', 'User has been removed as an owner of this Community', 'success', 6000);
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