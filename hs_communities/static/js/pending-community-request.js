$(document).ready(function () {
  const CommunityCreationRequestApp = new Vue({
    el: "#pending-community-request-app",
    delimiters: ['${', '}'],
    data: {
      request: REQUEST || null,
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
      onLoadOwnerCard: function(data) {
        const el = $(data.event.target);
        const cardWidth = 350;

        this.userCardSelected = data.user;
        this.cardPosition.left = el.position().left - (cardWidth / 2) + (el.width() / 2);
        this.cardPosition.top = el.position().top + 30;
      },
    }
  });
});