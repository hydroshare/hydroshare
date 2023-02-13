let groupCommunitiesApp = new Vue({
  el: '#group-communities',
  delimiters: ['${', '}'],
  data: {
      joined: null,
      pending: null,
      availableToJoin: null,
      groupsJoined: null,
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
    this.groupId = JSON.parse(document.getElementById('group_id').textContent);
    this.isGroupOwner = JSON.parse(document.getElementById('is_group_owner').textContent);
    this.joined = JSON.parse(document.getElementById('joined').textContent);
    this.groupsJoined = JSON.parse(document.getElementById('groups_joined').textContent);
    this.pending = JSON.parse(document.getElementById('pending').textContent);
    this.availableToJoin = JSON.parse(document.getElementById('available_to_join').textContent);
  },
  // watch: {
      
  // },
  // computed: {
      
  // },
  methods: {
    leave: async function(id) {
      this.$set(this.isLeaving, id, true)
      const url = '/access/_internal/group/' + this.groupId + '/leave/' + id + '/';
      try {
        const response = await $.post(url)
        delete this.isLeaving[id]
        $("#leave-community-modal").modal('hide')
        customAlert("Leave Community", response.message, "success", 6000);
        // TODO: update state
      }
      catch(e) {
        console.log(e)
        // abort
        this.$set(this.isLeaving, id, false)
      }
    },
    acceptInvitation: async function(id) {
      this.$set(this.isAcceptingInvitation, id, true)
      const url = '/access/_internal/group/' + this.groupId + '/approve/' + id + '/';
      try {
        const response = await $.post(url)
        // TODO: update state
        this.$set(this.isAcceptingInvitation, id, false)
        delete this.isAcceptingInvitation[id]
        customAlert("Join Community", 'The Community invitation has been accepted', "success", 6000);
      }
      catch(e) {
        console.log(e)
        // abort
        this.$set(this.isAcceptingInvitation, id, false)
      }
    },
    declineInvitation: async function(id) {
      this.$set(this.isDecliningInvitation, id, true)
      const url = '/access/_internal/group/' + this.groupId + '/decline/' + id + '/';
      try {
        const response = await $.post(url)
        // TODO: update state
        console.log(response)
        this.$set(this.isDecliningInvitation, id, false)
        delete this.isDecliningInvitation[id]
        customAlert("Decline Community Invitation", `The invitation has been declined`, "success", 6000);
      }
      catch(e) {
        console.log(e)
        // abort
        this.$set(this.isDecliningInvitation, id, false)
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
        this.$set(this.isRetractingRequest, id, false)
        delete this.isRetractingRequest[id]
        $("#retract-community-join-request-modal").modal('hide')
        customAlert("Retract Request", `The join request has been retracted`, "success", 6000);
      }
      catch(e) {
        console.log(e)
        $("#retract-community-join-request-modal").modal('hide')
      }
    },
    // join: async function(id) {
    //   this.$set(this.isJoining, id, true)
    //   const url = '/access/_internal/group/' + this.groupId + '/join/' + id + '/';
    //   try {
    //     const response = await $.post(url)
    //     // TODO: update state
    //     this.$set(this.isJoining, id, false)
    //     delete this.isJoining[id]
    //     customAlert("Join Community", response.message, "success", 6000);
    //   }
    //   catch(e) {
    //     console.log(e)
    //     // abort
    //     this.$set(this.isJoining, id, false)
    //   }
    // },
  }
});