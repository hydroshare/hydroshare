let groupCommunitiesApp = new Vue({
  el: '#group-communities',
  delimiters: ['${', '}'],
  data: {
      joined: JOINED,
      pending: PENDING,
      groupId: GROUP_ID,
      isGroupOwner: IS_GROUP_OWNER,
      isLeaving: { },
      isJoining: { },
  },
  watch: {
      
  },
  computed: {
      
  },
  methods: {
    leave: async function(id) {
      this.$set(this.isLeaving, id, true)
      // TODO: handle leaving
      const url = '/access/_internal/group/' + this.groupId + '/leave/' + id + '/';
      try {
        const  response = await $.get(url, { 'responseType': 'text' })
        console.log(response)
        this.joined = this.joined.filter(c => c.id !== id)
        delete this.isLeaving[id]
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
      const url = '/access/_internal/group/' + this.groupId + '/join/' + id + '/';
      try {
        const response = await $.get(url, { 'responseType': 'text' })
        console.log(response)
        const community = this.pending.find(c => c.id === id)
        // Add to joined communities
        this.joined = [community, ...this.joined]
        this.pending = this.pending.filter(c => c.id !== id)
        delete this.isJoining[id]
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