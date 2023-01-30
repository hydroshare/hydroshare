let groupCommunitiesApp = new Vue({
  el: '#group-communities',
  delimiters: ['${', '}'],
  data: {
      joined: JOINED,
      pending: PENDING,
      allCommunities: ALL_COMMUNITIES,
      groupsJoined: GROUPS_JOINED,
      groupId: GROUP_ID,
      isGroupOwner: IS_GROUP_OWNER,
      isLeaving: { },
      isJoining: { },
      targetCommunity: null
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
    acceptInvite: async function(id) {
      this.$set(this.isJoining, id, true)
      const url = '/access/_internal/group/' + this.groupId + '/approve/' + id + '/';
      try {
        const response = await $.post(url)
        // TODO: update state
        this.$set(this.isJoining, id, false)
        delete this.isJoining[id]
        customAlert("Join Community", response.message, "success", 6000);
      }
      catch(e) {
        console.log(e)
        // abort
        this.$set(this.isJoining, id, false)
      }
    },
    join: async function(id) {
      this.$set(this.isJoining, id, true)
      const url = '/access/_internal/group/' + this.groupId + '/join/' + id + '/';
      try {
        const response = await $.post(url)
        // TODO: update state
        this.$set(this.isJoining, id, false)
        delete this.isJoining[id]
        customAlert("Join Community", response.message, "success", 6000);
      }
      catch(e) {
        console.log(e)
        // abort
        this.$set(this.isJoining, id, false)
      }
    },
  }
});