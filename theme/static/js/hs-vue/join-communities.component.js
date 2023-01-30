
Vue.component('join-communities', {
    delimiters: ['${', '}'],
    template: '#join-communities-template',
    props: {
        groups: {
            type: Array, required: true, default: []
        },
        communities: {
            type: Array, required: true, default: []
        },
        defaultGroupId: { type: Number, required: false },
        defaultCommunityId: { type: Number, required: false },
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
            const url = `/access/_internal/community/${this.selectedCommunityId}/invite/${this.selectedGroupId}/`;
            try {
                const response = await $.post(url)
                if (response.members) {
                    this.$emit('update-members', response.members)
                }
                if (response.pending) {
                    this.$emit('update-pending', response.pending)
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