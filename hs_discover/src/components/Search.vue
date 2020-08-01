<template>
    <div id="discover-search">
        <div>
            <div id="search" @keyup.enter="searchClick" class="input-group">
                <input id="search-input" type="search" class="form-control" v-model="searchtext"
                       placeholder="Search all Public and Discoverable Resources">
                <i id="search-clear" style="cursor:pointer" v-on:click="clearSearch"  class="fa fa-times-circle inside"></i>
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
    if (document.getElementById('qstring').value.trim() !== '') {
      this.searchtext = document.getElementById('qstring').value.trim();
    }
    const startd = new Date();
    const geodata = [];
    axios.get('/searchjson/', { params: { data: {} } })
      .then((response) => {
        if (response.status === 200) {
          console.log(`/searchjson/ call in: ${(new Date() - startd) / 1000} sec`);
          response.data.forEach((item) => {
            const val = JSON.parse(item);
            if (val.coverage_type) {
              // TODO if coverage_type box ensure northlimit, southlimit, eastlimit, westlimit are floats or integers
              // TODO if point ensure east north
              geodata.push(val);
            }
          });
          this.geodata = geodata;
        } else {
          console.log(`Error: ${response.statusText}`);
        }
      })
      .catch((error) => {
        console.error(`server /searchjson/ error: ${error}`); // eslint-disable-line
        // this.geoloaded = false;
      });
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
              this.resources = JSON.parse(response.data.resources);
              console.log(`/discoverapi/ call in: ${(new Date() - startdApiSearch) / 1000} sec`);
              this.setAllMarkers();
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
    setAllMarkers() {
      if (document.getElementById('map-view').style.display === 'block' && this.geodata.length > 0) {
        deleteMarkers();
        const shids = this.resources.map(x => x.short_id);
        const geopoints = this.geodata.filter(element => shids.indexOf(element.short_id) > -1);

        const pts = geopoints.filter(x => x.coverage_type === 'point');
        const pointlocs = [];
        pts.forEach((x) => {
          if (!x.north || !x.east) {
            console.log(`Bad geodata ${x.short_id} ${x.north} ${x.east}`);
          }
          const lat = x.north || 0.0;
          const lng = x.east || 0.0;
          pointlocs.push({ lat, lng });
        });
        const pointuids = pts.map(x => x.short_id);
        const pointlbls = pts.map(x => x.title);
        createBatchMarkers(pointlocs, pointuids, pointlbls);
      }
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
