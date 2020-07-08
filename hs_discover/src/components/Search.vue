<template>
    <div id="discover-search">
        <div>
            <h2 class="page-title">Discover
                <small class="text-muted"><i>Public resources shared with the community</i></small>
            </h2>
            <div id="search" @keyup.enter="searchClick()">
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
      gridColumns: ['type', 'name', 'author', 'created', 'modified'],
      gridColumnLabels: ['Type', 'Title', 'First Author', 'Date Created', 'Last Modified'],
    };
  },
  components: {
    resourceListing: Resources,
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

</style>
