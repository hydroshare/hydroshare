$(document).ready(function () {
  const CommunityCreationRequestApp = new Vue({
    el: "#pending-community-request-app",
    delimiters: ['${', '}'],
    data: {
      request: REQUEST || null,
      isEditMode: false,
      isSaving: false,
      isApproving: false,
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
    created() {
      console.log(this.request)
    },
    mounted() {

    },
    methods: {
      onLoadOwnerCard(data) {
        const el = $(data.event.target);
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
          // Redirect to requests page
          window.location.href = "/communities/manage-requests/";
        }
        this.isApproving = false
      },
      async onReject() {
        if (!this.rejectReason) {
          return false
        }
        this.isRejecting = true
        const response = await $.post(`/access/_internal/crequest/decline/${this.request.id}/`, { reason: this.rejectReason} )
        console.log(response)

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
          this.isEditMode = false
        }
        else {
          // show error
        }

        this.isSaving = false
      },
      onCancel() {
        // restore to original values
        this.isEditMode = false
        console.log(this.request.community_to_approve.name)
      }
    }
  });
});