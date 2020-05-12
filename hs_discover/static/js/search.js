let DiscoverApp = new Vue({
    delimiters: ['${', '}'],
    el: '#discover-search',
    data: {
        searchQuery: '',
        gridColumns: ['type', 'name', 'author', 'created', 'modified'],
        gridColumnLabels: ['Type', 'Title', 'First Author', 'Date Created', 'Last Modified'],
        q: ''
    },
    components: {
        VueBootstrapTypeahead
    },
    beforeMount: function() {
        this.$data.searchQuery = q;
        this.$data.q = q;
    },
    mounted: function() {
        this.$refs.searchQuery.inputValue = this.searchQuery;
    },
    methods: {
        searchClick: function (csrf_token) {
            window.location="/search/?q="+this.$data.searchQuery  // TODO validation or complete refactor anyway
            // console.log(this)
            // let formData = new FormData();
            // formData.append("csrfmiddlewaretoken", csrf_token);
            // formData.append("q", this.searchQuery);
            // $.ajax({
            //     type: "POST",
            //     data: formData,
            //     processData: false,
            //     contentType: false,
            //     url: "/search/",
            //     success: function (response) {
            //         console.log("Successful post")
            //     },
            //     error: function (response) {
            //         console.log(response.responseText);
            //     }
            // });
        },
        clearSearch: function () {
            this.searchQuery = '';
            this.$refs.searchQuery.inputValue = '';
        }
    }
});