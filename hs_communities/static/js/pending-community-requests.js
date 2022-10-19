$(document).ready(function () {
  const PendingCommunityRequestsApp = new Vue({
    el: "#pending-community-requests-app",
    delimiters: ['${', '}'],
    data: {
      pendingRequests: PENDING_REQUESTS || []
    },
    created() {
      console.log(this.pendingRequests[0])
    },
    mounted() {
      
    },
    methods: {
      removeOwner: async function(owner) {
        
      }
    }
  });
});