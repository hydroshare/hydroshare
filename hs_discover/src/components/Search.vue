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
          if (response) {
            this.$data.resources = JSON.parse(response.data.resources);
            axios.get('/searchjson/', { params: { data: {} } })
              .then((mapResponse) => {
                if (mapResponse.status === 200) {
                  mapResponse.data.forEach((mapResource) => {
                    const thisRes = JSON.parse(mapResource);
                    if (thisRes.coverage_type === 'point') {
                      console.log(`mapdata: ${thisRes.coverage_type} ${thisRes.north} ${thisRes.east}`);
                      createMarker({ lat: thisRes.north, lng: thisRes.east });
                    }
                  });
                } else {
                  console.log(`Error map API response: ${mapResponse.statusText}`);
                }
              })
              .catch((error) => {
                  console.error(error); // eslint-disable-line
              });
          }
        })
        .catch((error) => {
          console.error(error); // eslint-disable-line
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
