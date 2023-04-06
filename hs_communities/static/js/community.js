var resourceTable;

var ACTIONS_COL = 0;
var RESOURCE_TYPE_COL = 1;
var TITLE_COL = 2;
var OWNER_COL = 3;
var DATE_CREATED_COL = 4;
var LAST_MODIFIED_COL = 5;
var SUBJECT_COL = 6;
var AUTHORS_COL = 7;
var PERM_LEVEL_COL = 8;
var LABELS_COL = 9;
var FAVORITE_COL = 10;
var LAST_MODIF_SORT_COL = 11;
var SHARING_STATUS_COL = 12;
var DATE_CREATED_SORT_COL = 13;
var ACCESS_GRANTOR_COL = 14;

var colDefs = [
    {
        "targets": [ACTIONS_COL],     // Row selector and controls
        "visible": false,
    },
    {
        "targets": [RESOURCE_TYPE_COL],     // Resource type
        "width": "100px"
    },
    {
        "targets": [ACTIONS_COL],     // Actions
        "orderable": false,
        "searchable": false,
        "width": "70px"
    },
    {
        "targets": [LAST_MODIFIED_COL],     // Last modified
        "iDataSort": LAST_MODIF_SORT_COL
    },
    {
        "targets": [DATE_CREATED_COL],     // Created
        "iDataSort": DATE_CREATED_SORT_COL
    },
    {
        "targets": [SUBJECT_COL],     // Subject
        "visible": false,
        "searchable": true
    },
    {
        "targets": [AUTHORS_COL],     // Authors
        "visible": false,
        "searchable": true
    },
    {
        "targets": [PERM_LEVEL_COL],     // Permission level
        "visible": false,
        "searchable": true
    },
    {
        "targets": [LABELS_COL],     // Labels
        "visible": false,
        "searchable": true
    },
    {
        "targets": [FAVORITE_COL],     // Favorite
        "visible": false,
        "searchable": true
    },
    {
        "targets": [LAST_MODIF_SORT_COL],     // Last modified (for sorting)
        "visible": false,
        "searchable": true
    },
    {
        "targets": [DATE_CREATED_SORT_COL],     // Last modified (for sorting)
        "visible": false,
        "searchable": true
    },
    {
        "targets": [SHARING_STATUS_COL],     // Sharing status
        "visible": false,
        "searchable": false
    },
    {
        "targets": [ACCESS_GRANTOR_COL],     // Access Grantor
        "visible": false,
        "searchable": true
    }
];

$(document).ready(function () {
  const CommunityApp = new Vue({
    el: "#community-app",
    delimiters: ['${', '}'],
    data: {
      filterTo: [],
      groupIds: [],
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
      this.members = appData.members;
      this.pending = appData.pending;
      console.log(this.members)
    },
    mounted() {
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
        let userId;

        if ($("#user-deck > .hilight").length > 0) {
          userId = parseInt($("#user-deck > .hilight")[0].getAttribute("data-value"));
        }
        else {
          return false;   // No user selected
        }

        $(".hilight > span").click(); // Clear the autocomplete

        const url = `/access/_internal/community/${this.community.id}/owner/${userId}/add`
        try {
          const response = await $.post(url)
          if (response.community) {
            this.community.owners = response.community.owners
            customAlert('Add Community Owner', 'User has been added as an owner of this Community', 'success', 6000, true);
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
});