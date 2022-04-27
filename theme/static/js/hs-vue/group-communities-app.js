let groupCommunitiesApp = new Vue({
  el: '#group-communities',
  delimiters: ['${', '}'],
  data: {
      joined: JOINED,
      pending: PENDING,
      availableToJoin: COMMUNITIES_CAN_JOIN,
      groupId: GROUP_ID,
      isGroupOwner: IS_GROUP_OWNER,
      isLeaving: { },
      isJoining: { },
      test: 'TEST',
      targetCommunity: null
  },
  watch: {
      
  },
  computed: {
      
  },
  methods: {
    leave: async function(id) {
      this.$set(this.isLeaving, id, true)
      // TODO: handle leaving
      const url = '/access/_internal/groupjson/' + this.groupId + '/leave/' + id + '/';
      try {
        const response = await $.get(url)
        this.joined = response.joined
        this.availableToJoin = response.available_to_join
        delete this.isLeaving[id]
        $("#leave-community-modal").modal('hide')
        customAlert("Leave Community", response.message, "success", 6000);
      }
      catch(e) {
        console.log(e)
        // abort
        this.$set(this.isLeaving, id, false)
      }
    },
    join: async function(id) {
      this.$set(this.isJoining, id, true)
      // TODO: handle leaving
      const url = '/access/_internal/groupjson/' + this.groupId + '/join/' + id + '/';
      try {
        const response = await $.get(url, { 'responseType': 'text' })
        console.log(response)
        this.joined = response.joined
        this.availableToJoin = response.available_to_join
        delete this.isJoining[id]
        customAlert("Join Community", response.message, "success", 6000);
      }
      catch(e) {
        console.log(e)
        // abort
        this.$set(this.isJoining, id, false)
      }
    },
  },
  created() {
    console.log(this.groupId)
  }
});