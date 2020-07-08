<template>
    <div class="main-container">
        <link rel="stylesheet" type="text/css" href="/static/css/datepick.css"/>
    <input type="hidden" id="static-url" value="/static/">
    <div class="container" id="discover-main">
        <div class="row">
            <div class="col-xs-12" id="items">
                    <div id="discover-search">
        <div>
            <h2 class="page-title">Discover
                <small class="text-muted"><i>Public resources shared with the community.</i></small>
            </h2>
<!--            <span id="solr-help-info" class="glyphicon-->
<!--            glyphicon-info-sign info-popover-glypn-->
<!--            c-pointer" data-toggle="popover"-->
<!--                  data-placement="bottom" data-original-title="" title="">-->
<!--            </span>-->
            <div id="search" @keyup.enter="searchClick()">
                <input type="search" class="form-control" v-model="searchtext"
                       placeholder="Search all Public and Discoverable Resources">
<!--                <i class="fa fa-search" aria-hidden="true"></i>-->
            </div>

        </div>
        <table cellpadding='20'>
            <tr>
                <td>
                    &nbsp;
                </td>
                <td>
                    &nbsp;
                </td>
            </tr>
        </table>
        <resource-listing :resources="resources"
                          :key="resources"
                          :columns="gridColumns"
                          :labels="gridColumnLabels">
        </resource-listing>
    </div>
            </div>
        </div>
    </div>

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
