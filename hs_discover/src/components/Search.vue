<template>
    <div id="discover-search">
        <div>
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
    if (document.getElementById('qstring').value.trim() !== '') {
      this.searchtext = document.getElementById('qstring').value.trim();
    }
    this.searchClick();
  },
  methods: {
    searchClick() {
      const startdApiSearch = new Date();
      document.body.style.cursor = 'wait';
      axios.get('/discoverapi/', { params: { q: this.$data.searchtext } })
        .then((response) => {
          if (response) {
            try {
              this.$data.resources = JSON.parse(response.data.resources);
              console.log(`/discoverapi/ call in: ${(new Date() - startdApiSearch) / 1000} sec`);
              document.body.style.cursor = 'default';
            } catch (e) {
              console.log(`Error parsing discoverapi JSON: ${e}`);
              document.body.style.cursor = 'default';
            }
          }
        })
        .catch((error) => {
          console.error(`server /discoverapi/ error: ${error}`); // eslint-disable-line
          document.body.style.cursor = 'default';
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
