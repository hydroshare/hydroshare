let leftHeaderApp = new Vue({
    el: '#left-header-table',
    delimiters: ['${', '}'],
    data: {
        owners: [
            {
                user_type: "owner_1",
                access: "owner_1",
                id: "owner_1",
                pictureUrl: "owner_1",
                best_name: "owner_1",
                user_name: "owner_1",
                can_undo: "owner_1",
                email: "owner_1",
                organization: "owner_1",
                title: "owner_1",
                contributions: "owner_1",
                subject_areas: ["one", "two", "three"],
                identifiers: [],
                state: "owner_1",
                joined: "owner_1",
            },
            {
                user_type: "owner_2",
                access: "owner_2",
                id: "owner_2",
                pictureUrl: "owner_2",
                best_name: "owner_2",
                user_name: "owner_2",
                can_undo: "owner_2",
                email: "owner_2",
                organization: "owner_2",
                title: "owner_2",
                contributions: "owner_2",
                subject_areas: ["one", "two", "three"],
                identifiers: [],
                state: "owner_2",
                joined: "owner_2",
            },
        ],
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
            subject_areas: [],
            identifiers: [],
            state: null,
            joined: null,
        },
    },
    methods: {
        onLoadCard: function(user) {
            this.userCardSelected = user;
        }
    }
});