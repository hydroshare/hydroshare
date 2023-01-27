$(document).ready(function () {
  const CommunityApp = new Vue({
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

      $('#groups-list li').each(function () {
        const groupId = parseInt($(this).attr('id'));
        groupIds[$(this).text()] = groupId;
      });

      $("input[name='user-autocomplete']").attr("placeholder", "Search by name or username").addClass("form-control");

      this.$data.groupIds = groupIds;

      const filterGroup = $('#filter-querystring').text();
      if (filterGroup && this.$data.groupIds[filterGroup]) {
        this.$data.filterTo.push(this.$data.groupIds[filterGroup])
      }
    },
    methods: {
      onLoadOwnerCard(data) {
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
      remove: async function (id) {
        this.$set(this.isRemoving, id, true)
        // TODO: handle leaving
        const url = '/access/_internal/communityjson/' + this.community.id + '/remove/' + id + '/';
        try {
          const response = await $.get(url)
          this.availableToInvite = response.groups
          this.members = response.members
          this.$set(this.isRemoving, id, false)
          $("#remove-group-modal").modal('hide')
          customAlert("Remove Group", response.message, "success", 6000);
        }
        catch (e) {
          console.log(e)
          // abort
          this.$set(this.isRemoving, id, false)
        }
      },
      invite: async function (id) {
        this.$set(this.isInviting, id, true)
        // TODO: handle leaving
        const url = '/access/_internal/communityjson/' + this.community.id + '/invite/' + id + '/';
        try {
          const response = await $.get(url, { 'responseType': 'text' })
          const group = this.availableToInvite.find(g => g.id === id)
          group.wasInvited = true

          // this.availableToInvite = response.groups
          this.members = response.members
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
        const url = '/access/_internal/communityjson/' + this.community.id + '/approve/' + id + '/';
        try {
          const response = await $.get(url, { 'responseType': 'text' })
          // this.joined = response.joined
          // this.availableToJoin = response.available_to_join
          this.$set(this.isApproving, id, false)
        }
        catch (e) {
          console.log(e)
          // abort
          this.$set(this.isApproving, id, false)
        }
      },
      onRemoveOwner: async function (owner) {
        console.log('removing owner')
      },
      onAddOwner: async function () {
        let targetUserId;

        if ($("#user-deck > .hilight").length > 0) {
          targetUserId = parseInt($("#user-deck > .hilight")[0].getAttribute("data-value"));
        }
        else {
          return false;   // No user selected
        }

        $(".hilight > span").click(); // Clear the autocomplete
        console.log(targetUserId)
        // add owner here

        const url = `/access/_internal/community/${this.community.id}/owner/${targetUserId}/add`
        try {
          const response = await $.post(url, { 'responseType': 'text' })
          console.log(response)
        }
        catch (e) {
          console.log(e)
          // abort
          this.$set(this.isApproving, id, false)
        }
      },
    }
  });
});