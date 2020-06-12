<template>
    <div>
        <p v-if="resources.length">Results: {{resources.length}}</p>
        <div class="table-wrapper">
            <table v-if="resources.length"
                   class="table-hover table-striped resource-custom-table" id="items-discovered">
                <thead>
                    <tr>
                        <th v-for="key in labels" v-bind:key="key"
                            @click="sortBy(key)"
                            :class="{ active: sortKey === key }">
                            {{key}}
                            <span class="arrow" :class="sortOrders[key] >
                            0 ? 'asc' : 'dsc'"></span></th>
                    </tr>
                </thead>
                <tbody>
                <tr v-for="entry in filteredResources" v-bind:key="entry">
                    <td>
                        <img :src="entry.availabilityurl" data-toggle="tooltip"
                             :title="entry.availability" :alt="entry.availability" :key="entry">
                    </td>
                    <td>
                        <a :href="entry.link" data-toggle="tooltip"
                           :title="entry.abstract" data-placement="top">{{entry.name}}</a>
                    </td>
                    <td>
                        <a :href="entry.author_link">{{entry.author}}</a>
                    </td>
                    <td>{{entry.created}}</td>
                    <td>{{entry.modified}}</td>
                </tr>
                </tbody>
            </table>
            <div v-for="(author) in authors" v-bind:key="author">
                <input type="checkbox" :value=author v-model="authorFilter" :id="name-author">
                <label :for="name-author">{{author}}</label>
            </div>
            <br>
            <span>Would filter by author(s): {{ authorFilter }}</span>
        </div>
    </div>
</template>

<script>
export default {
  data() {
    return {
      authorFilter: [],
      sortKey: '',
      sortOrders: { Type: -1, Title: 1, 'First Author': -1 },
    };
  },
  name: 'Resources',
  props:
  ['resources', 'authors', 'columns', 'labels'],
  computed: {
    filteredResources() {
      const { sortKey } = this;
      if (sortKey) {
        // sort by column
      }
      // console.log(this.authors); // eslint-disable-line
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
