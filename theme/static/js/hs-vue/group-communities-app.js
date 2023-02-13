let groupCommunitiesApp = new Vue({
  el: '#group-communities',
  delimiters: ['${', '}'],
  data: {
      joined: null,
      pending: null,
      allCommunities: null,
      groupsJoined: null,
      groupId: null,
      isGroupOwner: null,
      isLeaving: { },
      isJoining: { },
      targetCommunity: null
  },
  beforeMount() {
    // Load data
    this.groupId = JSON.parse(document.getElementById('group_id').textContent);
    this.isGroupOwner = JSON.parse(document.getElementById('is_group_owner').textContent);
    this.joined = JSON.parse(document.getElementById('joined').textContent);
    this.groupsJoined = JSON.parse(document.getElementById('groups_joined').textContent);
    this.pending = JSON.parse(document.getElementById('pending').textContent);
    this.allCommunities = JSON.parse(document.getElementById('all_communities').textContent);
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