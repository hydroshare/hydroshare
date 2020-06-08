<template>
    <div id="discover-search">
    <div class="flex">
        <span id="solr-help-info" class="glyphicon glyphicon-info-sign info-popover-glypn c-pointer"
              data-toggle="popover" data-placement="bottom" data-original-title="" title="">
        </span>
        <div id="discover-resource-search" class="resource-search">
            <div class="fieldWrapper">
                <span class="glyphicon glyphicon-search search-icon"></span>
                <input type="search" class="form-control" v-model="searchtext"
                       placeholder="Search All Public and Discoverable Resources">
            </div>
        </div>
    </div>
<!--    <div id="discover-search">-->
<!--        <div id="wrapper">-->
<!--            <div id="search" class="search-field" @keyup.enter="searchClick()">-->
<!--                <span class="glyphicon glyphicon-search search-icon"></span>-->
<!--                <span @click="clearSearch()"-->
<!--                      class="glyphicon
 glyphicon-remove-sign btn-clear-search c-pointer"></span>-->
<!--                <input v-model="searchtext"-->
<!--                       placeholder="Search all Public and Discoverable Resources">-->
<!--            </div>-->
<!--        </div>-->
<!--        <div v-if="searchtext">-->
        <resource-listing :resources="resources"
                          :key="resources"
                          :itemcount="55"
                          :columns="gridColumns"
                          :labels="gridColumnLabels"
                          :filter-key="searchQuery">
         </resource-listing>
<!--        </div>-->
    </div>
</template>

<script>
import axios from 'axios';
import Resources from './Resources.vue';

export default {
  name: 'Search',
  data() {
    return {
      resources: [],
      csrf_token: 'abc123',
      searchtext: '',
      searchQuery: '',
      gridColumns: ['type', 'name', 'author', 'created', 'modified'],
      gridColumnLabels: ['Type', 'Title', 'First Author', 'Date Created', 'Last Modified'],
    };
  },
  components: {
    resourceListing: Resources,
  },
  beforeMount() {
    // this.$data.searchQuery = this.searchtext;
    // this.$data.q = this.searchtext;
  },
  mounted() {
    // axios.get('/discoverapi/', { params: { searchtext: this.$data.searchtext } })
    //   .then((response) => {
    //     console.log(response);
    //   })
    //   .catch((error) => {
    //     console.error(error);
    //   });
    // this.$refs.searchQuery.inputValue = this.searchQuery;
  },
  methods: {
    searchClick() {
      axios.get('/discoverapi/', { params: { searchtext: this.$data.searchtext } })
        .then((response) => {
          this.$data.resources = response.data.resources;
          console.log(response);
        })
        .catch((error) => {
          console.error(error);
        });

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
    clearSearch() {
      // this.searchQuery = '';
      // this.$refs.searchQuery.inputValue = '';
    },
  },
};
</script>

<style scoped>
    /*<link rel="stylesheet" type="text/css" href="{{ STATIC_URL }}css/search.css"/>*/
    #wrapper {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        margin-bottom: 2em;
    }

    #wrapper .search-field, #advanced-discover-search {
        flex-grow: 1;
        max-width: 800px;
        position: relative;
    }

    #wrapper .search-field div {
        width: 100%;
    }

    #wrapper > a {
        margin-left: 1em;
    }

    #search input {
        width: 100%;
        padding-left: 25px;
        padding-right: 25px;
    }

    #items-discovered {
        margin-top: 1em;
    }

    #advanced-search-items {
        margin-top: 1em;
        max-width: 600px;
    }

    table tr th {
        cursor: pointer;
    }

    div.table-wrapper {
        max-width: 100%;
        overflow: auto;
    }

    .btn-clear-search {
        /*position: absolute;*/
        top: 10px;
        right: 8px;
    }
</style>
