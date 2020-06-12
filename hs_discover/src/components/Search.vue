<template>
    <div id="discover-search">
        <div class="flex">
            <span id="solr-help-info" class="glyphicon
            glyphicon-info-sign info-popover-glypn
            c-pointer" data-toggle="popover"
            data-placement="bottom" data-original-title="" title="">
            </span>
            <div id="search" class="search-field" @keyup.enter="searchClick()">
                <span class="glyphicon glyphicon-search search-icon"></span>
                <span @click="clearSearch()"
                      class="glyphicon glyphicon-remove-sign btn-clear-search c-pointer"></span>
                <input type="search" class="form-control" v-model="searchtext"
                       placeholder="Search all Public and Discoverable Resources">
            </div>
        </div>
        <resource-listing :resources="resources"
                          :key="resources"
                          :authors="authors"
                          :columns="gridColumns"
                          :labels="gridColumnLabels">
        </resource-listing>
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
      authors: [],
      csrf_token: 'abc123',
      searchtext: '',
      gridColumns: ['availability', 'name', 'author', 'created', 'modified'],
      gridColumnLabels: ['Availability', 'Title', 'First Author', 'Date Created', 'Last Modified'],
    };
  },
  components: {
    resourceListing: Resources,
  },
  beforeMount() {
  },
  mounted() {
  },
  methods: {
    searchClick() {
      axios.get('/discoverapi/', { params: { searchtext: this.$data.searchtext } })
        .then((response) => {
          this.$data.resources = JSON.parse(response.data.resources);
          this.$data.authors = JSON.parse(response.data.authors);
          // console.log(this.resources); // eslint-disable-line
        })
        .catch((error) => {
          console.error(error); // eslint-disable-line
        });
    },
    clearSearch() {
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
        max-width: 500px;
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
