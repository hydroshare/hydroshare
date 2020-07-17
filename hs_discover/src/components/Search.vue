<template>
    <div id="discover-search">
        <div>
            <h2 class="page-title">Discover
                <small class="text-muted"><i>Public resources shared with the community</i></small>
            </h2>
            <div id="search" @keyup.enter="searchClick" class="input-group">
                <input type="search" class="form-control" v-model="searchtext"
                       placeholder="Search all Public and Discoverable Resources">
                <i id="search-clear" v-on:click="clearSearch"  class="fa fa-times-circle inside"></i>
            </div>
        </div>
        <resource-listing :resources="resources"
                          :geodata="geodata"
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
      geodata: [],
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
    this.loadGeo();
  },
  methods: {
    searchClick() {
      const startdApiSearch = new Date();
      axios.get('/discoverapi/', { params: { searchtext: this.$data.searchtext } })
        .then((response) => {
          if (response) {
            try {
              this.$data.resources = JSON.parse(response.data.resources);
              console.log(`/discoverapi/ call in: ${(new Date() - startdApiSearch) / 1000} sec`);
            } catch (e) {
              console.log(`Error parsing discoverapi JSON: ${e}`);
            }
          }
        })
        .catch((error) => {
          console.error(`server /discoverapi/ error: ${error}`); // eslint-disable-line
        });
    },
    loadGeo() {
      console.log('loading geo...');
      axios.get('/searchjson/', { params: { data: {} } })
        .then((response) => {
          if (response.status === 200) {
            response.data.forEach((item) => {
              const val = JSON.parse(item);
              if (val.coverage_type) {
                this.$data.geodata.push(val);
              }
            });
          } else {
            console.log(`Error: ${response.statusText}`);
          }
        })
        .catch((error) => {
          console.error(`server /searchjson/ error: ${error}`); // eslint-disable-line
        });
    },
    clearSearch() {
      this.searchtext = '';
      this.searchClick();
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
        z-index: 1;
    }
    .inside {
        position: absolute;
        top: 10px;
        right: 20px;
        z-index: 2;
    }
</style>
