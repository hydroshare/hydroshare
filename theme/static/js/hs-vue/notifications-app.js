var notificationsApp;

// Vue.component('notification', {
//     delimiters: ['${', '}'],
//     template: '#notification',
//     props: {
//         title: { type: Object, required: true },
//         status: { type: Boolean, required: true },
//     },
//     data: function () {
//         return {}
//     },
// });

$(document).ready(function () {
    const checkDelay = 1000; // ms

    $('#notifications-dropdown').on('show.bs.dropdown', function () {
        notificationsApp.fetchTasks();
    });

    notificationsApp = new Vue({
        el: '#app-notifications',
        delimiters: ['${', '}'],
        data: {
            tasks: [],
            loading: true,
            isCheckingStatus: false,
            taskMessages: {
                "bag download": {
                    title: "Download all content as Zipped BagIt Archive",
                    status: {
                        "Pending execution": "Pending...",
                        "In progress": "Getting your files ready for download...",
                        "Aborted": "Aborted",
                        "Failed": "Download failed"
                    }
                },
                "zip download": {
                    title: "File download",
                    status: {
                        "Pending execution": "Pending...",
                        "In progress": "Getting your files ready for download...",
                        "Aborted": "Aborted",
                        "Failed": "Download failed"
                    }
                }
            },
            statusIcons: {
                "Aborted": "glyphicon glyphicon-ban-circle",
                "Failed": "glyphicon glyphicon-remove-sign",
                "Completed": "glyphicon glyphicon-ok-sign",
                "Pending execution": "fa fa-spinner fa-pulse fa-2x fa-fw icon-blue",
                "In progress": "fa fa-spinner fa-pulse fa-2x fa-fw icon-blue"
            }
        },
        computed: {
            someInProgress: function () {
                return this.tasks.find(function (task) {
                    return task.status === "In progress" || task.status === "Pending execution";
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
                    success: function (ret_data) {
                        vue.loading = false;
                        tasks = ret_data['tasks']
                        for (let i = 0; i < tasks.length; i++) {
                            vue.registerTask(tasks[i]);
                        }
                    },
                    error: function (response) {
                        console.log(response);
                        vue.loading = false;
                    }
                });
            },
            dismissTask: function (task) {
                let vue = this;
                if (vue.canBeDismissed(task)) {
                    $.ajax({
                        type: "GET",
                        url: '/hsapi/_internal/dismiss_task/' + task.id,
                        success: function (task) {
                            vue.tasks = vue.tasks.filter(function(t) {
                                return t.id !== task.id;
                            });
                        },
                        error: function (response) {
                            console.log(response);
                        }
                    });
                }
            },
            canBeDismissed: function (task) {
                return task.status === 'Completed'
                    || task.status === 'Failed'
                    || task.status === 'Aborted'
            },
            abortTask: function(task) {
                let vue = this;
                if (vue.canBeAborted(task)) {
                    $.ajax({
                        type: "GET",
                        url: '/hsapi/_internal/abort_task/' + task.id,
                        success: function (task) {
                            vue.registerTask(task);
                        },
                        error: function (response) {
                            console.log(response);
                        }
                    });
                }
            },
            canBeAborted: function (task) {
                return task.status === 'In progress'
                    || task.status === 'Pending execution'
            },
            clear: function () {
                let vue = this;
                vue.tasks = vue.tasks.filter(function(task) {
                    return !vue.canBeDismissed(task);
                });
            },
            scheduleCheck() {
                let vue = this;
                if (vue.someInProgress && !vue.isCheckingStatus) {
                    vue.isCheckingStatus = true;

                    // check in 1s
                    setTimeout(function() {
                        vue.checkStatus();
                    }, checkDelay);
                }
                else {
                    vue.isCheckingStatus = false;
                }
            },
            // Checks every 1s for every task in progress
            checkStatus: function () {
                let vue = this;

                if (vue.someInProgress) {
                    const tasksInProgress = vue.tasks.filter(function (task) {
                        return task.status === "In progress" || task.status === "Pending execution";
                    });

                    let calls = tasksInProgress.map(function (task) {
                        return vue.checkTaskStatus(task);
                    });

                    // wait for all of task checks to finish and recall self after 1s
                    $.when.apply($, calls).done(function () {
                        setTimeout(function() {
                            vue.checkStatus();
                        }, checkDelay);
                    });
                }
                else {
                    vue.isCheckingStatus = false;
                }
            },
            checkTaskStatus(task) {
                let vue = this;
                
                return $.ajax({
                    type: "GET",
                    url: '/hsapi/_internal/get_task/' + task.id,
                    success: function (task) {
                        vue.registerTask(task);
                    },
                    error: function (response) {
                        console.log(response);
                    }
                });
            },
            downloadFile: function (url, taskId) {
                // Remove previous temporary download frames
                $(".temp-download-frame").remove();

                $("body").append("<iframe class='temp-download-frame' id='task-"
                    + taskId + "' style='display:none;' src='" + url + "'></iframe>");
            },
            processTask: function (task) {
                let vue = this;
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

                switch (task.status) {
                    case "Pending execution":
                        vue.scheduleCheck();
                        break;
                    case "In progress":
                        vue.scheduleCheck();
                        break;
                }
            },
            registerTask: function (task) {
                let vue = this;
                let targetTask = null;

                // Minor type checking
                if (!task.hasOwnProperty('id') || !task.hasOwnProperty('name')) {
                    return  // Object passed is not a task
                }

                targetTask = vue.tasks.find(function (t) {
                    return t.id === task.id;
                });

                if (targetTask) {
                    // Update existing task only if values have changed to avoid Vue change detection
                    if (task.status !== targetTask.status || task.payload !== targetTask.payload) {
                        targetTask.status = task.status;
                        targetTask.payload = task.payload;
                        vue.processTask(targetTask);
                    }
                }
                else {
                    // Add new task
                    targetTask = task;
                    vue.tasks = [targetTask, ...vue.tasks];
                    vue.processTask(targetTask);
                }
            },
            // Used to know when a task should inform users of alternative way to download their files
            canNotifyDownload: function (task) {
                return task.status === 'Completed'
                    && (task.name === 'bag download' || task.name === 'zip download')
            }
        },
        mounted: function () {
            let vue = this;
            vue.fetchTasks();
        }
    });
});