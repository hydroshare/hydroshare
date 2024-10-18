$(document).ready(function () {
  const CommunityApp = new Vue({
    el: "#community-app",
    delimiters: ['${', '}'],
    data: {
      filterTo: [],
      resourcesByGroup: {},
      availableToInvite: null,
      members: null,
      community: null,
      isAdmin: null,
      pending: null,
      targetGroup: null,
      targetOwner: null,
      selectedLogo: null,
      selectedBanner: null,
      isRemoving: {},
      isApprovingGroup: {},
      isInviting: {},
      isRemovingOwner: {},
      isCancelingInvitation: {},
      isRejectingGroup: {},
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
    beforeMount() {
      // Load data
      const appData = JSON.parse(document.getElementById('community-app-data').textContent);

      this.community = appData.community;
      this.isAdmin = appData.is_admin;
      this.availableToInvite = appData.groups;
      this.members = appData.members.sort((a, b) => a < b ? -1 : 1);
      this.pending = appData.pending;
      this.resourcesByGroup = appData.community_resources_by_group;
    },
    mounted() {
      // Styling and placeholder for user auto-complete
      $("input[name='user-autocomplete']")
        .attr("placeholder", "Search by name or username")
        .addClass("form-control");
    },
    methods: {
      loadOwnerCard(data) {
        const el = $(data.event.target).closest('.profile-link');
        const cardWidth = 350;

        this.userCardSelected = data.user;
        this.cardPosition.left = el.position().left - (cardWidth / 2) + (el.width() / 2);
        this.cardPosition.top = el.position().top + 30;
      },
      isVisible(resourceId) {
        if (!this.filterTo.length) {
          return true;  // If no selections show all
        }

        return this.filterTo.some((groupId) => {
          return this.resourcesByGroup[groupId]?.includes(resourceId);
        });
      },
      updateContributors(groupId) {
        const index = this.filterTo.indexOf(groupId);

        if (index < 0) {
          this.filterTo.push(groupId)
        } else {
          this.filterTo.splice(index, 1);
        }
      },
      removeGroup: async function (id) {
        this.$set(this.isRemoving, id, true)
        const url = '/access/_internal/community/' + this.community.id + '/remove/' + id + '/';
        $("#remove-group-modal").modal('hide')
        try {
          const response = await $.post(url)
          this.members = response.members
          this.availableToInvite = response.groups
          customAlert("Remove Group", 'Group has been removed from your Community', "success", 6000, true);
        }
        catch (e) {
          customAlert("Remove Group", 'Failed to remove Group from your Community', "error", 6000, true);
          console.log(e)
          // abort
        }
        this.$set(this.isRemoving, id, false)
      },
      inviteGroup: async function (id) {
        this.$set(this.isInviting, id, true)
        const url = '/access/_internal/community/' + this.community.id + '/invite/' + id + '/';
        try {
          const response = await $.post(url)
          const group = this.availableToInvite.find(g => g.id === id)
          group.wasInvited = true

          if (response.hasOwnProperty('pending')) {
            this.pending = response.pending
          }
          if (response.hasOwnProperty('members')) {
            this.members = response.members
          }
          customAlert("Invite Group", 'The Group has been invited to join', "success", 6000, true);
        }
        catch (e) {
          customAlert("Invite Group", 'Failed to send invitation', "error", 6000, true);
          console.log(e)
        }
        this.$set(this.isInviting, id, false)
      },
      rejectGroup: async function (id) {
        this.$set(this.isRejectingGroup, id, true)
        const url = '/access/_internal/community/' + this.community.id + '/decline/' + id + '/';
        try {
          const response = await $.post(url);

          if (response.hasOwnProperty('pending')) {
            this.pending = response.pending
          }
          if (response.hasOwnProperty('members')) {
            this.members = response.members
          }
          $("#reject-group-modal").modal('hide');
          customAlert("Reject Group", "The Group's request to join the Community has been rejected", "success", 6000, true);
        }
        catch (e) {
          console.log(e)
          customAlert("Reject Group", `Failed to reject Group`, "error", 6000, true);
          $("#reject-group-modal").modal('hide');
        }
        this.$set(this.isRejectingGroup, id, false)
      },
      cancelGroupInvitation: async function(id) {
        this.$set(this.isCancelingInvitation, id, true)
        const url = `/access/_internal/community/${this.community.id}/retract/${id}/`
        try {
          const response = await $.post(url)
          this.pending = response.pending;
          this.availableToInvite = response.groups;
          $("#cancel-group-invitation-modal").modal('hide');
          customAlert("Retract Group Invitation", 'The invitation has been retracted', 'success', 6000, true);
        }
        catch(e) {
          console.log(e)
          $("#cancel-group-invitation-modal").modal('hide');
          customAlert("Retract Group Invitation", 'Failed to retract invitation', 'error', 6000, true);
        }
        this.$set(this.isCancelingInvitation, id, false)
      },
      deleteCommunity: async function() {
        const url = `/access/_internal/community/${this.community.id}/deactivate/`;
        this.isDeletingCommunity = true
        try {
          await $.post(url);
          // redirect to my-communities
          window.location.href = "/my-communities/";
        }
        catch (e) {
          console.log(e)
          customAlert("Delete Community", 'Failed to delete Community', 'error', 6000, true);
        }
        $("#delete-community-dialog").modal('hide')
        this.isDeletingCommunity = false
      },
      approveGroup: async function (id) {
        this.$set(this.isApprovingGroup, id, true)
        const url = `/access/_internal/community/${this.community.id}/approve/${id}/`;
        try {
          const response = await $.post(url);
          if (response.hasOwnProperty('pending')) {
            this.pending = response.pending
          }
          if (response.hasOwnProperty('members')) {
            this.members = response.members
          }
          customAlert("Approve Group Join Request", "The Group's request to join the Community has been accepted", "success", 6000, true);
        }
        catch (e) {
          console.log(e)
          customAlert("Approve Group Join Request", 'Failed to approve request', 'error', 6000, true);
        }
        this.$set(this.isApprovingGroup, id, false);
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
              this.isAdmin = !!response.is_admin
              if (!this.isAdmin) {
                // User should no longer see the admin tab. Make resources tab active.
                $('#user-profile-tabs a[href="#resources"]').tab('show')
              }
            }
            customAlert('Remove Community Owner', 'User has been removed as an owner of this Community', 'success', 6000, true);
          }
        }
        catch (e) {
          console.log(e);
          customAlert("Add Community Owner", 'Failed to remove Community owner', 'error', 6000, true);
        }
        this.$set(this.isRemovingOwner, userId, false)
      },
      addOwner: async function () {
        let userId = $("#id_user").find(':selected').val();

        const url = `/access/_internal/community/${this.community.id}/owner/${userId}/add`
        try {
          const response = await $.post(url)
          if (response.community) {
            this.community.owners = response.community.owners
            customAlert('Add Community Owner', 'User has been added as an owner of this Community', 'success', 6000, true);
            // close the modal
            $("#community-settings-add-owner").modal('hide')
          }
        }
        catch (e) {
          if (e.status === 400 && e.responseText.indexOf('already owns community') >= 0) {
            customAlert('Add Community Owner', 'User is already an owner of this Community', 'info', 6000, true);
          }
          else {
            console.log(e);
            customAlert("Add Community Owner", 'Failed to add user as Community owner', 'error', 6000, true);
          }
        }
      },
      onLogoChange(event) {
        const label = event.target.value
          .replace(/\\/g, '/')
          .replace(/.*\//, '');
        this.selectedLogo = label
      },
      onBannerChange(event) {
        const label = event.target.value
          .replace(/\\/g, '/')
          .replace(/.*\//, '');
        this.selectedBanner = label
      }
    }
  });

  // prevent default form submission
  let button = $("#community-settings-add-owner-btn");
  button.click(function (e) {
    e.preventDefault();
  });
});