$(document).ready(function () {
  const CommunityCreationRequestApp = new Vue({
    el: "#pending-community-request-app",
    delimiters: ['${', '}'],
    data: {
      request: null,
      isEditMode: false,
      isSaving: false,
      isApproving: false,
      isResubmitting: false,
      isRejecting: false,
      rejectReason: '',
      userCardSelected: {
        user_type: null,
        access: null,
        id: null,
        pictureUrl: null,
        best_name: null,
        user_name: null,
        can_undo: null,
        email: null,
        organization: null,
        title: null,
        contributions: null,
        subject_areas: null,
        identifiers: [],
        state: null,
        country: null,
        joined: null,
      },
      cardPosition: {
        top: 0,
        left: 0,
      }
    },
    // created() {
    // },
    beforeMount() {
      // Load data
      this.request = JSON.parse(document.getElementById('community_request').textContent)
    },
    // mounted() {
    // },
    methods: {
      loadOwnerCard(data) {
        const el = $(data.event.target).closest('.profile-link');
        const cardWidth = 350;

        this.userCardSelected = data.user;
        this.cardPosition.left = el.position().left - (cardWidth / 2) + (el.width() / 2);
        this.cardPosition.top = el.position().top + 30;
      },
      async onApprove() {
        this.isApproving = true
        const url = `/access/_internal/crequest/approve/${this.request.id}/`;
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            // Do not set content-type header. The browser will set it for you.
            // https://muffinman.io/blog/uploading-files-using-fetch-multipart-form-data/
            'X-CSRFToken': getCookie('csrftoken')
          }
        });

        if (response.status === 200) {
          this.$set(this.request.community_to_approve, 'status', 'Approved');
          this.$set(this.request, 'status', 'Approved');
          // Redirect to requests page
          window.location.href = "/communities/manage-requests/";
        }
        else {
          customAlert("Approve Community Request", 'Failed to approve Request', "error", 6000, true);
        }
        this.isApproving = false
      },
      async onResubmit() {
        this.isResubmitting = true
        try {
          const url = `/access/_internal/crequest/resubmit/${this.request.id}/`;
          const response = await $.post(url);
          if (response.message === 'Request has been resubmitted') {
            this.$set(this.request.community_to_approve, 'status', 'Submitted');
            this.$set(this.request, 'status', 'Submitted');
          }
        }
        catch(e) {
          customAlert("Resubmit Community", 'Failed to resubmit this request', "error", 6000, true);
          console.error(e);
        }
        
        this.isResubmitting = false
      },
      async onReject() {
        if (!this.rejectReason) {
          return false;
        }
        this.isRejecting = true
        const response = await $.post(`/access/_internal/crequest/decline/${this.request.id}/`, { reason: this.rejectReason });

        if (response.message === 'Request declined') {
          this.$set(this.request.community_to_approve, 'status', 'Rejected');
          // Redirect to requests page
          window.location.href = "/communities/manage-requests/";
        }
        this.isRejecting = false
      },
      async onUpdate() {
        this.isSaving = true;
        const url = `/access/_internal/crequest/update/${this.request.id}/`;
        const formData = new FormData();
        const fields = ['name', 'description', 'purpose', 'email', 'url'];

        for (let field of fields) {
          formData.append(field, this.$refs[field].value)
        }

        const response = await fetch(url, {
          method: 'POST',
          headers: {
            // Do not set content-type header. The browser will set it for you.
            // https://muffinman.io/blog/uploading-files-using-fetch-multipart-form-data/
            'X-CSRFToken': getCookie('csrftoken')
          },
          body: formData
        });
        
        if (response.status === 200) {
          for (let field of fields) {
            this.$set(this.request.community_to_approve, field, formData.get(field));
          }
          this.isEditMode = false;
          customAlert("New Community Request", 'Your changes have been saved', "success", 6000, true);
        }
        else {
          customAlert("New Community Request", 'Failed to save changes', "error", 6000, true);
        }

        this.isSaving = false;
      },
      onCancel() {
        // restore to original values
        this.isEditMode = false;
      }
    }
  });
});