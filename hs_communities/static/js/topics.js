let TopicsApp = new Vue({
    el: '#topics-app',
    data: {
        numbers: [],
        newTopic: ''
    },
    mounted() {
        topics_from_page.forEach(function (topic) {  // defined inline in topics.html
            this.$data.numbers.push({'val': topic, 'edit': false})
        }.bind(this))
    },
    methods: {
        toggleEdit: function (ev, num) {
            Vue.set(num, 'edit', !num.edit);
            this.$data.numbers.forEach(function (item) {
                if (item !== num) {
                    Vue.set(item, 'edit', false)
                }
            })
        },
        saveEdit: function (csrf_token, ev, topic) {
            let formData = new FormData();
            Vue.set(topic, 'edit', false);
            formData.append("csrfmiddlewaretoken", csrf_token);
            formData.append("id", topic.val[0].toString());
            formData.append("name", topic.val[1].toString());
            formData.append("action", "UPDATE");
            $.ajax({
                type: "POST",
                data: formData,
                processData: false,
                contentType: false,
                url: "/topics/",
                success: function (response) {
                    // do nothing
                },
                error: function (response) {
                    console.log(response.responseText);
                }
            });
        },
        addTopic: function(csrf_token) {
            let formData = new FormData();
            formData.append("csrfmiddlewaretoken", csrf_token);
            formData.append("name", this.$data.newTopic);
            formData.append("action", "CREATE");
            $.ajax({
                type: "POST",
                data: formData,
                processData: false,
                contentType: false,
                url: "/topics/",
                success: function () {
                    $("#add-topic").val('');
                    window.location.href = "/topics/";
                },
                error: function (response) {
                    console.log(response.responseText);
                }
            });
        },
        deleteTopic: function(csrf_token, topic_id) {
            let formData = new FormData();
            formData.append("csrfmiddlewaretoken", csrf_token);
            formData.append("id", topic_id);
            formData.append("action", "DELETE");
            $.ajax({
                type: "POST",
                data: formData,
                processData: false,
                contentType: false,
                url: "/topics/",
                success: function () {
                    window.location.href = "/topics/";
                },
                error: function (response) {
                    console.log(response.responseText);
                }
            });
        }
    }
});
