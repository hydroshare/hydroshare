
Vue.component('join-communities', {
  delimiters: ['${', '}'],
  template: '#join-communities-template',
  props: {
    groups: {
      type: Array, default: []
    },
    communities: {
      type: Array, default: []
    },
    defaultGroupId: { type: Number },
    defaultCommunityId: { type: Number },
  },
  computed: {

  },
  data: () => {
    return {
      selectedGroupId: null,
      selectedCommunityId: null,
      isSendingInvite: false,
      message: { type: 'success', text: '' }
    }
  },
  created() {
    if (this.defaultGroupId) {
      this.selectedGroupId = this.defaultGroupId
    }

    if (this.defaultCommunityId) {
      this.selectedCommunityId = this.defaultCommunityId
    }
  },
  methods: {
    inviteGroup: async function () {
      if (!this.selectedCommunityId || !this.selectedGroupId) {
        return
      }
      this.isSendingInvite = true
      this.message.text = ''
      // const isCommunityInvitingGroup = this.defaultCommunityId;
      const url = `/access/_internal/group/${this.selectedGroupId}/join/${this.selectedCommunityId}/`
      try {
        const response = await $.post(url);
        if (response.hasOwnProperty('members')) {
          this.$emit('update-members', response.members)
        }
        if (response.hasOwnProperty('pending')) {
          this.$emit('update-pending', response.pending)
        }
        if (response.hasOwnProperty('available_to_join')) {
          this.$emit('update-available-to-join', response.available_to_join)
        }
        if (response.hasOwnProperty('joined')) {
          this.$emit('update-joined', response.joined)
        }
        this.message.type = 'success'
        this.message.text = 'Invitation sent!'
      }
      catch (e) {
        console.log(e)
        this.message.type = 'danger'
        this.message.text = 'Failed to send join request'
      }
      this.isSendingInvite = false
    },
  }
});