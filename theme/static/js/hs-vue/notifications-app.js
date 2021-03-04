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
                        "progress": "Getting your files ready for download...",
                        "aborted": "Aborted",
                        "failed": "Download failed",
                        "delivered": "Download delivered"
                    }
                },
                "file unzip": {
                    title: "File Unzipping",
                    status: {
                        "progress": "Unzipping your file...",
                        "completed": "Completed",
                        "failed": "Unzip failed",
                        "delivered": "Unzipping completed"
                    }
                },
                "zip download": {
                    title: "File download",
                    status: {
                        "progress": "Getting your files ready for download...",
                        "aborted": "Aborted",
                        "failed": "Download failed",
                        "delivered": "Download delivered"
                    }
                },
                "resource copy": {
                    title: "Resource copy",
                    status: {
                        "progress": "In progress...",
                        "aborted": "Aborted",
                        "completed": "Completed",
                        "failed": "Failed",
                        "delivered": "Delivered"
                    }
                },
                "resource version": {
                    title: "Resource versioning",
                    status: {
                        "progress": "In progress...",
                        "completed": "Completed",
                        "failed": "Failed",
                        "delivered": "Delivered"
                    }
                },
                "resource copy to user zone": {
                    title: "Resource copy to user zone",
                    status: {
                        "progress": "In progress...",
                        "aborted": "Aborted",
                        "completed": "Completed",
                        "failed": "Failed",
                        "delivered": "Delivered"
                    }
                },
                "resource delete": {
                    title: "Resource delete",
                    status: {
                        "progress": "In progress...",
                        "completed": "Completed",
                        "failed": "Failed",
                        "delivered": "Delivered"
                    }
                }
            },
            statusIcons: {
                "aborted": "glyphicon glyphicon-ban-circle",
                "failed": "glyphicon glyphicon-remove-sign",
                "completed": "glyphicon glyphicon-ok-sign",
                "progress": "fa fa-spinner fa-pulse fa-2x fa-fw icon-blue",
                "delivered": "glyphicon glyphicon-ok-sign"
            }
        },
        computed: {
            someInProgress: function () {
                return this.tasks.find(function (task) {
                    return task.status === "progress";
                });
            }
        },
        methods: {
            // Shows the tasks dropdown
            show: function () {
                $('#notifications-dropdown').addClass('open');
            },
            getUpdatedTask: function(in_task) {
                return this.tasks.find(function(task) {
                    return task.id === in_task.id
                });
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
                        vue.scheduleCheck();
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
                return task.status === 'completed'
                    || task.status === 'failed'
                    || task.status === 'aborted'
                    || task.status === 'delivered'
            },
            deliverTask: function(task) {
                let vue = this;
                if (vue.canBeDelivered(task)) {
                    $.ajax({
                        type: "GET",
                        url: '/hsapi/_internal/set_task_delivered/' + task.id,
                        success: function (task) {
                        },
                        error: function (response) {
                            console.log(response);
                        }
                    });
                }
            },
            canBeDelivered: function (task) {
                return task.status === 'completed'
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
                let vue = this;
                return "aborted" in vue.taskMessages[task.name].status && (task.status === 'progress')
            },
            clear: function () {
                let vue = this;
                vue.tasks = vue.tasks.filter(function(task) {
                    if (vue.canBeDismissed(task))
                        vue.dismissTask(task);
                    return !vue.canBeDismissed(task);
                });
            },
            scheduleCheck: function() {
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
                        return task.status === "progress";
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
            checkTaskStatus: function(task) {
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
                        if (task.status === "completed" && task.payload) {
                            const bagUrl = task.payload;
                            vue.downloadFile(bagUrl, task.id);
                            vue.deliverTask(task);
                        }
                        break;
                    case "zip download":
                        // Check if zip creation is finished
                        if (task.status === "completed" && task.payload) {
                            const zipUrl = task.payload;
                            vue.downloadFile(zipUrl, task.id);
                            vue.deliverTask(task);
                        }
                        break;
                    case "resource copy":
                        if (task.status === "completed" && task.payload) {
                            vue.deliverTask(task);
                        }
                        break;
                    case "resource version":
                        if (task.status === "completed" && task.payload) {
                            vue.deliverTask(task);
                        }
                        break;
                    case "resource copy to user zone":
                        if (task.status === "completed") {
                            vue.deliverTask(task);
                        }
                        break;
                    case "resource delete":
                        if (task.status === "completed" && task.payload) {
                            vue.deliverTask(task);
                        }
                        break;
                    case "file unzip":
                        if (task.status === "completed" && task.payload) {
                            vue.deliverTask(task);
                        }
                        break;
                    default:
                        break;
                }
                if (task.status === 'progress')
                    vue.scheduleCheck();
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
                        if (task.status !== 'delivered')
                            vue.processTask(targetTask);
                    }
                }
                else {
                    // Add new task
                    targetTask = task;
                    vue.tasks = [targetTask, ...vue.tasks];
                    if (task.status !== 'delivered')
                        vue.processTask(targetTask);
                }
            },
            // Used to know when a task should inform users of alternative way to download their files
            canNotifyDownload: function (task) {
                return task.status === 'completed'
                    && (task.name === 'bag download' || task.name === 'zip download')
            }
        },
        mounted: function () {
            let vue = this;
            vue.fetchTasks();
        }
    });
});