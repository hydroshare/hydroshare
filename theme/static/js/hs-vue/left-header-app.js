let leftHeaderApp = new Vue({
    el: '#left-header-table',
    delimiters: ['${', '}'],
    data: {
        owners: USERS_JSON.map(function(user) {
            user.loading = false;
            return user;
        }).filter(function(user){
            return user.access === 'owner';
        }),
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
    },
    methods: {
        onLoadCard: function(user) {
            this.userCardSelected = user;
        }
    }
});