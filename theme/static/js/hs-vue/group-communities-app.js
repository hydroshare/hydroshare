let groupCommunitiesApp = new Vue({
  el: '#group-communities',
  delimiters: ['${', '}'],
  data: {
      joined: null,
      pending: null,
      availableToJoin: null,
      groupId: null,
      isGroupOwner: null,
      isLeaving: { },
      targetCommunity: null,
      isDecliningInvitation: { },
      isAcceptingInvitation: { },
      isRetractingRequest: { },
  },
  beforeMount() {
    // Load data
    const appData = JSON.parse(document.getElementById('communities-app-data').textContent);
    
    this.isGroupOwner = appData.is_group_owner;
    this.groupId = appData.gid;
    this.joined = appData.joined;
    this.pending = appData.pending;
    this.availableToJoin = appData.available_to_join;
    this.isGroupPrivate = appData.is_group_private;
  },
  methods: {
    leaveCommunity: async function(id) {
      this.$set(this.isLeaving, id, true)
      const url = '/access/_internal/group/' + this.groupId + '/leave/' + id + '/';
      try {
        const response = await $.post(url)
        if (response.hasOwnProperty('joined')) {
          this.joined = response.joined
        }
        if (response.hasOwnProperty('available_to_join')) {
          this.availableToJoin = response.available_to_join
        }
        if (response.hasOwnProperty('joined')) {
          this.joined = response.joined;
        }
        this.$set(this.isLeaving, id, false);
        delete this.isLeaving[id];
        $("#leave-community-modal").modal('hide');
        customAlert("Leave Community", `The Group has left this Community`, "success", 6000, true);
      }
      catch(e) {
        // abort
        console.log(e)
        customAlert("Leave Community", `Failed to leave this Community`, "error", 6000, true);
        this.$set(this.isLeaving, id, false);
      }
    },
    acceptInvitation: async function(id) {
      this.$set(this.isAcceptingInvitation, id, true)
      const url = '/access/_internal/group/' + this.groupId + '/approve/' + id + '/';
      try {
        const response = await $.post(url)
        if (response.hasOwnProperty('pending')) {
          this.pending = response.pending;
        }
        if (response.hasOwnProperty('available_to_join')) {
          this.availableToJoin = response.available_to_join;
        }
        if (response.hasOwnProperty('joined')) {
          this.joined = response.joined;
        }
        this.$set(this.isAcceptingInvitation, id, false)
        delete this.isAcceptingInvitation[id]
        customAlert("Join Community", 'The Community invitation has been accepted', "success", 6000, true);
      }
      catch(e) {
        // abort
        console.log(e);
        customAlert("Join Community", 'Failed to accept Community invitation', "error", 6000, true);
        this.$set(this.isAcceptingInvitation, id, false)
      }
    },
    declineInvitation: async function(id) {
      this.$set(this.isDecliningInvitation, id, true)
      const url = '/access/_internal/group/' + this.groupId + '/decline/' + id + '/';
      try {
        const response = await $.post(url)
        if (response.hasOwnProperty('pending')) {
          this.pending = response.pending;
        }
        if (response.hasOwnProperty('available_to_join')) {
          this.availableToJoin = response.available_to_join;
        }
        this.$set(this.isDecliningInvitation, id, false)
        delete this.isDecliningInvitation[id];
        $('#decline-community-invitation-modal').modal('hide');
        customAlert("Decline Community Invitation", `The invitation has been declined`, "success", 6000, true);
      }
      catch(e) {
        console.log(e)
        customAlert("Decline Community Invitation", `Failed to decline Community invitation`, "error", 6000, true);
        // abort
        this.$set(this.isDecliningInvitation, id, false);
        $('#decline-community-invitation-modal').modal('hide');
      }
    },
    retractRequest: async function(id) {
      this.$set(this.isRetractingRequest, id, true)
      const url = '/access/_internal/group/' + this.groupId + '/retract/' + id + '/';
      try {
        const response = await $.post(url)
        if (response.hasOwnProperty('pending')) {
          this.pending = response.pending
        }
        if (response.hasOwnProperty('available_to_join')) {
          this.availableToJoin = response.available_to_join
        }
        this.$set(this.isRetractingRequest, id, false);
        delete this.isRetractingRequest[id];
        $("#retract-community-join-request-modal").modal('hide');
        customAlert("Retract Request", `The join request has been retracted`, "success", 6000, true);
      }
      catch(e) {
        console.log(e)
        this.$set(this.isRetractingRequest, id, false);
        customAlert("Retract Request", `Failed to retract request`, "error", 6000, true);
        $("#retract-community-join-request-modal").modal('hide');
      }
    },
  }
});