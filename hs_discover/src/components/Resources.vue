<template>
    <div>
        <p v-if="filteredResources.length">Results: {{filteredResources.length}}</p>
        <div class="table-wrapper">
            <table v-if="filteredResources.length"
                   class="table-hover table-striped resource-custom-table" id="items-discovered">
                <thead>
                <tr>
                    <th v-for="key in labels"
                        @click="sortBy(key)"
                        :class="{ active: sortKey == key }">
                        {{key}}
                        <span class="arrow" :class="sortOrders[key] > 0 ? 'asc' : 'dsc'"></span>
                    </th>
                </tr>
                </thead>
                <tbody>
                <tr v-for="entry in filteredResources">
                    <td>
                        <span>
                            <img v-bind:src="blank.jpg"
                                 data-toggle="tooltip" data-placement="right"
                                 :alt="entry.type" :title="entry.type"
                                 class="table-res-type-icon"/>
                        </span>

                        <img v-if="entry.availability.indexOf('published') >= 0"
                             src="blank.jpg"
                             data-toggle="tooltip" data-placement="right"
                             alt="Published Resource" title="Published"/>
                        <img v-else-if="entry.availability.indexOf('public') >= 0"
                             src="blank.jpg"
                             data-toggle="tooltip" data-placement="right"
                             alt="Public Resource" title="Public"/>
                        <img v-else-if="entry.availability.indexOf('discoverable') >= 0"
                             src="blank.jpg"
                             data-toggle="tooltip" data-placement="right"
                             alt="Discoverable Resource" title="Discoverable"/>
                        <img v-else="entry.availability.indexOf('private') >= 0"
                             src="blank.jpg"
                             data-toggle="tooltip" data-placement="right"
                             alt="Private Resource" title="Private"/>

                    </td>
                    <td>
                        <a :href="entry.link" data-toggle="tooltip"
                           :title="entry.abstract" data-placement="top">{{entry.name}}</a>
                    </td>
                    <!-- placeholder for link column -->
                    <td>
                        <!-- <a :href="entry.author_link">{{entry.author}}</a>-->
                        author
                    </td>
                    <!-- temporary placeholder for link column -->
                    <td>created</td>
                    <td>modified</td>
                </tr>
                </tbody>
            </table>
            <p v-else>No results found.</p>
        </div>
    </div>
</template>

<script>
export default {
  data() {
    return {
      a: [],
      sortKey: '',
      resTypeDict: {
        'Composite Resource': 'composite',
        Generic: 'generic',
        'Geopgraphic Raster': 'geographicraster',
        'Model Program Resource': 'modelprogram',
        'Collection Resource': 'collection',
        'Web App Resource': 'webapp',
        'Time Series': 'timeseries',
        'Model Instance Resource': 'modelinstance',
        'SWAT Model Instance Resource': 'swat',
        'MODFLOW Model Instance Resource': 'modflow',
        'Multidimensional (NetCDF)': 'multidimensional',
      },
    };
  },
  name: 'Resources', // delimiters: ['${', '}'],
  props:
            ['sample', 'itemcount', 'columns', 'labels', 'resources', 'filterKey'],
  computed: {
    filteredResources() {
      const vue = this;
      const { sortKey } = this;
      const order = this.sortOrders[sortKey] || 1;
      let resources = JSON.parse(this.sample); // TODO validation, security, error handling

      if (sortKey) {
        resources = resources.slice().sort((a, b) => {
          a = a[sortKey];
          b = b[sortKey];
          return (a === b ? 0 : a > b ? 1 : -1) * order;
        });
      }
      console.log(resources);
      vue.numItems = resources.length;
      return resources;
    },
  },
  filters: {
    capitalize(str) {
      if (str !== 'link' && str !== 'author_link') {
        // TODO instead of iterating through headings, explicitly choose and display
        return str.charAt(0).toUpperCase() + str.slice(1);
      }
    },
    date(date) {
      return date;
    },
  },
  methods: {
    sortBy(key) {
      this.sortKey = key;
      this.sortOrders[key] = this.sortOrders[key] * -1;
    },
  },
};
</script>

<style scoped>

</style>
