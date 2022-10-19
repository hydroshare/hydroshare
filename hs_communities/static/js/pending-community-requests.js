$(document).ready(function () {
  const PendingCommunityRequestsApp = new Vue({
    el: "#pending-community-requests-app",
    delimiters: ['${', '}'],
    data: {
      pendingRequests: PENDING_REQUESTS || []
    },
    mounted: function () {
    },
    methods: {
      removeOwner: async function(owner) {
        
      }
    }
  });
});