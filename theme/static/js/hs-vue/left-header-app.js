let leftHeaderApp = new Vue({
    el: '#left-header-table',
    delimiters: ['${', '}'],
    data: {
        owners: [
            {
                user_type: "initial",
                access: "initial",
                id: "initial",
                pictureUrl: "initial",
                best_name: "initial",
                user_name: "initial",
                can_undo: "initial",
                email: "initial",
                organization: "initial",
                title: "initial",
                contributions: "initial",
                subject_areas: ["one", "two", "three"],
                identifiers: [],
                state: "initial",
                joined: "initial",
            },
        ],
    },
    methods: {}
});