<template>
    <div id="discover-search">
        <div class="flex">
            <span id="solr-help-info" class="glyphicon
            glyphicon-info-sign info-popover-glypn
            c-pointer" data-toggle="popover"
            data-placement="bottom" data-original-title="" title="">
            </span>
            <div id="search" class="search-field" @keyup.enter="searchClick()">
<!--                <i class="glyphicon glyphicon-search search-icon"></i>-->
                <input type="search" class="form-control" v-model="searchtext"
                       placeholder="Search all Public and Discoverable Resources">
            </div>
        </div>
        <resource-listing :resources="resources"
                          :key="resources"
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
    this.searchClick();
  },
  methods: {
    searchClick() {
      axios.get('/discoverapi/', { params: { searchtext: this.$data.searchtext } })
        .then((response) => {
          this.$data.resources = JSON.parse(response.data.resources);
        })
        .catch((error) => {
          console.error(error); // eslint-disable-line
        });
    },
  },
};
</script>

<style scoped>
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

    table tr th {
        cursor: pointer;
    }

    div.table-wrapper {
        max-width: 100%;
        overflow: auto;
    }

</style>
