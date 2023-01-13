$(document).ready(function () {
  const MyCommunitiesApp = new Vue({
    el: "#my-communities-app",
    delimiters: ['${', '}'],
    data: {
      test: 'test!!',
      isRemoving: {},
      targetRequest: null,
      pendingRequests: PENDING_REQUESTS
    },
    mounted: function () {
    },
    methods: {
      remove: async function(id) {
        this.$set(this.isRemoving, id, true)
        const url = '/access/_internal/crequest/remove/' + id + '/';
        try {
          const response = await $.post(url)
          if (response.message === "Request removed") {
            this.pendingRequests = response.pending
          }
          this.$set(this.isRemoving, id, false)
          $("#remove-community-request-modal").modal('hide')
          customAlert("Cancel Request", response.message, "success", 6000);
        }
        catch(e) {
          console.log(e)
          // abort
          this.$set(this.isRemoving, id, false)
        }
      },
    }
  });
});