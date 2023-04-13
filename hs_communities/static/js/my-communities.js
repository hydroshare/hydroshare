$(document).ready(function () {
  const MyCommunitiesApp = new Vue({
    el: "#my-communities-app",
    delimiters: ['${', '}'],
    data: {
      isRemoving: {},
      targetRequest: null,
      pendingRequests: []
    },
    beforeMount() {
      // Load data
      const appData = JSON.parse(document.getElementById('my-communities-app-data').textContent);
      this.pendingRequests = appData.user_pending_requests;
      this.declinedRequests = appData.user_declined_requests;
    },
    computed: {
      allRequests() {
        return [...this.declinedRequests, ...this.pendingRequests];
      }
    },
    methods: {
      cancelRequest: async function(id) {
        this.$set(this.isRemoving, id, true);
        const url = '/access/_internal/crequest/cancel/' + id + '/';
        try {
          const response = await $.post(url);
          if (response.message === "Request has been cancelled") {
            this.pendingRequests = response.pending || [];
            this.declinedRequests = response.declined || [];
          }
          this.$set(this.isRemoving, id, false)
          $("#remove-community-request-modal").modal('hide');
          customAlert("Cancel Request", response.message, "success", 6000, true);
        }
        catch(e) {
          // abort
          console.log(e)
          customAlert("Cancel Request", 'Failed to cancel request', "error", 6000, true);
          this.$set(this.isRemoving, id, false);
        }
      }
    }
  });
});