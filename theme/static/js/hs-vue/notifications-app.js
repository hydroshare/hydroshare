var notificationsApp;

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
        notificationsApp.fetchTasks();
    });

    notificationsApp = new Vue({
        el: '#app-notifications',
        delimiters: ['${', '}'],
        data: {
            tasks: [],
            loading: true,
            isCheckingStatus: false
        },
        computed: {
            someInProgress: function () {
                return this.tasks.find(function (task) {
                    return task.status === "In progress";
                });
            }
        },
        methods: {
            // Shows the tasks dropdown
            show: function () {
                $('#notifications-dropdown').addClass('open');
            },
            fetchTasks: function () {
                let vue = this;
                vue.loading = true;
                $.ajax({
                    type: "GET",
                    url: '/hsapi/_internal/get_tasks_by_user/',
                    success: function (tasks) {
                        vue.loading = false;
                        vue.tasks = [];

                        for (let i = 0; i < tasks.length; i++) {
                            vue.registerTask(tasks[i]);
                        }
                        
                        if (vue.someInProgress && !vue.isCheckingStatus) {
                            // check again in 500ms
                            setTimeout(function() {
                                vue.checkStatus();
                            }, 500)
                        }
                    },
                    error: function (response) {
                        console.log(response);
                        vue.loading = false;
                    }
                });
            },
            // Checks every 500ms while there is at least one task in progress
            checkStatus: function () {
                let vue = this;
                vue.isCheckingStatus = true;
                $.ajax({
                    type: "GET",
                    url: '/hsapi/_internal/get_tasks_by_user/',
                    success: function (tasks) {
                        vue.tasks = [];

                        for (let i = 0; i < tasks.length; i++) {
                            vue.registerTask(tasks[i]);
                        }
                        
                        if (vue.someInProgress) {
                            // check again in 500ms
                            setTimeout(function() {
                                vue.checkStatus();
                            }, 500)
                        }
                        else {
                            vue.isCheckingStatus = false;
                        }
                    },
                    error: function (response) {
                        console.log(response);
                    }
                });
            },
            downloadFile: function (url, taskId) {
                $("body").append("<iframe class='temp-download-frame' id='task-"
                    + taskId + "' style='display:none;' src='" + url + "'></iframe>");
            },
            registerTask: function (task) {
                let vue = this;
                let existingTask = null;

                existingTask = vue.tasks.find(function (t) {
                    return t.id === task.id;
                });

                switch (task.name) {
                    case "bag download":
                        // Check if bag creation is finished
                        if (task.status === "Completed" && task.payload) {
                            const bagUrl = task.payload;
                            vue.downloadFile(bagUrl, task.id);
                        }
                        break;
                    case "zip download":
                        // Check if zip creation is finished
                        if (task.status === "Completed" && task.payload) {
                            const zipUrl = task.payload;
                            vue.downloadFile(zipUrl, task.id);
                        }
                        break;
                    default:
                        break;
                }

                if (existingTask) {
                    // Update existing task
                    existingTask = task;    
                }
                else {
                    // Add new task
                    vue.tasks = [task, ...vue.tasks];
                }
            }
        },
        mounted: function () {
            let vue = this;
            vue.fetchTasks();
        }
    });
});
