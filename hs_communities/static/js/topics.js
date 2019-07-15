let TopicsApp = new Vue({
        el: '#topics-app',
        data: {
            numbers: []
        },
        mounted() {
            // depends on topics.html making topics available by importing from Django namespace via JSON exchange
            // console.log(this.$data.numbers);
            // console.log(topics)
            topics_from_page.forEach(function(topic){
                this.$data.numbers.push({'val': topic, 'edit': false})
            }.bind(this))
        },
        methods:
            {
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
                    // console.log(topic.val[0], topic.val[1]);
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
                            if (response.status == "success") {
                                // console.log(response)
                            } else {
                                console.log("not success", response);
                            }
                        },
                        error: function (response) {
                            console.log(response.responseText);
                        }
                    });
                    // $(ev).ready(function () {
                    //     $.post( "/topics/", { name: "John", time: "2pm" } );
                    //
                    // })
                }
            }
});
