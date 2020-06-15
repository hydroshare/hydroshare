Vue.component('notification', {
    delimiters: ['${', '}'],
    template: '#notification',
    props: {
        title: { type: Object, required: true },
        status: { type: Boolean, required: true },
    },
    data: function () {
        return {}
    },
});

$(document).ready(function () {
    $('#notifications-dropdown').on('show.bs.dropdown', function () {
        console.log("shown");
        notificationsApp.open();
    });

    let notificationsApp = new Vue({
        el: '#app-notifications',
        delimiters: ['${', '}'],
        data: {
            tasks: [],
            loading: true
        },
        methods: {
            open: function () {
                console.log("Opening...")
                let vue = this;
                vue.loading = true;
                vue.fetchTasks();
            },
            fetchTasks: function () {
                let vue = this;
                $.ajax({
                    type: "GET",
                    url: '/hsapi/_internal/get_tasks_by_user',
                    success: function (response) {
                        console.log(response);
                        vue.loading = false;
                    },
                    error: function (response) {
                        console.log(response);
                        vue.loading = false;
                    }
                });
            }
        },
        mounted: function () {
            let vue = this;
            vue.fetchTasks();
        }
    });
});
