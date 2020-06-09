<template>
    <div v-if="resources.length">
        <p>Results: {{resources.length}}</p>
        <div class="table-wrapper">
            <table
                   class="table-hover table-striped resource-custom-table" id="items-discovered">
                <thead>
                    <tr>
                        <th v-for="key in labels" v-bind:key="key">
                            {{key}}
                        </th>
    <!--                    <th v-for="key in labels" v-bind:key="key"-->
    <!--                        @click="sortBy(key)"-->
    <!--                        :class="{ active: sortKey === key }">-->
    <!--                        {{key}}-->
    <!--                        <span class="arrow" :class="sortOrders[key]>
     0 ? 'asc' : 'dsc'"></span>-->
                    </tr>
                </thead>
                <tbody>
                <tr v-for="entry in resources" v-bind:key="entry">
                    <td>
                        <span>[type image]
<!--                            <img v-bind:src="blank.jpg"-->
<!--                                 data-toggle="tooltip" data-placement="right"-->
<!--                                 :alt="entry.type" :title="entry.type"-->
<!--                                 class="table-res-type-icon"/>-->
                        </span>
<!--                        <img v-if="entry.availability.indexOf('published') >= 0"-->
<!--                             src="blank.jpg"-->
<!--                             data-toggle="tooltip" data-placement="right"-->
<!--                             alt="Published Resource" title="Published"/>-->
<!--                        <img v-else-if="entry.availability.indexOf('public') >= 0"-->
<!--                             src="blank.jpg"-->
<!--                             data-toggle="tooltip" data-placement="right"-->
<!--                             alt="Public Resource" title="Public"/>-->
<!--                        <img v-else-if="entry.availability.indexOf('discoverable') >= 0"-->
<!--                             src="blank.jpg"-->
<!--                             data-toggle="tooltip" data-placement="right"-->
<!--                             alt="Discoverable Resource" title="Discoverable"/>-->
<!--                        <img v-else-if="entry.availability.indexOf('private') >= 0"-->
<!--                             src="blank.jpg"-->
<!--                             data-toggle="tooltip" data-placement="right"-->
<!--                             alt="Private Resource" title="Private"/>-->
                    </td>
                    <td>
                        <a :href="entry.link" data-toggle="tooltip"
                           :title="entry.abstract" data-placement="top">{{entry.name}}</a>
                    </td>
                    <!-- placeholder for link column -->
                    <td>
                         <a :href="entry.author_link">{{entry.author}}</a>
                    </td>
                    <!-- temporary placeholder for link column -->
                    <td>{{entry.created}}</td>
                    <td>{{entry.modified}}</td>
                </tr>
                </tbody>
            </table>
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
  name: 'Resources',
  props:
  ['resources', 'columns', 'labels', 'filterKey'],
  computed: {
    filteredResources() {
      // const vue = this;
      // const { sortKey } = this;
      // const order = this.sortOrders[sortKey] || 1;
      // let resources = JSON.parse(this.sample);
      // if (sortKey) {
      //   resources = resources.slice().sort((a, b) => {
      //     a = a[sortKey];
      //     b = b[sortKey];
      //     return (a === b ? 0 : a > b ? 1 : -1) * order;
      //   });
      // }
      console.log(this.resources); // eslint-disable-line
      // vue.numItems = resources.length;
      return this.resources;
    },
  },
  // filters: {
  //   capitalize(str) {
  //     if (str !== 'link' && str !== 'author_link') {
  //       return str.charAt(0).toUpperCase() + str.slice(1);
  //     }
  //   },
  //   date(date) {
  //     return date;
  //   },
  // },
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
